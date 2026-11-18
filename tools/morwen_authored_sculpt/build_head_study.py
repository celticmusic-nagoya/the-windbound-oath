"""Morwen original head/face and bob-hair surface study, candidate only.
Blender 5.2.4. Provisional local axes Z up, face -Y. No failed mesh imported.
Not a completed character; requires four-view image visual calibration.
"""
import bpy, math, json, hashlib, sys
from mathutils import Vector
from pathlib import Path

out=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else Path('/tmp/morwen-sculpt')
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene['asset']='MORWEN'; scene['status']='UNAPPROVED_ORIGINAL_HEAD_SURFACE_STUDY'
scene['unit_status']='PROVISIONAL_NOT_CANONICAL'; scene['forward']='-Y'; scene['up']='Z'
scene.render.engine='CYCLES'; scene.cycles.device='CPU'; scene.cycles.samples=16; scene.render.threads_mode='FIXED'; scene.render.threads=2; scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world.color=(0.18,0.18,0.18)
def mat(name,c,metal=0,rough=.65):
 m=bpy.data.materials.new(name);m.diffuse_color=(*c,1);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 return m
skin=mat('skin_warm_provisional',(.68,.48,.43));hair=mat('bob_dark_violet',(.075,.044,.12));iris=mat('iris_violet',(.35,.17,.55));gold=mat('gold_glasses',(.68,.46,.13),.72,.28)
def surface(name,levels,segments=80,material=None):
 verts=[];faces=[]
 for z,rx,ry,cy in levels:
  for j in range(segments):
   t=2*math.pi*j/segments
   # Face is -Y: subtly flatter back, tapered jaw and sculpted cheeks
   x=rx*math.cos(t)
   y=cy+ry*math.sin(t)
   if name=='Face_Sculpt_Study' and math.sin(t)<-.45:
    cheek=math.exp(-((z-1.48)/.115)**2)
    y-=.018*cheek*(.5+.5*abs(math.cos(t)))
   verts.append((x,y,z))
 for i in range(len(levels)-1):
  for j in range(segments):
   a=i*segments+j;b=i*segments+(j+1)%segments
   faces.append((a,b,b+segments,a+segments))
 faces.append(tuple(reversed(range(segments))))
 k=(len(levels)-1)*segments;faces.append(tuple(k+j for j in range(segments)))
 mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
 if material:ob.data.materials.append(material)
 for p in mesh.polygons:p.use_smooth=True
 return ob
# Independent ring-sculpt, not a repaired old cage; deliberate cranial, cheek, jaw and chin sections.
face=surface('Face_Sculpt_Study',[(1.20,.055,.065,.005),(1.23,.09,.09,.005),(1.28,.13,.115,0),(1.35,.17,.145,0),(1.43,.205,.166,.005),(1.51,.222,.175,.01),(1.59,.219,.173,.012),(1.67,.205,.162,.017),(1.74,.18,.144,.018),(1.80,.135,.112,.02),(1.83,.055,.05,.02)],material=skin)
# Dark straight bob with crown, cheek-length sides and independently shaped front bangs.
bob=surface('Hair_Crown_and_Bob_Study',[(1.34,.215,.18,.035),(1.40,.245,.199,.041),(1.52,.253,.208,.045),(1.64,.246,.202,.045),(1.74,.227,.186,.046),(1.82,.179,.148,.047),(1.86,.095,.083,.047)],material=hair)
# Two individual frontal hair curtains, separated by central fringe gap.
def hair_curtain(name,sign):
 v=[];f=[]
 for i in range(15):
  z=1.48+i*.021
  for j in range(13):
   u=j/12
   x=sign*(.045+.165*u)*(1-.05*i/14)
   y=-.177-.033*math.sin(math.pi*u)-.006*math.sin(i*.55)
   v.append((x,y,z))
 for i in range(14):
  for j in range(12):
   a=i*13+j;f.append((a,a+1,a+14,a+13))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update()
 ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob);mesh.materials.append(hair)
 for p in mesh.polygons:p.use_smooth=True
hair_curtain('Straight_Fringe_Left',-1);hair_curtain('Straight_Fringe_Right',1)
# Glasses are geometric placement guides, not finished optical frames.
def tube(name,points,radius,material):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3
 spl=curve.splines.new('POLY');spl.points.add(len(points)-1)
 for p,co in zip(spl.points,points):p.co=(*co,1)
 ob=bpy.data.objects.new(name,curve);scene.collection.objects.link(ob);curve.materials.append(material)
for sign in (-1,1):
 pts=[(sign*(.105+.064*math.cos(t)), -.173-.018*math.sin(t),1.535+.063*math.sin(t)) for t in [2*math.pi*i/64 for i in range(65)]]
 tube('Gold_Round_Glasses_Guide_'+str(sign),pts,.003,gold)
tube('Glasses_Bridge_Guide',[(-.042,-.195,1.548),(0,-.21,1.555),(.042,-.195,1.548)],.003,gold)
# Three review lights.
for pos,power,size in [((2,-3,4),850,3),((-2,-1,3),500,2),((0,2,3),900,2)]:
 d=bpy.data.lights.new('Review_Area','AREA');d.energy=power;d.shape='DISK';d.size=size
 o=bpy.data.objects.new('Review_Area',d);scene.collection.objects.link(o);o.location=pos
 o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
def render(name,loc):
 bpy.ops.object.camera_add(location=loc);cam=bpy.context.object;cam.name='Review_'+name
 cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat('-Z','Y').to_euler()
 cam.data.type='ORTHO';cam.data.ortho_scale=.94;scene.camera=cam
 scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(cam,do_unlink=True)
if '--export-only' not in sys.argv:\n for name,loc in [('front',(0,-4,1.54)),('back',(0,4,1.54)),('left',(-4,0,1.54)),('right',(4,0,1.54)),('three_quarter',(3,-3,1.8))]:render(name,loc)
# Temporary technical input only: no official artwork or production meshes are overwritten.
bpy.ops.object.select_all(action='DESELECT')
export_objects=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.name.startswith('Review_')]
for o in export_objects:o.select_set(True)
bpy.context.view_layer.objects.active=face
bpy.ops.export_scene.gltf(filepath=str(out/'morwen_head_study.glb'),export_format='GLB',use_selection=True)
assert (out/'morwen_head_study.glb').stat().st_size>0
bpy.ops.object.select_all(action='DESELECT')
blend=out/'MORWEN_HEAD_SCULPT_STUDY_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'asset':'Morwen','status':'UNAPPROVED_HEAD_STUDY_ONLY','method':'new independently authored ring sculpt with separate bob and fringe; no failed geometry reused','blender':bpy.app.version_string,'mesh_objects':{o.name:len(o.data.vertices) for o in scene.objects if o.type=='MESH'},'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'renders':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.png')},'G1':'BLOCKED_VISUAL_CALIBRATION','G2':'NOT_RUN_INDEPENDENT_ART','G3':'NOT_RUN_TOPOLOGY_UV_RIG','G4':'NOT_RUN'}
(out/'QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('MORWEN_HEAD_STUDY_CREATED',report['mesh_objects'])
