"""Verify trusted output bytes directly from a downloaded Actions ZIP.

No extracted copies are needed for a reuse decision. The archive is still
downloaded and SHA-verified by the existing authenticated transport.
"""
from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePosixPath
import stat
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from download_actions_artifact import download
from inspect_actions_artifact_metadata import inspect
from verify_actions_artifact import SHA256

MAX_PAYLOAD = 1024**3
MAX_FILES = 10000


def checked_files(manifest, expected_contract):
    if (not isinstance(manifest, dict) or not isinstance(expected_contract, str)
            or not expected_contract or manifest.get("output_contract") != expected_contract):
        raise ValueError("output contract mismatch")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files or len(files) > MAX_FILES:
        raise ValueError("invalid manifest inventory")
    for name, digest in files.items():
        if (not isinstance(name, str) or not name or "\\" in name or "\x00" in name
                or PurePosixPath(name).is_absolute()
                or any(part in ("", ".", "..") for part in name.split("/"))):
            raise ValueError("invalid manifest path")
        if not isinstance(digest, str) or SHA256.fullmatch(digest) is None:
            raise ValueError("invalid SHA256 digest")
    return files


def verify_zip(archive, manifest, expected_contract):
    files = checked_files(manifest, expected_contract)
    with ZipFile(archive) as zipped:
        members = {}
        for info in zipped.infolist():
            if info.filename in members:
                raise ValueError("duplicate ZIP entry")
            members[info.filename] = info
        total = 0
        for name in files:
            if name not in members:
                raise ValueError("missing ZIP entry: " + name)
            member = members[name]
            kind = stat.S_IFMT(member.external_attr >> 16)
            total += member.file_size
            if (member.is_dir() or kind not in (0, stat.S_IFREG)
                    or member.file_size < 0 or total > MAX_PAYLOAD):
                raise ValueError("invalid or excessive native payload")
        # Validate the entire selected inventory before decompressing any payload.
        for name, expected in files.items():
            member = members[name]
            digest = hashlib.sha256()
            count = 0
            with zipped.open(member) as src:
                for block in iter(lambda: src.read(1024 * 1024), b""):
                    count += len(block)
                    if count > member.file_size:
                        raise ValueError("ZIP payload length mismatch")
                    digest.update(block)
            if count != member.file_size or digest.hexdigest() != expected:
                raise ValueError("artifact SHA256 mismatch: " + name)
    return True


def verify_reuse(repo, token, artifact, run, expected_contract):
    manifest = artifact["manifest"]
    checked_files(manifest, expected_contract)
    if not isinstance(artifact.get("zip_sha256"), str) or SHA256.fullmatch(artifact["zip_sha256"]) is None:
        raise ValueError("expected ZIP SHA-256 required")
    metadata = inspect(repo, run["run_id"], artifact["artifact_name"], token)
    if (metadata["head_sha"] != run["head_sha"]
            or metadata["head_branch"] != run["head_branch"]
            or metadata["artifact_id"] != artifact["artifact_id"]):
        return False
    expires_at = datetime.fromisoformat(metadata["expires_at"].replace("Z", "+00:00"))
    if expires_at <= datetime.now(timezone.utc):
        return False
    with TemporaryDirectory() as directory:
        archive = Path(directory) / "artifact.zip"
        download(repo, metadata["artifact_id"], token, archive, artifact["zip_sha256"])
        return (verify_zip(archive, manifest, expected_contract)
                and expires_at > datetime.now(timezone.utc))
