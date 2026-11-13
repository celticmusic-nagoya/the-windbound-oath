"""Validate production promotion gate against known blocked fixture.
No Blender dependency; runs on every change to production_mesh_05.
"""
import json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
gate=ROOT/"tools/blender/production_mesh_05/preflight.py"
fixture=ROOT/"docs/design/MORWEN_BODY_04_PROMOTION_GATE.json"
proc=subprocess.run([sys.executable,str(gate),"--manifest",str(fixture)],capture_output=True,text=True)
assert proc.returncode==1,proc.stderr
d=json.loads(proc.stdout)
assert d["status"]=="BLOCKED"
assert "nonproduction_mesh_method" in d["errors"]
assert "art_qa_not_passed" in d["errors"]
# A complete PASS fixture must be accepted; prevents gate from always failing.
valid=json.loads(fixture.read_text())
valid.update(reference_available=True,view_alignment="PASS",silhouette_comparison="PASS",
             topology_deformation="PASS",asymmetry_check="PASS",art_qa="PASS",
             technical_qa="PASS",promotion_eligible=True,attempt_count=1,
             mesh_method="reference_aligned_continuous_mesh")
with tempfile.TemporaryDirectory() as tmp:
    path=Path(tmp)/"valid.json";path.write_text(json.dumps(valid))
    result=subprocess.run([sys.executable,str(gate),"--manifest",str(path)],capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
print("PROMOTION_GATE_TEST_PASS")
