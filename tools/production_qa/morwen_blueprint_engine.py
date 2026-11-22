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

def bounded_correction(target, tolerance, samples, current, max_step, limits):
    """Local secant response; only matched same-control observations qualify."""
    if len(samples)!=2 or tolerance is None or max_step<=0:
        raise ValueError("unqualified response")
    a,b=samples
    if not all(v.get("registration_verified") and v.get("evidence_sha256") for v in samples):
        raise ValueError("unregistered response")
    if a.get("control_id")!=b.get("control_id") or not a.get("control_id"):
        raise ValueError("mixed controls")
    if a.get("context_sha256")!=b.get("context_sha256") or not a.get("context_sha256"):
        raise ValueError("mixed camera or model context")
    if current!=b["control"] or a["control"]==b["control"]:
        raise ValueError("stale or zero control response")
    if not all(math.isfinite(v) for v in (target,tolerance,current,max_step,a["actual"],b["actual"],a["control"],b["control"],*limits)):
        raise ValueError("nonfinite")
    if tolerance<0 or not limits[0]<=current<=limits[1]:
        raise ValueError("invalid limits")
    residual=target-b["actual"]
    if abs(residual)<=tolerance:
        return dict(status="WITHIN_TOLERANCE",delta=0)
    slope=(b["actual"]-a["actual"])/(b["control"]-a["control"])
    if abs(slope)<1e-9:
        return dict(status="BLOCKED_NO_RESPONSE")
    delta=max(-max_step,min(max_step,residual/slope))
    proposed=max(limits[0],min(limits[1],current+delta))
    if proposed==current:
        return dict(status="BLOCKED_CONTROL_LIMIT")
    return dict(status="PROPOSED_REVIEW_REQUIRED",delta=proposed-current,control=proposed,
                predicted_residual=residual-slope*(proposed-current))

def self_test():
    a=dict(control_id="test",context_sha256="fixture",registration_verified=True,evidence_sha256="fixture",control=0.,actual=10.)
    b=dict(a,control=1.,actual=12.)
    assert bounded_correction(16,0.5,[a,b],1,0.25,(-2,2))["control"]==1.25
    assert bounded_correction(12,0.5,[a,b],1,0.25,(-2,2))["status"]=="WITHIN_TOLERANCE"
    assert bounded_correction(16,0.5,[a,dict(b,actual=10)],1,0.25,(-2,2))["status"]=="BLOCKED_NO_RESPONSE"
    try:
        bounded_correction(16,0.5,[a,dict(b,context_sha256="stale")],1,0.25,(-2,2))
    except ValueError:
        pass
    else:
        raise AssertionError("stale context accepted")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("blueprint",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--observations",type=Path)
    a=p.parse_args()
    self_test()
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
