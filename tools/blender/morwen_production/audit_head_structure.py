"""MORWEN-HEAD-STRUCTURE-01: read-only structural audit of the pinned VRoid CC0 head.

Runs inside Blender (``blender -b --python``) or with the ``bpy`` wheel.
Never saves, exports or edits the source: every measurement is taken on
in-memory BMesh copies. Output: render_output/morwen_head_structure/HEAD_STRUCTURE_AUDIT.json

Environment overrides:
  MORWEN_VRM  path to Base_Female.vrm (default render_output/morwen_vroid_review/Base_Female.vrm)
  MORWEN_OUT  output directory (default render_output/morwen_head_structure)
"""
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import bpy  # noqa: I001  (bpy before bmesh for the standalone bpy wheel)
import bmesh
from mathutils import Vector
from mathutils.kdtree import KDTree

SOURCE_SHA256_ZIP = "bf2717cff70b40a278df56e137dbb699c6499551096fa4c005e9aeca1de68eb3"
WELD_DIST = 1e-5
SRC = Path(os.environ.get("MORWEN_VRM", "render_output/morwen_vroid_review/Base_Female.vrm"))
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_head_structure"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def r(v, n=5):
    return [round(x, n) for x in v]


def load():
    assert SRC.is_file(), f"Pinned source missing: {SRC}"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(SRC.resolve()))


def head_anchor():
    arm = next(o for o in bpy.context.scene.objects if o.type == "ARMATURE")
    bones = arm.data.bones
    neck = arm.matrix_world @ bones["J_Bip_C_Neck"].head_local
    head = arm.matrix_world @ bones["J_Bip_C_Head"].head_local
    eyes = [arm.matrix_world @ bones[n].head_local for n in ("J_Adj_L_FaceEye", "J_Adj_R_FaceEye")]
    return {"neck": neck, "head": head, "eye_mid": (eyes[0] + eyes[1]) * 0.5, "armature": arm}


def world_bm(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)  # basis shape, rest pose: the source data as authored
    bm.transform(obj.matrix_world)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def components(bm):
    """Edge-connected islands. Returns list of (vert_index_set, face_index_list)."""
    seen = set()
    out = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, ids = [v], set()
        seen.add(v.index)
        while stack:
            q = stack.pop()
            ids.add(q.index)
            for e in q.link_edges:
                o = e.other_vert(q)
                if o.index not in seen:
                    seen.add(o.index)
                    stack.append(o)
        out.append(ids)
    face_of = defaultdict(list)
    for f in bm.faces:
        face_of[f.verts[0].index].append(f.index)
    res = []
    for ids in out:
        faces = [fi for vi in ids for fi in face_of.get(vi, [])]
        res.append((ids, faces))
    return res


def boundary_loops(edges):
    adj = defaultdict(list)
    for e in edges:
        a, b = e.verts
        adj[a.index].append(b.index)
        adj[b.index].append(a.index)
    seen, loops = set(), 0
    for start in adj:
        if start in seen:
            continue
        loops += 1
        stack = [start]
        seen.add(start)
        while stack:
            q = stack.pop()
            for n in adj[q]:
                if n not in seen:
                    seen.add(n)
                    stack.append(n)
    return loops


def winding_conflicts(bm):
    """Manifold edges whose two faces traverse the edge in the same direction (= one face flipped)."""
    bad = 0
    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        a, b = e.verts
        dirs = []
        for f in e.link_faces:
            vs = list(f.verts)
            i = vs.index(a)
            dirs.append(vs[(i + 1) % len(vs)] is b)
        if dirs[0] == dirs[1]:
            bad += 1
    return bad


