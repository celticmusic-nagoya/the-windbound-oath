"""Backward-compatibility check between two Blueprint Engine output trees (read-only).

For every target present in the baseline tree:
* the baseline target/request must still satisfy the current #468 target_issues
  (or fail for the same recorded hand-off reasons);
* recorded residual rows are re-evaluated with the current residual law and must
  give the same state;
* field-level differences against the candidate tree are classified, so a change
  of dependency SHA / qualification evidence is distinguished from a change of
  design values, tolerances or uncertainty.
"""
import argparse
import json
from pathlib import Path

from .. import digest_record, metric_state, target_issues

DESIGN_FIELDS = ("values", "tolerances", "uncertainty", "coordinate_system", "units",
                 "projection", "measurement_id", "target_id")


def check(baseline, candidate):
    baseline, candidate = Path(baseline), Path(candidate)
    report = dict(baseline=str(baseline), candidate=str(candidate), targets={}, ok=True)
    for path in sorted(baseline.rglob("targets/*.json")):
        rel = path.relative_to(baseline)
        old = json.loads(path.read_text())
        handoff = json.loads((path.parent.parent / "handoff" / path.name).read_text())
        issues = target_issues(old["target"], old["request"])
        recorded = [i for i in handoff["issues"] if not i.startswith(("correction_unqualified",
                                                                       "evidence:"))]
        row = dict(contract_issues_now=issues, contract_issues_recorded=recorded,
                   contract_stable=issues == recorded)
        residual = path.parent.parent / "residual" / path.name
        if residual.is_file():
            rec = json.loads(residual.read_text())
            mism = [k for k, m in rec["metrics"].items()
                    if metric_state(m["residual"], m["tolerance"], m["u"]) != m["state"]]
            row["residual_law_stable"] = not mism
            row["residual_mismatch"] = mism
        new_path = candidate / rel
        if new_path.is_file():
            new = json.loads(new_path.read_text())
            changed = sorted(k for k in set(old["target"]) | set(new["target"])
                             if old["target"].get(k) != new["target"].get(k))
            row.update(changed_fields=changed,
                       design_changed=[k for k in changed if k in DESIGN_FIELDS],
                       provenance_changed=[k for k in changed if k not in DESIGN_FIELDS],
                       contract_sha_old=digest_record(old["target"]),
                       contract_sha_new=digest_record(new["target"]))
        else:
            row["candidate"] = "MISSING"
        ok = row["contract_stable"] and row.get("residual_law_stable", True)
        row["ok"] = ok
        report["ok"] &= ok
        report["targets"][rel.as_posix()] = row
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--out")
    a = parser.parse_args()
    r = check(a.baseline, a.candidate)
    text = json.dumps(r, indent=1, sort_keys=True)
    if a.out:
        Path(a.out).write_text(text + "\n")
    print(json.dumps({k: dict(ok=v["ok"], design_changed=v.get("design_changed"),
                              provenance_changed=v.get("provenance_changed"))
                      for k, v in r["targets"].items()}, indent=1))
    print("OK" if r["ok"] else "FAIL")
    raise SystemExit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
