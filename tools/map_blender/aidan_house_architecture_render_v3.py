"""Blender headless five-view diagnostic renderer for Aidan v3."""
import bpy,os,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aidan_house_architecture_v3 import build
out=Path(os.environ.get('AIDAN_V3_OUTPUT','/tmp/aidan-v3-qa'));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
report=build()
from aidan_house_architecture_v3 import roof_normal
bad_normals=[]
for ob in bpy.data.objects:
 if ob.type!='MESH' or not ob.data.polygons:continue
 if ob.name.startswith('slate_'):
  side=-1 if sum(v.co.y for v in ob.data.vertices)/len(ob.data.vertices)<0 else 1
  if ob.data.polygons[0].normal.dot(roof_normal(side))<.5:bad_normals.append(ob.name)
 if ob.name.startswith('stone gable end'):
  x=sum(v.co.x for v in ob.data.vertices)/len(ob.data.vertices)
  if ob.data.polygons[0].normal.x*(1 if x>0 else -1)<.5:bad_normals.append(ob.name)
assert not bad_normals,'Incorrect outward normals: '+str(bad_normals[:12])
assert len([o for o in bpy.data.objects if o.name.startswith('stone gable end')])==2
assert report['porch_type']=='A_BELOW_EAVES'
report['geometry_qa']={'bad_outward_normals':len(bad_normals),'gable_count':2,'porch_clearance_below_eaves_m':round(report['dimensions']['eaves']-2.96,3)}

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
horizontal=15
vertical=horizontal*math.tan(math.radians(27))
views={'front':(0,-15,8),'rear':(0,15,8),'left':(-15,0,8),'right':(15,0,8),
       'game27':(horizontal/math.sqrt(2),-horizontal/math.sqrt(2),2.4+vertical)}
report['game_camera_elevation_degrees']=27.0
ground=bpy.data.materials.new('v3 neutral ground');ground.diffuse_color=(.36,.37,.36,1)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.34))
bpy.context.object.name='QA ground (not exported)'
bpy.context.object.data.materials.append(ground)
bpy.ops.object.light_add(type='SUN',location=(4,-7,14))
bpy.context.object.data.energy=1.2

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
