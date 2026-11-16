"""Scan-derived L-corner, contact-alignment candidate v2 (noncanonical).

Uses actual Poly Haven scan meshes; aligns the upper stone to the measured
lower stone top rather than assuming a hand-entered z. This is a NEW method
from block/noise, but art and physical support must be independently reviewed.
"""
import bpy,bmesh,json,os,pathlib,math
from mathutils import Vector
OUT=pathlib.Path(os.environ.get("AIDAN_SCAN_SHELL_OUT","/tmp/aidan-scan-shell"));OUT.mkdir(parents=True,exist_ok=True)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
source={s:next(o for o in bpy.data.objects if o.type=="MESH" and o.name.endswith(s)) for s in ("rock03","rock06","rock01")}
for obj in bpy.data.objects:
    if obj.type=="MESH":obj.hide_render=True
mat=bpy.data.materials.new("stone_scan_clay_review");mat.diffuse_color=(.51,.46,.38,1)
mat.use_nodes=True;mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.51,.46,.38,1)
def mesh_bounds(obj):
    pts=[obj.matrix_world@v.co for v in obj.data.vertices]
    return [[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)]
def shell(src,name,size,center_xy):
    mesh=src.data.copy();obj=bpy.data.objects.new(name,mesh);scene.collection.objects.link(obj)
    bm=bmesh.new();bm.from_mesh(mesh)
    lo=Vector([min(v.co[i] for v in bm.verts) for i in range(3)])
    hi=Vector([max(v.co[i] for v in bm.verts) for i in range(3)])
    mid=(lo+hi)*.5;ext=hi-lo
    for v in bm.verts:
        for i in range(3):v.co[i]=(v.co[i]-mid[i])*size[i]/ext[i]
    # Scan-derived outer silhouette is retained. Trim only hidden horizontal
    # bearing caps, never generate cuboid exterior faces.
    for z,normal in ((-.40*size[2],Vector((0,0,-1))),(.40*size[2],Vector((0,0,1)))):
        geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
        bmesh.ops.bisect_plane(bm,geom=geom,dist=.000001,plane_co=Vector((0,0,z)),
                               plane_no=normal,clear_outer=True,clear_inner=False)
        edges=[e for e in bm.edges if e.is_boundary]
        if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();mesh.update()
    obj.location=(center_xy[0],center_xy[1],0)
    obj.data.materials.clear();obj.data.materials.append(mat);obj.hide_render=False
    return obj
a=shell(source["rock06"],"scan_lower_west",(1.5,.95,.85),(-.58,0))
b=shell(source["rock03"],"scan_lower_north",(.95,1.5,.85),(.42,.61))
u=shell(source["rock01"],"scan_upper_bond",(1.38,1.20,.75),(-.04,.31))
# First align lower actual scan cap heights to z=0; then the upper bottom
# exactly to the actual top of the lower shells. Avoid floating Z gaps.
for o in (a,b):
    zmin=mesh_bounds(o)[2][0];o.location.z-=zmin
top=min(mesh_bounds(o)[2][1] for o in (a,b))
u.location.z+=top-mesh_bounds(u)[2][0]
bpy.context.view_layer.update()
report={"status":"SCAN_DERIVED_CANDIDATE_NOT_ART_APPROVED",
        "method":"organic_scan_silhouette_and_measured_z_contact",
        "blender":bpy.app.version_string,
        "source":"Poly Haven rock_moss_set_01_8k.blend CC0",
        "source_sha256":"23d6220c6c7613c4d7006d902ac99acebc7e7859f1368ba6dc0ae4123551cdc6",
        "meshes":[],"bearing_top_z":top}
for o in (a,b,u):
    bm=bmesh.new();bm.from_mesh(o.data)
    report["meshes"].append({"name":o.name,"vertices":len(bm.verts),"faces":len(bm.faces),
        "boundary_edges":sum(e.is_boundary for e in bm.edges),
        "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),
        "bounds":mesh_bounds(o)})
    bm.free()
report["measured_upper_bottom_gap"]=mesh_bounds(u)[2][0]-top
report["limitations"]="Z alignment only; actual XY bearing coverage, triangle penetration, natural art quality and canonical dimensions are not certified."
camera=bpy.data.cameras.new("camera");cam=bpy.data.objects.new("camera",camera)
scene.collection.objects.link(cam);scene.camera=cam;camera.type="ORTHO";camera.ortho_scale=4.5
light_data=bpy.data.lights.new("review_light","AREA");light=bpy.data.objects.new("review_light",light_data)
scene.collection.objects.link(light);light.location=(2,-3,5);light_data.energy=950;light_data.size=5
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat("-Z","Y").to_euler()
aim(light,(0,0,.7))
for view,pos in (("three_quarter",(3,-4,3)),("front",(0,-5,1.8)),("top",(0,-.01,6))):
    cam.location=pos;aim(cam,(0,0,.7));scene.render.filepath=str(OUT/("scan_shell_"+view+".png"))
    bpy.ops.render.render(write_still=True)
for dim in (48,96):
    scene.render.resolution_x=dim;scene.render.resolution_y=dim
    cam.location=(3,-4,3);aim(cam,(0,0,.7))
    scene.render.filepath=str(OUT/("scan_shell_"+str(dim)+"px.png"))
    bpy.ops.render.render(write_still=True)
(OUT/"scan_shell_audit.json").write_text(json.dumps(report,indent=2))
print("AIDAN_SCAN_SHELL="+json.dumps(report))
