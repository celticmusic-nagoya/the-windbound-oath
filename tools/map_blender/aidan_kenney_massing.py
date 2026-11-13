"""Aidan home: Kenney-derived architectural massing review, NOT G2 approved."""
import bpy,sys,zipfile,tempfile,pathlib,math,json,random
from mathutils import Vector
args=sys.argv[sys.argv.index('--')+1:]
archive,out=pathlib.Path(args[0]),pathlib.Path(args[1]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
random.seed(271828)
def mat(name,color,rough=0.85):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
 return m
stone=mat('warm weathered limestone',(0.46,0.43,0.35));wood=mat('dark hand-oiled oak',(0.19,0.115,0.075));thatch=mat('aged straw thatch',(0.48,0.32,0.13));earth=mat('earth',(0.25,0.29,0.20))
def box(name,loc,scale,material,bevel=0.0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(material)
 if bevel: mod=o.modifiers.new('hand-softened edges','BEVEL');mod.width=bevel;mod.segments=2;o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 assert 'CC0' in z.read('LICENSE_KENNEY.txt').decode('utf8','replace')
 with tempfile.TemporaryDirectory() as t:
  z.extractall(t)
  cache={}
  for name in ['wall-block','wall-corner','wall-wood','pillar-wood','roof-gable','roof-gable-end','roof-gable-top','wall-window-shutters','wall-door','chimney','chimney-top','roof-high-gable']:
   before=set(bpy.data.objects)
   bpy.ops.import_scene.gltf(filepath=str(pathlib.Path(t)/'models'/f'{name}.glb'))
   objects=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
   assert objects,name
   cache[name]=objects
   for ob in objects: ob.hide_render=True;ob.hide_set(True)
  def place(name,xyz,scale=(1,1,1),rotation=0):
   for src in cache[name]:
    obj=src.copy();obj.data=src.data.copy();bpy.context.collection.objects.link(obj)
    obj.name='Kenney_base_'+name;obj.hide_render=False;obj.hide_set(False)
    obj.location=xyz;obj.scale=scale;obj.rotation_euler.z=rotation
    return obj
  # 6 x 4 module cottage, stone plinth and timbered walls
  box('continuous irregular plinth',(0,0,0.22),(6.8,4.8,0.44),stone,.10)
  for x in range(-3,4):
   for y in [-2,2]:
    if y==-2 and x==0: part='wall-door'
    elif y==-2 and x in (-2,2):part='wall-window-shutters'
    else:part='wall-block'
    place(part,(x,y,0.44),(1,1,2.15),math.pi/2 if y==-2 else -math.pi/2)
  for y in range(-1,2):
   for x in [-3,3]:
    place('wall-window-shutters' if y==0 else 'wall-block',(x,y,0.44),(1,1,2.15),0 if x==3 else math.pi)
  for x in [-3,3]:
   for y in [-2,2]:
    place('pillar-wood',(x,y,0.45),(1,1,2.25))
  for y in [-2,2]:
   box('hand cut eave beam',(0,y,2.65),(6.7,.18,.20),wood,.035)
  for x in [-3,3]:
   box('gable tie beam',(x,0,2.65),(.18,4.4,.2),wood,.025)
  # overlapping gable roof modules with visible pitched silhouette
  for x in range(-3,4):
   place('roof-high-gable',(x,0,2.7),(1.06,4.7,1.25))
  # chimney and capped top
  place('chimney',(1.8,0.9,2.5),(1.2,1.2,2.0))
  place('chimney-top',(1.8,0.9,4.5),(1.2,1.2,1.0))
  # handcrafted beams and entrance furniture
  for x in [-2.7,2.7]:
   box('exposed wall brace',(x,-2.15,1.55),(.14,.16,2.0),wood,.035)
  box('front doorstep',(0,-2.45,.40),(1.4,.8,.25),stone,.08)
  box('packed earth clearing',(0,0,-.1),(12,10,.2),earth,.15)
  # scatter non-identical small stones along footpath
  for i in range(36):
   x=random.uniform(-1.2,1.2);y=random.uniform(-4.6,-2.7)
   box('path stone %02d'%i,(x,y,.02),(random.uniform(.12,.36),random.uniform(.12,.33),.07),stone,.035)
  world=bpy.context.scene.world;world.color=(.32,.34,.37)
  def camera(name,loc):
   bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=name
   direction=Vector((0,0,1.7))-o.location;o.rotation_euler=direction.to_track_quat('-Z','Y').to_euler()
   o.data.type='ORTHO';o.data.ortho_scale=11.8;return o
  bpy.ops.object.light_add(type='AREA',location=(-3,-4,9));bpy.context.object.data.energy=1600;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=7
  scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
  scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
  scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
  for name,loc in [('front',(8,-10,7)),('rear',(-8,10,7)),('left',(-10,-7,7)),('right',(10,7,7)),('top',(8,-8,13))]:
   scene.camera=camera(name,loc);scene.render.filepath=str(out/f'aidan_{name}.png');bpy.ops.render.render(write_still=True)
  bpy.ops.wm.save_as_mainfile(filepath=str(out/'aidan_kenney_massing.blend'))
  (out/'QA_STATUS.json').write_text(json.dumps({'stage':'ARCHITECTURAL_MASSING_REVIEW','G1':'PARTIAL','G2':'NOT_RUN','G3':'PENDING_IMAGE_INSPECTION','G4':'NOT_RUN','models':len(cache),'views':5},indent=2))
