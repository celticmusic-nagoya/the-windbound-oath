"""Re-tessellate the measured C10 wall polygon while locking its boundary."""
import argparse
import json
from pathlib import Path
import sys

import bmesh
import bpy

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
from export_blueprint import scene_record, sha, write
from junction_contact_faces import audit, TARGET
from sculpt_junction import mesh_stats

SOURCE_SHA = "e363269d37c29bc02463247c70408ef8c2275dc673a285c72f3b4c1a54818c14"
WALL = 37372
NEIGHBOR = 8518
DIAGONAL = (37429, 37430)


def surface(mesh, omitted=frozenset()):
    """Key each untouched corner by the oriented face loop and vertex ID."""
    result = {}
    for face in mesh.polygons:
        if face.index in omitted:
            continue
        ids = list(face.vertices)
        offset = ids.index(min(ids))
        loops = list(face.loop_indices)
        key = tuple(ids[offset:] + ids[:offset])
        result[key] = (face.material_index, face.use_smooth, tuple(
            (tuple(tuple(layer.uv[loop].vector) for layer in mesh.uv_layers),
             tuple(mesh.corner_normals[loop].vector))
            for loop in loops[offset:] + loops[:offset]))
    return result


def split_wall(mesh):
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        face = bm.faces[WALL]
        if len(face.verts) != 47:
            raise ValueError("Measured wall no longer matches locked geometry")
        a, b = (bm.verts[index] for index in DIAGONAL)
        new, _ = bmesh.utils.face_split(face, a, b)
        if new is None:
            raise RuntimeError("Could not constrain the wall diagonal")
        children = bmesh.ops.triangulate(bm, faces=[face, new],
                                         quad_method="BEAUTY", ngon_method="BEAUTY")["faces"]
        child_keys = {frozenset(vert.index for vert in poly.verts) for poly in children}
        bm.to_mesh(mesh)
        mesh.update()
        return {face.index for face in mesh.polygons if frozenset(face.vertices) in child_keys}
    finally:
        bm.free()


