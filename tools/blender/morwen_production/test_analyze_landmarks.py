"""Self-contained positive/negative tests; no real annotation is invented."""
import importlib.util
from pathlib import Path
script=Path(__file__).with_name("analyze_landmarks.py")
spec=importlib.util.spec_from_file_location("morwen_landmarks",script)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def empty():
 return {"schema":"MORWEN-LANDMARK-REVIEW-UNAPPROVED","coordinate_system":"image top-left; 384x1024","views":{k:{} for k in ("front","right","back","left")}}
d=empty()
r=module.analyze(d)
assert r["measured_points"]==0 and r["metrics"]=={}
d["views"]["front"]={"head_top":{"x":180,"y":100,"confidence":"MANUAL_UNREVIEWED"},"chin":{"x":180,"y":300,"confidence":"MANUAL_UNREVIEWED"},"left_eye_center":{"x":150,"y":180,"confidence":"MANUAL_UNREVIEWED"},"right_eye_center":{"x":210,"y":180,"confidence":"MANUAL_UNREVIEWED"}}
r=module.analyze(d)
assert r["measured_points"]==4
assert r["metrics"]["front_eye_separation_to_head_height"]==.3
for bad in ({"x":-1,"y":180,"confidence":"MANUAL_UNREVIEWED"},{"x":100,"y":180,"confidence":"APPROVED"}):
 d["views"]["front"]["head_top"]=bad
 try:module.analyze(d)
 except (AssertionError,KeyError,TypeError,ValueError):pass
 else:raise AssertionError("Invalid annotation accepted")
print("MORWEN-REBUILD-04 analysis unit tests PASS")
