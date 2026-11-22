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

def register_points(reference_anchors, actual_anchors, max_error):
    """Fit uniform scale and translation only; reject view/pose mismatch."""
    if len(reference_anchors)!=len(actual_anchors) or len(reference_anchors)<3 or max_error<=0:
        raise ValueError("insufficient registration anchors")
    if not all(len(p)==2 and all(math.isfinite(v) for v in p)
               for p in reference_anchors+actual_anchors):
        raise ValueError("invalid anchor")
    n=len(reference_anchors)
    rx,ry=(sum(p[i] for p in reference_anchors)/n for i in (0,1))
    ax,ay=(sum(p[i] for p in actual_anchors)/n for i in (0,1))
    den=sum((p[0]-ax)**2+(p[1]-ay)**2 for p in actual_anchors)
    if den<=0:
        raise ValueError("degenerate anchors")
    scale=sum((p[0]-ax)*(q[0]-rx)+(p[1]-ay)*(q[1]-ry)
              for p,q in zip(actual_anchors,reference_anchors))/den
    if scale<=0:
        raise ValueError("mirrored or invalid view")
    tx,ty=rx-scale*ax,ry-scale*ay
    errors=[math.hypot(scale*p[0]+tx-q[0],scale*p[1]+ty-q[1])
            for p,q in zip(actual_anchors,reference_anchors)]
    return dict(scale=scale,translation=[tx,ty],max_error=max(errors),
                registration_verified=max(errors)<=max_error)

def project_face_metrics(points, registration):
    if not registration["registration_verified"]:
        raise ValueError("unqualified camera registration")
    scale=registration["scale"]
    def dx(a,b):
        return abs(points[a][0]-points[b][0])*scale
    return dict(eye_width_left=dx("left_outer_eye","left_inner_eye"),
                eye_width_right=dx("right_inner_eye","right_outer_eye"),
                iris_center_distance=dx("left_iris_center","right_iris_center"),
                inner_eye_gap=dx("left_inner_eye","right_inner_eye"),
                mouth_width=dx("mouth_left","mouth_right"),
                nose_to_chin_vertical=abs(points["nose_tip"][1]-points["chin"][1])*scale)

def ratio_diagnostics(reference, actual):
    """Scale-independent exploratory ratios; not proof of camera match."""
    pairs=[("eye_width_left","eye_width_right"),
           ("mouth_width","iris_center_distance"),
           ("inner_eye_gap","iris_center_distance"),
           ("nose_to_chin_vertical","iris_center_distance")]
    result=[]
    for n,d in pairs:
        if reference[d]<=0 or actual[d]<=0:
            raise ValueError("invalid ratio denominator")
        target=reference[n]/reference[d]
        observed=actual[n]/actual[d]
        result.append(dict(id=n+"_over_"+d,target=target,actual=observed,
                           residual=observed-target,status="REVIEW_ONLY"))
    return result

def correction_loop(target, tolerance, samples, measure_and_apply, rollback,
                    max_step, limits, deadline, clock, max_attempts=8):
    """Adapter contract: verified native checkpoint, mutation, matched observation.
    Never retry an ambiguous mutation; rollback must verify restored state.
    """
    history=[]
    failures=0
    if tolerance is None:
        return {"status":"BLOCKED_TOLERANCE","history":history}
    for _ in range(max_attempts):
        if clock()>=deadline:
            return {"status":"BLOCKED_TIME_BUDGET","history":history}
        current=samples[-1]["control"]
        proposal=bounded_correction(target,tolerance,samples,current,max_step,limits)
        if proposal["status"]!="PROPOSED_REVIEW_REQUIRED":
            return {"status":proposal["status"],"history":history}
        prior=samples[-1]
        try:
            observed=measure_and_apply(proposal["control"])
            if (not observed.get("registration_verified") or not observed.get("evidence_sha256")
                or observed.get("context_sha256")!=prior["context_sha256"]
                or observed.get("control_id")!=prior["control_id"]
                or not math.isfinite(observed["actual"])
                or not math.isfinite(observed["control"])
                or abs(observed["control"]-proposal["control"])>0.001):
                raise ValueError("ambiguous mutation or observation")
        except Exception:
            restored=rollback(prior)
            return {"status":"BLOCKED_AMBIGUOUS_MUTATION" if restored else "BLOCKED_ROLLBACK",
                    "history":history}
        improved=abs(target-observed["actual"])<abs(target-prior["actual"])
        history.append({"proposal":proposal,"observed":observed,"improved":improved})
        if improved:
            samples=[prior,observed]
            failures=0
            if abs(target-observed["actual"])<=tolerance:
                return {"status":"WITHIN_TOLERANCE","history":history}
        else:
            if not rollback(prior):
                return {"status":"BLOCKED_ROLLBACK","history":history}
            failures+=1
            if failures>=2:
                return {"status":"BLOCKED_CAUSAL_REASSESSMENT","history":history}
            max_step/=2
    return {"status":"BLOCKED_ATTEMPT_BUDGET","history":history}

