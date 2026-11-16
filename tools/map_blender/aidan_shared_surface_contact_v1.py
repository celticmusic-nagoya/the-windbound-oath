"""Shared-surface masonry contact topology gate (NOT a final art asset).

Structural method switch: bearing faces are shared exact polygons; only side-wall
mid-rings may move. This intentionally uses simplified outlines for a *limited*
contact feasibility test, not completed architectural stone art.
"""
import bpy,bmesh,json,os,pathlib
from mathutils import Vector
out=pathlib.Path(os.getenv("AIDAN_SHARED_OUT","/tmp/aidan-shared-surface"))
out.mkdir(parents=True,exist_ok=True)
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
s=bpy.context.scene;s.render.engine="BLENDER_EEVEE"
s.render.resolution_x=960;s.render.resolution_y=720;s.render.resolution_percentage=100
mat=bpy.data.materials.new("neutral_clay");mat.diffuse_color=(.53,.48,.40,1)
# Three stones, common bearing interface z=.72. The upper polygon is
# fully supported by union of lower polygons, split exactly at shared x=0.
# Coordinates are explicitly NONCANONICAL test dimensions.
pieces=[
 {"name":"lower_west","x0":-1.40,"x1":0.0,"y0":-.55,"y1":.55,"z0":0.0,"z1":.72},
 {"name":"lower_east","x0":0.0,"x1":1.40,"y0":-.55,"y1":.55,"z0":0.0,"z1":.72},
 {"name":"upper_bond","x0":-.83,"x1":.83,"y0":-.42,"y1":.42,"z0":.72,"z1":1.40},
]
def make(d):
    x0,x1,y0,y1=d["x0"],d["x1"],d["y0"],d["y1"]
    # 8 vertices around rectangle: midpoint subdivisions on outer edges,
    # retained identically on both caps to guarantee exact support.
    perimeter=[(x0,y0),((x0+x1)/2,y0),(x1,y0),(x1,(y0+y1)/2),
               (x1,y1),((x0+x1)/2,y1),(x0,y1),(x0,(y0+y1)/2)]
    n=len(perimeter);height=d["z1"]-d["z0"]
    rings=[]
    for k,t in enumerate((0,.24,.76,1)):
        ring=[]
        for i,(x,y) in enumerate(perimeter):
            # Only mid-wall exteriors may vary; NEVER move contact/bearing caps.
            # Keep lower internal mating plane x=0 undistorted.
            if k in (1,2):
                if i in (1,5): y+=(-.055 if i==1 else .045)*(1 if k==1 else .7)
                if i in (3,7):
                    joint=(d["name"]=="lower_west" and i==3) or (d["name"]=="lower_east" and i==7)
                    if not joint: x+=(.05 if i==3 else -.05)*(1 if k==1 else .7)
            ring.append((x,y,d["z0"]+height*t))
        rings.append(ring)
    verts=[v for ring in rings for v in ring]
    faces=[tuple(reversed(range(n)))]
    for k in range(3):
        for i in range(n):
            j=(i+1)%n
            faces.append((k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i))
    faces.append(tuple(3*n+i for i in range(n)))
    mesh=bpy.data.meshes.new(d["name"]+"_mesh");mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(d["name"],mesh);s.collection.objects.link(obj);obj.data.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(mesh)
    result={"name":d["name"],"faces":len(bm.faces),"boundary_edges":sum(e.is_boundary for e in bm.edges),
            "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges)}
    bm.free()
    return result
audit={"status":"TECHNICAL_CONTACT_TEST_NOT_ART","method":"shared_exact_bearing_faces","meshes":[make(p) for p in pieces]}
w,e,u=pieces
def area_overlap(a,b):
    return max(0,min(a["x1"],b["x1"])-max(a["x0"],b["x0"]))*max(0,min(a["y1"],b["y1"])-max(a["y0"],b["y0"]))
area=(u["x1"]-u["x0"])*(u["y1"]-u["y0"])
support_w=area_overlap(u,w);support_e=area_overlap(u,e)
audit["bearing"]={"upper_area":round(area,6),"supported_west":round(support_w,6),
    "supported_east":round(support_e,6),"support_ratio":round((support_w+support_e)/area,6),
    "z_gap":round(u["z0"]-w["z1"],8),"coplanar_joint_x":w["x1"]==e["x0"],
    "lower_xy_overlap_area":area_overlap(w,e),
    "joint_vertical_overlap":min(w["z1"],e["z1"])-max(w["z0"],e["z0"])}
audit["limitations"]="Exact horizontal face coverage on simplified rectangles; side wall triangle collision, final L-corner architecture, canon dimensions, art quality and in-game QA NOT_RUN."
camera=bpy.data.cameras.new("camera");cam=bpy.data.objects.new("camera",camera);s.collection.objects.link(cam)
s.camera=cam;camera.type="ORTHO";camera.ortho_scale=4.0
ld=bpy.data.lights.new("area","AREA");light=bpy.data.objects.new("area",ld);s.collection.objects.link(light)
light.location=(2,-3,5);ld.energy=900;ld.size=4
def look(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat("-Z","Y").to_euler()
look(light,(0,0,.7))
for view,pos in [("three_quarter",(3,-4,3)),("front",(0,-5,1.7)),("top",(0,-.001,6))]:
    cam.location=pos;look(cam,(0,0,.7));s.render.filepath=str(out/("shared_"+view+".png"))
    bpy.ops.render.render(write_still=True)
(out/"shared_contact_audit.json").write_text(json.dumps(audit,indent=2))
print("AIDAN_SHARED_SURFACE="+json.dumps(audit))
