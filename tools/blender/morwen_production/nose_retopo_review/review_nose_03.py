"""MORWEN-LOCAL-RETOPO-03-REVIEW: evaluate the EXISTING #312 nose candidate (no regeneration).

1. Rebuild with the committed #312 code/params and assert the Face geometry hash equals the
   hash of the CI artifact .blend (run 43521557206) -> the reviewed mesh is the existing candidate.
2. Depth 0 vs 0.5 under identical fixed cameras and ONE world-fixed light (clay + toon).
3. Priority expressions: VRM preset -> target index mapping from the VRM JSON, observed motion per
   facial region (side/region consistency), pairwise distinctness, nose-patch geometry under each
   key, and toon/clay renders for visual QA.
4. Validation toon look (Cycles Toon BSDF + ambient fill + inverted-hull outline): front, +/-45 deg.
Writes $MORWEN_OUT/REVIEW_03R_REPORT.json and SHEET_*.png. Technical QA only: art QA is reported
separately by a human/independent reviewer; nothing here can mark G2 PASS.
"""
import hashlib
import importlib.util
import json
import os
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
NR = HERE.parent / "nose_retopo"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


R = _load(NR / "run_nose_retopo_03.py", "morwen_nose_run")   # also loads build + measure modules
B, M3 = R.B, R.M3
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_local_retopo_03_review"))
R.OUT = OUT
P = json.loads((HERE / "review_params_03r.json").read_text())
VIEWS = R.VIEWS


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def face_hash(me):
    h = hashlib.sha256()
    for kb in me.shape_keys.key_blocks:
        h.update(kb.name.encode())
        h.update(np.round(np.array([v.co[:] for v in kb.data]), 7).astype(np.float64).tobytes())
    h.update(np.array([v for p in me.polygons for v in p.vertices], dtype=np.int32).tobytes())
    h.update(np.round(np.array([lp.uv[:] for lp in me.uv_layers.active.data]), 7).tobytes())
    return h.hexdigest()


def vrm_groups():
    raw = M3.SRC.read_bytes()
    n = struct.unpack("<I", raw[12:16])[0]
    j = json.loads(raw[20:20 + n])
    out = {}
    for g in j["extensions"]["VRM"]["blendShapeMaster"]["blendShapeGroups"]:
        key = g["presetName"] if g["presetName"] != "unknown" else g["name"].lower()
        out[key] = {"name": g["name"], "binds": [(j["meshes"][b["mesh"]]["name"], b["index"], b["weight"]) for b in g["binds"]]}
    return out


