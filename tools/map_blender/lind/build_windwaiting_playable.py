"""Build the local exploration candidate from pinned, read-only inputs."""
import csv
import hashlib
import json
import math
import os
import random
import struct
import sys
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.noise import noise

ROOT = Path(__file__).resolve().parents[3]
C13 = ROOT / "assets/candidates/lind/windwaiting-cliff-c13"
CG = ROOT / "assets/approved/game/cliff/sunset_background.png"
CARRIER = "Cliff C8 B | joinable coastal segment"
ROAD_SOURCE = "Village_to_coastal_promontory"
GROUND = "Coastal footpath"
SUN = Vector((0.63, -0.77, 0.15)).normalized()
INPUT_SHA = {
    "E": "6ee2e96c69e2b510a344411a6b9ea90a6227c8095c4509bac74f723e233eaf6d",
    "left": "a7ffb05a4a95b197befc92cf9a2f3abdd4062c618c83c8ef0e24e1e0ec8377db",
    "right": "d42dcc399a39d3e7c0936af79ac2e8de631eaeb784782a6785a918e60fe2a16c",
    "rock": "551c083899a29b68110dac18ff2ea0ee93164453778c6c580aa1931b235a090d",
    "eco": "40e8f29a613dc99f5b47e2595a0830f04e321dd56c5d722c7817854d995b09cd",
    "route": "99f83e08faf8b7661049cb3c195f9ad85b821af6b5b07f54b3886a9dd2e22443",
    "CG": "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07",
}
GEOMETRY_E = "e226cb7a007a33da76541298af582a996ed12bbba84534a79a8f094397f893c3"
GEOMETRY_D4 = "ec2af2d59f922157de5a6f336c5c99208102e648a67b140a2f8eb994c42e0274"


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def geometry_sha(mesh):
    digest = hashlib.sha256()
    for v in mesh.vertices:
        digest.update(struct.pack("<3f", *v.co))
    for face in mesh.polygons:
        digest.update(struct.pack(f"<{len(face.vertices)}i", *face.vertices))
    return digest.hexdigest()


def append(path, names):
    with bpy.data.libraries.load(str(path), link=False) as (source, target):
        assert set(names) <= set(source.objects), (path, names)
        target.objects = list(names)
    return target.objects


def face_index(mesh):
    points = [tuple(round(a, 6) for a in v.co) for v in mesh.vertices]
    result = {tuple(sorted(points[v] for v in f.vertices)): f for f in mesh.polygons}
    assert len(result) == len(mesh.polygons), mesh.name
    return result


