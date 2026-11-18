"""Read existing local checkpoint for stable-ID retopology input."""
from pathlib import Path
import json,bpy
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01';Q.mkdir(parents=True,exist_ok=True)
p=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend';bpy.ops.wm.open_mainfile(filepath=str(p),use_scripts=False,load_ui=False);o=bpy.data.objects['MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED'];bpy.context.view_layer.update()
(Q/'source-mesh.json').write_text(json.dumps({'world':[list(o.matrix_world@v.co) for v in o.data.vertices],'local':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}))
