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
   if name=='Face_Sculpt_Study' and math.sin(t)<-.30:
    # Continuous front-surface relief: cheek volume, recessed eye sockets,
    # brow ridge and a narrow nose bridge. No detached cheek spheres.
    front=max(0.0,-math.sin(t))
    cheek=math.exp(-((z-1.48)/.085)**2)*math.exp(-((abs(x)-.115)/.060)**2)
    socket=math.exp(-((z-1.585)/.037)**2)*math.exp(-((abs(x)-.093)/.050)**2)
    brow=math.exp(-((z-1.638)/.030)**2)*math.exp(-((abs(x)-.090)/.064)**2)
    bridge=math.exp(-((z-1.53)/.075)**2)*math.exp(-(x/.033)**2)
    chin=math.exp(-((z-1.30)/.040)**2)*math.exp(-(x/.067)**2)
    y+=front*(-.025*cheek+.016*socket-.011*brow-.026*bridge-.010*chin)
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
bob=surface('Hair_Crown_and_Bob_Study',[(1.36,.188,.171,.048),(1.40,.218,.205,.053),(1.52,.248,.223,.061),(1.64,.253,.227,.060),(1.74,.234,.211,.058),(1.82,.186,.163,.052),(1.86,.095,.083,.047)],material=hair)
# Sculpted solid hair clumps with explicit elliptical cross-sections.
# Structural method switch: no Bezier bevel strands or floating flat cards.
def hair_clump(name,stations,material,sides=10):
 verts=[];faces=[]
 for x,y,z,wx,wy in stations:
  for j in range(sides):
   theta=2*math.pi*j/sides
   verts.append((x+wx*math.cos(theta),y+wy*math.sin(theta),z))
 for i in range(len(stations)-1):
  for j in range(sides):
   k=i*sides+j;n=i*sides+(j+1)%sides
   faces.append((k,n,n+sides,k+sides))
 faces.append(tuple(reversed(range(sides))))
 q=(len(stations)-1)*sides
 faces.append(tuple(q+j for j in range(sides)))
 mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);scene.collection.objects.link(ob)
 mesh.materials.append(material)
 for poly in mesh.polygons:poly.use_smooth=True
 return ob
# Inner and outer frontal locks arch along the forehead; tips end above eyebrows.
for sign,side in [(-1,'L'),(1,'R')]:
 for layer in range(2):
  for k,x in enumerate((.035,.087,.139)):
   tip=1.675-.008*k+.012*layer
   hair_clump('Sculpt_Bangs_'+side+'_'+str(layer)+'_'+str(k),[
    (sign*(x+.016),-.105+.008*layer,1.836,.025,.020),
    (sign*(x+.009),-.164-.006*layer,1.784,.027,.017),
    (sign*x,-.193-.007*layer,1.727,.022,.013),
    (sign*(x-.005),-.198-.006*layer,tip,.003,.003)],hair)
 # Side hair starts inside crown and hugs the temples.
 for k in range(3):
  x=.184+.017*k
  hair_clump('Sculpt_Side_'+side+'_'+str(k),[
   (sign*(x-.024),-.036,1.821,.035,.032),
   (sign*x,-.114,1.727,.033,.027),
   (sign*(x+.007),-.141,1.591,.029,.025),
   (sign*(x-.007),-.104,1.443,.004,.005)],hair)
# Back bob: two staggered overlapping layers and tucked nape ends.
for layer in range(2):
 for k in range(11):
  theta=math.pi*(k+.25*layer)/10
  x=.205*math.cos(theta);y=.070+.179*math.sin(theta)
  hair_clump('Sculpt_Back_'+str(layer)+'_'+str(k),[
   (x*.68,y*.62,1.832,.033,.032),
   (x,y,1.746,.036,.034),
   (x*1.06,y+.013+.009*layer,1.586,.036,.032),
   (x*.96,y+.015,1.457,.026,.026),
   (x*.80,y-.009,1.390+.009*layer,.003,.004)],hair)
