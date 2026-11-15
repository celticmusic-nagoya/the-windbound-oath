"""Reproduce the existing EYELID-05 baseline once; no new closure authoring."""
import hashlib
import json
import os
from pathlib import Path
import sys
import bpy

root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'eyelid_retopo'))
import build_eyelid_retopo_05 as B
out=Path('render_output/morwen_eyelid_structural_07')
out.mkdir(parents=True,exist_ok=True)
model=out/'BASELINE_07.blend'
if model.exists():
    raise RuntimeError('Refusing baseline overwrite')
p04=json.loads(B.E.PARAMS_PATH.read_text())
p05=json.loads(B.PARAMS_PATH.read_text())
targets=B.MT.compute()
B.M3.load()
nrec=B.E.build_base(p04)
rec,eyes,data=B.build(p05,p04,nrec,targets['targets_3d'])
# Existing source builder reproduces its recorded failed baseline. No optimization
# or retry of that stopped method is attempted here.
bpy.ops.wm.save_as_mainfile(filepath=str(model.resolve()),compress=True,copy=True)
os.environ['MORWEN_EYELID_BLEND']=str(model.resolve())
os.environ['MORWEN_SHAPEKEY_AUDIT_OUT']=str(out/'BASELINE_FINGERPRINTS_07.json')
import runpy
runpy.run_path(str(Path(__file__).with_name('verify_saved_shape_keys_07.py')),run_name='__main__')
(out/'BASELINE_BUILD_07.json').write_text(json.dumps({'status':'BASELINE_ONLY_NOT_CLOSURE_PASS','blender':bpy.app.version_string,'build':rec,'source_vrm_sha256':B.M3.sha(B.M3.SRC),'model_sha256':hashlib.sha256(model.read_bytes()).hexdigest()},indent=2)+'\n')
