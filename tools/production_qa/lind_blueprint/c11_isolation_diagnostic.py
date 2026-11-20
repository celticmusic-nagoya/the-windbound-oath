"""Read-only diagnostic: isolate carrier vs other objects and export section segments."""
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
src,out=map(lambda p:Path(p).resolve(),sys.argv[sys.argv.index("--")+1:])
out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
scene=bpy.context.scene
obj=bpy.data.objects.get("Cliff C8 B | joinable coastal segment")
assert obj and obj.type=="MESH"
meshes=[o for o in scene.objects if o.type=="MESH"]
records=[]
for o in meshes:
    records.append({"name":o.name,"vertices":len(o.data.vertices),"faces":len(o.data.polygons),"hide_render":o.hide_render,"matrix":[list(r) for r in o.matrix_world],"bounds":[list(o.matrix_world@Vector(v)) for v in o.bound_box]})
# Intersect triangulated carrier with horizontal local planes; keep source face IDs.
obj.data.calc_loop_triangles()
sections={}
for z in (0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0):
    segments=[]
    for tri in obj.data.loop_triangles:
        vs=[obj.data.vertices[i].co for i in tri.vertices]
        hits=[]
        for a,b in zip(vs,vs[1:]+vs[:1]):
            if (a.z<=z<b.z) or (b.z<=z<a.z):
                p=a+(b-a)*((z-a.z)/(b.z-a.z))
                hits.append([p.x,p.y])
        if len(hits)==2 and any(abs(p[0]+5.95)<1.5 for p in hits):
            segments.append({"face":tri.polygon_index,"xy":hits})
    sections[str(z)]=segments
(out/"sections.json").write_text(json.dumps({"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"objects":records,"sections":sections},indent=2))
scene.render.engine="CYCLES"
scene.cycles.samples=16
scene.render.resolution_x=1000
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
center=obj.matrix_world@Vector((-5.95,0,2.35))
cam=bpy.data.objects.new("DiagnosticCamera",bpy.data.cameras.new("DiagnosticCamera"))
scene.collection.objects.link(cam)
scene.camera=cam
cam.data.type="ORTHO"
cam.data.ortho_scale=9.5
cam.location=center+Vector((0,-12,5))
cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
light=bpy.data.objects.new("DiagnosticArea",bpy.data.lights.new("DiagnosticArea","AREA"))
scene.collection.objects.link(light)
light.location=center+Vector((-4,-5,9))
light.rotation_euler=(center-light.location).to_track_quat("-Z","Y").to_euler()
light.data.energy=2200
light.data.size=8
mat=bpy.data.materials.new("DiagnosticClay")
mat.diffuse_color=(0.55,0.55,0.55,1)
scene.view_layers[0].material_override=mat
original={o.name:o.hide_render for o in meshes}
for mode in ("all","carrier_only","without_carrier"):
    for o in meshes:
        o.hide_render=original[o.name] or (mode=="carrier_only" and o!=obj) or (mode=="without_carrier" and o==obj)
    scene.render.filepath=str(out/(mode+".png"))
    bpy.ops.render.render(write_still=True)

# Highlight candidate faces only in memory; never save over the source.
if hashlib.sha256(src.read_bytes()).hexdigest()=="d0e91ae7543f2995b70c2a3f2d59e625d7cc828e6328ccc90c9224d060b0b545":
    ids=[10159,10154,10235,10308,37656,37378,37745,37376,37588]
    scene.view_layers[0].material_override=None
    red=bpy.data.materials.new("SuspectFace")
    red.use_nodes=True
    shader=red.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value=(1,0.02,0.01,1)
    shader.inputs["Emission Color"].default_value=(1,0.02,0.01,1)
    shader.inputs["Emission Strength"].default_value=0.8
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    obj.data.materials.append(red)
    for p in obj.data.polygons:
        p.material_index=int(p.index in ids)
    for o in meshes:
        o.hide_render=original[o.name] or o!=obj
    scene.render.filepath=str(out/"suspect_faces.png")
    bpy.ops.render.render(write_still=True)