def patch_carrier(carrier, base, patches):
    source = carrier.data
    assert geometry_sha(source) == GEOMETRY_E
    assert geometry_sha(base.data) == GEOMETRY_D4
    original = face_index(base.data)
    keep = face_index(source)
    overlay = []
    counts = {}
    for label, patch in patches:
        revised = face_index(patch.data)
        csv_path = C13 / {"left": "LEFT_SHORE-vertex-map.csv", "right": "RIGHT_FAULT-vertex-map.csv"}[label]
        with csv_path.open() as rows:
            matches = list(csv.DictReader(rows))
        old_vertices = {int(row["d4_vertex_id"]) for row in matches}
        new_vertices = {int(row["c12_vertex_id"]) for row in matches}
        for row in matches:
            if row["boundary"] == "1":
                old = base.data.vertices[int(row["d4_vertex_id"])].co
                new = patch.data.vertices[int(row["c12_vertex_id"])].co
                assert (old - new).length <= 1e-6, (label, row)
        removed = {key for key, f in original.items() if set(f.vertices) <= old_vertices}
        added = {key for key, f in revised.items() if set(f.vertices) <= new_vertices}
        print("C12 scoped faces", label, len(removed), len(added), flush=True)
        assert removed and added and removed <= keep.keys(), label
        for face_key in removed:
            del keep[face_key]
        overlay.extend((patch.data, f) for key, f in revised.items() if key in added)
        counts[label] = {"removed": len(removed), "added": len(added)}
    vertices, polygons, normals, uvs, styles = [], [], [], [], []
    ids = {}
    for mesh, face in [(source, f) for f in keep.values()] + overlay:
        polygon = []
        for loop_id in face.loop_indices:
            loop = mesh.loops[loop_id]
            co = tuple(mesh.vertices[loop.vertex_index].co)
            key = tuple(round(a, 6) for a in co)
            if key not in ids:
                ids[key] = len(vertices)
                vertices.append(co)
            polygon.append(ids[key])
            normals.append(tuple(mesh.corner_normals[loop_id].vector))
            uvs.append(tuple(mesh.uv_layers.active.uv[loop_id].vector))
        polygons.append(polygon)
        styles.append((face.material_index, face.use_smooth))
    mesh = bpy.data.meshes.new("E with C12 face deltas")
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    for mat in source.materials:
        mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name=source.uv_layers.active.name)
    uv.uv.foreach_set("vector", [coordinate for point in uvs for coordinate in point])
    for f, (index, smooth) in zip(mesh.polygons, styles, strict=True):
        f.material_index = index
        f.use_smooth = smooth
    mesh.normals_split_custom_set(normals)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    topology = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "boundary": sum(e.is_boundary for e in bm.edges),
        "nonmanifold": sum(not e.is_manifold for e in bm.edges),
        "winding": sum(not e.is_contiguous for e in bm.edges),
        "degenerate": sum(f.calc_area() < 1e-10 for f in bm.faces),
    }
    bm.free()
    assert all(topology[k] == 0 for k in ("boundary", "nonmanifold", "winding", "degenerate")), topology
    mesh.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    tree = BVHTree.FromPolygons([v.co for v in mesh.vertices], triangles, all_triangles=True)
    contacts = sum(a < b and not set(triangles[a]).intersection(triangles[b]) for a, b in tree.overlap(tree))
    assert contacts == 0, contacts
    topology["nonadjacent_triangle_intersections"] = contacts
    carrier.data = mesh
    return {"deltas": counts, "topology": topology, "carrier_sha256": geometry_sha(mesh)}


def tree_for(obj):
    bpy.context.view_layer.update()
    return BVHTree.FromObject(obj, bpy.context.evaluated_depsgraph_get())


def hit(tree, x, y):
    return tree.ray_cast(Vector((x, y, 18)), Vector((0, 0, -1)))[:2]


def simple_material(name, color, roughness=0.86):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    pbr = mat.node_tree.nodes.get("Principled BSDF")
    pbr.inputs["Base Color"].default_value = (*color, 1)
    pbr.inputs["Roughness"].default_value = roughness
    return mat, pbr


def collection(name):
    group = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(group)
    return group


def place_route(source, terrain, group):
    mesh = source.data.copy()
    along = Vector((-0.76, 0.65)).normalized()
    across = Vector((-along.y, along.x))
    raw = [(v.co.xy.dot(along), v.co.xy.dot(across)) for v in mesh.vertices]
    lo, hi = min(t for t, _ in raw), max(t for t, _ in raw)
    start, end = Vector((8.0, 17.25)), Vector((-5.2, 2.8))
    run = end - start
    width_axis = Vector((-run.y, run.x)).normalized()
    center = sum(side for _, side in raw) / len(raw)
    for vertex, (t, side) in zip(mesh.vertices, raw, strict=True):
        point = start + run * ((t - lo) / (hi - lo)) + width_axis * (side - center) * 0.83
        vertex.co = (*point, 0)
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=3, use_grid_fill=True)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    contact = []
    for vertex in mesh.vertices:
        p, n = hit(terrain, *vertex.co.xy)
        assert p is not None and n.z > 0.75 and p.z > 4.5, (vertex.co[:], p, n)
        vertex.co.z = p.z + 0.028
    if sum(f.normal.z for f in mesh.polygons) < 0:
        for f in mesh.polygons:
            f.flip()
    mesh.update()
    color = mesh.color_attributes.new(name="Route tone", type="FLOAT_COLOR", domain="POINT")
    for v, c in zip(mesh.vertices, color.data):
        tone = max(0.63, min(1.28, 0.95 + noise(v.co * 9) * 0.26 + noise(v.co * 1.5) * 0.16))
        c.color = (0.31 * tone, 0.22 * tone, 0.105 * tone, 1)
    mat, pbr = simple_material("Weathered ochre footpath", (0.3, 0.21, 0.10))
    rgb = mat.node_tree.nodes.new("ShaderNodeVertexColor")
    rgb.layer_name = color.name
    mat.node_tree.links.new(rgb.outputs["Color"], pbr.inputs["Base Color"])
    mesh.materials.clear()
    mesh.materials.append(mat)
    obj = bpy.data.objects.new(GROUND, mesh)
    group.objects.link(obj)
    for f in mesh.polygons:
        p, _ = hit(terrain, *f.center.xy)
        contact.append(f.center.z - p.z)
    assert min(contact) > 0 and max(contact) < 0.11, (min(contact), max(contact))
    return obj, start, end, {"source_object": source.name, "start_xy": list(start), "end_xy": list(end),
                             "terrain_gap_face_centers_bu": [min(contact), max(contact)], "samples": len(contact)}


