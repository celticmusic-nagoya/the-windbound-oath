"""MORWEN-FABLE-01 deterministic read-only inspection + fixed-camera render.

Usage (Blender 5.3 python module `bpy`, or `blender -b -P`):
  python3 morwen_fable_eval_inspect_render.py -- <input.blend> <out_dir> [--samples 16] [--no-render]
The input .blend is opened read-only and never saved. No randomness is used
(Cycles seed fixed to 0). Camera, light-independent emission look, resolution and
framing are constants so A/B candidates can be compared under identical settings.
"""
import bpy, bmesh, sys, os, json, hashlib, time, math
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
SRC, OUT = argv[0], argv[1]
SAMPLES = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 16
RENDER = "--no-render" not in argv
os.makedirs(OUT, exist_ok=True)
t0 = time.time()

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()

src_sha_before = sha256(SRC)
bpy.ops.wm.open_mainfile(filepath=SRC)
scene = bpy.context.scene
deps = bpy.context.evaluated_depsgraph_get()

rep = {"schema": "TWO_MORWEN_FABLE_EVAL_INSPECT_V1", "source": os.path.basename(SRC),
       "source_sha256": src_sha_before, "blender": bpy.app.version_string,
       "unit": {"system": scene.unit_settings.system, "scale_length": scene.unit_settings.scale_length},
       "objects": [], "notes": []}

visible = []
for o in scene.objects:
    e = {"name": o.name, "type": o.type, "hide_render": o.hide_render,
         "parent": o.parent.name if o.parent else None}
    if o.type == "MESH":
        me = o.data
        bm = bmesh.new(); bm.from_mesh(me)
        e.update(verts=len(bm.verts), faces=len(bm.faces),
                 tris=sum(len(f.verts) - 2 for f in bm.faces),
                 quads=sum(1 for f in bm.faces if len(f.verts) == 4),
                 ngons=sum(1 for f in bm.faces if len(f.verts) > 4),
                 boundary_edges=sum(1 for ed in bm.edges if len(ed.link_faces) == 1),
                 multi_face_edges=sum(1 for ed in bm.edges if len(ed.link_faces) > 2),
                 loose_verts=sum(1 for v in bm.verts if not v.link_edges),
                 uv_layers=[u.name for u in me.uv_layers],
                 materials=[m.name if m else None for m in me.materials],
                 shape_keys=len(me.shape_keys.key_blocks) if me.shape_keys else 0,
                 vertex_groups=len(o.vertex_groups),
                 modifiers=[m.type for m in o.modifiers])
        bm.free()
        ws = [o.matrix_world @ v.co for v in me.vertices]
        e["world_bbox"] = [[round(min(v[i] for v in ws), 5) for i in range(3)],
                           [round(max(v[i] for v in ws), 5) for i in range(3)]]
        if not o.hide_render and o.users_collection and all(c.name != "glTF_not_exported" for c in o.users_collection):
            visible.append(o)
    rep["objects"].append(e)

arm = next((o for o in scene.objects if o.type == "ARMATURE"), None)
bones = {}
if arm:
    for b in arm.data.bones:
        bones[b.name] = [round(c, 5) for c in (arm.matrix_world @ b.head_local)]
    rep["armature"] = {"name": arm.name, "bone_count": len(arm.data.bones),
                       "naming": "VRoid/VRM (J_Bip_*)" if any(n.startswith("J_Bip_") for n in bones) else "other"}

# ---- orientation (measured, not assumed) -------------------------------------
face = bpy.data.objects.get("Face"); body = bpy.data.objects.get("Body"); eyes = bpy.data.objects.get("MORWEN_Eyes")
ori = {}
if arm and "J_Bip_L_UpperArm" in bones and "J_Bip_C_Head" in bones:
    lx = bones["J_Bip_L_UpperArm"][0]
    ori["left_arm_bone_x_sign"] = "+X" if lx > 0 else "-X"
    if eyes:
        ey = sum((eyes.matrix_world @ v.co).y for v in eyes.data.vertices) / len(eyes.data.vertices)
        ori["face_front_axis"] = "+Y" if ey > bones["J_Bip_C_Head"][1] else "-Y"
    f = ori.get("face_front_axis"); 
    if f:
        # right-handed, +Z up: left = Z x forward
        left = "-X" if f == "+Y" else "+X"
        ori["geometric_left_for_this_front"] = left
        ori["bone_L_matches_geometric_left"] = (left == ori["left_arm_bone_x_sign"])
rep["orientation_measured"] = ori

# ---- proportion measurements (candidate only; method stated) ------------------
prop = {}
if body and face:
    bw = [body.matrix_world @ v.co for v in body.data.vertices]
    fw = [face.matrix_world @ v.co for v in face.data.vertices]
    floor = min(v.z for v in bw); top = max(max(v.z for v in bw), max(v.z for v in fw))
    front_sign = 1 if ori.get("face_front_axis") == "+Y" else -1
    ymax = max(v.y * front_sign for v in fw)
    # chin: lowest face vertex on the front third of the face mesh, near the midline
    front = [v for v in fw if abs(v.x) < 0.015 and v.y * front_sign > ymax - 0.045]
    chin = min(v.z for v in front)
    prop = {"floor_z": round(floor, 5), "top_incl_hair_z": round(top, 5),
            "stature_incl_hair_and_soles_m": round(top - floor, 5),
            "chin_z_method": "lowest Face vertex with |x|<15mm within 45mm of the frontmost face point",
            "chin_z": round(chin, 5),
            "head_len_chin_to_hair_top_m": round(top - chin, 5),
            "heads_tall_chin_to_hair_top": round((top - floor) / (top - chin), 3),
            "pose": "T-pose" if arm and abs(bones.get("J_Bip_L_Hand", [0])[0]) > 0.4 else "unknown",
            "caveat": "Hair volume and shoe soles are included; skull vertex is not exposed, so this is a silhouette head count, not an anatomical one."}
    for k in ("J_Bip_C_Hips", "J_Bip_C_Neck", "J_Bip_C_Head", "J_Bip_L_UpperLeg", "J_Bip_L_LowerLeg", "J_Bip_L_Foot", "J_Bip_L_UpperArm", "J_Bip_L_Hand"):
        if k in bones: prop["bone_" + k + "_z"] = bones[k][2]
    if "J_Bip_L_UpperLeg" in bones:
        prop["leg_len_hipjoint_to_floor_over_stature"] = round((bones["J_Bip_L_UpperLeg"][2] - floor) / (top - floor), 3)
