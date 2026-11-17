import bpy, json, hashlib, sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index("--")+1])
out.mkdir(parents=True, exist_ok=True)
scene=bpy.context.scene
scene.render.engine="BLENDER_EEVEE"
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
if not scene.camera:
    raise RuntimeError("Candidate D has no camera: do not invent viewpoint")
scene.render.filepath=str(out/"candidate-d-existing-camera.png")
bpy.ops.render.render(write_still=True)
image=out/"candidate-d-existing-camera.png"
report={"status":"RENDERED_EXISTING_CAMERA","source_blend":bpy.data.filepath,"camera":scene.camera.name,"render_engine":scene.render.engine,"resolution":[960,720],"image_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),"image_bytes":image.stat().st_size,"G1":"BLOCKED","G2":"NOT_RUN","G3_render":"PASS","G4":"NOT_RUN"}
(out/"render-manifest.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report))
