"""Render C11 candidate from three fixed viewpoints; no formal art PASS implied."""
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
src, out = map(lambda p: Path(p).resolve(), sys.argv[sys.argv.index("--")+1:])
out.mkdir(parents=True, exist_ok=True)
assert src.is_file()
bpy.ops.wm.open_mainfile(filepath=str(src))
obj = bpy.data.objects.get("Cliff C8 B | joinable coastal segment")
assert obj and obj.type == "MESH"
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.render.resolution_x = 1000
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.18, 0.18, 0.18)
# Camera locations are provisional asset-local; fixed across review runs.
center = obj.matrix_world @ Vector((-5.95, 0.0, 2.35))
views = {"front":(0,-12,5),"oblique":(8,-10,6),"low":(2,-9,2.0)}
camera_data = bpy.data.cameras.new("C11_REVIEW_FIXED_CAMERA")
camera = bpy.data.objects.new("C11_REVIEW_FIXED_CAMERA",camera_data)
scene.collection.objects.link(camera)
scene.camera = camera
camera_data.type = "ORTHO"
camera_data.ortho_scale = 9.5
light_data = bpy.data.lights.new("C11_REVIEW_AREA","AREA")
light = bpy.data.objects.new("C11_REVIEW_AREA",light_data)
scene.collection.objects.link(light)
light.location = center + Vector((-4,-5,9))
light_data.energy = 2200
light_data.shape = "DISK"
light_data.size = 8
records = []
for name, offset in views.items():
    camera.location = center + Vector(offset)
    direction = center-camera.location
    camera.rotation_euler = direction.to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(out / ("c11_"+name+".png"))
    bpy.ops.render.render(write_still=True)
    records.append({"view":name,"camera_location":list(camera.location),"target":list(center),"path":scene.render.filepath})
(out/"c11_render_manifest.json").write_text(json.dumps({"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"views":records,"G2":"NOT_RUN","G3_full":"NOT_RUN"},indent=2))