rep["proportions_candidate"] = prop

# ---- materials ---------------------------------------------------------------
mats = []
for m in bpy.data.materials:
    if not m.node_tree: continue
    ids = [n.bl_idname for n in m.node_tree.nodes]
    mats.append({"name": m.name, "users": m.users,
                 "shading": "unlit-emission" if "ShaderNodeEmission" in ids and "ShaderNodeBsdfPrincipled" not in ids and "ShaderNodeBsdfToon" not in ids else "lit",
                 "has_normal_map": "ShaderNodeNormalMap" in ids,
                 "textures": sorted({n.image.name + " %dx%d" % tuple(n.image.size) for n in m.node_tree.nodes if n.bl_idname == "ShaderNodeTexImage" and n.image})})
rep["materials"] = mats
rep["visible_render_objects"] = [o.name for o in visible]
rep["triangle_total_visible"] = sum(e["tris"] for e in rep["objects"] if e["name"] in rep["visible_render_objects"])

# ---- fixed-camera renders -----------------------------------------------------
renders = {}
if RENDER and prop:
    for o in scene.objects:
        if o.type == "MESH" and o not in visible: o.hide_render = True
        if o.type == "LIGHT": o.hide_render = True   # look is emission-only; keep A/B independent of rig lights
    scene.render.engine = "CYCLES"; scene.cycles.device = "CPU"; scene.cycles.samples = SAMPLES
    scene.cycles.seed = 0; scene.cycles.use_denoising = False; scene.cycles.use_adaptive_sampling = False
    scene.cycles.transparent_max_bounces = 16
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"; scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"; scene.view_settings.look = "None"
    scene.world = bpy.data.worlds.new("FABLE_EVAL_BLACK"); scene.world.color = (0, 0, 0)
    cam_d = bpy.data.cameras.new("FABLE_EVAL_CAM"); cam_d.type = "ORTHO"
    cam = bpy.data.objects.new("FABLE_EVAL_CAM", cam_d); scene.collection.objects.link(cam); scene.camera = cam
    fs = 1 if ori.get("face_front_axis") == "+Y" else -1
    H = prop["stature_incl_hair_and_soles_m"]; zc = prop["floor_z"] + H / 2
    FULL = dict(scale=H * 1.08, res=(900, 1200), z=zc)          # ortho_scale applies to the larger (vertical) side
    hz = (prop["chin_z"] + prop["top_incl_hair_z"]) / 2
    FACE = dict(scale=(prop["top_incl_hair_z"] - prop["chin_z"]) * 1.35, res=(1024, 1024), z=hz)
    D = 5.0
    views = {"front": (Vector((0, fs * D, 0)), FULL), "back": (Vector((0, -fs * D, 0)), FULL),
             # character-left side = camera placed on the character's left looking at it
             "left": (Vector(((-fs) * D, 0, 0)), FULL), "right": (Vector((fs * D, 0, 0)), FULL),
             "face_front": (Vector((0, fs * D, 0)), FACE),
             "face_q3": (Vector((fs * D * 0.6, fs * D * 0.8, 0)), FACE)}
    for name, (off, cfg) in views.items():
        cam_d.ortho_scale = cfg["scale"]
        scene.render.resolution_x, scene.render.resolution_y = cfg["res"]; scene.render.resolution_percentage = 100
        tgt = Vector((0, 0, cfg["z"])); cam.location = tgt + off
        cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
        p = os.path.join(OUT, f"A_baseline_{name}.png"); scene.render.filepath = p
        bpy.ops.render.render(write_still=True)
        renders[name] = {"file": os.path.basename(p), "sha256": sha256(p), "resolution": list(cfg["res"]),
                         "ortho_scale": round(cfg["scale"], 5), "camera_location": [round(c, 4) for c in cam.location]}
    rep["render_settings"] = {"engine": "CYCLES", "device": "CPU", "samples": SAMPLES, "seed": 0, "denoise": False,
                              "film_transparent": True, "view_transform": "Standard", "world": "black",
                              "scene_lights": "disabled (materials are unlit emission)", "camera": "orthographic, distance 5 m"}
rep["renders"] = renders
rep["source_sha256_after"] = sha256(SRC)
rep["source_unmodified"] = rep["source_sha256_after"] == src_sha_before
rep["elapsed_s"] = round(time.time() - t0, 1)
with open(os.path.join(OUT, "A_BASELINE_INSPECTION.json"), "w") as f:
    json.dump(rep, f, indent=1, ensure_ascii=False)
print("DONE", json.dumps({k: rep[k] for k in ("orientation_measured", "proportions_candidate", "triangle_total_visible", "source_unmodified", "elapsed_s")}, indent=1))
