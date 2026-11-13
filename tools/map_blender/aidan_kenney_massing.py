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
# Procedural surface detail: no external texture dependencies.
def textured(material,scale,strength,distance,light,dark):
 nodes=material.node_tree.nodes;links=material.node_tree.links
 bsdf=nodes.get('Principled BSDF')
 tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale
 tex.inputs['Detail'].default_value=4.0;tex.inputs['Roughness'].default_value=.72
 ramp=nodes.new('ShaderNodeValToRGB')
 ramp.color_ramp.elements[0].position=.22;ramp.color_ramp.elements[0].color=(*dark,1)
 ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(*light,1)
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=strength
 bump.inputs['Distance'].default_value=distance
 links.new(tex.outputs['Fac'],ramp.inputs['Fac'])
 links.new(tex.outputs['Fac'],bump.inputs['Height'])
 links.new(ramp.outputs['Color'],bsdf.inputs['Base Color'])
 links.new(bump.outputs['Normal'],bsdf.inputs['Normal'])
textured(stone,23,.35,.045,(.58,.54,.44),(.29,.28,.24))
textured(wood,31,.22,.018,(.31,.19,.11),(.105,.061,.034))
textured(thatch,78,.42,.055,(.65,.47,.22),(.27,.19,.075))
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
   # Kenney GLBs reference external/packed textures that render magenta in headless CI.
   # Replace only copied-source appearance with deterministic procedural palettes.
   for ob in objects:
    for slot in ob.material_slots:
     if 'roof' in name: slot.material=thatch
     elif 'wood' in name or 'pillar' in name or 'door' in name or 'shutters' in name: slot.material=wood
     else: slot.material=stone
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
  # ARCHITECTURAL STRUCTURE V2: original timber trusses and individually
  # staggered thatch courses. Kenney reference remains in the .blend but
  # no longer dictates the roof geometry.
  for x in range(-3,4):
   for side in (-1,1):
    y=side*2.16
    beam=box('roof rafter %d %d'%(x,side),(x,y/2,3.30),(.105,2.62,.16),wood,.025)
    beam.rotation_euler.x=-side*math.radians(33.4)
  # Ridge and edge beams, independent of source mesh dimensions
  box('continuous oak ridge',(0,0,4.25),(6.9,.18,.20),wood,.035)
  for side in (-1,1):
   box('oak fascia',(0,side*2.35,2.58),(7.05,.20,.24),wood,.035)
  for side in (-1,1):
   # A continuous watertight under-roof; individual thatch pieces are surface detail.
   backing=box('continuous pitched roof substrate %d'%side,(0,side*1.23,3.395),(7.12,2.98,.16),thatch,.025)
   backing.rotation_euler.x=-side*math.radians(33.4)
   for course in range(13):
    y=side*(.13+course*.19)
    z=4.21-(abs(y)/2.47)*1.63
    for col in range(20):
     x=-3.38+col*.356+(course%2)*.13
     jitter=random.uniform(-.025,.025)
     piece=box('hand laid thatch %d %d %d'%(side,course,col),
       (x+jitter,y,z),(.39,.29,.085),thatch,.018)
     piece.rotation_euler.x=-side*math.radians(33.4)
  # Broken eaves: dense loose straw ends along the roof lip, varied in length.
  # The surface shader supplies micro-fibres; these curves supply silhouette detail.
  straw_dark=mat('straw shadow tips',(.32,.23,.10))
  for side in (-1,1):
   for i in range(150):
    x=-3.46+i*(6.92/149)+random.uniform(-.012,.012)
    y=side*(2.40+random.uniform(-.025,.045))
    z=2.62+random.uniform(-.065,.065)
    length=random.uniform(.09,.27)
    curve=bpy.data.curves.new('eave fibre','CURVE');curve.dimensions='3D'
    curve.bevel_depth=.006;curve.bevel_resolution=1
    spline=curve.splines.new('POLY');spline.points.add(1)
    spline.points[0].co=(x,y,z,1)
    spline.points[1].co=(x+random.uniform(-.03,.03),y+side*length,z-random.uniform(.07,.19),1)
    obj=bpy.data.objects.new('loose straw tip',curve);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(straw_dark if i%5==0 else thatch)
  # Structural gate: roof substrates must be present on both pitches.
  substrates=[o for o in bpy.data.objects if o.name.startswith('continuous pitched roof substrate')]
  assert len(substrates)==2, 'Missing watertight roof substrate'
  assert all(abs(o.rotation_euler.x)>0.4 for o in substrates), 'Roof slope not applied'
  # chimney: coursed stone stack and cap with visible opening
  for course in range(11):
   z=2.65+course*.19
   for face in range(4):
    angle=face*math.pi/2
    x=1.85+math.cos(angle)*.36
    y=.95+math.sin(angle)*.36
    block=box('chimney dressed stone %02d %d'%(course,face),
      (x,y,z),(.78,.18,.19) if face%2 else (.18,.78,.19),stone,.025)
  box('chimney lip',(1.85,.95,4.80),(1.06,1.06,.17),stone,.035)
  box('chimney dark flue',(1.85,.95,4.90),(.61,.61,.025),wood,.008)
  # Exposed structural timber grid across the facade
  for x in (-2.5,-1.5,-.5,.5,1.5,2.5):
   box('front timber stud %.1f'%x,(x,-2.21,1.57),(.115,.14,2.05),wood,.018)
  for z in (.78,1.65,2.52):
   box('front continuous timber rail %.2f'%z,(0,-2.22,z),(6.55,.15,.13),wood,.02)
  # Door is a separate joinery assembly, not a painted wall rectangle.
  box('recessed oak entrance',(0,-2.32,1.32),(1.03,.12,1.85),wood,.05)
  for x in (-.35,-.12,.12,.35):
   box('vertical door plank %.2f'%x,(x,-2.40,1.32),(.18,.05,1.76),wood,.012)
  box('door stone lintel',(0,-2.47,2.34),(1.37,.34,.23),stone,.05)
  for x in (-.57,.57):
   box('door oak jamb %.2f'%x,(x,-2.43,1.33),(.13,.21,2.06),wood,.022)
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
