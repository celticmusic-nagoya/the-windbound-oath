"""Blender headless exporter for SHA-locked, unapproved cliff scenes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import write_views

SCHEMA = 1
DECIMALS = 9
TOLERANCE = 1e-6


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def clean(value):
    if isinstance(value, float):
        return round(value, DECIMALS) or 0.0
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {key: clean(item) for key, item in value.items()}
    return [clean(item) for item in value]


def write(path, data):
    path.write_text(json.dumps(clean({"schema_version": SCHEMA, **data}),
                               sort_keys=True, ensure_ascii=False, allow_nan=False,
                               separators=(",", ":")) + "\n", encoding="utf-8")


def properties(owner, names):
    return {name: getattr(owner, name) for name in names.split() if hasattr(owner, name)}


def graph(tree):
    if tree is None:
        return None

    def socket_record(socket):
        result = {"id": socket.identifier, "type": socket.bl_idname}
        value = getattr(socket, "default_value", None)
        if isinstance(value, bpy.types.ID):
            result["default_id"] = value.name
        elif isinstance(value, (str, int, bool, float, list, tuple)) or hasattr(value, "__iter__"):
            result["default"] = clean(value)
        return result

    nodes = []
    for node in sorted(tree.nodes, key=lambda item: item.name):
        record = {"name": node.name, "type": node.bl_idname,
                  "inputs": [socket_record(sock) for sock in node.inputs],
                  "outputs": [socket_record(sock) for sock in node.outputs],
                  **properties(node, "operation blend_type interpolation extension projection "
                                     "space uv_map attribute_name mute")}
        for attr in ("image", "node_tree", "object"):
            target = getattr(node, attr, None)
            if target is not None:
                record[attr] = target.name
        ramp = getattr(node, "color_ramp", None)
        if ramp is not None:
            record["color_ramp"] = {"interpolation": ramp.interpolation,
                                    "elements": [[item.position, item.color] for item in ramp.elements]}
        nodes.append(record)
    return {"nodes": nodes, "links": sorted(
        [link.from_node.name, link.from_socket.identifier, link.to_node.name, link.to_socket.identifier]
        for link in tree.links)}


def materials():
    images = []
    for image in sorted(bpy.data.images, key=lambda item: item.name):
        if image.source not in {"FILE", "TILED", "SEQUENCE", "MOVIE"} and not image.packed_files:
            continue
        external = Path(bpy.path.abspath(image.filepath, library=image.library))
        packed = [{"path": item.filepath, "sha256": hashlib.sha256(item.packed_file.data).hexdigest()}
                  for item in image.packed_files]
        external_hash = sha(external) if not packed and external.is_file() else None
        images.append({"name": image.name, "path": image.filepath, "size": image.size,
                       "source": image.source, "colorspace": image.colorspace_settings.name,
                       "packed": packed, "external_sha256": external_hash, "license": None,
                       "dependency_status": "PASS" if packed or external_hash else "BLOCKED"})
    return {"images": images, "node_groups": {tree.name: graph(tree) for tree in bpy.data.node_groups},
            "materials": {mat.name: {"graph": graph(mat.node_tree),
                                     **properties(mat, "diffuse_color metallic roughness surface_render_method "
                                                       "displacement_method")}
                          for mat in bpy.data.materials}}


def mesh_record(mesh, matrix, vertex_groups=()):
    mesh.calc_loop_triangles()
    local = [tuple(v.co) for v in mesh.vertices]
    world = [tuple(matrix @ v.co) for v in mesh.vertices]
    edges = [list(edge.vertices) for edge in mesh.edges]
    polygons = [list(face.vertices) for face in mesh.polygons]
    incidence = Counter(tuple(sorted(edge)) for face in mesh.polygons for edge in face.edge_keys)
    face_keys = Counter(tuple(sorted(face)) for face in polygons)
    roots = list(range(len(local)))

    def root(vertex):
        while roots[vertex] != vertex:
            roots[vertex] = roots[roots[vertex]]
            vertex = roots[vertex]
        return vertex

    for a, b in edges:
        first, second = sorted((root(a), root(b)))
        roots[second] = first
    components = [root(i) for i in range(len(local))]
    return {"name": mesh.name, "xyz_local": local, "xyz_world": world,
            "vertex_normals": [v.normal[:] for v in mesh.vertices],
            "edges": edges, "seams": [e.index for e in mesh.edges if e.use_seam],
            "sharp_edges": [e.index for e in mesh.edges if e.use_edge_sharp],
            "faces": [{"vertices": p, "loops": list(face.loop_indices), "normal": face.normal[:],
                       "area": face.area, "smooth": face.use_smooth, "material_slot": face.material_index}
                      for p, face in zip(polygons, mesh.polygons)],
            "loops": [[loop.vertex_index, loop.edge_index] for loop in mesh.loops],
            "corner_normals": [item.vector[:] for item in mesh.corner_normals],
            "triangles": [[tri.polygon_index, *tri.vertices] for tri in mesh.loop_triangles],
            "uv": {layer.name: [item.vector[:] for item in layer.uv] for layer in mesh.uv_layers},
            "active_uv": mesh.uv_layers.active.name if mesh.uv_layers.active else None,
            "render_uv": [layer.name for layer in mesh.uv_layers if layer.active_render],
            "slots": [m.name if m else None for m in mesh.materials],
            "vertex_groups": list(vertex_groups),
            "weights": [[[item.group, item.weight] for item in v.groups] for v in mesh.vertices],
            "attributes": [[a.name, a.domain, a.data_type] for a in mesh.attributes],
            "components": components,
            "bounds_world": [[min(column), max(column)] for column in zip(*world)],
            "diagnostics": {"boundary_edges": [i for i,e in enumerate(edges) if incidence[tuple(sorted(e))] == 1],
                            "nonmanifold_edges": [i for i,e in enumerate(edges) if incidence[tuple(sorted(e))] > 2],
                            "loose_edges": [i for i,e in enumerate(edges) if not incidence[tuple(sorted(e))]],
                            "loose_vertices": sorted(set(range(len(local))) - {v for e in edges for v in e}),
                            "degenerate_faces": [p.index for p in mesh.polygons if p.area <= TOLERANCE**2],
                            "duplicate_faces": [i for i,p in enumerate(polygons) if face_keys[tuple(sorted(p))] > 1],
                            "self_intersection": "NOT_RUN", "inter_object_intersection": "NOT_RUN"}}


def scene_record(scene):
    objects = {}
    for obj in sorted(scene.objects, key=lambda item: item.name):
        record = {"type": obj.type, "data": obj.data.name if obj.data else None,
                  "world_matrix": obj.matrix_world, "local_matrix": obj.matrix_local,
                  "parent_inverse": obj.matrix_parent_inverse, "parent": obj.parent.name if obj.parent else None,
                  "collections": sorted(c.name for c in obj.users_collection),
                  "render_hidden": obj.hide_render, "viewport_hidden": obj.hide_viewport,
                  "modifiers": [{"name": m.name, "type": m.type, "render": m.show_render,
                                 "viewport": m.show_viewport} for m in obj.modifiers],
                  "material_slots": [[slot.link, slot.material.name if slot.material else None]
                                     for slot in obj.material_slots]}
        if obj.type == "CAMERA":
            record["camera"] = properties(obj.data, "type lens ortho_scale clip_start clip_end shift_x shift_y "
                                                    "sensor_fit sensor_width sensor_height")
        if obj.type == "LIGHT":
            record["light"] = properties(obj.data, "type energy color angle shape size size_y "
                                                   "shadow_soft_size spot_size spot_blend")
        objects[obj.name] = record
    return {"scene": scene.name, "objects": objects,
            "collections": {c.name: {"children": sorted(child.name for child in c.children),
                                      "render_hidden": c.hide_render}
                            for c in (scene.collection, *bpy.data.collections)},
            "active_camera": scene.camera.name if scene.camera else None,
            "render": properties(scene.render, "engine resolution_x resolution_y resolution_percentage "
                                               "pixel_aspect_x pixel_aspect_y film_transparent"),
            "cycles": properties(scene.cycles, "samples seed device use_adaptive_sampling use_denoising"),
            "eevee": properties(scene.eevee, "taa_render_samples") if hasattr(scene, "eevee") else {},
            "view": properties(scene.view_settings, "view_transform look exposure gamma"),
            "display": properties(scene.display_settings, "display_device"),
            "compositor": graph(getattr(scene, "node_tree", None)),
            "world": {"name": scene.world.name, "color": scene.world.color,
                      "graph": graph(scene.world.node_tree)} if scene.world else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--input-ref", required=True)
    parser.add_argument("--allow-other-version", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = Path(bpy.data.filepath).resolve()
    if sha(source) != args.source_sha:
        raise ValueError("Source SHA-256 mismatch")
    if bpy.app.version != (5, 3, 0) and not args.allow_other_version:
        raise ValueError("Blender 5.3.0 required")
    out = args.output.resolve()
    if out in source.parents or out == source:
        raise ValueError("Output would overlap source")
    out.mkdir(parents=True)
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    exported = {}
    for obj in sorted(scene.objects, key=lambda item: item.name):
        if obj.type != "MESH":
            continue
        evaluated = obj.evaluated_get(dg)
        evaluated_mesh = evaluated.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
        try:
            groups = [group.name for group in obj.vertex_groups]
            exported[obj.name] = {"base": mesh_record(obj.data, obj.matrix_world, groups),
                                  "evaluated": mesh_record(evaluated_mesh, evaluated.matrix_world, groups)}
        finally:
            evaluated.to_mesh_clear()

    scene_data = scene_record(scene)
    material_data = materials()
    write(out / "mesh.json", {"indexing": "zero-based Blender indices", "objects": exported})
    write(out / "scene.json", scene_data)
    write(out / "materials.json", material_data)
    landmarks = write_views(out / "views", exported, scene_data)
    write(out / "landmarks.json", landmarks)
    # Copy native IDs and packed resources without resaving the source.
    shutil.copyfile(source, out / "master.blend")
    if sha(out / "master.blend") != args.source_sha or sha(source) != args.source_sha:
        raise ValueError("Master/source copy check failed")
    write(out / "qa.json", {"G1": "BLOCKED", "G2": "FAIL", "G3": "NOT_RUN", "G4": "NOT_RUN",
                            "source_integrity": "PASS", "round_trip": "NOT_RUN",
                            "fixed_camera_pixels": "NOT_RUN", "rerun": "NOT_RUN",
                            "geometry_tolerance_blender_units": TOLERANCE,
                            "uv_island_texel_density": "NOT_RUN",
                            "canonical_comparison": "BLOCKED"})
    write(out / "manifest.json", {
        "candidate": "UNAPPROVED", "measurement_scope": "candidate geometry, provisional scale",
        "axes": "+X along coast; -Y seaward; +Z up", "decimal_places": DECIMALS,
        "blender": bpy.app.version_string, "production_runtime": bpy.app.version == (5, 3, 0),
        "source_name": source.name, "source_sha256": args.source_sha, "input_ref": args.input_ref,
        "dependencies": material_data["images"],
        "outputs": {p.relative_to(out).as_posix(): sha(p) for p in sorted(out.rglob("*"))
                    if p.is_file() and p.name != "qa.json"}})


if __name__ == "__main__":
    main()