class ToonStage(R.Stage):
    """Same cameras as #312; light fixed in WORLD space for every view and depth."""

    def __init__(self, centre):
        super().__init__(centre)
        d = Vector(P["fixed_key_light_world_direction"]).normalized()
        self.sun.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        self.toon_cache = {}
        t = P["toon"]
        self.outline = bpy.data.materials.new("TOON_OUTLINE")
        self.outline.use_nodes = True
        nt = self.outline.node_tree
        nt.nodes.clear()
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*t["outline_rgb"], 1)
        mx = nt.nodes.new("ShaderNodeMixShader")
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        # inverted hull: flipped normals, so the visible rim is the FRONT-facing part of the shell;
        # the shell side between camera and skin is back-facing and must be transparent
        nt.links.new(geo.outputs["Backfacing"], mx.inputs[0])
        nt.links.new(em.outputs[0], mx.inputs[1])
        nt.links.new(tr.outputs[0], mx.inputs[2])
        nt.links.new(mx.outputs[0], o.inputs["Surface"])

    def toon(self, mat):
        if mat is None:
            return self.clay
        if mat.name not in self.toon_cache:
            t = P["toon"]
            m = bpy.data.materials.new("TOON_" + mat.name)
            m.use_nodes = True
            nt = m.node_tree
            nt.nodes.clear()
            img = next((n.image for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None)
            toon = nt.nodes.new("ShaderNodeBsdfToon")
            toon.inputs["Size"].default_value = t["toon_size"]
            toon.inputs["Smooth"].default_value = t["toon_smooth"]
            amb = nt.nodes.new("ShaderNodeEmission")
            amb.inputs["Strength"].default_value = t["ambient"]
            add = nt.nodes.new("ShaderNodeAddShader")
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            mx = nt.nodes.new("ShaderNodeMixShader")
            o = nt.nodes.new("ShaderNodeOutputMaterial")
            if img is not None:
                tex = nt.nodes.new("ShaderNodeTexImage")
                tex.image = img
                nt.links.new(tex.outputs["Color"], toon.inputs["Color"])
                nt.links.new(tex.outputs["Color"], amb.inputs["Color"])
                nt.links.new(tex.outputs["Alpha"], mx.inputs[0])
            else:
                mx.inputs[0].default_value = 1.0
            nt.links.new(toon.outputs[0], add.inputs[0])
            nt.links.new(amb.outputs[0], add.inputs[1])
            nt.links.new(tr.outputs[0], mx.inputs[1])
            nt.links.new(add.outputs[0], mx.inputs[2])
            nt.links.new(mx.outputs[0], o.inputs["Surface"])
            self.toon_cache[mat.name] = m
        return self.toon_cache[mat.name]

    def materials(self, mode, originals):
        for o in self.sc.objects:
            if o.type != "MESH" or o.hide_render or not originals.get(o.name):
                continue  # skip importer helpers (Icosphere) and slot-less meshes
            mod = o.modifiers.get("TOON_OUTLINE_HULL")
            n = len(originals[o.name])
            if mode == "toon":
                while len(o.material_slots) < n + 1:
                    o.data.materials.append(self.outline)
                for i in range(n):
                    o.material_slots[i].material = self.toon(originals[o.name][i])
                o.material_slots[n].material = self.outline
                if mod is None:
                    mod = o.modifiers.new("TOON_OUTLINE_HULL", "SOLIDIFY")
                    mod.thickness = P["toon"]["outline_thickness_m"]
                    mod.offset = 1.0
                    mod.use_flip_normals = True
                    mod.material_offset = n
                    mod.use_rim = False
                mod.show_render = True
            else:
                if mod is not None:
                    mod.show_render = False
                while len(o.material_slots) > n:
                    o.data.materials.pop()
        if mode != "toon":
            super().materials(mode, originals)

    def shot(self, set_name, view, mode, originals, scale=R.CLOSE_SCALE, res=R.RES):
        """Every mode uses the same world-fixed key light (no camera-relative lighting)."""
        sc = self.sc
        self.materials(mode, originals)
        sc.render.resolution_x = sc.render.resolution_y = res
        sc.cycles.samples = 24
        if mode == "toon":
            self.bg.inputs["Color"].default_value = (1, 1, 1, 1)
            self.bg.inputs["Strength"].default_value = P["world_ambient"]
        else:
            self.bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
            self.bg.inputs["Strength"].default_value = 0.6
        self.sun.hide_render = False
        d = Vector(VIEWS[view]).normalized()
        self.cam.data.ortho_scale = scale
        self.cam.location = self.centre + d * 1.5
        self.cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        sc.camera = self.cam
        tag = "" if scale == R.CLOSE_SCALE else "_face"
        f = OUT / "renders" / set_name / f"{view}_{mode}{tag}.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        sc.render.filepath = str(f.resolve())
        bpy.ops.render.render(write_still=True)
        R.Image.open(f).save(f)
        self.records.append(str(f.relative_to(OUT)))
        return f


def region_masks(W):
    out = {}
    for k, r in P["regions_world"].items():
        m = (W[:, 0] >= r["x"][0]) & (W[:, 0] <= r["x"][1]) & (W[:, 2] >= r["z"][0]) & (W[:, 2] <= r["z"][1])
        if "y_min" in r:
            m &= W[:, 1] >= r["y_min"]
        out[k] = m
    return out


MUST_NOT = {"blink_l": ["eye_R", "brow_R", "mouth"], "blink_r": ["eye_L", "brow_L", "mouth"],
            "a": ["eye_R", "eye_L", "brow_R", "brow_L"], "o": ["eye_R", "eye_L", "brow_R", "brow_L"],
            "u": ["eye_R", "eye_L", "brow_R", "brow_L"]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    params = json.loads(B.PARAMS_PATH.read_text())
    M3.load()
    face = bpy.data.objects["Face"]
    originals = {o.name: [s.material for s in o.material_slots] for o in bpy.context.scene.objects if o.type == "MESH"}
    base = M3.measure()
    tip0 = Vector(base["landmarks"]["pronasale"]["position"])
    rec = B.build(params)
    me = face.data
    h = face_hash(me)
    assert h == P["candidate"]["face_geometry_hash"], f"candidate differs from #312 artifact: {h}"
    patch = set(rec["patch_vertex_indices"])
    keys = me.shape_keys.key_blocks
    basis = np.array([v.co[:] for v in keys[0].data])
    W = R.world_verts(face, basis)
    masks = region_masks(W)
    groups = vrm_groups()
    thr = P["moving_threshold_mm"] / 1000
    expr = {}
    disp = {}
    for preset in P["priority_presets"]:
        g = groups[preset]
        idx = [b[1] for b in g["binds"] if b[0].startswith("Face")]
        assert len(idx) == 1, f"{preset}: expected one Face bind"
        kname = f"target_{idx[0]}"
        co = np.array([v.co[:] for v in keys[kname].data])
        d = np.linalg.norm(R.world_verts(face, co) - W, axis=1)
        disp[preset] = co - basis
        moved = {k: round(float(d[m].max() * 1000), 2) for k, m in masks.items()}
        moving = {k for k, v in moved.items() if v > P["moving_threshold_mm"]}
        exp_ok = set(P["expected_regions"][preset]) <= moving
        forbid = [k for k in MUST_NOT.get(preset, []) if k in moving]
        geo = R.patch_geometry_stats(face, patch, co, basis)
        expr[preset] = {"vrm_group_name": g["name"], "binds": g["binds"], "shape_key": kname,
                        "region_max_motion_mm": moved, "expected_regions": P["expected_regions"][preset],
                        "mapping_consistent": bool(exp_ok and not forbid), "unexpected_motion": forbid,
                        "nose_patch": {"folded": geo["folded_vs_basis"], "edge_ratio_p99": geo["edge_ratio_p99"],
                                       "inner_dihedral_deg_max": geo["inner_dihedral_deg_max"]},
                        "visual_qa": "PENDING_REVIEW (see REVIEW_03R.md; automated evidence is not art QA)"}
    distinct = {}
    names = list(disp)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            distinct[f"{a}|{b}"] = round(float(np.abs(disp[a] - disp[b]).max() * 1000), 3)
    identical = [k for k, v in distinct.items() if v < 0.01]

    # ---- renders ----------------------------------------------------------------------------
    centre = Vector((M3.MID_X, tip0.y - 0.02, tip0.z + 0.004))
    st = ToonStage(centre)
    dk = keys[params["design_range"]["shape_key_name"]]
    for d in P["depths"]:
        dk.value = d
        for v in VIEWS:
            st.shot(f"depth_{d}", v, "clay", originals)
            st.shot(f"depth_{d}", v, "toon", originals)
        for v in ("front", "q3L", "q3R"):
            st.shot(f"depth_{d}", v, "toon", originals, scale=R.FACE_SCALE)
    dk.value = P["review_depth"]
    for preset in P["priority_presets"]:
        kb = keys[expr[preset]["shape_key"]]
        kb.value = 1.0
        st.shot(f"expr_{preset}", "front", "toon", originals, scale=R.FACE_SCALE)
        st.shot(f"expr_{preset}", "q3L", "toon", originals, scale=R.FACE_SCALE)
        st.shot(f"expr_{preset}", "front", "clay", originals)
        kb.value = 0.0
    dk.value = 0.0

    # ---- sheets -----------------------------------------------------------------------------
    Rr = OUT / "renders"
    order = list(VIEWS)
    R.grid([(f"depth {d} clay", [(v, Rr / f"depth_{d}" / f"{v}_clay.png") for v in order]) for d in P["depths"]] +
           [(f"depth {d} toon", [(v, Rr / f"depth_{d}" / f"{v}_toon.png") for v in order]) for d in P["depths"]],
           320, OUT / "SHEET_DEPTH_0_VS_05.png",
           "Depth 0 vs 0.5 (0.5 = provisional, not adopted): identical ortho cameras, one world-fixed key light")
    R.grid([(f"depth {d}", [(v, Rr / f"depth_{d}" / f"{v}_toon_face.png") for v in ("q3R", "front", "q3L")]) for d in P["depths"]],
           400, OUT / "SHEET_TOON_FRONT_45.png",
           "Validation toon look (Cycles Toon BSDF + outline) - NOT the final game shader; right 45 / front / left 45")
    R.grid([(f"{p_} ({expr[p_]['shape_key']})", [("toon front", Rr / f"expr_{p_}" / "front_toon_face.png"),
                                                  ("toon left 45", Rr / f"expr_{p_}" / "q3L_toon_face.png"),
                                                  ("clay close-up", Rr / f"expr_{p_}" / "front_clay.png")])
            for p_ in P["priority_presets"]],
           300, OUT / "SHEET_PRIORITY_EXPRESSIONS.png", f"Priority expressions at 1.0, nose depth {P['review_depth']}")

    unreviewed = sorted(set(json.loads((HERE / "blocked_before_review.json").read_text())) -
                        {expr[p]["shape_key"] for p in P["priority_presets"]})
    report = {
        "task_id": P["task_id"], "blender_version": bpy.app.version_string,
        "source_vrm_sha256": M3.VRM_SHA256, "source_modified": False,
        "candidate": P["candidate"] | {"face_geometry_hash_rebuilt": h, "identical_to_artifact": True},
        "nose_regenerated": False,
        "expressions": expr, "pairwise_max_difference_mm": distinct, "identical_pairs": identical,
        "still_blocked_unreviewed_keys": unreviewed,
        "renders": st.records, "sheets": {p.name: sha(p) for p in sorted(OUT.glob("SHEET_*.png"))},
        "technical_qa": {
            "candidate_identical": True,
            "mapping_consistent_all": all(e["mapping_consistent"] for e in expr.values()),
            "nose_patch_no_folds_all": all(e["nose_patch"]["folded"] == 0 for e in expr.values()),
            "identical_expression_pairs": identical,
        },
        "art_qa": "NOT AUTOMATED - see REVIEW_03R.md (Claude self-review) and independent reviewer",
        "G1": "PASS for source preservation only (v5.61 binary unavailable)", "G2": "NOT_RUN (art review pending)",
        "G3": "see technical_qa", "G4": "NOT_RUN",
    }
    (OUT / "REVIEW_03R_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    assert sha(M3.SRC) == M3.VRM_SHA256
    print("review technical:", report["technical_qa"])


if __name__ == "__main__":
    main()
