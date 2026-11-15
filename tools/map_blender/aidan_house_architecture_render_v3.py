"""Blender headless five-view diagnostic renderer for Aidan v3."""
import bpy,os,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aidan_house_architecture_v3 import build
out=Path(os.environ.get('AIDAN_V3_OUTPUT','/tmp/aidan-v3-qa'));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
report=build()
world=bpy.context.scene.world or bpy.data.worlds.new('v3 neutral world')
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.67,.70,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
bpy.ops.object.light_add(type='AREA',location=(-6,-9,12))
lamp=bpy.context.object;lamp.data.energy=1800;lamp.data.shape='DISK';lamp.data.size=9
bpy.ops.object.camera_add()
cam=bpy.context.object;cam.data.type='ORTHO';cam.data.ortho_scale=15
scene=bpy.context.scene;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=16
scene.render.resolution_x=800;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
target=Vector((0,0,2.4))
views={'front':(0,-15,8),'rear':(0,15,8),'left':(-15,0,8),'right':(15,0,8),'game27':(11,-11,9.4)}
report['views']=[]
for name,pos in views.items():
 cam.location=pos
 direction=target-cam.location
 cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
 path=out/('aidan_v3_'+name+'.png');scene.render.filepath=str(path)
 bpy.ops.render.render(write_still=True)
 report['views'].append({'name':name,'file':path.name,'bytes':path.stat().st_size,
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
bpy.ops.wm.save_as_mainfile(filepath=str(out/'aidan_v3_diagnostic.blend'))
(out/'manifest.json').write_text(json.dumps(report,indent=2))
print('AIDAN_V3_RENDER='+json.dumps(report))