def mesh_structure(obj, anchor, mat_names):
    bm = world_bm(obj)
    raw_v, raw_f = len(bm.verts), len(bm.faces)
    raw_comps = components(bm)
    # duplicate faces on raw data (same vertex positions, any order)
    keys = Counter(tuple(sorted(tuple(round(c, 6) for c in v.co) for v in f.verts)) for f in bm.faces)
    dup_faces = sum(n - 1 for n in keys.values() if n > 1)
    degenerate = sum(1 for f in bm.faces if f.calc_area() < 1e-12)
    # position weld (UV/normal seam split undo) on the in-memory copy only
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=WELD_DIST)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    comps = components(bm)
    head_z = anchor["neck"].z
    comp_rows = []
    for ids, faces in sorted(comps, key=lambda c: -len(c[0])):
        co = [bm.verts[i].co for i in ids]
        lo = Vector([min(c[k] for c in co) for k in range(3)])
        hi = Vector([max(c[k] for c in co) for k in range(3)])
        mats = Counter(mat_names[bm.faces[fi].material_index] for fi in faces)
        fset = [bm.faces[fi] for fi in faces]
        edges = {e for f in fset for e in f.edges}
        bnd = [e for e in edges if e.is_boundary]
        nonman = [e for e in edges if len(e.link_faces) > 2]
        cen = sum(co, Vector()) / len(co)
        inward = sum(1 for f in fset if f.normal.dot(f.calc_center_median() - cen) < 0) if fset else 0
        comp_rows.append({
            "vertices": len(ids), "faces": len(faces),
            "materials": dict(mats),
            "bounds_min": r(lo), "bounds_max": r(hi),
            "in_head_region": hi.z > head_z,
            "boundary_edges": len(bnd), "boundary_loops": boundary_loops(bnd),
            "non_manifold_edges": len(nonman),
            "faces_pointing_toward_centroid": inward,
        })
    result = {
        "raw_vertices": raw_v, "raw_faces": raw_f,
        "raw_edge_components": len(raw_comps),
        "welded_vertices": len(bm.verts),
        "seam_duplicate_vertices": raw_v - len(bm.verts),
        "welded_components": len(comps),
        "duplicate_faces": dup_faces,
        "degenerate_faces": degenerate,
        "boundary_edges": sum(1 for e in bm.edges if e.is_boundary),
        "non_manifold_edges_gt2": sum(1 for e in bm.edges if len(e.link_faces) > 2),
        "winding_conflict_edges": winding_conflicts(bm),
        "loose_vertices": sum(1 for v in bm.verts if not v.link_edges),
        "has_custom_split_normals": bool(obj.data.has_custom_normals),
        "components": comp_rows,
    }
    bm.free()
    return result


def material_audit(mat):
    info = {
        "blend_method": getattr(mat, "blend_method", None),
        "surface_render_method": getattr(mat, "surface_render_method", None),
        "backface_culling": bool(mat.use_backface_culling),
        "images": [], "alpha_linked": False, "base_color_factor": None,
    }
    if mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                info["images"].append({"name": n.image.name, "size": list(n.image.size),
                                       "alpha_mode": n.image.alpha_mode})
            if n.type == "BSDF_PRINCIPLED":
                info["alpha_linked"] = n.inputs["Alpha"].is_linked
                info["alpha_value"] = round(n.inputs["Alpha"].default_value, 4)
                bc = n.inputs["Base Color"]
                info["base_color_linked"] = bc.is_linked
                info["base_color_factor"] = r(bc.default_value, 4)
    return info


def skin_audit(obj):
    vg = {g.index: g.name for g in obj.vertex_groups}
    unweighted, influences, dominant = 0, Counter(), Counter()
    for v in obj.data.vertices:
        ws = [(g.weight, vg[g.group]) for g in v.groups if g.weight > 0]
        if not ws:
            unweighted += 1
            continue
        influences[len(ws)] += 1
        dominant[max(ws)[1]] += 1
    keys = []
    sk = obj.data.shape_keys
    if sk:
        basis = sk.key_blocks[0].data
        for kb in sk.key_blocks[1:]:
            disp = max(((kb.data[i].co - basis[i].co).length for i in range(len(basis))), default=0)
            keys.append({"name": kb.name, "value": round(kb.value, 4), "max_displacement": round(disp, 5)})
    return {
        "armature_modifiers": [m.object.name if m.object else None for m in obj.modifiers if m.type == "ARMATURE"],
        "unweighted_vertices": unweighted,
        "influence_histogram": dict(sorted(influences.items())),
        "dominant_bones_top10": dominant.most_common(10),
        "shape_keys": keys,
        "nonzero_shape_keys": [k["name"] for k in keys if k["value"] != 0],
    }


