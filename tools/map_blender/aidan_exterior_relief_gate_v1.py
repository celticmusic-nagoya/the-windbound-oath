"""Exterior-only stone relief feasibility, NOT completed CC0 scan/PBR artwork.

Preserves bearing caps and shared internal x=0 plane exactly. Uses deterministic
procedural microrelief as a *technical displacement test*; do not label as
scan-derived or final art. Independent art direction follows this gate.
"""
import bpy,bmesh,json,math,os,pathlib,runpy
from mathutils import Vector
from mathutils.noise import noise_vector
out=pathlib.Path(os.getenv("AIDAN_RELIEF_OUT","/tmp/aidan-relief"))
out.mkdir(parents=True,exist_ok=True)
os.environ["AIDAN_SHARED_OUT"]=str(out/"baseline")
runpy.run_path(str(pathlib.Path(__file__).with_name("aidan_shared_surface_contact_v1.py")),run_name="__main__")
objects=[bpy.data.objects[x] for x in ("lower_west","lower_east","upper_bond")]
report={"method":"exterior_only_displacement_technical_gate","status":"NOT_FINAL_ART","objects":[]}
for obj in objects:
    before=obj.data
    z0=min(v.co.z for v in before.vertices)
    z1=max(v.co.z for v in before.vertices)
    bm=bmesh.new();bm.from_mesh(before)
    bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=4,use_grid_fill=True)
    bm.verts.ensure_lookup_table();bm.normal_update()
    count=0;caps=0;joints=0
    for v in bm.verts:
        p=v.co.copy()
        # Exact shared horizontal bearing/ground faces and vertical x=0 joints
        # are frozen. Never displace a cap or an internal mating surface.
        if abs(p.z-z0)<1e-5 or abs(p.z-z1)<1e-5:
            caps+=1;continue
        if obj.name=="lower_west" and abs(p.x)<1e-5:
            joints+=1;continue
        if obj.name=="lower_east" and abs(p.x)<1e-5:
            joints+=1;continue
        # Two-frequency nonperiodic surface irregularity for topology feasibility.
        # Noise amplitude is intentionally small; art quality NOT certified.
        n=noise_vector(p*5.1+Vector((1.3,3.1,4.7)))
        n2=noise_vector(p*13.2+Vector((7.3,1.1,2.7)))
        delta=(n*.026+n2*.008)
        v.co+=Vector((delta.x,delta.y,delta.z*.45))
        count+=1
    bm.normal_update()
    new=bpy.data.meshes.new(obj.name+"_exterior_relief")
    bm.to_mesh(new);new.update()
    boundary=sum(e.is_boundary for e in bm.edges)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    for mat in before.materials:new.materials.append(mat)
    obj.data=new
    report["objects"].append({"name":obj.name,"vertices":len(new.vertices),
      "displaced_vertices":count,"frozen_cap_vertices":caps,"frozen_joint_vertices":joints,
      "boundary_edges":boundary,"nonmanifold_edges":nonmanifold})
# Actual top and bottom face positions remain frozen after tessellation.
def cap_z_check(obj):
    zlo=min(v.co.z for v in obj.data.vertices);zhi=max(v.co.z for v in obj.data.vertices)
    return zlo,zhi
report["cap_extents"]={o.name:list(cap_z_check(o)) for o in objects}
# Existing scene camera/lighting inherited from the source study.
scene=bpy.context.scene
scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
cam=scene.camera
for name,xyz in [("three_quarter",(3,-4,3)),("front",(0,-5,1.7)),("top",(0,-.001,6))]:
    cam.location=xyz
    cam.rotation_euler=(Vector((0,0,.7))-cam.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath=str(out/("relief_"+name+".png"))
    bpy.ops.render.render(write_still=True)
scene.render.resolution_x=48;scene.render.resolution_y=48;scene.render.resolution_percentage=100
cam.location=(3,-4,3)
cam.rotation_euler=(Vector((0,0,.7))-cam.location).to_track_quat("-Z","Y").to_euler()
scene.render.filepath=str(out/"relief_48px.png")
bpy.ops.render.render(write_still=True)
(out/"relief_qa.json").write_text(json.dumps(report,indent=2))
print("AIDAN_EXTERIOR_RELIEF="+json.dumps(report))