def bridge_distance(x, y, start, end):
    offset = Vector((x, y)) - start
    span = end - start
    return (offset - span * min(1, max(0, offset.dot(span) / span.length_squared))).length


def add_vegetation(path, terrain, start, end):
    names = ["eco_tree_deciduous_a", "eco_grass_card_lod1", "eco_grass_tuft_short",
             "eco_flower_patch", "eco_rocks_coastal"]
    group = collection("ECO | tree, grass, flowers and moss")
    prototypes = dict(zip(names, append(path, names)))
    rng = random.Random(421)
    placements = []
    exclusions = []
    moss, pbr = simple_material("Moss over loose coastal stones", (0.105, 0.155, 0.033))
    knots = moss.node_tree.nodes
    links = moss.node_tree.links
    tex = knots.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 9
    ramp = knots.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.035, 0.045, 0.021, 1)
    ramp.color_ramp.elements[1].color = (0.23, 0.33, 0.06, 1)
    links.new(tex.outputs["Fac"], ramp.inputs[0])
    links.new(ramp.outputs["Color"], pbr.inputs["Base Color"])
    prototypes[names[-1]].data.materials.clear()
    prototypes[names[-1]].data.materials.append(moss)
    for name in (names[2], names[3], names[4]):
        proto = prototypes[name]
        group.objects.link(proto)
        bpy.context.view_layer.objects.active = proto
        for modifier in list(proto.modifiers):
            proto.modifiers.remove(modifier)
        decimate = proto.modifiers.new("Trial meadow geometry budget", "DECIMATE")
        decimate.ratio = {names[2]: 0.32, names[3]: 0.135, names[4]: 0.24}[name]
        bpy.ops.object.modifier_apply(modifier=decimate.name)
        group.objects.unlink(proto)

    def plant(name, x, y, scale, radius):
        if bridge_distance(x, y, start, end) < 1.5 + radius:
            return False
        p, _ = hit(terrain, x, y)
        if p is None or p.z < 4.9:
            return False
        footprint = max(radius, 0.32)
        for dx, dy in [(0, 0), (-footprint, 0), (footprint, 0), (0, -footprint), (0, footprint)]:
            q, normal = hit(terrain, x + dx, y + dy)
            if q is None or normal.z < 0.84 or abs(q.z - p.z) > 0.23:
                return False
        obj = bpy.data.objects.new(name, prototypes[name].data)
        group.objects.link(obj)
        obj.location = (x, y, p.z - (0.025 if radius > 0.4 else 0.008))
        obj.rotation_euler.z = rng.uniform(0, math.tau)
        obj.scale = (scale, scale, scale)
        placements.append({"name": obj.name, "xy": [x, y], "height": p.z,
                           "planting_depth": p.z - obj.location.z, "radius": radius})
        if radius > 0:
            exclusions.append((x, y, radius))
        return True

    for x, y, scale in [(-8.5, 7.2, 1.0), (-13, 9, 0.86), (-12, 20, 0.93), (11, 15, 0.72), (17, 24, 0.90)]:
        plant(names[0], x, y, scale, 0.64 * scale)
    for name, target, scale, radius in [(names[1], 145, 0.82, 0), (names[2], 46, 1.05, 0),
                                        (names[3], 21, 0.46, 0), (names[4], 10, 0.24, 0.53)]:
        placed = 0
        for attempt in range(target * 16):
            x = rng.uniform(-14, 12)
            y = rng.uniform(1.3, 19)
            if name in (names[1], names[3]) and attempt < target:
                x, y = rng.uniform(-13, -7), rng.uniform(2.0, 7.4)
            if any(math.hypot(x - bx, y - by) < br + radius + 0.3 for bx, by, br in exclusions):
                continue
            placed += plant(name, x, y, scale * rng.uniform(0.77, 1.25), radius)
            if placed == target:
                break
        assert placed == target, (name, placed)
    return placements, exclusions


