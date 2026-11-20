"""C11 matched clay + close-up review renders (no art PASS implied).

Same three fixed cameras/light as c11_render_review.py, all materials replaced by
one neutral clay; plus two fixed front close-ups (west / central repair islands)
in clay and in the authored material. Also exports horizontal mesh sections of
the carrier through both islands to JSON for plotting.

  blender -b --factory-startup --python c11_clay_closeup_review.py -- IN.blend OUT_DIR TAG
"""
import bpy, sys, json, hashlib, bmesh
from pathlib import Path
from mathutils import Vector

src, out, tag = sys.argv[sys.argv.index("--") + 1:]
src, out = Path(src).resolve(), Path(out).resolve()
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(src))
obj = bpy.data.objects["Cliff C8 B | joinable coastal segment"]
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.cycles.seed = 0
scene.render.resolution_x = 1000
scene.render.resolution_y = 720
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.world.color = (0.18, 0.18, 0.18)
center = obj.matrix_world @ Vector((-5.95, 0.0, 2.35))
cam_d = bpy.data.cameras.new("C11_REVIEW_FIXED_CAMERA")
cam = bpy.data.objects.new("C11_REVIEW_FIXED_CAMERA", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam
cam_d.type = "ORTHO"
light_d = bpy.data.lights.new("C11_REVIEW_AREA", "AREA")
light = bpy.data.objects.new("C11_REVIEW_AREA", light_d)
scene.collection.objects.link(light)
light.location = center + Vector((-4, -5, 9))
light_d.energy = 2200
light_d.shape = "DISK"
light_d.size = 8

shots = [("front", center, (0, -12, 5), 9.5), ("oblique", center, (8, -10, 6), 9.5), ("low", center, (2, -9, 2.0), 9.5),
         ("close_west", Vector((-7.8, 0.0, 3.9)), (0, -12, 2.5), 4.2),
         ("close_central", Vector((-5.75, 0.0, 4.6)), (0, -12, 2.5), 4.2)]


def render_all(prefix, names):
    rec = []
    for name, tgt, off, scale in shots:
        if name not in names:
            continue
        cam_d.ortho_scale = scale
        cam.location = tgt + Vector(off)
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(out / f"{tag}_{prefix}_{name}.png")
        bpy.ops.render.render(write_still=True)
        rec.append({"view": name, "camera_location": list(cam.location), "target": list(tgt), "ortho_scale": scale})
    return rec


records = {"material": render_all("mat", {"close_west", "close_central"})}
clay = bpy.data.materials.new("C11_REVIEW_CLAY")
clay.use_nodes = True
bsdf = clay.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.2, 0.2, 0.2, 1)
bsdf.inputs["Roughness"].default_value = 0.8
for o in scene.objects:
    if o.type == "MESH":
        for i in range(len(o.material_slots)):
            o.material_slots[i].material = clay
        if not o.material_slots:
            o.data.materials.append(clay)
records["clay"] = render_all("clay", {s[0] for s in shots})
# UV checker pass on the close-ups (active UV map), for UV distortion review
chk = bpy.data.materials.new("C11_REVIEW_UV_CHECKER")
chk.use_nodes = True
nt = chk.node_tree
b2 = nt.nodes.get("Principled BSDF")
tex = nt.nodes.new("ShaderNodeTexChecker")
tex.inputs["Scale"].default_value = 60.0
tex.inputs["Color1"].default_value = (0.35, 0.35, 0.35, 1)
tex.inputs["Color2"].default_value = (0.08, 0.08, 0.08, 1)
uvn = nt.nodes.new("ShaderNodeUVMap")
uvn.uv_map = obj.data.uv_layers.active.name
nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
nt.links.new(tex.outputs["Color"], b2.inputs["Base Color"])
for i in range(len(obj.material_slots)):
    obj.material_slots[i].material = chk
records["uv_checker"] = render_all("uvchecker", {"close_west", "close_central"})
# horizontal sections through the carrier near the islands
sections = {}
bm = bmesh.new()
bm.from_mesh(obj.data)
for z in (2.0, 2.6, 3.2, 3.8, 4.4, 5.0, 5.6, 6.2):
    segs = []
    for f in bm.faces:
        vs = [v.co for v in f.verts]
        if min(v.z for v in vs) > z or max(v.z for v in vs) < z:
            continue
        if max(v.x for v in vs) < -8.9 or min(v.x for v in vs) > -4.9:
            continue
        pts = []
        for a, b in zip(vs, vs[1:] + vs[:1]):
            if (a.z - z) * (b.z - z) < 0:
                t = (z - a.z) / (b.z - a.z)
                pts.append([round(a.x + t * (b.x - a.x), 5), round(a.y + t * (b.y - a.y), 5)])
        if len(pts) == 2 and min(p[1] for p in pts) < -1.0:
            segs.append(pts)
    sections[str(z)] = segs
bm.free()
(out / f"{tag}_sections.json").write_text(json.dumps(sections))
(out / f"{tag}_clay_closeup_manifest.json").write_text(json.dumps(
    {"source_sha256": hashlib.sha256(src.read_bytes()).hexdigest(), "records": records,
     "G2": "NOT_RUN"}, indent=2))
