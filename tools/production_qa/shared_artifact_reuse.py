"""Verify a trusted output manifest against the specified Actions artifact."""
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import shutil
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from download_actions_artifact import download
from inspect_actions_artifact_metadata import inspect
from verify_actions_artifact import verify


def verify_reuse(repo, token, artifact, run, expected_contract):
    metadata = inspect(repo, run["run_id"], artifact["artifact_name"], token)
    if (metadata["head_sha"] != run["head_sha"]
            or metadata["head_branch"] != run["head_branch"]
            or metadata["artifact_id"] != artifact["artifact_id"]):
        return False
    expires_at = datetime.fromisoformat(metadata["expires_at"].replace("Z", "+00:00"))
    if expires_at <= datetime.now(timezone.utc):
        return False
    manifest = artifact["manifest"]
    with TemporaryDirectory() as directory:
        root = Path(directory)
        archive = root / "artifact.zip"
        download(repo, metadata["artifact_id"], token, archive, artifact["zip_sha256"])
        files = root / "verified"
        files.mkdir()
        with ZipFile(archive) as zipped:
            members = {}
            for info in zipped.infolist():
                if info.filename in members:
                    raise ValueError("duplicate ZIP entry")
                members[info.filename] = info
            total = 0
            for name in manifest["files"]:
                path = PurePosixPath(name)
                if path.is_absolute() or "\\" in name or any(
                    part in ("", ".", "..") for part in name.split("/")
                ):
                    raise ValueError("invalid manifest path")
                member = members[name]
                total += member.file_size
                if member.is_dir() or total > 1024**3:
                    raise ValueError("invalid or excessive native payload")
                output = files.joinpath(*path.parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                with zipped.open(member) as src, output.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
        report = verify(files, manifest, expected_contract)
        return (report["local_sha256_verified"] is True
                and expires_at > datetime.now(timezone.utc))
