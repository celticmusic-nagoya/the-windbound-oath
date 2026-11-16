"""Fail the CI QA gate if recorded real lash surface intersections are nonzero."""
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args()
    d=json.loads(a.report.read_text())
    if d.get("status") not in ("PASS_SURFACE_ONLY_LIMITED","FAIL_SURFACE_INTERSECTIONS"):
        raise SystemExit("FAIL: unknown QA status")
    totals={s:{k:d["intersection_counts"][s][k] for k in ("cage","eyes")} for s in ("R","L")}
    if any(v>0 for side in totals.values() for v in side.values()):
        raise SystemExit(f"FAIL: real lash surface intersections: {totals}")
    if d["status"]!="PASS_SURFACE_ONLY_LIMITED":
        raise SystemExit("FAIL: inconsistent QA status")
    print(f"PASS_SURFACE_ONLY_LIMITED: {totals}; art/alpha/motion QA remain NOT_RUN")

if __name__=="__main__":main()
