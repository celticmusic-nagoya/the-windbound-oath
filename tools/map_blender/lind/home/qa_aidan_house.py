"""LIND-HOME-01 technical QA (G3 evidence) for the Aidan house candidate.

    python3 tools/map_blender/lind/home/qa_aidan_house.py --blend <file.blend> --candidate <dir> --out <json>
    blender -b --python tools/map_blender/lind/home/qa_aidan_house.py -- --blend ... (same args)

Checks (each reported PASS/FAIL with numbers; nothing is assumed):
  mesh: UV map present, material slots valid, degenerate faces, non-manifold / boundary edges,
        closed-shell orientation (signed volume per connected component > 0 = outward normals)
  budgets: triangles per collection vs docs/production/lind/home/arch-kit-contract.v1.json
  materials: unique exported material count, contract IDs
  naming: GEO_/COL_/ANC_/STG_/LGT_/CAM_ prefixes; required anchors; collision proxies non-rendered
  sources: SHA-256 of approved references, world master and CC0 textures unchanged
  renders: PNG size <= 1280, not blank; determinism = identical geometry_sha256 across run manifests
"""
import argparse
import glob
import hashlib
import json
import os
import sys

import bpy
import bmesh

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../.."))
HERE = os.path.dirname(os.path.abspath(__file__))

APPROVED = {
    "assets/approved/world/rilde_village.png": "c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a",
    "assets/approved/game/rilde_story/raid/attack_background_only.png": "a19e782ec0927f9ef983cf896cf31a18ace0aca8bf2b165714342b1cfe528c3e",
    "assets/approved/game/rilde_story/aftermath/ruins_background_only.png": "78b0801f10b6a763c66aa44265ab381edc398f3b5adfb1b3d3dee0e6c6d917b2",
    "data/maps/rilde_in_aidan.json": None,  # filled from git HEAD blob at runtime (must be unmodified)
}
WORLD_MASTER = ("/home/claude/refs/lind_world_master_abbb3997.png", "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620")
# objects where open boundaries are by design (single-sided cloth, terrain staging, roof deck ridge seam,

