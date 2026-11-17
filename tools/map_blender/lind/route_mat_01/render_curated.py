"""Render saved Method C geometry without rerunning sculpt/boolean work."""
import bpy,sys,json,hashlib
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1]).resolve()
s=bpy.context.scene;s.cycles.use_denoising=False;s.cycles.samples=64
# Save runtime-capable render settings before separately reopening for mesh audit.
bpy.ops.wm.save_as_mainfile(filepath=str(out/'abutment.blend'),compress=True)
for name in ['front','oblique','side']:
 s.camera=bpy.data.objects['QA_'+name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
(out/'build.json').write_text(json.dumps({'method':s['method'],'blender':bpy.app.version_string,'metric_status':s['metric_status'],'canonical_world_transform':None,'source_geometry':'CC0 Poly Haven boulder_01 and rock_07; exact originals preserved in sources','materials':'neutral clay; no texture/normal/height image inputs','samples':64,'denoising':False,'recovery':'geometry build saved; local Blender lacks OpenImageDenoise; renderer only resumed','G1':'BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'},indent=2))
