#!/usr/bin/env python3
"""Character Asset Studio — AI Collaboration Pipeline v0.5 (CLI).

Machine-to-machine helpers for ChatGPT <-> Claude asset work. Requires Python 3.9+, Pillow, numpy,
jsonschema (all usually present in AI sandboxes). Run from anywhere; paths are repository-relative.

  validate FILE...                         schema check (asset-set, anchor-set, manifest, brief, qa-report, motion, BASE_BODY_SPEC)
  qa ASSET_SET [--report OUT]              automated image QA -> cas/qa-report/0.5
  brief ... --out-dir DIR                  guide PNGs + production brief JSON for AI image generation
  align SRC DST --preset ID                new candidate PNG with ground contact moved onto the anchor
  manifest-build ROOT --out FILE           SHA-256 MANIFEST (protected files keep CANONICAL_PROTECTED)
  manifest-verify FILE [--report OUT]      re-hash; protected change = FAIL
  protect-verify [--report OUT]            the protected (canonical) list: all present, SHA-256 unchanged
  protect-diff --base REF                  FAIL if a git change set touches a protected path
  pr-summary REPORT... [--out MD]          Markdown summary of QA reports for a Draft PR
  pr-append --repo O/R --pr N --file MD    append the summary to a DRAFT PR body (refuses non-draft; never merges)

Exit code: 0 = no FAIL/BLOCKED, 1 = FAIL, 2 = BLOCKED, 64 = usage/policy error.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from caslib import core, schemas, imageqa, manifest, report, brief as briefmod, align as alignmod  # noqa: E402


def _write(path, text):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _emit(rep, out=None):
    text = core.stable_dumps(rep)
    if out:
        core.guard_write(out, allow_overwrite=True)
        _write(out, text)
    print(json.dumps({"overall": rep["overall"], "counts": rep["counts"]}))
    return {"FAIL": 1, "BLOCKED": 2}.get(rep["overall"], 0)


def cmd_validate(a):
    worst = 0
    for f in a.files:
        r = schemas.validate_file(f)
        print(json.dumps({"file": f, **r}, ensure_ascii=False))
        worst = max(worst, {"FAIL": 1, "BLOCKED": 2}.get(r["result"], 0))
    return worst


def cmd_qa(a):
    doc = core.load_json(a.asset_set)
    return _emit(imageqa.run(doc, a.asset_set), a.report)


def cmd_brief(a):
    b = briefmod.build_brief(a.task_id, a.kind, a.character, a.preset, a.out_dir, a.deliver_to, a.frames, a.slot,
                             a.description, a.body_spec, a.views.split(","), not a.no_preview, a.overwrite)
    out = Path(a.out_dir) / "production_brief.json"
    core.guard_write(out, allow_overwrite=a.overwrite)
    _write(out, core.stable_dumps(b))
    v = schemas.validate(b)
    print(json.dumps({"brief": core.rel(out), "schema": v["result"], "errors": v["errors"]}))
    return 0 if v["result"] == "PASS" else 1


def cmd_align(a):
    p = core.preset(a.preset)
    c = core.preset_canvas(p)
    r = alignmod.align(a.src, a.dst, c, core.to_pixel(p["ground"], c), align_x=not a.no_x)
    print(core.stable_dumps(r), end="")
    return 0 if r["result"] == "PASS" else 1


def cmd_manifest_build(a):
    m = manifest.build(a.root, a.status, a.note)
    core.guard_write(a.out, allow_overwrite=True)
    _write(a.out, core.stable_dumps(m))
    print(json.dumps({"manifest": a.out, "files": len(m["files"]), "schema": schemas.validate(m)["result"]}))
    return 0


def cmd_manifest_verify(a):
    return _emit(manifest.verify(core.load_json(a.file)), a.report)


def cmd_protect_verify(a):
    return _emit(manifest.verify_protected(), a.report)


def cmd_protect_diff(a):
    out = subprocess.run(["git", "diff", "--name-only", f"{a.base}...{a.head}"], cwd=core.REPO_ROOT, capture_output=True, text=True)
    if out.returncode:
        print(json.dumps({"overall": "BLOCKED", "reason": out.stderr.strip()[:200]}))
        return 2
    hits = manifest.changed_protected([l for l in out.stdout.splitlines() if l])
    print(json.dumps({"overall": "FAIL" if hits else "PASS", "protectedChanged": hits}))
    return 1 if hits else 0


def cmd_pr_summary(a):
    reps = [(Path(f).name, core.load_json(f)) for f in a.reports]
    md = report.to_markdown(reps, a.title)
    if a.out:
        core.guard_write(a.out, allow_overwrite=True)
        _write(a.out, md)
    print(md, end="")
    return 0


MARK = "<!-- cas-pipeline-summary -->"


def cmd_pr_append(a):
    def gh(*args, inp=None):
        return subprocess.run(["gh", "api", *args], capture_output=True, text=True, input=inp)
    r = gh(f"repos/{a.repo}/pulls/{a.pr}")
    if r.returncode:
        print(json.dumps({"overall": "BLOCKED", "reason": "gh api failed: " + r.stderr.strip()[:200]}))
        return 2
    pr = json.loads(r.stdout)
    if not pr.get("draft") or pr.get("state") != "open":
        print(json.dumps({"overall": "BLOCKED", "reason": "PR is not an open Draft; refusing to edit"}))
        return 2
    body = (pr.get("body") or "") + "\n\n" + MARK + "\n" + Path(a.file).read_text(encoding="utf-8")
    if a.footer:
        body += "\n" + Path(a.footer).read_text(encoding="utf-8")
    r = gh("-X", "PATCH", f"repos/{a.repo}/pulls/{a.pr}", "--input", "-", inp=json.dumps({"body": body}))
    ok = r.returncode == 0
    print(json.dumps({"overall": "PASS" if ok else "BLOCKED", "draft": json.loads(r.stdout).get("draft") if ok else None}))
    return 0 if ok else 2


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cas.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("validate"); p.add_argument("files", nargs="+"); p.set_defaults(fn=cmd_validate)
    p = sp.add_parser("qa"); p.add_argument("asset_set"); p.add_argument("--report"); p.set_defaults(fn=cmd_qa)
    p = sp.add_parser("brief")
    p.add_argument("--task-id", required=True); p.add_argument("--kind", required=True, choices=["base_body", "costume_layer", "walk_frames"])
    p.add_argument("--character", required=True); p.add_argument("--preset", required=True); p.add_argument("--out-dir", required=True)
    p.add_argument("--deliver-to", required=True); p.add_argument("--frames", type=int); p.add_argument("--slot"); p.add_argument("--description")
    p.add_argument("--body-spec"); p.add_argument("--views", default=",".join(core.VIEWS)); p.add_argument("--no-preview", action="store_true")
    p.add_argument("--overwrite", action="store_true"); p.set_defaults(fn=cmd_brief)
    p = sp.add_parser("align"); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--preset", required=True); p.add_argument("--no-x", action="store_true"); p.set_defaults(fn=cmd_align)
    p = sp.add_parser("manifest-build"); p.add_argument("root"); p.add_argument("--out", required=True); p.add_argument("--status", default="UNAPPROVED_CANDIDATE"); p.add_argument("--note"); p.set_defaults(fn=cmd_manifest_build)
    p = sp.add_parser("manifest-verify"); p.add_argument("file"); p.add_argument("--report"); p.set_defaults(fn=cmd_manifest_verify)
    p = sp.add_parser("protect-verify"); p.add_argument("--report"); p.set_defaults(fn=cmd_protect_verify)
    p = sp.add_parser("protect-diff"); p.add_argument("--base", required=True); p.add_argument("--head", default="HEAD"); p.set_defaults(fn=cmd_protect_diff)
    p = sp.add_parser("pr-summary"); p.add_argument("reports", nargs="+"); p.add_argument("--out"); p.add_argument("--title", default="Pipeline QA summary"); p.set_defaults(fn=cmd_pr_summary)
    p = sp.add_parser("pr-append"); p.add_argument("--repo", required=True); p.add_argument("--pr", required=True, type=int); p.add_argument("--file", required=True); p.add_argument("--footer"); p.set_defaults(fn=cmd_pr_append)
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except core.PolicyError as e:
        print(json.dumps({"overall": "BLOCKED", "policy": str(e)}, ensure_ascii=False))
        return 64


if __name__ == "__main__":
    sys.exit(main())
