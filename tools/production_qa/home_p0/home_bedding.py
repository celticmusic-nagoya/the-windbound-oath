"""Blender 5.3.0 isolated HOME bedding edit and native checkpoint QA."""
import hashlib
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector


SOURCE = "dff3a32df533c8786f3122e07cf681c18f4805bd913d750f04ce15b321b10fed"
BED_SHA = "a50de6986a171065971b4a51d1aec26cdc417565397742029691ca299346646d"
ARCH_SHA = "8e869c56a2684f4a0fdb9f7eda304ac8ecee5c100768add979fdba02fae5ef63"
HOST = "GEO_AIDANHOUSE_INT_SOFT"
TARGET = "LIND-HOME_BEDDING_BLANKET_P0"
OLD = set(range(142, 312))
MATERIAL = "LIND_HOME_P0_WOOL"
TOLERANCE = 0.00001


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def record_mesh(exclude_old):
    """Fingerprint protected mesh geometry, UVs, materials and object transforms."""
    state = hashlib.sha256()
    for obj in sorted(bpy.context.scene.objects, key=lambda item: item.name):
        if obj.name == TARGET:
            continue
        state.update(repr((obj.name, obj.matrix_world[:])).encode())
        if obj.type != "MESH":
            continue
        mesh = obj.data
        state.update(repr([slot.name for slot in obj.material_slots]).encode())
        uv = mesh.uv_layers.active
        faces = []
        for poly in mesh.polygons:
            if obj.name == HOST and exclude_old and set(poly.vertices) <= OLD:
                assert mesh.materials[poly.material_index].name == "MAT_FABRIC_WOOL_GREEN_A"
                continue
            corners = tuple((tuple(mesh.vertices[i].co), tuple(uv.data[j].uv) if uv else ())
                            for i, j in zip(poly.vertices, poly.loop_indices))
            canonical = min(corners[i:] + corners[:i] for i in range(len(corners)))
            faces.append((canonical, poly.material_index, poly.use_smooth))
        state.update(repr(sorted(faces)).encode())
    return state.hexdigest()


def replace_blanket(target):
    source = bpy.data.objects[HOST]
    old_x = [(source.matrix_world @ source.data.vertices[i].co).x for i in OLD]
    old_min, old_max = min(old_x), max(old_x)
    mesh = bmesh.new()
    mesh.from_mesh(source.data)
    matching = [face for face in mesh.faces if {v.index for v in face.verts} <= OLD]
    assert {v.index for face in matching for v in face.verts} == OLD
    bmesh.ops.delete(mesh, geom=matching, context="FACES_ONLY")
    mesh.to_mesh(source.data)
    mesh.free()
    source.data.update()

    rows, columns = target["grid"]
    x0, x1 = target["top_x"]
    thickness = target["thickness"]
    vertices, uvs = [], []
    for row in range(rows):
        u = row / (rows - 1)
        x = old_min + (old_max - old_min) * u
        for column in range(columns):
            v = 2 * column / (columns - 1) - 1
            y = 0.548 * v
            edge = max(0, (abs(y) - 0.459) / (0.548 - 0.459))
            fold = sum(amp * math.exp(-((u - center - slope * v) / width) ** 2)
                       for center, slope, width, amp in
                       ((.18, .23, .055, .025), (.46, -.31, .085, .019), (.78, .19, .045, .034)))
            z = .865 + fold - .185 * edge ** 1.6
            vertices.append((x, 2.2 + y, z))
            uvs.append(((x1 - x0) * u, y + 0.548))
    faces = [(r * columns + c, (r + 1) * columns + c,
              (r + 1) * columns + c + 1, r * columns + c + 1)
             for r in range(rows - 1) for c in range(columns - 1)]
    data = bpy.data.meshes.new(TARGET)
    data.from_pydata(vertices, [], faces)
    assert not data.validate()
    obj = bpy.data.objects.new(TARGET, data)
    source.users_collection[0].objects.link(obj)
    uv = data.uv_layers.new(name="Metric")
    for poly in data.polygons:
        poly.use_smooth = True
        for i in poly.loop_indices:
            uv.data[i].uv = uvs[data.loops[i].vertex_index]
    obj["source_endpoint_residual_m"] = [old_min + 3.93 - x0, old_max + 3.93 - x1]
    for vert in data.vertices:
        vert.co.x = -3.93 + x0 + (vert.co.x - old_min) / (old_max - old_min) * (x1 - x0)
    modifier = obj.modifiers.new("Wool thickness", "SOLIDIFY")
    modifier.thickness = thickness
    modifier.offset = -1
    material = bpy.data.materials["MAT_FABRIC_WOOL_GREEN_A"].copy()
    material.name = MATERIAL
    material.use_nodes = True
    shader = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    shader.inputs["Roughness"].default_value = .82
    data.materials.append(material)
    return obj


