"""Durable checkpoint callback and independent restore for the shared controller.

Run from a Git object store. Only an approved existing private remote or a
disposable Git remote should be supplied by the owning integration.
"""
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
from tempfile import TemporaryDirectory, TemporaryFile
import time

from shared_asset_lease import assert_owned, checkpoint_ref, git, publish_checkpoint
from shared_blueprint_contract import matches_digest
from shared_session_contract import asset_key


LEDGER = "ledger.json"
GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")


def files_for(records):
    if not isinstance(records, dict):
        raise ValueError("invalid checkpoint ledger")
    files = {}
    for entry in records.values():
        if not isinstance(entry, dict) or entry.get("reopened") is not True:
            raise ValueError("checkpoint must be independently reopened")
        evidence = entry.get("files", {})
        if not isinstance(evidence, dict):
            raise ValueError("invalid checkpoint evidence")
        for path, digest in [*evidence.items(), (entry.get("path"), entry.get("sha256"))]:
            if (not isinstance(path, str) or not path or not matches_digest(digest)
                    or PurePosixPath(path).is_absolute() or "\\" in path
                    or any(part in ("", ".", "..", ".git") for part in path.split("/"))
                    or any(character in path for character in "\r\n\t\0")
                    or path == LEDGER or path.startswith(("ledger.json/", "quarantine/"))
                    or path in files and files[path] != digest):
                raise ValueError("invalid or conflicting checkpoint file")
            files[path] = digest
    return files


def sha_stream(stream, deadline):
    digest = hashlib.sha256()
    while block := stream.read(1024 * 1024):
        if time.monotonic() >= deadline:
            raise TimeoutError("checkpoint verification deadline exhausted")
        digest.update(block)
    return digest.hexdigest()


def read_blob(object_name, output, deadline):
    timeout = deadline - time.monotonic()
    if timeout <= 0:
        raise TimeoutError("checkpoint restore deadline exhausted")
    subprocess.run(["git", "cat-file", "blob", object_name], check=True, stdout=output, timeout=timeout)


class GitCheckpointStore:
    def __init__(self, remote, asset, root, previous=None):
        if previous is not None and (not isinstance(previous, str) or not GIT_SHA.fullmatch(previous)):
            raise ValueError("previous checkpoint revision SHA required")
        self.remote = remote
        self.asset = asset_key(asset)
        self.root = Path(root).resolve()
        self.previous = previous

    def __call__(self, records, token, deadline):
        files = files_for(records)
        assert_owned(self.remote, self.asset, token, deadline=deadline)
        if self.previous is not None:
            ref = checkpoint_ref(self.asset)
            if git("ls-remote", "--refs", self.remote, ref, deadline=deadline) != f"{self.previous}\t{ref}":
                raise RuntimeError("checkpoint changed since restore")
            persisted = json.loads(git("show", f"{self.previous}:{LEDGER}", deadline=deadline))
            if persisted == records:
                return token
        if not records and self.previous is None:
            return token

        with TemporaryDirectory() as directory:
            ledger = Path(directory) / LEDGER
            ledger.write_text(json.dumps(records, sort_keys=True, allow_nan=False) + "\n")
            entries = [(LEDGER, git("hash-object", "-w", "--no-filters", str(ledger), deadline=deadline))]
            for name, expected in files.items():
                path = (self.root / name).resolve()
                if not path.is_relative_to(self.root) or not path.is_file():
                    raise ValueError(f"checkpoint file is missing or escapes root: {name}")
                blob = git("hash-object", "-w", "--no-filters", str(path), deadline=deadline)
                with TemporaryFile() as captured:
                    read_blob(blob, captured, deadline)
                    captured.seek(0)
                    if sha_stream(captured, deadline) != expected:
                        raise ValueError(f"checkpoint file SHA mismatch: {name}")
                entries.append((name, blob))
            index = Path(directory) / "git-index"
            update = "".join(f"100644 {blob}\t{name}\n" for name, blob in entries)
            env = {**os.environ, "GIT_INDEX_FILE": str(index)}
            for args, data in ((["update-index", "--index-info"], update), (["write-tree"], None)):
                timeout = deadline - time.monotonic()
                if timeout <= 0:
                    raise TimeoutError("checkpoint tree deadline exhausted")
                process = subprocess.run(["git", *args], input=data, text=True, capture_output=True,
                                         env=env, check=True, timeout=timeout)
            tree = process.stdout.strip()
        parent = ["-p", self.previous] if self.previous else []
        revision = git("commit-tree", tree, *parent, "-m", f"Verified {self.asset} checkpoint", deadline=deadline)
        successor = publish_checkpoint(self.remote, self.asset, token, revision, self.previous, deadline=deadline)
        self.previous = revision
        return successor


def restore_checkpoint(remote, asset, revision, destination, deadline):
    """Fetch the pinned latest checkpoint into a previously unused directory."""
    if not isinstance(revision, str) or not GIT_SHA.fullmatch(revision):
        raise ValueError("checkpoint revision SHA required")
    destination = Path(destination).absolute()
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    git("fetch", "--no-tags", remote, checkpoint_ref(asset_key(asset)), deadline=deadline)
    if git("rev-parse", "FETCH_HEAD", deadline=deadline) != revision:
        raise RuntimeError("remote checkpoint does not match the requested revision")
    raw = git("show", f"{revision}:{LEDGER}", deadline=deadline)
    records = json.loads(raw)
    files = files_for(records)
    with TemporaryDirectory(dir=destination.parent) as directory:
        stage = Path(directory) / "verified"
        stage.mkdir()
        for name, expected in files.items():
            path = stage / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x+b") as output:
                read_blob(f"{revision}:{name}", output, deadline)
                output.seek(0)
                if sha_stream(output, deadline) != expected:
                    raise ValueError(f"restored file SHA mismatch: {name}")
        (stage / LEDGER).write_text(raw + "\n")
        stage.rename(destination)
    return records
