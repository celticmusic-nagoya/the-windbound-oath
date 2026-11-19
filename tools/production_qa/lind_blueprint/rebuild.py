"""Reconstruct mesh cages from JSON while retaining the native shading template."""
import argparse
from array import array
import json
from pathlib import Path
import sys

import bpy
from mathutils import Matrix

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_blueprint import clean, materials, mesh_record, scene_record, sha, TOLERANCE, write


def flatten(rows):
    return [value for row in rows for value in row]


def read(path):
    record = json.loads(path.read_text())
    if record.pop("schema_version") != 1:
        raise ValueError(f"Unsupported schema: {path}")
    return record


def make_mesh(original, data):
    if original.has_custom_normals:
        # Blender's split-normal encoding depends on the original corner frames.
        # Re-encoding decoded vectors loses precision along the authored tile seam.
        if ([list(edge.vertices) for edge in original.edges] != data["edges"]
                or [[loop.vertex_index, loop.edge_index] for loop in original.loops] != data["loops"]
                or [list(face.vertices) for face in original.polygons] != [f["vertices"] for f in data["faces"]]):
            raise ValueError(f"Encoded custom normals require unchanged topology on {original.name}")
        mesh = original.copy()
    else:
        mesh = bpy.data.meshes.new(original.name + " | Blueprint")
        mesh.vertices.add(len(data["xyz_local"]))
        mesh.edges.add(len(data["edges"]))
        mesh.edges.foreach_set("vertices", flatten(data["edges"]))
        mesh.loops.add(len(data["loops"]))
        mesh.loops.foreach_set("vertex_index", [loop[0] for loop in data["loops"]])
        mesh.loops.foreach_set("edge_index", [loop[1] for loop in data["loops"]])
        mesh.polygons.add(len(data["faces"]))
        mesh.polygons.foreach_set("loop_start", [face["loops"][0] for face in data["faces"]])
        for mat in data["slots"]:
            mesh.materials.append(bpy.data.materials[mat] if mat else None)
    mesh.vertices.foreach_set("co", flatten(data["xyz_local"]))

    for face, record in zip(mesh.polygons, data["faces"]):
        face.material_index = record["material_slot"]
        face.use_smooth = record["smooth"]
    for i in data["seams"]:
        mesh.edges[i].use_seam = True
    for i in data["sharp_edges"]:
        mesh.edges[i].use_edge_sharp = True
    for name, coords in data["uv"].items():
        layer = mesh.uv_layers.get(name) or mesh.uv_layers.new(name=name, do_init=False)
        layer.uv.foreach_set("vector", flatten(coords))
        if name == data["active_uv"]:
            mesh.uv_layers.active = layer
        if name in data["render_uv"]:
            layer.active_render = True
    mesh.update()
    return mesh


def max_delta(left, right):
    if len(left) != len(right):
        return None
    return max((abs(a-b) for a,b in zip(left,right)), default=0.0)