OPEN_OK = {"GEO_AIDANHOUSE_PROPS_LAUNDRY", "STG_AIDANHOUSE_GROUND", "GEO_AIDANHOUSE_ROOFDECK"}
REQUIRED_ANCHORS = ["ANC_AIDANHOUSE_DOOR_MAIN_EXT", "ANC_AIDANHOUSE_DOOR_MAIN_INT", "ANC_AIDANHOUSE_SPAWN_BEDSIDE",
                    "ANC_AIDANHOUSE_EVENT_BED", "ANC_AIDANHOUSE_SAVE_BED"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def mesh_checks(ob):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.edges.ensure_lookup_table()
    boundary = sum(1 for e in bm.edges if len(e.link_faces) == 1)
    nonman = sum(1 for e in bm.edges if len(e.link_faces) > 2)
    wire = sum(1 for e in bm.edges if len(e.link_faces) == 0)
    degen = sum(1 for f in bm.faces if f.calc_area() < 1e-9)
    # connected components + signed volume (closed shells only)
    parent = list(range(len(bm.verts)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    comp_vol = {}
    comp_open = set()
    for e in bm.edges:
        if len(e.link_faces) != 2:
            comp_open.add(find(e.verts[0].index))
    for f in bm.faces:
        c = find(f.verts[0].index)
        v0 = f.verts[0].co
        for i in range(1, len(f.verts) - 1):
            v1, v2 = f.verts[i].co, f.verts[i + 1].co
            comp_vol[c] = comp_vol.get(c, 0.0) + v0.dot(v1.cross(v2)) / 6.0
    closed = {c: v for c, v in comp_vol.items() if c not in comp_open}
    inverted = sum(1 for v in closed.values() if v <= 0)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    bm.free()
    mat_ok = len(me.materials) > 0 and all(m is not None for m in me.materials) and \
        all(p.material_index < len(me.materials) for p in me.polygons)
    return {
        "tris": tris, "faces": len(me.polygons), "uv": "UVMap" in me.uv_layers, "materials": [m.name for m in me.materials if m],
        "material_slots_ok": mat_ok, "degenerate_faces": degen, "boundary_edges": boundary, "nonmanifold_edges_gt2": nonman,
        "wire_edges": wire, "components": len(comp_vol), "closed_components": len(closed), "inverted_closed_components": inverted,
    }


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--manifests", default="", help="glob of build_manifest.json files from separate runs")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    bpy.ops.wm.open_mainfile(filepath=a.blend)
    contract = json.load(open(os.path.join(REPO, "docs/production/lind/home/arch-kit-contract.v1.json")))
    res = {"task_id": "LIND-HOME-01", "blender": bpy.app.version_string, "blend": os.path.relpath(a.blend, REPO),
           "blend_sha256": sha(a.blend), "checks": {}, "objects": {}}
    C = res["checks"]
    fails = []

    def check(name, ok, detail):
        C[name] = {"result": "PASS" if ok else "FAIL", "detail": detail}
        if not ok:
            fails.append(name)

    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in meshes:
        res["objects"][o.name] = mesh_checks(o)
    O = res["objects"]
    render_meshes = [n for n in O if not n.startswith("COL_")]
    check("uv_present", all(O[n]["uv"] for n in render_meshes), [n for n in render_meshes if not O[n]["uv"]])
    check("material_slots_valid", all(O[n]["material_slots_ok"] for n in render_meshes), [n for n in render_meshes if not O[n]["material_slots_ok"]])
    check("degenerate_faces_zero", all(O[n]["degenerate_faces"] == 0 for n in O), {n: O[n]["degenerate_faces"] for n in O if O[n]["degenerate_faces"]})
    check("nonmanifold_gt2_zero", all(O[n]["nonmanifold_edges_gt2"] == 0 for n in O), {n: O[n]["nonmanifold_edges_gt2"] for n in O if O[n]["nonmanifold_edges_gt2"]})
    closed_req = [n for n in O if n not in OPEN_OK]
    check("closed_shells_where_required", all(O[n]["boundary_edges"] == 0 for n in closed_req),
          {n: O[n]["boundary_edges"] for n in closed_req if O[n]["boundary_edges"]})
    check("open_boundaries_by_design_listed", True, {n: O[n]["boundary_edges"] for n in OPEN_OK if n in O})
    check("normals_outward_closed_components", all(O[n]["inverted_closed_components"] == 0 for n in O),
          {n: O[n]["inverted_closed_components"] for n in O if O[n]["inverted_closed_components"]})

    # budgets
    def coll_tris(cname):
        c = bpy.data.collections.get(cname)
        return sum(O[o.name]["tris"] for o in c.all_objects if o.type == "MESH") if c else 0
    shell = sum(coll_tris(c) for c in ("FOUNDATION", "WALL_SHELL", "MASONRY", "TIMBER", "ROOF_STRUCT", "ROOF_SLATE", "OPENINGS", "CHIMNEY", "PORCH"))
    b = contract["lod_budgets_tris"]
    budgets = {
        "LOD0_master_house_shell": (shell, b["LOD0_master_house_shell"]),
        "LOD0_props_ext": (coll_tris("PROPS_EXT"), b["LOD0_props_ext"]),
        "LOD0_interior": (coll_tris("INTERIOR"), b["LOD0_interior"]),
        "collision": (coll_tris("COLLISION"), b["collision"]),
    }
    check("tri_budgets", all(v <= lim for v, lim in budgets.values()), {k: {"tris": v, "budget": lim} for k, (v, lim) in budgets.items()})
    C["lod1_lod2"] = {"result": "NOT_RUN", "detail": "LOD1/LOD2 not generated in candidate c01"}

    # materials
    used = sorted({m.name for o in meshes if not o.name.startswith("STG_") for m in o.data.materials if m})
    shell_cols = ("FOUNDATION", "WALL_SHELL", "MASONRY", "TIMBER", "ROOF_STRUCT", "ROOF_SLATE", "OPENINGS", "CHIMNEY", "PORCH")
    shell_mats = sorted({m.name for c in shell_cols for o in bpy.data.collections[c].all_objects if o.type == "MESH" for m in o.data.materials if m})
    check("material_count_le_contract", len(shell_mats) <= contract["max_unique_materials_per_building"],
          {"building_shell_count": len(shell_mats), "contract_max": contract["max_unique_materials_per_building"], "shell_materials": shell_mats,
           "all_exported_incl_interior_props": len(used), "all": used})
    missing_ids = [k for k in contract["materials"] if k not in used]
    check("contract_material_ids_present", not missing_ids, {"missing": missing_ids})

    # naming / anchors / collision
    bad = [o.name for o in bpy.data.objects if not o.name.split("_")[0] in ("GEO", "COL", "ANC", "STG", "LGT", "CAM")]
    check("naming_prefixes", not bad, bad)
    anchors = {o.name: dict(o.items()) for o in bpy.data.objects if o.name.startswith("ANC_")}
    check("required_anchors", all(n in anchors for n in REQUIRED_ANCHORS), {"present": sorted(anchors)})
    cols = [o for o in bpy.data.objects if o.name.startswith("COL_")]
    check("collision_nonrender", bool(cols) and all(o.hide_render for o in cols), {"count": len(cols)})

    # sources unchanged
    src = {}
    ok = True
    import subprocess
    for p, want in APPROVED.items():
        full = os.path.join(REPO, p)
        got = sha(full)
        if want is None:
            blob = subprocess.run(["git", "-C", REPO, "show", "c0223b5:" + p], capture_output=True).stdout
            want = hashlib.sha256(blob).hexdigest()
        src[p] = {"sha256": got, "expected": want, "ok": got == want}
        ok &= got == want
    if os.path.isfile(WORLD_MASTER[0]):
        got = sha(WORLD_MASTER[0])
        src["world_master(local ref copy)"] = {"sha256": got, "expected": WORLD_MASTER[1], "ok": got == WORLD_MASTER[1]}
        ok &= got == WORLD_MASTER[1]
    tex = json.load(open(os.path.join(HERE, "texture_sources.json")))["files"]
    texdir = next((d for d in (os.environ.get("LIND_TEX_CACHE", ""), "/home/claude/.cache/lind_home_tex") if d and os.path.isdir(d)), None)
    for f, rec in tex.items():
        p = os.path.join(texdir or "", f)
        got = sha(p) if os.path.isfile(p) else "MISSING"
        src["tex:" + f] = {"sha256": got, "expected": rec["sha256"], "ok": got == rec["sha256"]}
        ok &= got == rec["sha256"]
    check("source_sha_unchanged", ok, src)

    # renders
    try:
        from PIL import Image, ImageStat
        rend = {}
        rok = True
        for p in sorted(glob.glob(os.path.join(a.candidate, "*.png")) + glob.glob(os.path.join(a.candidate, "game", "*.png"))):
            im = Image.open(p)
            st = ImageStat.Stat(im.convert("L"))
            r = {"size": im.size, "mode": im.mode, "std": round(st.stddev[0], 2), "sha256": sha(p)}
            r["ok"] = max(im.size) <= 1280 and (st.stddev[0] > 3 or "nearest" in p or "px" in p)
            rok &= r["ok"]
            rend[os.path.relpath(p, REPO)] = r
        check("renders_size_nonblank", rok and bool(rend), rend)
    except ImportError:
        C["renders_size_nonblank"] = {"result": "NOT_RUN", "detail": "PIL unavailable"}
    if a.manifests:
        hs = {}
        for m in sorted(glob.glob(a.manifests)):
            hs[m] = json.load(open(m))["geometry_sha256"]
        check("deterministic_geometry_across_runs", len(set(hs.values())) == 1 and len(hs) >= 2, hs)
    res["summary"] = {"fail": fails, "result": "PASS" if not fails else "FAIL", "note": "G3 technical scope only; not art (G2) or runtime (G4)"}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1, default=str)
    print("QA", res["summary"])
    for k, v in C.items():
        print(" ", k, v["result"])


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
