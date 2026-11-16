"""CC0 scan-derived dressed-stone contact study. NOT a canonical house asset.
Run: blender -b rock_moss_set_01_8k.blend -t 2 --python this_file.py
"""
import bpy,bmesh,math,json,os,pathlib
from mathutils import Vector
OUT=pathlib.Path(os.environ.get("AIDAN_FITTED_OUT","/tmp/aidan-fitted"));OUT.mkdir(parents=True,exist_ok=True)
sc=bpy.context.scene
sc.render.engine="BLENDER_EEVEE";sc.render.resolution_x=960;sc.render.resolution_y=720
sc.render.resolution_percentage=100;sc.render.image_settings.file_format="PNG"
sc.world.color=(.12,.12,.12)
# Real scanned geometry; no cubes, ring generators or random-vertex perturbation.
source={s:next(o for o in bpy.data.objects if o.type=="MESH" and o.name.endswith(s)) for s in ("rock03","rock06","rock01")}
for o in bpy.data.objects:
    if o.type=="MESH":o.hide_render=True
mat=bpy.data.materials.new("clay_no_texture");mat.diffuse_color=(.53,.49,.43,1)
mat.use_nodes=True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.53,.49,.43,1)
def dress(src,name,target,location):
    mesh=src.data.copy();obj=bpy.data.objects.new(name,mesh);sc.collection.objects.link(obj)
    obj.matrix_world.identity()
    # Work in original mesh-local geometry. Transform scan to target proportions.
    bm=bmesh.new();bm.from_mesh(mesh)
    coords=[v.co.copy() for v in bm.verts]
    lo=Vector([min(p[i] for p in coords) for i in range(3)])
    hi=Vector([max(p[i] for p in coords) for i in range(3)])
    center=(lo+hi)*.5;ext=hi-lo
    for v in bm.verts:
        for i in range(3):
            v.co[i]=(v.co[i]-center[i])*target[i]/ext[i]
    # Physically designed horizontal bedding and side mating planes:
    # scan remains source of the weathered outside contour.
    planes=[(Vector((0,0,1)),target[2]*.40,True),
            (Vector((0,0,-1)),target[2]*.40,True),
            (Vector((1,0,0)),target[0]*.43,True),
            (Vector((-1,0,0)),target[0]*.43,True)]
    for normal,dist,_ in planes:
        geom=list(bm.verts)+list(bm.edges)+list(bm.faces)
        bmesh.ops.bisect_plane(bm,geom=geom,dist=.00001,
             plane_co=normal*dist,plane_no=normal,clear_outer=True,clear_inner=False)
        boundary=[e for e in bm.edges if e.is_boundary]
        if boundary:
            try:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
            except Exception:pass
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh);bm.free();mesh.update()
    obj.location=location
    obj.data.materials.clear();obj.data.materials.append(mat)
    obj.hide_render=False
    return obj
# A noncanonical miniature L-corner: lower stones turn through 90 degrees;
# top course overlaps both. Fitting is to be MEASURED, not presumed PASS.
stones=[
    dress(source["rock06"],"lower_east",(1.35,.85,.75),(-.73,0,.39)),
    dress(source["rock03"],"lower_north",(.85,1.35,.75),(.18,.68,.39)),
    dress(source["rock01"],"upper_bond",(1.25,1.15,.70),(-.20,.27,1.12)),
]
# Explicit dimensional / overlap diagnostics; not a substitute for mesh collision.
bpy.context.view_layer.update()
boxes=[]
for o in stones:
    pts=[o.matrix_world@Vector(v) for v in o.bound_box]
    boxes.append((Vector([min(v[i] for v in pts) for i in range(3)]),
                  Vector([max(v[i] for v in pts) for i in range(3)])))
pairs=[]
for i in range(len(stones)):
    for j in range(i+1,len(stones)):
        overlap=[min(boxes[i][1][k],boxes[j][1][k])-max(boxes[i][0][k],boxes[j][0][k]) for k in range(3)]
        pairs.append({"pair":[stones[i].name,stones[j].name],
          "aabb_overlap_xyz":[round(float(x),5) for x in overlap],
          "aabb_intersects":all(x>0 for x in overlap)})
camera=bpy.data.cameras.new("review_camera");cam=bpy.data.objects.new("review_camera",camera)
sc.collection.objects.link(cam);sc.camera=cam;cam.data.type="ORTHO";cam.data.ortho_scale=4.4
light_data=bpy.data.lights.new("review_area","AREA");light=bpy.data.objects.new("review_area",light_data)
sc.collection.objects.link(light);light_data.energy=950;light_data.size=5
light.location=(1,-3,5)
def aim(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat("-Z","Y").to_euler()
aim(light,(0,0,.6))
for view,pos in [("three_quarter",(3,-4,3)),("front",(0,-5,1.8)),("top",(0,-.01,6))]:
    cam.location=pos;aim(cam,(0,0,.7))
    sc.render.filepath=str(OUT/f"fitted_scan_{view}.png")
    bpy.ops.render.render(write_still=True)
report={"status":"CANDIDATE_NOT_ART_APPROVED","blender":bpy.app.version_string,
        "source":"Poly Haven rock_moss_set_01 CC0","source_meshes":list(source),
        "meshes":[{"name":o.name,"vertices":len(o.data.vertices),"polygons":len(o.data.polygons)} for o in stones],
        "aabb_pairs":pairs,"render_views":["three_quarter","front","top"],
        "g1":"BLOCKED","g2":"NOT_RUN","g3":"PARTIAL_PASS","g4":"NOT_RUN"}
(OUT/"fitted_scan_audit.json").write_text(json.dumps(report,indent=2))
print("AIDAN_FITTED_SCAN="+json.dumps(report))
