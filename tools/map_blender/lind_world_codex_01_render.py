"""Recover renders from existing candidate geometry; never regenerate or overwrite it."""
import bpy,sys,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'assets/candidates/lind-spatial-codex-01/world';target=out/'world-renderable.blend'
if target.exists():raise FileExistsError(target)
s=bpy.context.scene;s.cycles.use_denoising=False
src=root/'assets/sources/lind-world-20261116/original.png';expected='abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620';assert hashlib.sha256(src.read_bytes()).hexdigest()==expected
im=bpy.data.images.load(str(src),check_existing=True);im.pack();im.use_fake_user=True
bpy.ops.wm.save_as_mainfile(filepath=str(target))
for name in ['overview','coast','river']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'schema':'lind-world-candidate-v1','primary_blend':'world-renderable.blend','blender_version':bpy.app.version_string,'source_sha256':expected,'method_family':'continuous_signed_distance_terrain_plus_channel_incision','coordinates_status':'CANDIDATE_UNSCALED','meters_per_unit':None,'terrain_vertices':len(bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'].data.vertices),'terrain_faces':len(bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'].data.polygons),'G1':'BLOCKED_SPATIAL_EVENT_REVIEW','G2':'INDEPENDENT_REVIEW_REQUIRED','G3':'PARTIAL_RENDER_ONLY','G4':'NOT_RUN','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ['.blend','.png']}}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('WORLD_RENDER_RECOVERY_COMPLETE')
