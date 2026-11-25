"""Candidate adapter for the existing Git CAS lease; no live writer takeover."""
import json
import re
import time
import uuid

from shared_asset_lease import git, ref_for, assert_owned


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


def read_binding(remote, asset, token, expected, deadline):
    ref = ref_for(asset)
    assert_owned(remote, asset, token, deadline=deadline)
    git("fetch", "--no-tags", remote, ref, deadline=deadline)
    tag = git("cat-file", "tag", token, deadline=deadline)
    header, body = tag.split("\n\n", 1)
    lines = header.splitlines()
    if lines[:2] != ["object " + expected["revision"], "type commit"]:
        raise RuntimeError("lease revision mismatch")
    actual = json.loads(body)
    nonce = actual.pop("nonce", "")
    if not re.fullmatch(r"[0-9a-f]{32}", nonce) or actual != expected:
        raise RuntimeError("lease request/run binding mismatch")
    assert_owned(remote, asset, token, deadline=deadline)


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
    return replace(remote, asset, token, expected, deadline)


def verify(remote, asset, token, revision, request, run, attempt):
    expected = binding(asset, revision, request, run, attempt)
    read_binding(remote, asset, token, expected, time.monotonic() + 45)
