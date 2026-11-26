"""Candidate adapter for the existing Git CAS lease; no live writer takeover."""
import json
import os
import re
import time
import uuid

from shared_asset_lease import git, ref_for, assert_owned, release


def binding(asset, revision, request, run=None, attempt=None):
    ref_for(asset)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("revision SHA required")
    if not re.fullmatch(r"[1-9][0-9]{0,19}", request):
        raise ValueError("request ID required")
    if run is not None:
        if not re.fullmatch(r"[1-9][0-9]{0,19}", run) or attempt != "1":
            raise ValueError("first-attempt run ID required")
    elif attempt is not None:
        raise ValueError("attempt without run")
    return dict(schema="morwen-transfer-v1", asset=asset, revision=revision,
                request=request, run=run, attempt=attempt)


def read_binding(remote, asset, token, expected, deadline, reservation=None):
    ref = ref_for(asset)
    cwd = os.environ.get("MORWEN_TRANSFER_GIT_DIR") or None
    if cwd is not None:
        if git("rev-parse", "HEAD", deadline=deadline, cwd=cwd) != expected["revision"]:
            raise RuntimeError("transfer checkout revision mismatch")
    assert_owned(remote, asset, token, deadline=deadline, cwd=cwd)
    shallow = git("rev-parse", "--is-shallow-repository", deadline=deadline, cwd=cwd)
    if shallow not in ("true", "false"):
        raise RuntimeError("unknown shallow repository status")
    args = ["fetch", "--no-tags", "--no-recurse-submodules"]
    if shallow == "true":
        args.append("--depth=1")
    git(*args, remote, ref, deadline=deadline, cwd=cwd)
    tag = git("cat-file", "tag", token, deadline=deadline, cwd=cwd)
    header, body = tag.split("\n\n", 1)
    lines = header.splitlines()
    if lines[:2] != ["object " + expected["revision"], "type commit"]:
        raise RuntimeError("lease revision mismatch")
    actual = json.loads(body)
    nonce = actual.pop("nonce", "")
    if expected["run"] is not None:
        parent = actual.pop("reservation", "")
        if not re.fullmatch(r"[0-9a-f]{40}", parent) or (reservation is not None and parent != reservation):
            raise RuntimeError("lease predecessor reservation mismatch")
    if not re.fullmatch(r"[0-9a-f]{32}", nonce) or actual != expected:
        raise RuntimeError("lease request/run binding mismatch")
    assert_owned(remote, asset, token, deadline=deadline, cwd=cwd)


def replace(remote, asset, previous, expected, deadline):
    ref = ref_for(asset)
    nonce = uuid.uuid4().hex
    body = json.dumps(dict(expected, nonce=nonce), sort_keys=True)
    tag = (f'object {expected["revision"]}\ntype commit\ntag two-transfer-{nonce}\n'
           f'tagger TWO lease <lease@invalid> 1700000000 +0000\n\n{body}\n')
    token = git("mktag", stdin=tag, deadline=deadline)
    git("push", "--porcelain", f"--force-with-lease={ref}:{previous}",
        remote, f"{token}:{ref}", deadline=deadline)
    assert_owned(remote, asset, token, deadline=deadline)
    return token


def reserve(remote, asset, revision, request):
    """Caller must separately verify the immutable owner request before use."""
    expected = binding(asset, revision, request)
    return replace(remote, asset, "", expected, time.monotonic() + 45)


def claim(remote, asset, token, revision, request, run, attempt):
    """Caller must verify actual Actions run identity before use; no auto-release."""
    deadline = time.monotonic() + 45
    expected = binding(asset, revision, request, run, attempt)
    read_binding(remote, asset, token, binding(asset, revision, request), deadline)
    return replace(remote, asset, token, dict(expected, reservation=token), deadline)


def verify(remote, asset, token, revision, request, run, attempt):
    expected = binding(asset, revision, request, run, attempt)
    read_binding(remote, asset, token, expected, time.monotonic() + 45)


def await_bound(remote, asset, reservation, revision, request, run, attempt, timeout=60):
    """Read only: wait for launcher to bind the one-time reservation to this run."""
    expected = binding(asset, revision, request, run, attempt)
    if not re.fullmatch(r"[0-9a-f]{40}", reservation) or not 0 < timeout <= 120:
        raise ValueError("invalid reservation or wait limit")
    ref = ref_for(asset)
    cwd = os.environ.get("MORWEN_TRANSFER_GIT_DIR") or None
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = git("ls-remote", "--refs", remote, ref, deadline=deadline, cwd=cwd)
        match = re.fullmatch(r"([0-9a-f]{40})\t" + re.escape(ref), current)
        if not match:
            raise RuntimeError("transfer reservation missing or ambiguous")
        token = match.group(1)
        if token != reservation:
            read_binding(remote, asset, token, expected, deadline, reservation=reservation)
            return token
        # The exact unconsumed reservation is the only permissible wait state.
        try:
            read_binding(remote, asset, token, binding(asset, revision, request), deadline)
        except RuntimeError:
            # A legitimate CAS handoff may race the read. Re-read once; fail on other errors.
            updated = git("ls-remote", "--refs", remote, ref, deadline=deadline, cwd=cwd)
            if updated == current:
                raise
            continue
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(0.5, remaining))
    raise TimeoutError("launcher did not bind reservation to this run")


def complete(remote, asset, reservation, revision, request, run, attempt, producer_sha, receipt):
    """Only after both worker jobs terminated successfully and private byte readback."""
    if not isinstance(receipt, dict) or receipt.get("scope") != "PRIVATE_CANDIDATE_READBACK_VERIFIED" or receipt.get("adoption") != "NOT_ADOPTED":
        raise ValueError("durable private receipt required")
    if receipt.get("kind") != "blend" or receipt.get("revision") != revision or not re.fullmatch(r"[0-9a-f]{64}", producer_sha) or receipt.get("source_archive_sha256") != producer_sha:
        raise ValueError("receipt stage or source mismatch")
    if receipt.get("run_id") != run or receipt.get("request_id") != request:
        raise ValueError("receipt run/request mismatch")
    if not re.fullmatch(r"[0-9a-f]{64}", receipt.get("sha256", "")):
        raise ValueError("receipt digest required")
    if any(type(receipt.get(k)) is not int or receipt[k] <= 0 for k in ("release_id", "asset_id", "bytes")) or receipt["bytes"] > 128 * 1024 * 1024:
        raise ValueError("receipt identity or size")
    token = await_bound(remote, asset, reservation, revision, request, run, attempt)
    # Use the established compare-and-delete; never remove another owner's tag.
    release(remote, asset, token)
    if git("ls-remote", "--refs", remote, ref_for(asset)):
        raise RuntimeError("lease not absent after completion; reconcile without retry")
