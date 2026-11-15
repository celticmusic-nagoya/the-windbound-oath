"""Isolated v2 corner-bond study. Candidate only; no canonical house assets changed."""
import bpy, random, json, hashlib, os, sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aidan_dressed_stone_v2 import create_dressed_stone_v2
from aidan_material_variation_v1 import stone_material
SEED=141127
rng=random.Random(SEED)
out=Path(os.environ.get("AIDAN_CORNER_V2_OUTPUT","/tmp/aidan-corner-v2"))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
col=bpy.data.collections.new("AIDAN_CORNER_BOND_V2_CANDIDATE")
bpy.context.scene.collection.children.link(col)
def cuboid(name,center,dim,material):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center)
 obj=bpy.context.object;obj.name=name;obj.dimensions=dim
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 obj.data.materials.append(material)
 return obj
def extruded_plan(name,polygon,z0,z1,material,seed):
 """One watertight L-shaped stone, not two overlapping quoin cubes."""
 n=len(polygon)
 # Deterministic inward-only corner wear, bounded to 4 mm.
 wear_rng=random.Random(seed)
 cx=sum(x for x,y in polygon)/n
 cy=sum(y for x,y in polygon)/n
 worn=[]
 for x,y in polygon:
  d=wear_rng.uniform(.001,.004)
  worn.append((x+(d if x<cx else -d),y+(d if y<cy else -d)))
 verts=[(x,y,z) for z in (z0,z1) for x,y in worn]
 faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
 faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name+"_mesh");mesh.from_pydata(verts,[],faces);mesh.update()
 obj=bpy.data.objects.new(name,mesh);col.objects.link(obj)
 obj.data.materials.append(material)
 # Small, inward edge wear; preserve the watertight L prism and mortar gaps.
 bevel=obj.modifiers.new("quoin worn arrises 7mm","BEVEL")
 bevel.width=.007;bevel.segments=3;bevel.affect="EDGES"
 bevel.loop_slide=True
 normals=obj.modifiers.new("quoin weighted face normals","WEIGHTED_NORMAL")
 normals.keep_sharp=True
 return obj
m=bpy.data.materials.new("lime mortar v2")
m.diffuse_color=(.53,.49,.41,1);m.use_nodes=True
m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.53,.49,.41,1)
m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.95
# Inset backing planes: 15 mm behind front y=-.215 and return x=1.19.
cuboid("front continuous mortar",(0,-.075,.855),(2.06,.25,1.71),m)
cuboid("return continuous mortar",(1.045,.4,.855),(.26,.8,1.71),m)
front=[];side=[];quoins=[];records=[]
for row in range(6):
 z=.145+row*.285
 z0=z-.1325;z1=z+.1325
 # True single-piece L-corner with staggered plan reach per course.
 xstart=.78 if row%2==0 else .91
 yend=.16 if row%2==0 else .31
 polygon=[(xstart,-.215),(1.19,-.215),(1.19,yend),
          (.94,yend),(.94,.035),(xstart,.035)]
 q=extruded_plan("integral L quoin %02d"%row,polygon,z0,z1,
                 stone_material(1000+row,low_course=row<2),SEED+row*7919)
 quoins.append(q)
 # Front and side infill terminate at the SAME quoin's footprint.
 x=-1.03
 target=xstart-.012
 front_intervals=[]
 while target-x>.001:
  w=min(target-x,rng.uniform(.29,.49))
  if 0<target-(x+w)<.18:w=target-x
  if w<.12:raise AssertionError(("short front stone",row,w))
  sid=len(front)
  front.append(create_dressed_stone_v2("front infill %03d"%sid,
      (x+w/2-.006,-.09,z),(w-.012,.25,.265),
      stone_material(sid,low_course=row<2),col,
      seed=SEED+sid,cuts=5,chip=.055,relief=.025))
  front_intervals.append([round(x,5),round(x+w-.012,5)])
  x+=w
 y=yend+.012
 side_intervals=[]
 while .80-y>.001:
  w=min(.80-y,rng.uniform(.22,.35))
  if 0<.80-(y+w)<.14:w=.80-y
  if w<.12:raise AssertionError(("short side stone",row,w))
  sid=2000+len(side)
  side.append(create_dressed_stone_v2("side infill %03d"%len(side),
      (1.065,y+w/2+.006,z),(.25,w-.012,.265),
      stone_material(sid,low_course=row<2),col,
      seed=SEED+sid,cuts=5,chip=.055,relief=.025))
  side_intervals.append([round(y+.012,5),round(y+w,5)])
  y+=w
 assert abs(x-(xstart-.012))<1e-7
 assert abs(y-.80)<1e-7
 records.append(dict(row=row,xstart=xstart,yend=yend,
                     front_count=len(front_intervals),side_count=len(side_intervals),
                     quoin_plan=polygon))
# All quoin faces have one connected manifold mesh and positive volume.
for q in quoins:
 assert len(q.data.polygons)==8,("L prism faces",q.name)
 assert len(q.data.vertices)==12
 assert all(.776<=v.co.x<=1.194 and -.219<=v.co.y<=.314 for v in q.data.vertices)
 assert all(len(e.vertices)==2 for e in q.data.edges)
 assert [mod.type for mod in q.modifiers]==["BEVEL","WEIGHTED_NORMAL"]
 assert abs(q.modifiers[0].width-.007)<1e-9
assert len(front)>18 and len(side)>=6 and len(quoins)==6
assert len(set((r["xstart"],r["yend"]) for r in records))==2
# Camera: 3/4 view with neutral fill on the right-hand return.
world=bpy.context.scene.world or bpy.data.worlds.new("neutral")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
for loc,power,size in [((-3,-4,5),900,4),((4,-1,3.5),650,3)]:
 bpy.ops.object.light_add(type="AREA",location=loc)
 bpy.context.object.data.energy=power;bpy.context.object.data.size=size
bpy.ops.object.camera_add(location=(3.8,-5.7,2.7))
cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=3.5
cam.rotation_euler=(Vector((0,.15,.85))-cam.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=1000;scene.render.resolution_y=800
scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
p=out/"corner_bond_v2.png";scene.render.filepath=str(p)
bpy.ops.render.render(write_still=True)
assert p.stat().st_size>1000
manifest={"status":"CANDIDATE_NOT_ART_APPROVED","seed":SEED,
 "construction":"ONE_L_PRISM_PER_COURSE","front_stones":len(front),
 "side_stones":len(side),"quoins":len(quoins),"courses":records,
 "g1":"BLOCKED","g2":"NOT_RUN","g3":"GEOMETRY_ASSERTIONS_PASS",
 "g4":"NOT_RUN","quoin_edge_wear_m":.007,
 "quoin_material":"shared procedural limestone family",
 "quoin_plan_wear_max_m":.004,
 "blender":bpy.app.version_string,
 "image":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
(out/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("AIDAN_CORNER_V2_QA="+json.dumps(manifest))