def write_detail(root, before, after, obj, replacement):
    bounds = [p for pair in before["pairs"] for tri in pair["triangles"] for p in tri["world_xyz"]]
    center = [(min(p[i] for p in bounds)+max(p[i] for p in bounds))/2 for i in range(3)]
    radius = .36
    for axis in (0, 1, 2):
        other = [i for i in range(3) if i != axis]
        parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="920" height="490">',
                 '<rect width="920" height="490" fill="#f2f5f5"/>',
                 f'<text x="20" y="28">C10 junction | view normal {"XYZ"[axis]} | candidate-local BU</text>']
        def polygon(coords, offset, label):
            points = " ".join(f"{offset+210+(p[other[0]]-center[other[0]])*460:.3f},"
                              f"{245-(p[other[1]]-center[other[1]])*460:.3f}" for p in coords)
            return f'<polygon points="{points}" fill="none" stroke="#2b5166"><title>{label}</title></polygon>'
        for offset, label in ((10, "Before | face 8518 / 37372"), (465, "After | fixed boundary")):
            parts.append(f'<text x="{offset+10}" y="56">{label}</text>')
            parts.append(f'<clipPath id="p{offset}"><rect x="{offset}" y="64" width="440" height="400"/></clipPath>')
            parts.append(f'<g clip-path="url(#p{offset})">')
            if offset == 10:
                for pair in before["pairs"]:
                    for tri in pair["triangles"]:
                        parts.append(polygon(tri["world_xyz"], offset,
                                             f'face {tri["face_id"]}, vertices {tri["vertex_ids"]}'))
            else:
                mesh = obj.data
                for face_id in sorted(replacement):
                    face = mesh.polygons[face_id]
                    coords = [obj.matrix_world @ mesh.vertices[i].co for i in face.vertices]
                    if any(all(abs(p[i]-center[i]) <= radius for i in other) for p in coords):
                        parts.append(polygon(coords, offset, f"face {face_id}, vertices {list(face.vertices)}"))
            parts.append("</g>")
        parts.append("</svg>")
        (root / f"junction_projection_{'xyz'[axis]}.svg").write_text("\n".join(parts), encoding="utf8")
    write(root / "junction_contact_faces.json", {"before": before, "after": after})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    source, out = args.source.resolve(), args.output.resolve()
    if bpy.app.version != (5,3,0) or sha(source) != SOURCE_SHA or out in source.parents:
        raise ValueError("Invalid runtime, locked candidate, or output")
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    obj = scene.objects[TARGET]
    before = audit(obj)
    if len(before["pairs"]) != 2 or any(
        set(pair["face_ids"]) != {WALL, NEIGHBOR} or pair["intersection"]["kind"] != "CROSSING"
        for pair in before["pairs"]
    ):
        raise ValueError("Locked geometry no longer has the two measured crossings")
    original_xyz = [tuple(vertex.co) for vertex in obj.data.vertices]
    old_surface = surface(obj.data, {WALL})
    old_wall = obj.data.polygons[WALL]
    old_wall_slot = old_wall.material_index
    old_wall_uv = {obj.data.loops[k].vertex_index: tuple(tuple(layer.uv[k].vector)
                    for layer in obj.data.uv_layers) for k in old_wall.loop_indices}
    scene_before = scene_record(scene)
    stats_before, _ = mesh_stats(obj)
    replacement = split_wall(obj.data)
    bpy.context.view_layer.update()
    stats, _ = mesh_stats(obj)
    after = audit(obj)
    new_surface = surface(obj.data, replacement)
    uv_match = old_surface.keys() == new_surface.keys() and all(
        old[:2] == new_surface[key][:2] and all(a[0] == b[0]
        for a,b in zip(old[2],new_surface[key][2])) for key,old in old_surface.items())
    uv_match &= all(obj.data.polygons[i].material_index == old_wall_slot and all(
        tuple(tuple(layer.uv[k].vector) for layer in obj.data.uv_layers)
        == old_wall_uv[obj.data.loops[k].vertex_index] for k in obj.data.polygons[i].loop_indices)
        for i in replacement)
    normal_delta = max((abs(x-y) for key,old in old_surface.items() if key in new_surface
                        for a,b in zip(old[2],new_surface[key][2]) for x,y in zip(a[1],b[1])), default=0.0)
    sys.path.insert(0, str(Path.cwd() / "tools/map_blender/lind"))
    from inspect_windwaiting_cliff_C8 import headland_visibility
    try:
        visibility = headland_visibility(scene, obj)
    except AssertionError as error:
        visibility = error.args[0]
    visible = [row["unoccluded_face_samples"] for row in visibility]
    checks = {
        "nonadjacent_self_contacts_zero": after["nonadjacent_bvh_pairs"] == 0,
        "all_vertex_positions_bitwise_equal_by_id": original_xyz == [tuple(v.co) for v in obj.data.vertices],
        "visibility_at_least_10_4_13": len(visible) == 3 and all(a >= b for a,b in zip(visible,(10,4,13))),
        "closed_usable_topology": stats["nonmanifold_edges"] == stats["degenerate_faces"] == stats["boundary_edges"] == 0,
        "wall_retriangulated": len(replacement) == 45,
        "unchanged_uv_material_and_unedited_face_connectivity": uv_match,
        "outside_normal_component_delta_within_1e-6": normal_delta <= 1e-6,
        "camera_lights_and_object_settings_unchanged": scene_before == scene_record(scene),
        "input_sha_preserved": sha(source) == SOURCE_SHA,
    }
    scene["candidate"] = "C10_JUNCTION_RETOPO_UNAPPROVED"
    scene["junction_retopo_source_sha256"] = SOURCE_SHA
    destination = out / "junction_retopo_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    write_detail(out, before, after, obj, replacement)
    write(out / "local_qa.json", {"checks":checks,"before":stats_before,"after":stats,
                                  "source_sha256":SOURCE_SHA,"candidate_sha256":sha(destination),
                                  "replacement_face_ids":sorted(replacement),"visible":visibility,
                                  "outside_normal_max_delta":normal_delta,
                                  "G1":"BLOCKED","G2":"NOT_RUN",
                                  "G3":"BLOCKED" if all(checks.values()) else "FAIL","G4":"NOT_RUN"})
    print("RETOPO_LOCAL_QA", json.dumps(checks,sort_keys=True), normal_delta, flush=True)


if __name__ == "__main__":
    main()
