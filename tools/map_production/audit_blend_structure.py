"""Read-only structural audit of a .blend file (MAP-ASSET-PREP-01).

Usage (bpy module or Blender):
  python3 audit_blend_structure.py --blend FILE --out report.json
  blender -b --python audit_blend_structure.py -- --blend FILE --out report.json

Never saves the .blend. Embedded scripts are not executed (use_scripts=False).
Metrics are evidence for the structural audit; they are not an art PASS.
"""
import argparse, collections, hashlib, json, math, os, re, sys


def args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    p = argparse.ArgumentParser()
    p.add_argument("--blend", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def family(name):
    return re.sub(r"[._]\d+$", "", name)


def main():
    a = args()
    import bpy, bmesh
    bpy.ops.wm.open_mainfile(filepath=a.blend, load_ui=False, use_scripts=False)
    dg = bpy.context.evaluated_depsgraph_get()
    fam = collections.Counter()
    fam_tris = collections.Counter()
    tris = verts = 0
    nonmanifold = 0
    no_uv = 0
    dims_by_family = collections.defaultdict(set)
    mats_used = set()
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    for o in meshes:
        f = family(o.name)
        fam[f] += 1
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        me.calc_loop_triangles()
        t = len(me.loop_triangles)
        tris += t; verts += len(me.vertices); fam_tris[f] += t
        if not me.uv_layers:
            no_uv += 1
        bm = bmesh.new(); bm.from_mesh(me)
        nonmanifold += sum(1 for e in bm.edges if not e.is_manifold)
        bm.free()
        ev.to_mesh_clear()
        dims_by_family[f].add(tuple(round(d, 2) for d in o.dimensions))
        for s in o.material_slots:
            if s.material:
                mats_used.add(s.material.name)
    images = [{"name": i.name, "filepath": i.filepath, "size": list(i.size)} for i in bpy.data.images]
    tex_nodes = 0
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree:
            tex_nodes += sum(1 for n in m.node_tree.nodes if n.type == "TEX_IMAGE")
    rep = {
        "blend": os.path.basename(a.blend),
        "blend_sha256": sha256(a.blend),
        "audited_with_blender": bpy.app.version_string,
        "saved_with_blender": "%d.%d.%d" % tuple(bpy.data.version),
        "objects_total": len(bpy.data.objects),
        "mesh_objects": len(meshes),
        "evaluated_triangles": tris,
        "evaluated_vertices": verts,
        "nonmanifold_edges_evaluated": nonmanifold,
        "mesh_objects_without_uv": no_uv,
        "materials_used": len(mats_used),
        "image_texture_nodes": tex_nodes,
        "images": images,
        "collections": [c.name for c in bpy.data.collections],
        "families": {k: {"count": v, "triangles": fam_tris[k],
                          "distinct_dimensions": len(dims_by_family[k])}
                     for k, v in fam.most_common()},
        "scene": {
            "engine": bpy.context.scene.render.engine,
            "resolution": [bpy.context.scene.render.resolution_x, bpy.context.scene.render.resolution_y],
            "cameras": [o.name for o in bpy.data.objects if o.type == "CAMERA"],
        },
        "note": "Read-only evidence. Not an art/G2 PASS.",
    }
    with open(a.out, "w") as f:
        json.dump(rep, f, indent=2, ensure_ascii=False)
    print(json.dumps({k: rep[k] for k in ("blend", "mesh_objects", "evaluated_triangles", "materials_used", "image_texture_nodes", "mesh_objects_without_uv")}))


if __name__ == "__main__":
    main()
