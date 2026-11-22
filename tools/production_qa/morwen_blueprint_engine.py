"""Blueprint target compilation and evidence comparison. No GUI mutation or implied QA."""
import argparse
import hashlib
import json
import math
from pathlib import Path

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def compile_targets(bp):
    rows = []
    def add(i, module, value, tolerance, source, observable):
        rows.append(dict(id=i,module=module,target=value,tolerance=tolerance,
                         source=source,observable=observable,
                         operation_status="UNQUALIFIED",status="NOT_RUN"))
    for k,v in bp["face_front_review"]["projected_metrics_px"].items():
        add("face.front."+k,"face",v,6,"face_front_review","matched_source_px")
    for view in ("front","right"):
        for group in bp["hair"][view+"_groups"]:
            for n,pt in enumerate(group["guide_px"]):
                for axis,v in zip("xy",pt):
                    add(f"hair.{view}.{group['id']}.{n}.{axis}","hair",v,10,
                        "hair."+view+"_groups","matched_source_px")
    for view, spans in bp["body"]["scanlines"]["views"].items():
        for y, span in zip(bp["body"]["scanlines"]["ys"],spans):
            if isinstance(span,list) and len(span)==2:
                add(f"body.{view}.{y}.width","body",span[1]-span[0]+1,None,
                    "body.scanlines","matched_source_px")
    for view, info in bp["wardrobe"]["projected_vertical_extents"]["views"].items():
        for part, extent in info["parts"].items():
            module="equipment" if part=="bag" else "wardrobe"
            for key,v in zip(("top","bottom"),extent):
                add(f"{module}.{view}.{part}.{key}",module,v,12,
                    "wardrobe.projected_vertical_extents","matched_source_px")
    assert len({r["id"] for r in rows})==len(rows)
    assert {r["module"] for r in rows}=={"face","body","hair","wardrobe","equipment"}
    return rows

def compare(rows, observations):
    known={r["id"] for r in rows}
    if set(observations)-known:
        raise ValueError("unknown observation IDs")
    for row in rows:
        obs=observations.get(row["id"])
        if obs is None:
            continue
        if obs.get("observable")!=row["observable"] or not obs.get("evidence_sha256") or not obs.get("registration_verified"):
            row["status"]="BLOCKED"
            continue
        actual=obs["actual"]
        if not isinstance(actual,(float,int)) or not math.isfinite(actual):
            raise ValueError("invalid actual")
        row.update(actual=actual,residual=actual-row["target"],evidence_sha256=obs["evidence_sha256"])
        row["status"]="BLOCKED" if row["tolerance"] is None else ("PASS" if abs(row["residual"])<=row["tolerance"] else "FAIL")
    return rows

def main():
    p=argparse.ArgumentParser()
    p.add_argument("blueprint",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--observations",type=Path)
    a=p.parse_args()
    fingerprint=sha(a.blueprint)
    rows=compile_targets(json.loads(a.blueprint.read_text()))
    if a.observations:
        data=json.loads(a.observations.read_text())
        if data["blueprint_sha256"]!=fingerprint:
            raise ValueError("stale blueprint")
        compare(rows,data["observations"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(dict(blueprint_sha256=fingerprint,targets=rows,
        status="MEASUREMENT_LEDGER_NOT_ART_QA",
        gaps=["matched camera registration","native control calibration","body tolerance",
              "hidden geometry","equipment attachment and clearance","UV rig deformation runtime"]),indent=2)+"\n")
if __name__=="__main__":
    main()
