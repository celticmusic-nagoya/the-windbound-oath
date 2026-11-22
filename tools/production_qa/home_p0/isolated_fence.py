"""Single-run bare Git isolation and negative fencing checks."""
import json
from pathlib import Path
import subprocess
import sys

from shared_asset_lease import acquire, assert_owned, release

remote, asset, state, mode = sys.argv[1:]
state = Path(state)
if mode == "open":
    subprocess.run(["git", "init", "--bare", remote], check=True, capture_output=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    tree = subprocess.check_output(["git", "mktree"], input="", text=True).strip()
    head = subprocess.check_output(
        ["git", "-c", "user.name=HOME isolated QA", "-c", "user.email=qa@invalid",
         "commit-tree", tree, "-m", "HOME isolated writer for " + revision],
        text=True,
    ).strip()
    stale = acquire(remote, asset, head)
    release(remote, asset, stale)
    token = acquire(remote, asset, head)
    for action in (lambda: release(remote, asset, stale), lambda: acquire(remote, asset, head)):
        try:
            action()
        except (RuntimeError, subprocess.CalledProcessError):
            pass
        else:
            raise RuntimeError("invalid writer was accepted")
    state.write_text(json.dumps({"token": token, "head": head, "revision": revision}))
else:
    token = json.loads(state.read_text())["token"]
    assert_owned(remote, asset, token)
    if mode == "close":
        release(remote, asset, token)
print("ISOLATED_FENCING_OK", mode)
