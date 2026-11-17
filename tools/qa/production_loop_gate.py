#!/usr/bin/env python3
"""Shared fail-closed render/review/repair controller. Stdlib only; no writes to canon."""
import argparse,json,pathlib,sys

STATES={"PASS","FAIL","BLOCKED","NOT_RUN"}
def decide(d):
    required=("G1","G2","G3","G4")
    gates=d.get("gates",{})
    if any(gates.get(k) not in STATES for k in required):
        return "BLOCKED","Missing or invalid G1-G4 evidence"
    if gates["G1"]!="PASS":
        return "BLOCKED","Canonical alignment must PASS before progression"
    if d.get("source_verified") is not True or d.get("render_sha256_verified") is not True:
        return "BLOCKED","Source/render hashes not verified"
    if gates["G3"]=="FAIL":
        return retry(d,"Technical failure")
    if gates["G3"]!="PASS":
        return "BLOCKED","Technical QA not PASS"
    if gates["G2"]=="FAIL":
        return retry(d,"Art QA failed")
    if gates["G2"]!="PASS":
        return "BLOCKED","Independent art QA not PASS"
    if gates["G4"]=="FAIL":
        return retry(d,"Game/device QA failed")
    if gates["G4"]!="PASS":
        return "BLOCKED","Game/device QA not PASS"
    return "NEXT_STAGE","All four evidence gates PASS"

def retry(d,reason):
    family=d.get("method_family")
    count=d.get("same_cause_attempts")
    if not isinstance(family,str) or not family.strip() or type(count) is not int or count<0:
        return "BLOCKED","Method-family and cumulative attempt count required"
    if count>=2:return "METHOD_SWITCH_REQUIRED",reason+"; two attempts exhausted"
    if d.get("repair_plan_approved") is not True:return "BLOCKED",reason+"; no approved repair plan"
    if d.get("repair_is_non_destructive") is not True:return "BLOCKED","Repair safety not verified"
    return "REPAIR_AND_RENDER",reason+"; approved scoped retry"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("input");p.add_argument("output")
    a=p.parse_args()
    data=json.loads(pathlib.Path(a.input).read_text())
    state,reason=decide(data)
    out={"schema":"TWO_PRODUCTION_LOOP_GATE_V1","decision":state,"reason":reason,"source_commit":data.get("source_commit"),"method_family":data.get("method_family"),"same_cause_attempts":data.get("same_cause_attempts"),"gates":data.get("gates"),"automatic_formal_adoption":False,"main_merge_authorized":False}
    dst=pathlib.Path(a.output);dst.parent.mkdir(parents=True,exist_ok=True)
    dst.write_text(json.dumps(out,indent=2)+"\n")
    print(json.dumps({"decision":state,"reason":reason}))
    return 0 if state in {"NEXT_STAGE","REPAIR_AND_RENDER","METHOD_SWITCH_REQUIRED","BLOCKED"} else 1
if __name__=="__main__":sys.exit(main())