def self_test():
    reg=register_points([[0,0],[10,0],[0,10]],[[5,5],[10,5],[5,10]],0.01)
    assert reg['registration_verified'] and reg['scale']==2
    assert not register_points([[0,0],[10,0],[0,10]],[[5,5],[10,5],[5,15]],0.01)['registration_verified']
    a=dict(control_id="test",context_sha256="fixture",registration_verified=True,evidence_sha256="fixture",control=0.,actual=10.)
    b=dict(a,control=1.,actual=12.)
    result=correction_loop(13,0.01,[a,b],lambda c:dict(b,control=c,actual=10+2*c),lambda prior:True,0.25,(-2,2),100,lambda:0)
    assert result["status"]=="WITHIN_TOLERANCE" and len(result["history"])==2
    assert bounded_correction(16,0.5,[a,b],1,0.25,(-2,2))["control"]==1.25
    assert bounded_correction(12,0.5,[a,b],1,0.25,(-2,2))["status"]=="WITHIN_TOLERANCE"
    assert bounded_correction(16,0.5,[a,dict(b,actual=10)],1,0.25,(-2,2))["status"]=="BLOCKED_NO_RESPONSE"
    try:
        bounded_correction(16,0.5,[a,dict(b,context_sha256="stale")],1,0.25,(-2,2))
    except ValueError:
        pass
    else:
        raise AssertionError("stale context accepted")

def batch_summary(rows, stages):
    modules={}
    for name in ("face","body","hair","wardrobe","equipment"):
        subset=[r for r in rows if r["module"]==name]
        counts={k:sum(r["status"]==k for r in subset) for k in ("PASS","FAIL","BLOCKED","NOT_RUN")}
        events=[v for k,v in stages if k==name or k.startswith(name+"-")]
        modules[name]=dict(counts=counts,events=events,
            status="BLOCKED" if counts["BLOCKED"] or any(v.startswith("BLOCKED") for v in events)
            else "FAIL" if counts["FAIL"] else "NOT_RUN" if counts["NOT_RUN"]
            else "MEASUREMENT_PASS_NOT_ADOPTED")
    return modules

def validate_batch_plan(plan, root):
    for key in ("blueprint","wardrobe"):
        entry=plan[key]
        path=root/entry["path"]
        data=path.read_bytes()
        blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
        if blob!=entry["blob"]:
            raise ValueError("stale batch dependency: "+key)
    stages=plan["stages"]
    seen=set()
    for stage in stages:
        if stage["id"] in seen or not set(stage["depends"])<=seen or not stage["accept"]:
            raise ValueError("invalid stage dependency graph")
        seen.add(stage["id"])
    if seen!={"face","hair","body","wardrobe","equipment"}:
        raise ValueError("incomplete stage inventory")
    return [dict(id=s["id"],depends=s["depends"],accept=s["accept"],
                 mutation="BLOCKED_UNQUALIFIED_ADAPTER",survey_allowed=s["id"] in plan["independent_surveys"])
            for s in stages]

