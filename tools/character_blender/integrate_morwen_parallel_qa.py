"""Fail-closed Morwen parallel lane integration report. No file mutations."""
import argparse,json,pathlib,sys
p=argparse.ArgumentParser()
p.add_argument("--root",required=True)
p.add_argument("--out",required=True)
a=p.parse_args()
root=pathlib.Path(a.root)
report={"schema":"TWO_MORWEN_PARALLEL_GATE_V1","lanes":{},"artistic_qa":"NOT_RUN","game_qa":"NOT_RUN","canonical_promotion":"BLOCKED","overall":"BLOCKED"}
def load(role,filename):
 path=root/role/filename
 if not path.is_file():return {"status":"BLOCKED_MISSING_REPORT"}
 try:return json.loads(path.read_text(encoding="utf-8"))
 except (OSError,ValueError) as e:return {"status":"BLOCKED_INVALID_REPORT","error":str(e)}
canonical=load("canonical","report.json")
report["lanes"]["canonical"]={"status":"PASS" if canonical.get("status")=="PASS" and len(canonical.get("results",[]))==5 and all(x.get("status")=="PASS" for x in canonical["results"]) else "BLOCKED"}
design=load("design","report.json")
report["lanes"]["design"]={"status":"PASS_REFERENCE_INPUTS_ONLY" if design.get("status")=="PASS_REFERENCE_INPUTS_ONLY" and design.get("canonical_unchanged") is True else "BLOCKED"}
art=load("art-review","report.json")
report["lanes"]["art-review"]={"status":"BLOCKED_VISUAL_REVIEW_REQUIRED" if art.get("status")=="BLOCKED_VISUAL_REVIEW_REQUIRED" and art.get("canonical_unchanged") is True else "BLOCKED_MISSING_OR_INVALID_EVIDENCE"}
rig=load("rig","MORWEN_RIG_POSE_SMOKE.json")
rig_ok=rig.get("source_unchanged") is True and rig.get("status")=="PARTIAL_TECHNICAL_MEASUREMENTS" and len(rig.get("poses",[]))==6 and all(x.get("status")=="MEASURED_ONLY" for x in rig["poses"])
report["lanes"]["rig"]={"status":"PASS_TECHNICAL_MEASUREMENTS_ONLY" if rig_ok else "BLOCKED","reported_status":rig.get("status")}
render=load("render","MORWEN_RENDER_QA_REPORT.json")
render_ok=render.get("source_unchanged") is True and render.get("status")=="PASS_TECHNICAL_FRAMING_ONLY" and any(x.get("status")=="PASS_TECHNICAL_FRAMING" for x in render.get("attempts",[]))
report["lanes"]["render"]={"status":"PASS_TECHNICAL_FRAMING_ONLY" if render_ok else "FAIL_OR_BLOCKED","reported_status":render.get("status"),"attempts":len(render.get("attempts",[]))}
report["technical_gates"]="PASS" if report["lanes"]["canonical"]["status"]=="PASS" and report["lanes"]["design"]["status"]=="PASS_REFERENCE_INPUTS_ONLY" and report["lanes"]["art-review"]["status"]=="BLOCKED_VISUAL_REVIEW_REQUIRED" and rig_ok and render_ok else "FAIL_OR_BLOCKED"
# All four production gates cannot PASS without independent artistic and in-game review.
pathlib.Path(a.out).parent.mkdir(parents=True,exist_ok=True)
pathlib.Path(a.out).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
if report["technical_gates"]!="PASS":sys.exit(1)
