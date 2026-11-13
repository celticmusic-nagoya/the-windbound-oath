"""Independent QA contract for generated Morwen FK rig artifacts."""
import json
from pathlib import Path

p = Path("render_output/morwen_motion_qa")
q = json.loads((p / "QA.json").read_text(encoding="utf-8"))
assert q["bones"] == 26 and q["fk_frames"] == 8, q
assert q["parenting_checks"] == len(q["parenting_check_names"]), q
assert q["parenting_checks"] >= 14, q
assert q["technical_rig_qa"] == "PASS", q
assert q["skin_deformation_qa"] == "BLOCKED_NO_PRODUCTION_MESH", q
assert q["production_approved"] is False, q
assert (p / "MORWEN_FK_MOTION_TEMPLATE.blend").stat().st_size > 1000
print("MORWEN_FK_ARTIFACT_QA_PASS")