def verify_observation_files(data, root):
    """Measurements must refer to actual immutable evidence in the run directory."""
    root=root.resolve()
    for obs in data["observations"].values():
        path=(root/obs["evidence_path"]).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("missing or unsafe measurement evidence")
        if sha(path)!=obs["evidence_sha256"]:
            raise ValueError("measurement evidence digest mismatch")
        model=(root/obs["model_path"]).resolve()
        if not model.is_relative_to(root) or not model.is_file():
            raise ValueError("missing native measurement checkpoint")
        if sha(model)!=obs["model_sha256"]:
            raise ValueError("measurement checkpoint digest mismatch")

def measured_face_observations(bp, packet, root):
    """Convert independently annotated original-pixel points to measured targets.
    Registration must use separate reviewed anchors; no self-asserted PASS.
    """
    ref=bp["face_front_review"]
    if packet["reference_sha256"]!=ref["source_sha256"]:
        raise ValueError("wrong reference")
    if packet.get("annotation_status")!="INDEPENDENTLY_REVIEWED":
        raise ValueError("unreviewed landmarks")
    verify_observation_files({"observations":{"face":packet}},root)
    if packet.get("view")!="front" or packet.get("projection_review")!="MATCHED":
        raise ValueError("unqualified projection")
    reg=register_points(packet["reference_anchors"],packet["actual_anchors"],3)
    metrics=project_face_metrics(packet["points"],reg)
    uncertainty=packet["uncertainty_px"]*reg["scale"]
    if not math.isfinite(uncertainty) or not 0<=uncertainty<=3:
        raise ValueError("insufficient landmark precision")
    return {"face.front."+k:dict(packet,actual=v,observable="matched_source_px",
        registration_verified=True,registration=reg,uncertainty_px=uncertainty)
        for k,v in metrics.items()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("blueprint",type=Path)
    p.add_argument("output",type=Path)
    p.add_argument("--observations",type=Path)
    p.add_argument("--face-packet",type=Path)
    p.add_argument("--evidence-root",type=Path)
    p.add_argument("--diagnostic-face",type=Path)
    p.add_argument("--stages",type=Path)
    p.add_argument("--batch-plan",type=Path)
    a=p.parse_args()
    self_test()
    fingerprint=sha(a.blueprint)
    rows=compile_targets(json.loads(a.blueprint.read_text()))
    if a.observations:
        data=json.loads(a.observations.read_text())
        if data["blueprint_sha256"]!=fingerprint:
            raise ValueError("stale blueprint")
        if not a.evidence_root:
            raise ValueError("evidence root required for observations")
        verify_observation_files(data,a.evidence_root)
        compare(rows,data["observations"])
    if a.face_packet:
        if not a.evidence_root or a.observations:
            raise ValueError("face packet needs evidence root and exclusive input")
        compare(rows,measured_face_observations(json.loads(a.blueprint.read_text()),json.loads(a.face_packet.read_text()),a.evidence_root))
    diagnostics=[]
    if a.diagnostic_face:
        trial=json.loads(a.diagnostic_face.read_text())
        bp=json.loads(a.blueprint.read_text())
        if trial["reference_sha256"]!=bp["face_front_review"]["source_sha256"]:
            raise ValueError("wrong diagnostic reference")
        diagnostics=ratio_diagnostics(bp["face_front_review"]["projected_metrics_px"],trial["raw_metrics"])
    plan=[]
    if a.batch_plan:
        plan=validate_batch_plan(json.loads(a.batch_plan.read_text()),Path.cwd())
    stages=[]
    if a.stages and a.stages.exists():
        stages=[tuple(line.split("\t",1)) for line in a.stages.read_text().splitlines()[1:] if "\t" in line]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(dict(blueprint_sha256=fingerprint,targets=rows,face_ratio_diagnostics=diagnostics,modules=batch_summary(rows,stages),execution_plan=plan,
        status="MEASUREMENT_LEDGER_NOT_ART_QA",
        gaps=["matched camera registration","native control calibration","body tolerance",
              "hidden geometry","equipment attachment and clearance","UV rig deformation runtime"]),indent=2)+"\n")
if __name__=="__main__":
    main()
