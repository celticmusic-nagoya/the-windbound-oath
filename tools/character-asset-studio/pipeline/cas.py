#!/usr/bin/env python3
"""Character Asset Studio — AI Collaboration Pipeline v0.5.1 (CLI).

Machine-to-machine helpers for ChatGPT <-> Claude asset work. Requires Python 3.9+, Pillow, numpy,
jsonschema (all usually present in AI sandboxes). Run from anywhere; paths are repository-relative.

  validate FILE...                         schema check (asset-set, anchor-set, manifest, brief, qa-report, motion, BASE_BODY_SPEC 2.0 / 1.0-legacy)
  qa ASSET_SET [--report OUT]              automated image QA -> cas/qa-report/0.5 (overall + adoptionReady)
  brief ... --out-dir DIR                  guide PNGs + production brief JSON for AI image generation
  align SRC DST --preset ID                new candidate PNG with ground contact moved onto the anchor
  body-spec-upgrade SRC --out DST          BASE_BODY_SPEC v1.0 (pixel) -> v2.0 (normalised) as a NEW file
  manifest-build ROOT --out FILE           SHA-256 MANIFEST (protected files keep CANONICAL_PROTECTED)
  manifest-verify FILE [--report OUT]      re-hash; protected change = FAIL
  protect-verify [--report OUT]            the protected (canonical) list: all present, SHA-256 unchanged
  protect-diff --base REF                  FAIL if a git change set touches a protected path
  pr-summary REPORT... [--out MD]          Markdown summary of QA reports for a Draft PR
  pr-append --repo O/R --pr N --file MD    idempotent section in a DRAFT PR body (replace by --key; never merges)

QA verdicts and exit codes are separate. Every QA command prints JSON with "overall" (PASS/FAIL/BLOCKED/NOT_RUN)
and "adoptionReady" (true only if everything incl. human checks PASSed). The exit code says whether the command
ran, unless a gate is requested:
  --gate none (default)  0 = report produced, whatever the verdict
  --gate no-fail         1 = overall FAIL, 2 = overall BLOCKED, else 0
  --gate adoption        1 = FAIL, 2 = BLOCKED, 3 = not adoptionReady (e.g. NOT_RUN human checks), else 0
  64 = refused by policy (protected path, overwrite not allowed, approval status, …), 65 = invalid input, 70 = internal error
Overwriting: only with --overwrite, never for protected paths, never under assets/, and only for files the
pipeline generated (qa-report / manifest / production-brief JSON, marked Markdown, guides listed in the brief).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from caslib import core, schemas, imageqa, manifest, report, prbody, bodyspec, brief as briefmod, align as alignmod  # noqa: E402

EXIT_OK, EXIT_POLICY, EXIT_INPUT, EXIT_INTERNAL = 0, 64, 65, 70


def gate_code(gate, overall, ready):
    if gate == "none":
        return EXIT_OK
    if overall == "FAIL":
        return 1
    if overall == "BLOCKED":
        return 2
    if gate == "adoption" and not ready:
        return 3
    return EXIT_OK


def _write(path, text, overwrite=False):
    p = core.guard_write(path, overwrite=overwrite)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _emit(rep, a):
    if getattr(a, "report", None):
        _write(a.report, core.stable_dumps(rep), a.overwrite)
    print(json.dumps({"overall": rep["overall"], "adoptionReady": rep["adoptionReady"], "counts": rep["counts"],
                      "adoptionBlockers": rep["adoptionBlockers"], "gate": a.gate}, ensure_ascii=False))
    return gate_code(a.gate, rep["overall"], rep["adoptionReady"])


def cmd_validate(a):
    rows = []
    for f in a.files:
        r = schemas.validate_file(f)
        if not a.report:
            print(json.dumps({"file": f, **r}, ensure_ascii=False))
        row = {"id": "schema_valid", "scope": core.rel(f), "result": r["result"], "kind": "automated", "detail": {"schema": r["schema"]}}
        if r["errors"]:
            row["detail"]["errors"] = r["errors"]
        rows.append(row)
    if a.report:
        return _emit(report.make_report({"kind": "schema-validation"}, rows, adoption_subject=False), a)
    return gate_code(a.gate, report.overall(rows), False)  # schema validity alone is never adoption


def cmd_qa(a):
    return _emit(imageqa.run(core.load_json(a.asset_set), a.asset_set), a)


def cmd_brief(a):
    b = briefmod.build_brief(a.task_id, a.kind, a.character, a.preset, a.out_dir, a.deliver_to, a.frames, a.slot,
                             a.description, a.body_spec, a.views.split(","), not a.no_preview, a.overwrite)
    out = Path(a.out_dir) / "production_brief.json"
    _write(out, core.stable_dumps(b), a.overwrite)
    v = schemas.validate(b)
    print(json.dumps({"brief": core.rel(out), "schema": v["result"], "errors": v["errors"], "status": b["status"], "autoAdopt": False}))
    return EXIT_OK if v["result"] == "PASS" else EXIT_INTERNAL


def cmd_align(a):
    p = core.preset(a.preset)
    c = core.preset_canvas(p)
    r = alignmod.align(a.src, a.dst, c, core.to_pixel(p["ground"], c), align_x=not a.no_x)
    r["adoptionReady"] = False
    print(core.stable_dumps(r), end="")
    return EXIT_OK if (a.gate == "none" or r["result"] == "PASS") else 1


def cmd_body_spec_upgrade(a):
    src = core.load_json(a.src)
    try:
        out = bodyspec.upgrade_v1(src, a.preset)
    except (ValueError, KeyError) as e:
        print(json.dumps({"result": "FAIL", "error": str(e)}))
        return EXIT_INPUT
    _write(a.out, core.stable_dumps(out), False)   # always a new file; the source is never modified
    v = schemas.validate(out)
    print(json.dumps({"written": core.rel(a.out), "schema": v["schema"], "result": v["result"], "sourceUnchanged": True}))
    return EXIT_OK if v["result"] == "PASS" else EXIT_INTERNAL


def cmd_measure_canon(a):
    from caslib import canonmeasure
    ev, rep = canonmeasure.run(a.character, a.observations, a.out_dir, a.overwrite)
    if ev:
        print(json.dumps({"landmarkStatusCounts": ev["summary"]["landmarkStatusCounts"], "groundRowPx": ev["summary"]["groundRowPx"]}))
    print(json.dumps({"overall": rep["overall"], "adoptionReady": rep["adoptionReady"], "counts": rep["counts"], "gate": a.gate}))
    return gate_code(a.gate, rep["overall"], rep["adoptionReady"])


def cmd_manifest_build(a):
    m = manifest.build(a.root, a.status, a.note)
    _write(a.out, core.stable_dumps(m), a.overwrite)
    print(json.dumps({"manifest": a.out, "files": len(m["files"]), "schema": schemas.validate(m)["result"]}))
    return EXIT_OK


def cmd_manifest_verify(a):
    return _emit(manifest.verify(core.load_json(a.file)), a)


def cmd_protect_verify(a):
    return _emit(manifest.verify_protected(), a)


def cmd_protect_diff(a):
    out = subprocess.run(["git", "diff", "--name-only", f"{a.base}...{a.head}"], cwd=core.REPO_ROOT, capture_output=True, text=True)
    if out.returncode:
        print(json.dumps({"overall": "BLOCKED", "adoptionReady": False, "reason": out.stderr.strip()[:200]}))
        return gate_code(a.gate, "BLOCKED", False)
    hits = manifest.changed_protected([l for l in out.stdout.splitlines() if l])
    ov = "FAIL" if hits else "PASS"
    print(json.dumps({"overall": ov, "adoptionReady": False, "protectedChanged": hits}))
    return gate_code(a.gate, ov, False)


def cmd_pr_summary(a):
    reps = [(Path(f).name, core.load_json(f)) for f in a.reports]
    md = report.to_markdown(reps, a.title)
    if a.out:
        _write(a.out, md, a.overwrite)
    print(md, end="")
    return EXIT_OK


def cmd_pr_append(a):
    def gh(*args, inp=None):
        return subprocess.run(["gh", "api", *args], capture_output=True, text=True, input=inp)
    content = Path(a.file).read_text(encoding="utf-8")
    if a.footer:
        content = content.rstrip() + "\n\n" + Path(a.footer).read_text(encoding="utf-8")
    r = gh(f"repos/{a.repo}/pulls/{a.pr}")
    if r.returncode:
        print(json.dumps({"result": "BLOCKED", "reason": "gh api failed: " + r.stderr.strip()[:200]}))
        return 2
    pr = json.loads(r.stdout)
    if not pr.get("draft") or pr.get("state") != "open":
        print(json.dumps({"result": "BLOCKED", "reason": "PR is not an open Draft; refusing to edit"}))
        return 2
    old = pr.get("body") or ""
    try:
        new, action = prbody.merge(old, a.key, content)
    except ValueError as e:
        print(json.dumps({"result": "BLOCKED", "reason": str(e)}))
        return 2
    info = {"key": a.key, "action": action, "sections": prbody.sections(new), "changed": new != old, "dryRun": a.dry_run}
    if new == old or a.dry_run:
        print(json.dumps({"result": "PASS", **info}))
        return EXIT_OK
    r = gh("-X", "PATCH", f"repos/{a.repo}/pulls/{a.pr}", "--input", "-", inp=json.dumps({"body": new}))
    if r.returncode:
        print(json.dumps({"result": "BLOCKED", "reason": r.stderr.strip()[:200], **info}))
        return 2
    print(json.dumps({"result": "PASS", "draft": json.loads(r.stdout).get("draft"), **info}))
    return EXIT_OK


def main(argv=None):
    ap = argparse.ArgumentParser(prog="cas.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)

    def gated(p):
        p.add_argument("--gate", choices=["none", "no-fail", "adoption"], default="none")
        return p

    def writes(p):
        p.add_argument("--overwrite", action="store_true", help="replace an existing pipeline-generated output (never protected or assets/ files)")
        return p
    p = writes(gated(sp.add_parser("validate"))); p.add_argument("files", nargs="+"); p.add_argument("--report"); p.set_defaults(fn=cmd_validate)
    p = writes(gated(sp.add_parser("qa"))); p.add_argument("asset_set"); p.add_argument("--report"); p.set_defaults(fn=cmd_qa)
    p = writes(sp.add_parser("brief"))
    p.add_argument("--task-id", required=True); p.add_argument("--kind", required=True, choices=["base_body", "costume_layer", "walk_frames"])
    p.add_argument("--character", required=True); p.add_argument("--preset", required=True); p.add_argument("--out-dir", required=True)
    p.add_argument("--deliver-to", required=True); p.add_argument("--frames", type=int); p.add_argument("--slot"); p.add_argument("--description")
    p.add_argument("--body-spec"); p.add_argument("--views", default=",".join(core.VIEWS)); p.add_argument("--no-preview", action="store_true")
    p.set_defaults(fn=cmd_brief)
    p = gated(sp.add_parser("align")); p.add_argument("src"); p.add_argument("dst"); p.add_argument("--preset", required=True); p.add_argument("--no-x", action="store_true"); p.set_defaults(fn=cmd_align)
    p = writes(gated(sp.add_parser("measure-canon"))); p.add_argument("--character", required=True); p.add_argument("--observations", required=True)
    p.add_argument("--out-dir", required=True); p.set_defaults(fn=cmd_measure_canon)
    p = sp.add_parser("body-spec-upgrade"); p.add_argument("src"); p.add_argument("--out", required=True); p.add_argument("--preset"); p.set_defaults(fn=cmd_body_spec_upgrade)
    p = writes(sp.add_parser("manifest-build")); p.add_argument("root"); p.add_argument("--out", required=True); p.add_argument("--status", default="UNAPPROVED_CANDIDATE"); p.add_argument("--note"); p.set_defaults(fn=cmd_manifest_build)
    p = writes(gated(sp.add_parser("manifest-verify"))); p.add_argument("file"); p.add_argument("--report"); p.set_defaults(fn=cmd_manifest_verify)
    p = writes(gated(sp.add_parser("protect-verify"))); p.add_argument("--report"); p.set_defaults(fn=cmd_protect_verify)
    p = gated(sp.add_parser("protect-diff")); p.add_argument("--base", required=True); p.add_argument("--head", default="HEAD"); p.set_defaults(fn=cmd_protect_diff)
    p = writes(sp.add_parser("pr-summary")); p.add_argument("reports", nargs="+"); p.add_argument("--out"); p.add_argument("--title", default="Pipeline QA summary"); p.set_defaults(fn=cmd_pr_summary)
    p = sp.add_parser("pr-append"); p.add_argument("--repo", required=True); p.add_argument("--pr", required=True, type=int); p.add_argument("--file", required=True)
    p.add_argument("--footer"); p.add_argument("--key", default="pipeline-qa", help="section id; re-running with the same key replaces that section")
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(fn=cmd_pr_append)
    a = ap.parse_args(argv)
    try:
        return a.fn(a)
    except core.PolicyError as e:
        print(json.dumps({"result": "BLOCKED", "policy": str(e)}, ensure_ascii=False))
        return EXIT_POLICY
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(json.dumps({"result": "BLOCKED", "inputError": str(e)}, ensure_ascii=False))
        return EXIT_INPUT


if __name__ == "__main__":
    sys.exit(main())
