"""Blender 5.3: build the reversible PR #421 composition from packed inputs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[3]
ASSETS = ROOT / "assets/candidates/lind/windwaiting-cliff-playable"
NATIVE = ASSETS / "eco-v2/cliff_eco_v2_UNAPPROVED.blend"
TREE = ASSETS / "eco-v2/glb/eco_tree_deciduous_a_LOD1.glb"
CG = ROOT / "assets/approved/game/cliff/sunset_background.png"

# x, seaward crest y, crest elevation in provisional Blender units.
# From left background headland to right-hand descending stacks in the CG.
PROFILES = [
    [(-78, -46, 2.4), (-68, -43, 3.1), (-58, -42, 4.8), (-48, -43, 5.1),
     (-37, -46, 4.5), (-31, -48, 2.7), (-27, -51, 1.2)],
    [(-47, -73, 2.5), (-33, -69, 4.4), (-15, -64, 6.3), (-8, -64, 6.9),
     (3, -65, 6.1), (8, -68, 5.3), (12, -71, 3.6), (14, -72, 1.1)],
    [(16, -73, 1.7), (19, -71, 3.1), (21, -72, 2.6), (22.5, -74, 1.0)],
    [(24, -75, .7), (25, -74, 1.6), (27, -75, 1.2), (28, -77, .4)],
]


def digest(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Roughness"].default_value = .9
    return mat


def export(path, objects, attributes=False):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path), use_selection=True, export_extras=True,
                              export_attributes=attributes, export_tangents=True,
                              export_animations=False)


def build_coast():
    vertices, faces, slots = [], [], []
    for landmarks in PROFILES:
        profile = []
        for j, (a, b) in enumerate(zip(landmarks, landmarks[1:])):
            profile.append(a)
            for step in (1 / 3, 2 / 3):
                x, y, z = [u + (v - u) * step for u, v in zip(a, b)]
                profile.append((x, y + .76 * math.sin(x * .9), z + .39 * math.sin(j * 2.8 + step * 9)))
        profile.append(landmarks[-1])
        start = len(vertices)
        for i, (x, y, z) in enumerate(profile):
            seam = math.sin(i * 2.37 + x)
            vertices.extend([
                (x + .8 * seam, y + 1.9, -.45),
                (x + .25 * seam, y + .65 + .4 * seam, z * .32),
                (x - .17 * seam, y - .2, z * .74),
                (x, y, z),
                (x - .3 * seam, y - 3.7, z * .91),
                (x - .7 * seam, y - 10.2, z * .47),
                (x, y - 14, -.45),
            ])
        for i in range(len(profile) - 1):
            for row in range(7):
                a = start + 7 * i + row
                b = start + 7 * i + (row + 1) % 7
                faces.extend([(a, b, a + 7), (b, b + 7, a + 7)])
                slots.extend([int(3 <= row <= 4)] * 2)
        faces.extend([tuple(range(start + 6, start - 1, -1)),
                      tuple(range(start + len(profile) * 7 - 7, start + len(profile) * 7))])
        slots.extend([0, 0])
    mesh = bpy.data.meshes.new("Stepped sedimentary headlands and stacks")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("Offshore coastal strata | provisional", mesh)
    bpy.context.collection.objects.link(obj)
    mesh.materials.append(material("Blue slate at distance", (.125, .148, .20)))
    mesh.materials.append(material("Windward distant turf", (.145, .164, .119)))
    for face, slot in zip(mesh.polygons, slots, strict=True):
        face.material_index = slot
    mesh.calc_loop_triangles()
    return obj


def shade_road(ground, road):
    start, end = Vector((8, 17.25, 0)), Vector((-5.2, 2.8, 0))
    direction = (end - start).normalized()
    lateral = Vector((-direction.y, direction.x, 0))
    sides = [(v.co - start).dot(lateral) for v in road.data.vertices]
    for index, old in enumerate(list(ground.data.materials)):
        if old is None or not old.use_nodes or not any(name in old.name for name in ("turf", "Slate")):
            continue
        mat = old.copy()
        mat.name = old.name + " | continuous footpath"
        ground.data.materials[index] = mat
        nodes, links = mat.node_tree.nodes, mat.node_tree.links

        def math_node(op, a, b):
            node = nodes.new("ShaderNodeMath")
            node.operation = op
            for slot, value in zip(node.inputs, (a, b)):
                if isinstance(value, (int, float)):
                    slot.default_value = value
                else:
                    links.new(value, slot)
            return node.outputs[0]

        def smooth(value, lo, hi):
            node = nodes.new("ShaderNodeMapRange")
            node.interpolation_type = "SMOOTHSTEP"
            node.inputs["From Min"].default_value = lo
            node.inputs["From Max"].default_value = hi
            links.new(value, node.inputs["Value"])
            return node.outputs[0]

        pos = nodes.new("ShaderNodeNewGeometry").outputs["Position"]
        local = nodes.new("ShaderNodeVectorMath")
        local.operation = "SUBTRACT"
        links.new(pos, local.inputs[0])
        local.inputs[1].default_value = start

        def project(axis):
            node = nodes.new("ShaderNodeVectorMath")
            node.operation = "DOT_PRODUCT"
            links.new(local.outputs["Vector"], node.inputs[0])
            node.inputs[1].default_value = axis
            return node.outputs["Value"]

        along, side = project(direction), project(lateral)
        edge = math_node("MINIMUM", math_node("SUBTRACT", side, min(sides)),
                         math_node("SUBTRACT", max(sides), side))
        start_mask = smooth(along, -.45, .2)
        end_mask = math_node("SUBTRACT", 1, smooth(along, (end - start).length - .2,
                                                  (end - start).length + .45))
        noise = nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 6
        links.new(pos, noise.inputs["Vector"])
        edge = math_node("ADD", edge, math_node("MULTIPLY", math_node("SUBTRACT", noise.outputs["Fac"], .5), .24))
        mask = math_node("MULTIPLY", smooth(edge, -.55, .24), math_node("MULTIPLY", start_mask, end_mask))
        bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        base = bsdf.inputs["Base Color"]
        mix = nodes.new("ShaderNodeMixRGB")
        if base.is_linked:
            links.new(base.links[0].from_socket, mix.inputs[1])
        else:
            mix.inputs[1].default_value = base.default_value
        tread = nodes.new("ShaderNodeMixRGB")
        links.new(noise.outputs["Fac"], tread.inputs[0])
        tread.inputs[1].default_value = (.13, .073, .033, 1)
        tread.inputs[2].default_value = (.28, .18, .095, 1)
        links.new(tread.outputs[0], mix.inputs[2])
        links.new(mask, mix.inputs[0])
        links.new(mix.outputs[0], base)


def inspect_road():
    road = bpy.data.objects["Coastal footpath"]
    ground = bpy.data.objects["Cliff C8 B | joinable coastal segment"]
    ground_bvh = BVHTree.FromPolygons(
        [ground.matrix_world @ v.co for v in ground.data.vertices],
        [list(f.vertices) for f in ground.data.polygons],
    )
    road.data.calc_loop_triangles()
    gaps, normals = [], []
    for tri in road.data.loop_triangles:
        a, b, c = [road.matrix_world @ road.data.vertices[i].co for i in tri.vertices]
        normals.append(tri.normal.z)
        for u, v in ((.333, .333), (.1, .1), (.8, .1), (.1, .8)):
            sample = a + (b - a) * u + (c - a) * v
            hit, *_ = ground_bvh.ray_cast(Vector((sample.x, sample.y, 18)), Vector((0, 0, -1)))
            if hit is not None:
                gaps.append(sample.z - hit.z)
    shade_road(ground, road)
    road.hide_render = True
    road.hide_set(True)
    return {"triangles": len(normals), "samples": len(gaps), "gap_bu": [min(gaps), max(gaps)],
            "below_terrain_samples": sum(g < 0 for g in gaps),
            "road_face_normal_z": [min(normals), max(normals)], "uv_layers": len(road.data.uv_layers)}


def improve_tree(out):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(TREE))
    objects = list(set(bpy.data.objects) - before)
    tree = next(obj for obj in objects if obj.type == "MESH")
    mesh = tree.data
    bark = next(i for i, m in enumerate(mesh.materials) if "bark" in m.name.lower())
    bark_faces = [f for f in mesh.polygons if f.material_index == bark]
    bark_vertices = {i for f in bark_faces for i in f.vertices}
    for vertex in mesh.vertices:
        # Give the upper crown a windward lean while holding its branch joins.
        height = max(0, vertex.co.z - 1.2)
        vertex.co.x += .022 * height * height
        vertex.co.y -= .010 * height * height
    for index in bark_vertices:
        p = mesh.vertices[index].co
        # Preserve the canopy junctions, with a wider asymmetric buttress at grade.
        basal = max(0.0, min(1.0, 1.0 - p.z / .95))
        theta = math.atan2(p.y, p.x)
        flare = 1 + basal**2 * (.38 + .31 * math.cos(4 * theta + .5))
        p.x *= flare
        p.y *= flare
        p.x += basal * .07
    bark_texture = ASSETS / "photo-pbr/bark_brown_02"
    bark_source = json.loads((bark_texture / "manifest.json").read_text())
    assert bark_source["license"] == "CC0"
    nodes = mesh.materials[bark].node_tree
    shader = next(n for n in nodes.nodes if n.type == "BSDF_PRINCIPLED")
    for role, record in bark_source["textures"].items():
        path = bark_texture / record["path"]
        assert digest(path) == record["sha256"], path
        texture = nodes.nodes.new("ShaderNodeTexImage")
        texture.image = bpy.data.images.load(str(path), check_existing=True)
        texture.image.colorspace_settings.name = record["color_space"]
        if role == "normal":
            normal = nodes.nodes.new("ShaderNodeNormalMap")
            nodes.links.new(texture.outputs["Color"], normal.inputs["Color"])
            nodes.links.new(normal.outputs["Normal"], shader.inputs["Normal"])
        else:
            target = {"basecolor": "Base Color", "roughness": "Roughness"}[role]
            nodes.links.new(texture.outputs["Color"], shader.inputs[target])
    uv = mesh.uv_layers.active
    for face in bark_faces:
        for loop_index in face.loop_indices:
            coord = uv.data[loop_index].uv
            coord.x *= 1.5
            coord.y *= 2.4
    corner_normals = [item.vector.copy() for item in mesh.corner_normals]
    for face in bark_faces:
        for loop_index in face.loop_indices:
            corner_normals[loop_index] = (0, 0, 0)
    mesh.normals_split_custom_set(corner_normals)
    mesh.update()
    export(out / "tree.glb", objects, attributes=True)
    for old in bpy.context.scene.objects:
        if old.name.startswith("eco_tree_deciduous_a v2 #"):
            old.data = mesh
    for prototype in objects:
        prototype.hide_render = True
        prototype.hide_set(True)
    return {"bark_faces": len(bark_faces), "uv_density_multiplier": [1.5, 2.4],
            "wind_attribute": "_wind_weight" in mesh.attributes or "_WIND_WEIGHT" in mesh.attributes,
            "bark_source": bark_source}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    out = parser.parse_args(sys.argv[sys.argv.index("--") + 1:]).output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "composition_UNAPPROVED.blend").exists()
    bpy.ops.wm.open_mainfile(filepath=str(NATIVE))
    road = inspect_road()
    coast = build_coast()
    export(out / "distant-coast.glb", [coast])
    tree = improve_tree(out)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "composition_UNAPPROVED.blend"), compress=True)
    data = {"status": "UNAPPROVED", "blender": bpy.app.version_string,
            "inputs_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (NATIVE, TREE, CG)},
            "terrain": {"coordinates": "provisional Z-up, sea is -Y, glTF (X,Z,-Y)",
                        "crest_sections": PROFILES, "triangles": len(coast.data.loop_triangles)},
            "old_road": road, "tree": tree, "independent_art_qa": "NOT_RUN"}
    (out / "geometry-qa.json").write_text(json.dumps(data, indent=2) + "\n")


if __name__ == "__main__":
    main()