def head_coverage(anchor):
    """Which materials cover the skull above the eye line, split front/back of the head centre."""
    hc = anchor["head"]
    eye_z = anchor["eye_mid"].z
    rows = Counter()
    for obj in (o for o in bpy.context.scene.objects if o.type == "MESH"):
        if obj.users_collection and obj.users_collection[0].name == "glTF_not_exported":
            continue
        mw = obj.matrix_world
        for p in obj.data.polygons:
            c = mw @ p.center
            if c.z < eye_z:
                continue
            side = "front" if c.y > hc.y else "back"
            mat = obj.material_slots[p.material_index].material.name if obj.material_slots else "<none>"
            rows[f"{side}|{obj.name}|{mat}"] += 1
    return {k: v for k, v in sorted(rows.items())}


def face_body_seam():
    """Open border of the Face mesh vs nearest Body vertex (the two objects are never welded)."""
    face = bpy.data.objects["Face"]
    body = bpy.data.objects["Body"]
    bmf = world_bm(face)
    bmesh.ops.remove_doubles(bmf, verts=bmf.verts, dist=WELD_DIST)
    border = {v for e in bmf.edges if e.is_boundary for v in e.verts
              if any("SKIN" in face.material_slots[f.material_index].material.name.upper() for f in v.link_faces)}
    bmb = world_bm(body)
    kd = KDTree(len(bmb.verts))
    for v in bmb.verts:
        kd.insert(v.co, v.index)
    kd.balance()
    d = sorted(kd.find(v.co)[2] for v in border)
    n = len(d)
    out = {"face_skin_border_vertices": n,
           "nearest_body_vertex_distance_m": {
               "min": round(d[0], 6), "median": round(d[n // 2], 6),
               "p95": round(d[int(n * .95)], 6), "max": round(d[-1], 6)},
           "coincident_within_0_1mm": sum(1 for x in d if x < 1e-4),
           "interpretation": "Face mask border meets Body head skin as separate unwelded objects"}
    bmf.free()
    bmb.free()
    return out


def main():
    load()
    OUT.mkdir(parents=True, exist_ok=True)
    anchor = head_anchor()
    report = {
        "task_id": "MORWEN-HEAD-STRUCTURE-01",
        "source_file": SRC.name, "source_vrm_sha256": sha256(SRC),
        "source_zip_sha256_pinned": SOURCE_SHA256_ZIP,
        "source_modified": False,
        "blender_version": bpy.app.version_string,
        "units": "Blender world metres after glTF import (Y-forward model faces +Y)",
        "anchor": {k: r(v) for k, v in anchor.items() if k != "armature"},
        "objects": [], "meshes": {}, "materials": {}, "skinning": {},
    }
    for o in bpy.context.scene.objects:
        report["objects"].append({
            "name": o.name, "type": o.type,
            "parent": o.parent.name if o.parent else None,
            "collection": o.users_collection[0].name if o.users_collection else None,
            "children": [c.name for c in o.children],
        })
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        names = [s.material.name if s.material else "<none>" for s in o.material_slots] or ["<none>"]
        report["meshes"][o.name] = mesh_structure(o, anchor, names)
        report["meshes"][o.name]["faces_per_material"] = dict(Counter(names[p.material_index] for p in o.data.polygons))
        report["skinning"][o.name] = skin_audit(o)
    for m in bpy.data.materials:
        report["materials"][m.name] = material_audit(m)
    report["skull_coverage_above_eye_line"] = head_coverage(anchor)
    report["face_body_seam"] = face_body_seam()
    (OUT / "HEAD_STRUCTURE_AUDIT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    # source must be byte-identical after the run
    assert sha256(SRC) == report["source_vrm_sha256"]
    print("HEAD_STRUCTURE_AUDIT written", OUT)


if __name__ == "__main__":
    main()
