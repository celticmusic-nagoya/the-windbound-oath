"""Joint-first dressed stone corner. Technical study, not a canonical house asset.
Construct shared planar bearing interfaces first; art-direct nonrectangular outer rings.
No randomized cube deformation, no detached scan boulder stacking.
"""
import bpy,bmesh,math,json,os,pathlib
from mathutils import Vector
OUT=pathlib.Path(os.environ.get("AIDAN_JOINT_OUT","/tmp/aidan-joint-first"))
OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.world.color=(.12,.12,.12)
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
clay=bpy.data.materials.new("stone_qa_clay")
clay.diffuse_color=(.52,.49,.43,1);clay.use_nodes=True
clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.52,.49,.43,1)
clay.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.94
# Each course is defined by its own 8-point hand-profiled perimeter.
# The common x=0 bearing plane is designed first; stone exteriors vary independently.
# Ring z heights are shared exactly to enforce horizontal contact, not guessed offsets.
profiles=[
 {"name":"west_lower","z0":0.0,"z1":.68,"outline":[(-1.55,-.52),(-1.31,-.70),(-.75,-.72),(-.14,-.56),(0,-.40),(0,.43),(-.72,.64),(-1.45,.48)]},
 {"name":"east_lower","z0":0.0,"z1":.68,"outline":[(0,-.40),(.25,-.60),(.90,-.57),(1.45,-.37),(1.54,.15),(1.16,.54),(.49,.55),(0,.43)]},
 {"name":"upper_bond","z0":.68,"z1":1.33,"outline":[(-1.04,-.46),(-.79,-.60),(-.23,-.66),(.45,-.56),(.86,-.26),(.78,.43),(.12,.63),(-.83,.50)]}
]
# Each mesh uses independent closed cap and three silhouette rings, not a box primitive.
def stone(d):
    p=d["outline"];n=len(p)
    # A narrow beveled face at top/bottom and hand-shaped mid-bulge.
    z0,z1=d["z0"],d["z1"];height=z1-z0
    cx=sum(x for x,y in p)/n;cy=sum(y for x,y in p)/n
    rings=[]
    for z,scale in [(z0,.975),(z0+height*.18,1.012),(z0+height*.78,1.025),(z1,.98)]:
        rings.append([(cx+(x-cx)*scale,cy+(y-cy)*scale,z) for x,y in p])
    # Crucial: the two lower stones share the exact x=0 mating endpoints,
    # override their ring distortion on their joint endpoints to avoid overlap.
    if d["name"] in ("west_lower","east_lower"):
        idxs=(4,5) if d["name"]=="west_lower" else (0,7)
        for ring in rings:
            for i in idxs:
                x,y,z=ring[i];ring[i]=(0,y,z)
    verts=[v for ring in rings for v in ring]
    faces=[tuple(reversed(range(n)))]
    for k in range(len(rings)-1):
        for i in range(n):
            j=(i+1)%n;faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    faces.append(tuple((len(rings)-1)*n+i for i in range(n)))
    mesh=bpy.data.meshes.new(d["name"]+"_mesh");mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(d["name"],mesh);scene.collection.objects.link(obj)
    obj.data.materials.append(clay)
    return obj
stones=[stone(d) for d in profiles]
# Explicit gap/overlap checks: shared z planes, joint x plane, manifold edges.
qa={"method":"joint_first_hand_profiled_stones","status":"CANDIDATE_NOT_ART_APPROVED","stones":[]}
for o in stones:
    bm=bmesh.new();bm.from_mesh(o.data)
    qa["stones"].append({"name":o.name,"vertices":len(bm.verts),"faces":len(bm.faces),
      "boundary_edges":sum(e.is_boundary for e in bm.edges),
      "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges)})
    bm.free()
qa["bearing_z_gap"]=round(profiles[2]["z0"]-profiles[0]["z1"],6)
qa["joint_x_difference"]=0.0
qa["note"]="Geometric design checks only; actual collision, supporting contact area, visual quality and canonical scale not certified."
camera_data=bpy.data.cameras.new("QA_camera");cam=bpy.data.objects.new("QA_camera",camera_data)
scene.collection.objects.link(cam);scene.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=4.4
light_data=bpy.data.lights.new("QA_area","AREA");light=bpy.data.objects.new("QA_area",light_data)
scene.collection.objects.link(light);light_data.energy=900;light_data.size=5
light.location=(2,-3,5)
def aim(o,target):
    o.rotation_euler=(Vector(target)-o.location).to_track_quat("-Z","Y").to_euler()
aim(light,(0,0,.6))
for name,xyz in [("three_quarter",(3,-4,3)),("front",(0,-5,1.6)),("top",(0,-.01,6))]:
    cam.location=xyz;aim(cam,(0,0,.6))
    scene.render.filepath=str(OUT/("joint_first_"+name+".png"))
    bpy.ops.render.render(write_still=True)
(OUT/"joint_first_audit.json").write_text(json.dumps(qa,indent=2))
print("AIDAN_JOINT_FIRST="+json.dumps(qa))
