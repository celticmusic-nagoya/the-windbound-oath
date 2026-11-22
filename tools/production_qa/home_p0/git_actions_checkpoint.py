"""Package and independently restore passed HOME bytes through a Git bundle."""
import json
import os
from pathlib import Path
import sys
import time

from session_plan import ready, sha
from shared_asset_lease import acquire, checkpoint_ref, git, release
from shared_blueprint_contract import digest_record
from shared_git_checkpoint_store import GitCheckpointStore, restore_checkpoint


OWNER = "dff3a32df533c8786f3122e07cf681c18f4805bd913d750f04ce15b321b10fed"
ISOLATED = "fa4da274f034a14d5a163b1af6a090ea0fc98988faf1acff587eff22cfcd7800"
DESIGN = {
    "docs/production/lind/home/interior-bed-target.v1.json": "a50de6986a171065971b4a51d1aec26cdc417565397742029691ca299346646d",
    "docs/production/LIND_INTEGRATED_ARCHITECTURE_BLUEPRINT_20261121.md": "8e869c56a2684f4a0fdb9f7eda304ac8ecee5c100768add979fdba02fae5ef63",
}
ASSET = "LIND-HOME"


def main():
    mode, working, design_root = sys.argv[1:]
    work = Path(working).resolve()
    design_root = Path(design_root).resolve()
    actual = {name: sha(design_root / name) for name in DESIGN}
    if actual != DESIGN:
        raise ValueError("owner design SHA mismatch")
    evidence = {"owner_source_sha256": OWNER, "checkpoint_sha256": ISOLATED, "design": actual}
    stage = dict(id="existing_isolated_checkpoint", deps=[], qualified=True,
                 seconds=1, fingerprint=digest_record(evidence))
    bundle = work / "checkpoint.bundle"
    anchor = work / "objects"
    anchor.mkdir()
    os.chdir(anchor)
    git("init", "-q")
    deadline = time.monotonic() + 90
    if mode == "package":
        native = work / "input"
        if sha(native / "owner.blend") != OWNER or sha(native / "isolated.blend") != ISOLATED:
            raise ValueError("native input manifest mismatch")
        (native / "provenance.json").write_text(json.dumps(evidence, sort_keys=True))
        record = dict(path="isolated.blend", sha256=ISOLATED, reopened=True,
                      fingerprint=stage["fingerprint"], files={
                          "owner.blend": OWNER,
                          "provenance.json": sha(native / "provenance.json"),
                      })
        git("config", "user.name", "Isolated checkpoint QA")
        git("config", "user.email", "qa@invalid")
        git("commit", "--allow-empty", "-qm", "read-only isolated checkpoint anchor")
        remote = str(work / "isolated.git")
        git("init", "--bare", "-q", remote)
        token = acquire(remote, ASSET, git("rev-parse", "HEAD"))
        store = GitCheckpointStore(remote, ASSET, native)
        token = store({stage["id"]: record}, token, deadline)
        release(remote, ASSET, token)
        git("--git-dir", remote, "bundle", "create", str(bundle), checkpoint_ref(ASSET), deadline=deadline)
        (work / "bundle.json").write_text(json.dumps(dict(commit=store.previous,
                                                           sha256=sha(bundle), evidence=evidence)))
    elif mode == "restore":
        manifest = json.loads((work / "bundle.json").read_text())
        if manifest["sha256"] != sha(bundle) or manifest["evidence"] != evidence:
            raise ValueError("bundle provenance mismatch")
        restored = work / "restored"
        records = restore_checkpoint(str(bundle), ASSET, manifest["commit"], restored, deadline)
        if json.loads((restored / "provenance.json").read_text()) != evidence:
            raise ValueError("checkpoint design or dependency mismatch")
        if sha(restored / "owner.blend") != OWNER or sha(restored / "isolated.blend") != ISOLATED:
            raise ValueError("restored native SHA mismatch")
        if ready([stage], records, restored, 60, 10):
            raise RuntimeError("verified stage would execute again")
        stale = {**stage, "fingerprint": digest_record({**evidence, "owner_source_sha256": "0"*64})}
        if ready([stale], records, restored, 60, 10) != [stage["id"]]:
            raise RuntimeError("dependency change did not invalidate the affected stage")
        print("GIT_BUNDLE_RESTORE_PASS completed_reruns=0 dependency_invalidation=PASS")
    else:
        raise ValueError("unknown phase")


if __name__ == "__main__":
    main()
