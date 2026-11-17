"""Read the existing v02 body for local sculpt input; no reference/source import."""
from pathlib import Path
import bpy,json
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend'),load_ui=False,use_scripts=False)
o=bpy.data.objects['MORWEN_BODY_FIT_V02_UNAPPROVED'];bpy.context.view_layer.update()
Path('/tmp/morwen-local-source.json').write_text(json.dumps({'coords':[list(o.matrix_world@v.co) for v in o.data.vertices],'local_coords':[list(v.co) for v in o.data.vertices],'faces':[list(p.vertices) for p in o.data.polygons]}))