def nav_data(terrain, route, start, end, exclusions):
    stride = 0.24
    max_step = 0.24
    # Runtime converts a Blender (X, Y, Z) point to glTF (X, Z, -Y).
    ox, oz = -14.4, -23.04
    width, height = 123, 109
    route_tree = tree_for(route)
    levels = [None] * (width * height)
    terrain_rejected = obstacles_rejected = 0
    offset = 0.56
    for row in range(height):
        for col in range(width):
            x, y = ox + col * stride, -(oz + row * stride)
            if any(math.hypot(x - bx, y - by) <= br + 0.29 for bx, by, br in exclusions):
                obstacles_rejected += 1
                continue
            p, n = hit(terrain, x, y)
            if p is None or p.z < 4.8 or n.z < 0.83:
                terrain_rejected += 1
                continue
            good = True
            for dx, dy in [(-offset, 0), (offset, 0), (0, -offset), (0, offset),
                           (-0.40, -0.40), (-0.40, 0.40), (0.40, -0.40), (0.40, 0.40)]:
                q, normal = hit(terrain, x + dx, y + dy)
                if q is None or normal.z < 0.77 or abs(q.z - p.z) > 0.31:
                    good = False
                    break
            if good:
                on_road, _ = hit(route_tree, x, y)
                levels[row * width + col] = round(max(p.z, on_road.z if on_road else p.z), 5)
            else:
                terrain_rejected += 1

    def grid_id(p):
        return round((-p.y - oz) / stride) * width + round((p.x - ox) / stride)

    spawn, overlook = grid_id(start.lerp(end, 0.12)), grid_id(end)
    assert levels[spawn] is not None and levels[overlook] is not None
    connected = {spawn}
    queue = deque([spawn])
    while queue:
        cell = queue.popleft()
        for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            col, row = cell % width + dc, cell // width + dr
            candidate = row * width + col
            if not (0 <= col < width and 0 <= row < height) or candidate in connected:
                continue
            if levels[candidate] is None or abs(levels[candidate] - levels[cell]) > max_step:
                continue
            queue.append(candidate)
            connected.add(candidate)
    assert overlook in connected and len(connected) > 1000
    to_point = lambda i: [round(ox + i % width * stride, 4), levels[i], round(oz + i // width * stride, 4)]
    return {
        "origin": [ox, oz], "stride": stride, "width": width, "height": height,
        "maxStep": max_step, "levels": [v if i in connected else None for i, v in enumerate(levels)],
        "spawn": to_point(spawn), "overlook": to_point(overlook), "rayTop": 18,
        "ground": [CARRIER, GROUND], "cameraBlockers": ["C10 large rock 03", "C10 large rock 04"],
        "obstacles": [[x, -y, r + 0.29] for x, y, r in exclusions],
        "cameraYaw": 2.8, "sun": [SUN.x * 40, SUN.z * 40, -SUN.y * 40],
    }, {"connected_cells": len(connected), "terrain_rejected": terrain_rejected,
        "obstacles_rejected": obstacles_rejected, "guard_probe_radius": offset}


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def compose_light(scene):
    group = collection("LIGHT | sunset composition")
    for obj in list(scene.objects):
        if obj.type == "LIGHT":
            obj.hide_render = True
    sun = bpy.data.lights.new("Low amber sunlight", "SUN")
    sun.energy = 2.65
    sun.color = (1, 0.72, 0.42)
    sun.angle = 0.065
    obj = bpy.data.objects.new(sun.name, sun)
    group.objects.link(obj)
    obj.location = SUN * 50
    look_at(obj, (0, 0, 0))

    fill = bpy.data.lights.new("Cool skylight fill", "SUN")
    fill.energy = 0.55
    fill.color = (0.58, 0.72, 1)
    fill_obj = bpy.data.objects.new(fill.name, fill)
    group.objects.link(fill_obj)
    fill_obj.location = (-10, 15, 23)
    look_at(fill_obj, (0, 0, 0))

    world = bpy.data.worlds.new("Blue-violet sky and amber horizon")
    world.use_nodes = True
    nodes, links = world.node_tree.nodes, world.node_tree.links
    bg = nodes.get("Background")
    bg.inputs["Strength"].default_value = 0.62
    direction = nodes.new("ShaderNodeTexCoord")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(direction.outputs["Normal"], sep.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    height = nodes.new("ShaderNodeMath")
    height.operation = "MULTIPLY_ADD"
    height.inputs[1].default_value = -2.65
    height.inputs[2].default_value = 0.15
    links.new(sep.outputs["Z"], height.inputs[0])
    links.new(height.outputs[0], ramp.inputs[0])
    ramp.color_ramp.elements[0].color = (0.82, 0.37, 0.16, 1)
    ramp.color_ramp.elements[1].position = 0.8
    ramp.color_ramp.elements[1].color = (0.12, 0.23, 0.51, 1)
    ramp.color_ramp.elements.new(0.29).color = (0.64, 0.38, 0.42, 1)
    clouds = nodes.new("ShaderNodeTexNoise")
    clouds.inputs["Scale"].default_value = 13
    clouds.inputs["Detail"].default_value = 4
    links.new(direction.outputs["Normal"], clouds.inputs["Vector"])
    cloud_mask = nodes.new("ShaderNodeMapRange")
    cloud_mask.inputs["From Min"].default_value = 0.50
    cloud_mask.inputs["From Max"].default_value = 0.72
    cloud_mask.inputs["To Max"].default_value = 0.32
    links.new(clouds.outputs["Fac"], cloud_mask.inputs["Value"])
    atmosphere = nodes.new("ShaderNodeMixRGB")
    atmosphere.inputs[2].default_value = (1.0, 0.40, 0.26, 1.0)
    links.new(cloud_mask.outputs["Result"], atmosphere.inputs[0])
    links.new(ramp.outputs["Color"], atmosphere.inputs[1])
    links.new(atmosphere.outputs[0], bg.inputs["Color"])
    scene.world = world

    sea = bpy.data.objects["Provisional sea at Z=0"]
    mat, pbr = simple_material("Indigo sea", (0.045, 0.124, 0.229), 0.28)
    pbr.inputs["Metallic"].default_value = 0.47
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 3.4
    coord = nodes.new("ShaderNodeTexCoord")
    stretch = nodes.new("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (0.37, 1.4, 1)
    links.new(coord.outputs["Object"], stretch.inputs[0])
    links.new(stretch.outputs["Vector"], tex.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.06
    links.new(tex.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], pbr.inputs["Normal"])
    sea.data.materials.clear()
    sea.data.materials.append(mat)

    # A distant emissive disk supplies the reference's sun and actual water reflection.
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=3.7, location=SUN * 380)
    disk = bpy.context.object
    disk.name = "Setting sun disk"
    disk.data.materials.append(simple_material("Amber sun disk", (1, 0.49, 0.13))[0])
    pbr = disk.data.materials[0].node_tree.nodes.get("Principled BSDF")
    pbr.inputs["Emission Color"].default_value = (1, 0.52, 0.12, 1)
    pbr.inputs["Emission Strength"].default_value = 18
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 18
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "AgX"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 620
    scene.render.resolution_percentage = 100
    camera_specs = [
        ("Sunset study", (-13.0, 4.6, 8.15), (10.5, -8, 5.85), 22, "sunset.png"),
        ("Route gameplay", (8.3, 21.8, 10.5), (1.5, 10.0, 5.6), 32, "gameplay.png"),
        ("Coast integration", (-14, -17, 11), (0, 1, 4.2), 36, "coast.png"),
    ]
    result = []
    for name, origin, target, lens, filename in camera_specs:
        camera = bpy.data.cameras.new(name)
        camera.lens = lens
        camera.clip_end = 850
        view = bpy.data.objects.new(name, camera)
        group.objects.link(view)
        view.location = origin
        look_at(view, target)
        result.append((view, filename, {"name": name, "origin": origin, "target": target, "lens_mm": lens}))
    scene.camera = result[0][0]
    return result


def runtime_materials(objects):
    replacements = {
        "Slate and weathered limestone": ((0.29, 0.27, 0.26), "rock_face_01_diff_1k.jpg"),
        "Damp lower bedrock": ((0.14, 0.16, 0.18), None),
        "C9 CC0 | Wet boulders and talus": ((0.27, 0.24, 0.20), "boulder_01_diff_1k.jpg"),
        "Windward olive turf": ((0.19, 0.25, 0.076), None),
        "Moss over loose coastal stones": ((0.14, 0.24, 0.044), None),
    }
    assigned = {}
    for obj in objects:
        for slot in obj.material_slots:
            old = slot.material
            if old is None or old.name not in replacements:
                continue
            if old.name not in assigned:
                color, image = replacements[old.name]
                mat, pbr = simple_material(old.name + " | WebGL", color)
                if image:
                    texture = mat.node_tree.nodes.new("ShaderNodeTexImage")
                    texture.image = bpy.data.images[image]
                    mat.node_tree.links.new(texture.outputs["Color"], pbr.inputs["Base Color"])
                elif old.name == "Windward olive turf":
                    vertex_color = mat.node_tree.nodes.new("ShaderNodeVertexColor")
                    vertex_color.layer_name = "Turf modulation"
                    mat.node_tree.links.new(vertex_color.outputs["Color"], pbr.inputs["Base Color"])
                assigned[old.name] = mat
            slot.material = assigned[old.name]
    for obj in objects:
        mesh = obj.data
        if not any(m and m.name.startswith("Windward olive turf") for m in mesh.materials):
            continue
        color = mesh.color_attributes.new(name="Turf modulation", type="FLOAT_COLOR", domain="POINT")
        for v, c in zip(mesh.vertices, color.data):
            p = obj.matrix_world @ v.co
            k = max(0.47, min(1.50, 1.0 + noise(p * 0.78) * 0.40 + noise(p * 8) * 0.27))
            c.color = (0.19 * k, 0.25 * k, 0.075 * k, 1.0)


ECO_TEXTURE_SHA = {
    "leaf_cluster_oak.png": "b757ed344c4ad164acf2b975f0b376d396a2630d6654d301bb9a52081fc99323",
    "leaf_cluster_apple.png": "b1c3ff3a57dc15d2b155ac53b3f32d730ba21262f6e91c479ebac7535e0de763",
    "leaf_cluster_beech.png": "ddf57989e4414b446bd16cf60796f9f52bebee539c63ceae37a5282a8cd8365c",
    "leaf_spray_needle.png": "d5fefff7bfb40a4cfde12d94bf2295af32b76f1f8c976b926c667bc04cd01d14",
    "grass_card_lod1.png": "a7c04540c4611d66324a8ccbe5dc0ea2b62fe61f91bd28952a4aad8f23b7b290",
}


def pack_inputs(texture_dir):
    for image in bpy.data.images:
        filename = Path(image.filepath).name
        if filename in ECO_TEXTURE_SHA and not image.packed_file:
            path = texture_dir / filename
            assert sha(path) == ECO_TEXTURE_SHA[filename], path
            image.filepath = str(path)
            image.reload()
            image.pack()
    bpy.ops.file.pack_all()



def main():
    e, route_path, eco, out = map(lambda s: Path(s).resolve(), sys.argv[sys.argv.index("--") + 1:])
    out.mkdir(parents=True, exist_ok=True)
    paths = {"E": e, "route": route_path, "eco": eco, "CG": CG,
             "left": C13 / "C12_LEFT_SHORE_UNAPPROVED.blend",
             "right": C13 / "C12_RIGHT_FAULT_UNAPPROVED.blend",
             "rock": C13 / "junction/C13_JUNCTION_UNAPPROVED.blend"}
    for name, path in paths.items():
        assert sha(path) == INPUT_SHA[name], (name, path)
    bpy.ops.wm.open_mainfile(filepath=str(e), load_ui=False)
    scene = bpy.context.scene
    carrier = bpy.data.objects[CARRIER]
    reference, replacement = append(paths["rock"], [CARRIER, "C10 large rock 03"])
    patches = [(side, append(paths[side], [CARRIER])[0]) for side in ("left", "right")]
    bedrock = patch_carrier(carrier, reference, patches)
    rock = bpy.data.objects["C10 large rock 03"]
    assert rock.matrix_world == replacement.matrix_world and rock.data.materials[0].name.split(".")[0] == replacement.data.materials[0].name.split(".")[0]
    rock.data = replacement.data
    rock.data.materials[0] = bpy.data.materials["Slate and weathered limestone"]
    rock.hide_render = False
    rock.hide_set(False)
    terrain = tree_for(carrier)
    route_source = append(route_path, [ROAD_SOURCE])[0]
    route, start, end, route_qa = place_route(route_source, terrain, collection("ROUTE | coastal approach"))
    placements, exclusions = add_vegetation(eco, terrain, start, end)
    data, nav_qa = nav_data(terrain, route, start, end, exclusions)
    cameras = compose_light(scene)

    (out / "navigation.json").write_text(json.dumps(data, separators=(",", ":")) + "\n")
    manifest = {
        "status": "UNAPPROVED_PLAYTEST", "inputs_sha256": INPUT_SHA,
        "source_commits": {"421": "4e471edce7d4075cdee54831b6526412b3f3deb3",
                           "351": "73264bbef9b78fab5ef6eb739f6ed7eb928214c6",
                           "357": "54e7d854ffa268c93437b5edba1dda5c2e676fc6",
                           "353": "5257d2b19bed76fff1fabccf5e3ff1854a096c09"},
        "E_artifact": {"run": 44713884694, "id": 14617769408,
                       "zip_sha256": "1cfebd0d9621f2a7f0a15d4d2f232d727f6e771cdb96458b1ba17e186d31c23c"},
        "eco_texture_sha256": ECO_TEXTURE_SHA, "E_geometry_sha256": GEOMETRY_E, "rock03_geometry_sha256": geometry_sha(rock.data),
        "blender": bpy.app.version_string, "builder_sha256": sha(Path(__file__)),
        "coordinates": {"origin": [0, 0, 0], "space": "candidate-local-unscaled",
                        "blender": "right-handed, Z up, sea toward -Y", "gltf": "(X, Z, -Y)"},
        "seed": 421, "cameras": [settings for _, _, settings in cameras],
        "assembly_checks": {"bedrock": bedrock, "road": route_qa, "navigation": nav_qa, "vegetation": placements},
        "gates": {"G1": "Partial source/CG SHA pass; official metric and placement BLOCKED",
                  "G2": "Inherited FAIL; assembled scene independent review NOT_RUN",
                  "G3": "Candidate assembly checks only", "G4": "See browser QA; Android device NOT_RUN"},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    assert all(sha(path) == INPUT_SHA[name] for name, path in paths.items())
    pack_inputs(eco.parent / "textures")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "cliff_UNAPPROVED.blend"), compress=True)
    objects = [obj for obj in scene.objects if obj.type == "MESH" and not obj.hide_render and obj.name != "Setting sun disk"]
    runtime_materials(objects)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out / "cliff.glb"), use_selection=True, export_format="GLB",
                              export_gpu_instances=True, export_animations=False, export_yup=True,
                              export_all_vertex_colors=False)

    if not os.environ.get("TWO_SKIP_RENDER"):
        bpy.ops.wm.open_mainfile(filepath=str(out / "cliff_UNAPPROVED.blend"), load_ui=False)
        scene = bpy.context.scene
        missing = [image.name for image in bpy.data.images
                   if image.source == "FILE" and image.users and not image.packed_file]
        assert not missing, missing
        for _, filename, settings in cameras:
            scene.camera = bpy.data.objects[settings["name"]]
            scene.render.filepath = str(out / filename)
            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
