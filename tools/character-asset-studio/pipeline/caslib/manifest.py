"""SHA-256 MANIFEST build/verify and protected-asset (canon) verification."""
from pathlib import Path

from .core import REPO_ROOT, protected_list, sha256_file, is_protected, assert_writable_status, rel
from .report import Checks, make_report

SKIP_PARTS = {"__pycache__", ".git", "node_modules"}


def _image_info(path):
    try:
        from PIL import Image
        with Image.open(path) as im:
            return {"width": im.width, "height": im.height, "mode": im.mode}
    except Exception:
        return {}


def build(root, status="UNAPPROVED_CANDIDATE", note=None, repo_root=REPO_ROOT, exclude=("MANIFEST.json",)):
    """Hash every file under root. Files on the protected list keep status CANONICAL_PROTECTED (read from the
    protected list, not chosen by the caller); everything else gets the caller's unapproved status."""
    assert_writable_status(status)
    root = Path(root)
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file() or SKIP_PARTS & set(p.parts) or p.name in exclude:
            continue
        r = rel(p, repo_root)
        e = {"path": r, "sha256": sha256_file(p), "bytes": p.stat().st_size,
             "status": "CANONICAL_PROTECTED" if is_protected(r) else status}
        if p.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg"):
            e.update(_image_info(p))
        files.append(e)
    m = {"schema": "cas/manifest/0.5", "root": rel(root, repo_root), "files": files}
    if note:
        m["note"] = note
    return m


def verify(manifest, repo_root=REPO_ROOT, check_untracked=True):
    ck = Checks()
    listed = set()
    for e in manifest["files"]:
        p = Path(repo_root) / e["path"]
        listed.add(e["path"])
        prot = e["status"] == "CANONICAL_PROTECTED" or is_protected(e["path"])
        cid = "protected_sha256" if prot else "file_sha256"
        if not p.exists():
            ck.add(cid, e["path"], "FAIL", reason="file missing")
            continue
        sha = sha256_file(p)
        ck.add(cid, e["path"], "PASS" if sha == e["sha256"] else "FAIL",
               detail=None if sha == e["sha256"] else {"recorded": e["sha256"], "actual": sha},
               reason=None if sha == e["sha256"] else ("PROTECTED ASSET CHANGED" if prot else "hash differs from MANIFEST"))
        if e["status"] == "CANONICAL_PROTECTED" and not is_protected(e["path"]):
            ck.add("protected_status_backed_by_list", e["path"], "FAIL", reason="CANONICAL_PROTECTED but not on protected_assets.json")
    if check_untracked:
        root = Path(repo_root) / manifest["root"]
        extra = [rel(p, repo_root) for p in sorted(root.rglob("*")) if p.is_file() and not SKIP_PARTS & set(p.parts)
                 and p.name != "MANIFEST.json" and rel(p, repo_root) not in listed]
        ck.add("no_unlisted_files", manifest["root"], "PASS" if not extra else "FAIL", detail=extra[:50] or None)
    return make_report({"kind": "manifest", "path": manifest["root"]}, ck.rows)


def verify_protected(repo_root=REPO_ROOT):
    """Every protected asset exists and matches its recorded SHA-256."""
    ck = Checks()
    for e in protected_list()["files"]:
        p = Path(repo_root) / e["path"]
        if not p.exists():
            ck.add("protected_sha256", e["path"], "FAIL", reason="protected file missing")
            continue
        sha = sha256_file(p)
        ck.add("protected_sha256", e["path"], "PASS" if sha == e["sha256"] else "FAIL",
               detail=None if sha == e["sha256"] else {"recorded": e["sha256"], "actual": sha})
    return make_report({"kind": "protected-assets", "path": "tools/character-asset-studio/pipeline/protected_assets.json"}, ck.rows)


def changed_protected(changed_paths):
    """Given paths changed in a diff, return those that are protected (any hit = FAIL for the change set)."""
    return [p for p in changed_paths if is_protected(p)]