def render(scene, path):
    scene.camera = scene.objects.get("cg_review") or scene.camera
    if scene.camera is None:
        raise ValueError("Fixed camera missing")
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 65
    scene.render.image_settings.file_format = "PNG"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def pixels(path):
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        values = array("f", [0.0]) * len(image.pixels)
        image.pixels.foreach_get(values)
        return image.size[:], values
    finally:
        bpy.data.images.remove(image)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("blueprint", type=Path)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--determinism-verified", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    root = args.blueprint.resolve()
    manifest = read(root / "manifest.json")
    out = root / "verification"
    out.mkdir(exist_ok=True)
    for name, digest in manifest["outputs"].items():
        if sha(root / name) != digest:
            raise ValueError(f"Manifest mismatch: {name}")
    bpy.ops.wm.open_mainfile(filepath=str(root / "master.blend"))
    scene = bpy.context.scene
    mesh_data = read(root / "mesh.json")["objects"]
    scene_data = read(root / "scene.json")
    material_data = read(root / "materials.json")
    baseline = out / "source.png"
    before = scene_record(scene)
    if args.render:
        render(scene, baseline)
    replacements = {}
    for name, mesh in mesh_data.items():
        obj = scene.objects[name]
        data = mesh["base"]
        replacement = replacements.get(obj.data.name)
        if replacement is None:
            replacement = make_mesh(obj.data, data)
            replacements[obj.data.name] = replacement
        obj.data = replacement
        for slot, (link, mat) in zip(obj.material_slots, scene_data["objects"][name]["material_slots"]):
            slot.link = link
            slot.material = bpy.data.materials.get(mat) if mat else None
        for group_index, group in enumerate(obj.vertex_groups):
            for index, weights in enumerate(data["weights"]):
                for stored_index, weight in weights:
                    if group_index == stored_index:
                        group.add([index], weight, "REPLACE")

    for name, data in scene_data["objects"].items():
        obj = scene.objects[name]
        if clean(obj.matrix_parent_inverse) != data["parent_inverse"]:
            obj.matrix_parent_inverse = Matrix(data["parent_inverse"])
        if clean(obj.matrix_basis) != data["basis_matrix"]:
            obj.matrix_basis = Matrix(data["basis_matrix"])
        for key in ("camera", "light"):
            for prop, value in data.get(key, {}).items():
                if clean(getattr(obj.data, prop)) != value:
                    setattr(obj.data, prop, value)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    checks = {}
    failures = []
    for name, expected in mesh_data.items():
        obj = scene.objects[name]
        evaluation = obj.evaluated_get(dg)
        emesh = evaluation.to_mesh(preserve_all_data_layers=True, depsgraph=dg)
        try:
            pairs = {
                "base": mesh_record(obj.data, obj.matrix_world),
                "evaluated": mesh_record(emesh, evaluation.matrix_world),
            }
            for kind, actual in pairs.items():
                reference = expected[kind]
                key = f"{name}/{kind}"
                coord = max_delta(flatten(actual["xyz_local"]), flatten(reference["xyz_local"]))
                world = max_delta(flatten(actual["xyz_world"]), flatten(reference["xyz_world"]))
                uv = [max_delta(flatten(actual["uv"][layer]), flatten(reference["uv"][layer]))
                      for layer in sorted(set(actual["uv"]) & set(reference["uv"]))]
                topology = all(actual[k] == reference[k] for k in ("edges", "loops", "seams", "sharp_edges"))
                faces = lambda d: [[f[k] for k in ("vertices", "loops", "smooth", "material_slot")] for f in d["faces"]]
                assignments = actual["slots"] == reference["slots"]
                winding = faces(actual) == faces(reference)
                normals = max_delta(flatten(actual["corner_normals"]), flatten(reference["corner_normals"]))
                uv_match = (actual["uv"].keys() == reference["uv"].keys()
                            and all(d is not None and d <= TOLERANCE for d in uv))
                passed = (topology and winding and assignments and uv_match
                          and all(d is not None and d <= TOLERANCE for d in (coord, world, normals)))
                checks[key] = {"vertices": len(actual["xyz_local"]), "edges": len(actual["edges"]),
                               "faces": len(actual["faces"]), "loops": len(actual["loops"]),
                               "max_local_xyz_delta": coord, "max_world_xyz_delta": world,
                               "max_uv_delta": max((d for d in uv if d is not None), default=None),
                               "max_corner_normal_delta": normals, "edges_loops_seams_match": topology,
                               "face_winding_slots_smooth_match": winding, "material_slots_match": assignments,
                               "uv_match": uv_match, "status": "PASS" if passed else "FAIL"}
                if not passed:
                    failures.append(key)
        finally:
            evaluation.to_mesh_clear()

    after = scene_record(scene)
    scene_fail = []
    for name, obj in after["objects"].items():
        reference = scene_data["objects"][name]
        for matrix in ("local_matrix", "world_matrix"):
            delta = max_delta(flatten(obj[matrix]), flatten(reference[matrix]))
            if delta is None or delta > TOLERANCE:
                scene_fail.append([name, matrix, delta])
        for key in ("camera", "light", "material_slots"):
            if clean(obj.get(key)) != reference.get(key):
                scene_fail.append([name, key])
    for key in ("active_camera", "render", "cycles", "eevee", "view", "display", "world", "compositor"):
        if clean(before[key]) != scene_data[key]:
            scene_fail.append([key])
    actual_materials = clean(materials())
    for expected, actual in zip(material_data["images"], actual_materials["images"]):
        if expected["name"] == actual["name"]:
            expected.pop("provenance_by_sha")
            actual.pop("provenance_by_sha")
            expected.pop("license")
            actual.pop("license")
    material_match = actual_materials == material_data
    if not material_match or scene_fail:
        failures.append("scene/materials")
    pixel = {"status": "NOT_RUN"}
    if args.render:
        rebuilt = out / "rebuilt.png"
        render(scene, rebuilt)
        size_a, a = pixels(baseline)
        size_b, b = pixels(rebuilt)
        delta = max_delta(a, b) if size_a == size_b else None
        threshold = 1 / 255
        pixel = {"status": "PASS" if delta is not None and delta <= threshold else "FAIL",
                 "camera": scene.camera.name, "engine": scene.render.engine,
                 "resolution_percentage": 65, "size": size_a, "max_decoded_channel_delta": delta,
                 "max_channel_tolerance": threshold}
        if pixel["status"] != "PASS":
            failures.append("fixed_camera_pixels")
    qa = read(root / "qa.json")
    qa.update({"round_trip": "FAIL" if failures else "PASS", "G3": "FAIL" if failures else "BLOCKED",
               "fixed_camera_pixels": pixel, "mesh_checks": checks,
               "rerun": "PASS" if args.determinism_verified else "NOT_RUN", "scene_differences": scene_fail,
               "native_material_graph_match": material_match, "failures": failures,
               "limitations": ["uses native scene template for materials, modifiers and render settings",
                               "encoded custom normals retain native topology and frames",
                               "general custom attribute payloads unavailable from JSON",
                               "full-scene intersection and texel density coverage pending"]})
    write(root / "qa.json", qa)
    for kind in ("base", "evaluated"):
        subset = [row for name, row in checks.items() if name.endswith(f"/{kind}")]
        print("BLUEPRINT_MESH", kind, json.dumps({
            "counts": {key: sum(row[key] for row in subset) for key in ("vertices", "edges", "faces", "loops")},
            "max_deltas": {key: max((row[key] for row in subset if row[key] is not None), default=None)
                           for key in ("max_local_xyz_delta", "max_world_xyz_delta", "max_uv_delta",
                                       "max_corner_normal_delta")},
        }, sort_keys=True), flush=True)
    print("BLUEPRINT_ROUND_TRIP", json.dumps({"source_sha256": manifest["source_sha256"],
              "determinism": qa["rerun"], "mesh_checks": len(checks), "round_trip": qa["round_trip"],
              "pixels": pixel, "material_match": material_match, "scene_differences": scene_fail,
              "failures": failures}, sort_keys=True), flush=True)
    if failures:
        raise RuntimeError(f"Round-trip failures: {failures}")


if __name__ == "__main__":
    main()