def measure(obj, target):
    data = obj.data
    expected = target["top_x"]
    x_range = [min(v.co.x for v in data.vertices) + 3.93,
               max(v.co.x for v in data.vertices) + 3.93]
    residuals = [a - b for a, b in zip(x_range, expected)]
    thickness = obj.modifiers["Wool thickness"].thickness
    assert max(map(abs, residuals)) <= TOLERANCE
    assert abs(thickness - target["thickness"]) <= TOLERANCE
    hem = min(v.co.z for v in data.vertices) - .25 - thickness
    overhang = max(abs(v.co.y - 2.2) for v in data.vertices) - .51
    assert hem >= target["hem_z_min"]
    assert overhang <= target["side_overhang_max"]
    clearance = min(v.co.z for v in data.vertices if abs(v.co.y - 2.2) <= .44) - thickness - .85
    assert clearance >= 0
    return dict(source_endpoint_residual_m=list(obj["source_endpoint_residual_m"]),
                residual_m=residuals, thickness_m=thickness, hem_above_ffl_m=hem,
                overhang_m=overhang, conservative_mattress_clearance_m=clearance,
                vertices=len(data.vertices), quads=len(data.polygons))


def render_preview(path):
    scene = bpy.context.scene
    # Evidence setup is temporary and never saved into the native candidate.
    for obj in scene.objects:
        obj.hide_render = obj.name not in (HOST, TARGET)
    camera = bpy.data.objects.new("P0 evidence camera", bpy.data.cameras.new("P0 evidence camera"))
    scene.collection.objects.link(camera)
    camera.location = (-1.45, .72, 2.25)
    camera.rotation_euler = (Vector((-2.93, 2.2, .72)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    lamp = bpy.data.objects.new("P0 evidence light", bpy.data.lights.new("P0 evidence light", "AREA"))
    scene.collection.objects.link(lamp)
    lamp.location = (-2.2, 1.35, 3.1)
    lamp.rotation_euler = (Vector((-2.93, 2.2, .72)) - lamp.location).to_track_quat("-Z", "Y").to_euler()
    lamp.data.energy = 420
    lamp.data.shape = "DISK"
    lamp.data.size = 2.5
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 12
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    assert path.stat().st_size > 1000


def main():
    mode, source_path, bed, architecture, output, expected = sys.argv[sys.argv.index("--") + 1:]
    source, bed, architecture, output = map(Path, (source_path, bed, architecture, output))
    assert bpy.app.version == (5, 3, 0)
    assert sha(bed) == BED_SHA and sha(architecture) == ARCH_SHA
    assert sha(source) == expected
    output.mkdir(parents=True, exist_ok=True)
    target = json.loads(bed.read_text())["target"]["blanket"]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    if mode == "interrupt":
        measure(bpy.data.objects[TARGET], target)
        raise RuntimeError("P0_INTENTIONAL_INTERRUPTION_BEFORE_WRITE")
    if mode == "create":
        assert expected == SOURCE
        protected = record_mesh(True)
        replace_blanket(target)
    else:
        previous = json.loads((source.parent / "qa.json").read_text())
        protected = previous["protected_sha256"]
        assert record_mesh(False) == protected
        obj = bpy.data.objects[TARGET]
        measure(obj, target)
        shader = next(node for node in obj.data.materials[0].node_tree.nodes
                      if node.type == "BSDF_PRINCIPLED")
        assert abs(shader.inputs["Roughness"].default_value - .82) < TOLERANCE
        shader.inputs["Sheen Weight"].default_value = .18
    assert record_mesh(False) == protected
    result = measure(bpy.data.objects[TARGET], target)
    native = output / "home-p0.blend"
    assert not native.exists()
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    bpy.ops.wm.open_mainfile(filepath=str(native))
    assert record_mesh(False) == protected
    assert measure(bpy.data.objects[TARGET], target) == result
    render_preview(output / "preview.png")
    (output / "qa.json").write_text(json.dumps(dict(
        target_id=TARGET, source_sha256=expected, native_sha256=sha(native),
        blueprint_sha256=BED_SHA, architecture_sha256=ARCH_SHA,
        protected_sha256=protected, mode=mode, tolerance_m=TOLERANCE,
        measurement=result, reopened=True, independent_art_qa="NOT_RUN"), indent=2))


main()
