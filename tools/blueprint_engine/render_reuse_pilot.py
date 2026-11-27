"""Isolated CPU Cycles multiview A/B. No production files, no quality setting reduction."""
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import sys
import time

VIEWS = ((0, -8, 3), (8, 0, 3), (5, 5, 3))


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def fixture(path):
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.seed = 42
    scene.render.resolution_x = scene.render.resolution_y = 384
    scene.render.resolution_percentage = 100
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("fixture_world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    for k in range(5):
        mat = bpy.data.materials.new(f"fixture_material_{k}")
        mat.diffuse_color = (0.12 + .15*k, .45, .28, 1)
        mat.use_nodes = True
        mat.node_tree.nodes.get("Principled BSDF").inputs["Base Color"].default_value = mat.diffuse_color
    for i in range(8):
        for j in range(8):
            bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=.24,
                                                  location=((i-3.5)*.56,(j-3.5)*.56,.24))
            bpy.context.object.data.materials.append(bpy.data.materials[f"fixture_material_{(i+j)%5}"])
    bpy.ops.mesh.primitive_plane_add(size=14)
    bpy.ops.object.camera_add()
    scene.camera = bpy.context.object
    scene.camera.data.type = "ORTHO"
    scene.camera.data.ortho_scale = 6
    for pos in ((-3,-4,5),(4,3,4)):
        bpy.ops.object.light_add(type="AREA", location=pos)
        light = bpy.context.object
        light.data.energy = 500
        light.data.shape = "DISK"
        light.data.size = 4
        light.rotation_euler = (-Vector(pos)).to_track_quat("-Z","Y").to_euler()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))


def render(source, out, persistent):
    import bpy
    from mathutils import Vector
    from PIL import Image, ImageStat
    assert bpy.app.version_string == "5.3.0" and bpy.app.build_hash.decode() == "02f0899d78e3"
    original = sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
    scene = bpy.context.scene
    scene.render.use_persistent_data = persistent
    out.mkdir(exist_ok=False)
    rows = []
    for i, pos in enumerate(VIEWS):
        cam = scene.camera
        cam.location = pos
        cam.rotation_euler = (Vector((0,0,.3))-cam.location).to_track_quat("-Z","Y").to_euler()
        path = out / f"view-{i}.png"
        scene.render.filepath = str(path)
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        elapsed = time.monotonic()-start
        with Image.open(path) as image:
            rgb = image.convert("RGB")
            assert rgb.size == (384,384) and max(ImageStat.Stat(rgb).stddev) > 5
            pixels = hashlib.sha256(rgb.tobytes()).hexdigest()
        rows.append(dict(file=path.name, seconds=round(elapsed,3), png_sha256=sha(path), pixels_sha256=pixels))
    assert original == sha(source)
    (out / "receipt.json").write_text(json.dumps(dict(persistent=persistent, source_sha256=original,
        views=rows, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),indent=2))


def main():
    if sys.argv[1] == "fixture":
        fixture(Path(sys.argv[2]))
        return
    if sys.argv[1] == "render":
        render(Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]=="true")
        return
    out = Path(sys.argv[1]).resolve()
    out.mkdir(exist_ok=False)
    source = out / "fixture.blend"
    cmd = [sys.executable, "-I", str(Path(__file__).resolve())]
    subprocess.run(cmd+["fixture",str(source)],check=True,timeout=60)
    expected = sha(source)
    source.chmod(0o444)
    results = []
    for name in ("baseline","persistent"):
        subprocess.run(cmd+["render",str(source),str(out/name),str(name=="persistent").lower()],
                       check=True,timeout=150)
        results.append(json.loads((out/name/"receipt.json").read_text()))
    assert expected == sha(source) and all(r["source_sha256"]==expected for r in results)
    a,b=results
    exact=[x["pixels_sha256"]==y["pixels_sha256"] for x,y in zip(a["views"],b["views"])]
    totals=[round(sum(v["seconds"] for v in r["views"]),3) for r in results]
    summary=dict(status="QUALIFICATION_ONLY", exact_pixel_matches=exact,
                 baseline_seconds=totals[0],persistent_seconds=totals[1],
                 baseline_peak_rss_kib=a["peak_rss_kib"],persistent_peak_rss_kib=b["peak_rss_kib"],
                 source_sha256=expected, eligible_for_further_review=all(exact) and totals[1]<totals[0])
    (out/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary),flush=True)


if __name__=="__main__":
    main()
