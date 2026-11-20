import bpy, json, sys, os, hashlib
from collections import Counter

outdir = sys.argv[sys.argv.index("--")+1]
os.makedirs(outdir, exist_ok=True)
sc = bpy.context.scene
report = {
    "source_blend": os.path.basename(bpy.data.filepath),
    "source_sha256": hashlib.sha256(open(bpy.data.filepath,"rb").read()).hexdigest(),
    "blender_version": bpy.app.version_string,
    "objects": [],
    "mesh_count": 0,
}
for o in bpy.data.objects:
    item = {"name": o.name, "type": o.type, "parent": o.parent.name if o.parent else None}
    if o.type == 'MESH':
        me=o.data
        item.update(vertices=len(me.vertices), faces=len(me.polygons),
            material_face_counts={ (me.materials[i].name if i < len(me.materials) and me.materials[i] else "UNASSIGNED_"+str(i)): sum(1 for p in me.polygons if p.material_index == i) for i in sorted(set(p.material_index for p in me.polygons)) },
            material_vertex_counts={ (me.materials[i].name if i < len(me.materials) and me.materials[i] else "UNASSIGNED_"+str(i)): len(set(v for p in me.polygons if p.material_index == i for v in p.vertices)) for i in sorted(set(p.material_index for p in me.polygons)) },
            uv_layers=list(me.uv_layers.keys()),
            material_slots=[m.name if m else None for m in me.materials],
            shape_keys=[k.name for k in me.shape_keys.key_blocks] if me.shape_keys else [],
            modifiers=[{"name":m.name,"type":m.type} for m in o.modifiers],
            vertex_groups=len(o.vertex_groups))
        # Per-region reproducible fingerprints; distinguish same counts from identical geometry.
        regions = {}
        for i in sorted(set(p.material_index for p in me.polygons)):
            mat_name = me.materials[i].name if i < len(me.materials) and me.materials[i] else "UNASSIGNED_"+str(i)
            faces = [p for p in me.polygons if p.material_index == i]
            vertex_ids = sorted({v for p in faces for v in p.vertices})
            payload = {
                "faces": [(p.index, list(p.vertices), p.loop_start, p.loop_total) for p in faces],
                "vertices": [(v, [round(float(c), 8) for c in me.vertices[v].co]) for v in vertex_ids],
                "uv": [(p.index, [[round(float(c), 8) for c in me.uv_layers.active.data[li].uv] for li in p.loop_indices]) for p in faces] if me.uv_layers.active else [],
            }
            def digest(value):
                return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",",":")).encode()).hexdigest()
            keys = {}
            if me.shape_keys:
                for key in me.shape_keys.key_blocks:
                    coords = [(v, [round(float(c), 8) for c in key.data[v].co]) for v in vertex_ids]
                    keys[key.name] = digest(coords)
            groups = {}
            for v in vertex_ids:
                groups[str(v)] = [(o.vertex_groups[g.group].name, round(float(g.weight), 8)) for g in me.vertices[v].groups if g.group < len(o.vertex_groups)]
            regions[mat_name] = {
                "shape_key_position_sha256": keys,
                "weights_sha256": digest(groups),
                "faces": len(faces), "vertices": len(vertex_ids),
                "topology_sha256": digest(payload["faces"]),
                "positions_sha256": digest(payload["vertices"]),
                "uv_sha256": digest(payload["uv"]),
                "shared_vertices_with_other_regions": sum(1 for v in vertex_ids if any(p.material_index != i for p in me.polygons if v in p.vertices)),
            }
        item["regions"] = regions
        report["mesh_count"] += 1
    report["objects"].append(item)
with open(os.path.join(outdir,"structure.json"),"w") as f:
    json.dump(report,f,ensure_ascii=False,indent=2)
print("STRUCTURE_AUDIT",report["source_blend"],"MESHES",report["mesh_count"])
# No edits or misleading renders: source scene inspection only.
