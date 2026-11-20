"""MAP-VEG-01: noncanonical meadow grass candidate, Blender 4.2.3.
Generate deterministic individually curved, tapered leaf blades with true mesh geometry.
Usage: blender -b --python tools/map_blender/map_veg_01_generate.py -- --out /tmp/map-veg-01 --seed 20261116
"""
import argparse,hashlib,json,math,os,pathlib,random,sys
import bpy
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
p=argparse.ArgumentParser();p.add_argument("--out",required=True);p.add_argument("--seed",type=int,default=20261116);p.add_argument("--samples",type=int,default=32);a=p.parse_args(args)
out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
rng=random.Random(a.seed)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
sc.render.engine="CYCLES";sc.cycles.samples=a.samples
sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100
sc.render.image_settings.file_format="PNG";sc.render.image_settings.color_mode="RGBA"
sc.render.film_transparent=True
sc.world.color=(0.22,0.22,0.22)
sc.view_settings.view_transform="AgX"
def mat(name,color,rough=0.86):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 b=m.node_tree.nodes.get("Principled BSDF");b.inputs["Base Color"].default_value=(*color,1);b.inputs["Roughness"].default_value=rough
 return m
materials=[mat("grass_olive",(0.18,0.29,0.085)),mat("grass_fresh",(0.22,0.38,0.095)),mat("grass_sage",(0.28,0.34,0.15)),mat("grass_dry",(0.36,0.32,0.13))]
def leaf_mesh(name,base,height,width,angle,bend,material,arch=0.0):
 # Continuous longitudinal curvature and tapered 3D cross-section, not flat cards.
 vertices=[];faces=[];steps=10
 direction=Vector((math.cos(angle),math.sin(angle),0));across=Vector((-math.sin(angle),math.cos(angle),0))
 for j in range(steps+1):
  t=j/steps
  center=Vector(base)+Vector((direction.x*bend*t*t,direction.y*bend*t*t,height*t + arch*math.sin(math.pi*t)))
  w=width*(max(0.002,math.sin(math.pi*(0.08+0.92*t)))**0.65)*(1-t**2)*0.5
  ridge=0.004*(1-t)*math.sin(math.pi*t)
  vertices.extend([tuple(center-across*w),tuple(center+Vector((0,0,ridge))),tuple(center+across*w)])
 for j in range(steps):
  k=j*3;n=(j+1)*3
  faces.extend([(k,k+1,n+1,k+3),(k+1,k+2,n+2,n+1)])
 mesh=bpy.data.meshes.new(name+"_mesh");mesh.from_pydata(vertices,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);ob.data.materials.append(material)
 for poly in mesh.polygons:poly.use_smooth=True
 return ob
asset_stats=[]
for idx,(count,spread,scale) in enumerate([(24,0.17,0.85),(33,0.22,1.0),(42,0.26,1.14)]):
 collection=bpy.data.collections.new("Clump_%02d"%(idx+1));sc.collection.children.link(collection)
 ox=(idx-1)*1.25;objects=[]
 for j in range(count):
  theta=rng.uniform(0,math.tau);radius=spread*math.sqrt(rng.random())
  x=ox+radius*math.cos(theta);y=radius*math.sin(theta)
  basal=(j < int(count*0.62))
  h=(rng.uniform(0.14,0.29) if basal else rng.uniform(0.34,0.60))*scale
  w=(rng.uniform(0.036,0.065) if basal else rng.uniform(0.014,0.027))*scale
  angle=theta+rng.uniform(-0.75,0.75)
  bend=(rng.uniform(0.12,0.27) if basal else rng.uniform(0.05,0.17))*scale
  ob=leaf_mesh("grass_%02d_%03d"%(idx+1,j), (x,y,0),h,w,angle,bend,rng.choices(materials,weights=[3,5,3,1])[0],arch=(0.035 if basal else 0.01)*scale)
  for c in list(ob.users_collection):c.objects.unlink(ob)
  collection.objects.link(ob);objects.append(ob)
 tris=sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in objects)
 asset_stats.append({"name":collection.name,"leaf_count":count,"triangles":tris,"height_m_max":round(max(ob.dimensions.z for ob in objects),3)})
# A restrained shadow-catching surface is rendered but not exported as foliage.
ground=mat("ground_preview",(0.28,0.29,0.23))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-0.012));plane=bpy.context.object;plane.name="PREVIEW_GROUND";plane.data.materials.append(ground)
sun_data=bpy.data.lights.new("WarmKey","AREA");sun=bpy.data.objects.new("WarmKey",sun_data);sc.collection.objects.link(sun)
sun.location=(-3,-4,6);sun_data.energy=620;sun_data.shape="DISK";sun_data.size=4
def cam(name,loc,target):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);sc.collection.objects.link(ob)
 ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat("-Z","Y").to_euler()
 data.type="ORTHO";data.ortho_scale=4.5;return ob
views={"three_quarter":(3,-5,3.0),"front":(0,-6,1.5),"top":(0,-0.001,7)}
outputs=[]
for view,loc in views.items():
 camera=cam("CAM_"+view,loc,(0,0,0.13));sc.camera=camera
 sc.render.filepath=str((out/("veg_"+view+".png")).resolve())
 bpy.ops.render.render(write_still=True)
 f=pathlib.Path(sc.render.filepath)
 outputs.append({"path":f.name,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
# Save scene with all editable clumps; candidate only.
bpy.ops.wm.save_as_mainfile(filepath=str((out/"map_veg_01.blend").resolve()))
f=out/"map_veg_01.blend";outputs.append({"path":f.name,"sha256":hashlib.sha256(f.read_bytes()).hexdigest()})
manifest={"task_id":"MAP-VEG-01","candidate_id":"grass_master_B","status":"CANDIDATE_NOT_ADOPTED",
"blender_version":bpy.app.version_string,"seed":a.seed,"assets":asset_stats,"outputs":outputs,
"qa":{"G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"},
"notes":"Candidate B: two-layer basal broad leaf and upright stem architecture; procedural mesh geometry; no texture license needed. Preview ground is not vegetation. 48/96px game-scale and independent G2 are pending."}
(out/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("MAP_VEG_01_OUTPUT="+str(out))