# Eye sockets, lids and highlights are separate authored geometry, not texture decals.
lid=mat('eyelid_dark_provisional',(.085,.047,.10))
white=mat('eye_sclera_provisional',(.88,.78,.77))
shine=mat('eye_highlight_provisional',(.96,.92,.95))
for sign in (-1,1):
 def ellipsoid(name,loc,scale,material):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc)
  ob=bpy.context.object;ob.name=name;ob.scale=scale;ob.data.materials.append(material)
 ellipsoid('Eye_'+str(sign),(sign*.091,-.178,1.580),(.039,.012,.021),white)
 ellipsoid('Iris_'+str(sign),(sign*.091,-.190,1.579),(.015,.006,.017),iris)
 ellipsoid('Highlight_'+str(sign),(sign*.086,-.196,1.586),(.004,.003,.005),shine)
 ellipsoid('Upper_Lid_'+str(sign),(sign*.091,-.183,1.604),(.042,.006,.006),lid)
 ellipsoid('Brow_'+str(sign),(sign*.091,-.180,1.639),(.038,.006,.006),hair)
ellipsoid('Nose_Tip',(0,-.208,1.483),(.028,.025,.021),skin)
ellipsoid('Philtrum',(0,-.166,1.446),(.014,.009,.019),skin)
ellipsoid('Upper_Lip',(0,-.167,1.419),(.036,.012,.009),skin)
ellipsoid('Lower_Lip',(0,-.165,1.403),(.032,.011,.008),skin)
ellipsoid('Mouth_Seam',(0,-.179,1.411),(.032,.004,.0025),lid)
# Glasses are geometric placement guides, not finished optical frames.
def tube(name,points,radius,material):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3
 spl=curve.splines.new('POLY');spl.points.add(len(points)-1)
 for p,co in zip(spl.points,points):p.co=(*co,1)
 ob=bpy.data.objects.new(name,curve);scene.collection.objects.link(ob);curve.materials.append(material)
for sign in (-1,1):
 pts=[(sign*(.105+.064*math.cos(t)), -.188-.018*math.sin(t),1.535+.063*math.sin(t)) for t in [2*math.pi*i/64 for i in range(65)]]
 tube('Gold_Round_Glasses_Guide_'+str(sign),pts,.003,gold)
tube('Glasses_Bridge_Guide',[(-.042,-.205,1.548),(0,-.22,1.555),(.042,-.205,1.548)],.003,gold)
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
if '--export-only' not in sys.argv:
 for name,loc in [('front',(0,-4,1.54)),('back',(0,4,1.54)),('left',(-4,0,1.54)),('right',(4,0,1.54)),('three_quarter',(3,-3,1.8))]:render(name,loc)
# Temporary technical input only: no official artwork or production meshes are overwritten.
bpy.ops.object.select_all(action='DESELECT')
export_objects=[o for o in scene.objects if o.type in {'MESH','CURVE'} and not o.name.startswith('Review_')]
for o in export_objects:o.select_set(True)
bpy.context.view_layer.objects.active=face
bpy.ops.export_scene.gltf(filepath=str(out/'morwen_head_study.glb'),export_format='GLB',use_selection=True)
assert (out/'morwen_head_study.glb').stat().st_size>0
bpy.ops.object.select_all(action='DESELECT')
blend=out/'MORWEN_HEAD_SCULPT_STUDY_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report={'asset':'Morwen','status':'UNAPPROVED_HEAD_STUDY_ONLY','method':'continuous facial surface relief (cheeks, sockets, brow, nose bridge, chin) with existing sectioned hair; unapproved','blender':bpy.app.version_string,'mesh_objects':{o.name:len(o.data.vertices) for o in scene.objects if o.type=='MESH'},'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),'renders':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.png')},'G1':'BLOCKED_VISUAL_CALIBRATION','G2':'NOT_RUN_INDEPENDENT_ART','G3':'NOT_RUN_TOPOLOGY_UV_RIG','G4':'NOT_RUN'}
(out/'QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('MORWEN_HEAD_STUDY_CREATED',report['mesh_objects'])
