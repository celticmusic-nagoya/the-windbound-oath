"""Assemble the ECO v2 overlay on the preserved #421 candidate and render matched views."""
import hashlib
import json
import math
import os
import struct
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from vegetation_placement import VegetationPlacement

ROOT = HERE.parents[2]
TARGET = ROOT / "assets/candidates/lind/windwaiting-cliff-playable"
V2 = TARGET / "eco-v2"
BASE = TARGET / "cliff_UNAPPROVED.blend"
CAMERAS = ("Sunset study", "Route gameplay")
ARCHIVE_DIGEST = "1b4ca357cf2e959f73d8ae627f541694015f3fec4753259f91f84c423abb0705"


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def geometry(mesh):
    digest = hashlib.sha256()
    for vertex in mesh.vertices:
        digest.update(struct.pack("<3f", *vertex.co))
    for polygon in mesh.polygons:
        digest.update(struct.pack(f"<{len(polygon.vertices)}I", *polygon.vertices))
    return digest.hexdigest()


def open_base():
    bpy.ops.wm.open_mainfile(filepath=str(BASE), load_ui=False)


def setup():
    scene = bpy.context.scene
    assert scene.render.engine == "CYCLES"
    scene.render.resolution_percentage = 70
    scene.cycles.samples = 12
    return scene


def render(scene, version):
    for index, name in enumerate(CAMERAS):
        scene.camera = bpy.data.objects[name]
        scene.render.filepath = str(V2 / f"render-{version}-{('sunset', 'gameplay')[index]}.png")
        bpy.ops.render.render(write_still=True)


def asset_inventory():
    trusted = json.loads((V2 / "source.json").read_text())["members"]
    assets = {}
    for asset, digest in trusted.items():
        path = V2 / asset
        assert sha(path) == digest, path
        if path.suffix != ".glb":
            continue
        assert path.stem.endswith("_LOD1"), path
        raw = path.read_bytes()
        size = struct.unpack_from("<I", raw, 12)[0]
        doc = json.loads(raw[20:20 + size])
        tris = sum(doc["accessors"][prim["indices"]]["count"] // 3
                   for mesh in doc["meshes"] for prim in mesh["primitives"])
        assets[path.stem.removesuffix("_LOD1")] = {"path": asset, "triangles": tris, "lod": 1}
    return assets


def placements():
    scene = bpy.context.scene
    nav = json.loads((TARGET / "navigation.json").read_text())
    base_manifest = json.loads((TARGET / "manifest.json").read_text())
    road = base_manifest["assembly_checks"]["road"]
    origin, end = Vector(road["start_xy"]), Vector(road["end_xy"])
    span = end - origin
    carrier = bpy.data.objects[nav["ground"][0]]
    collider = BVHTree.FromObject(carrier, bpy.context.evaluated_depsgraph_get())
    assert carrier.matrix_world.is_identity

    def surface(x, y):
        point, normal, *_ = collider.ray_cast(Vector((x, y, nav["rayTop"])), Vector((0, 0, -1)))
        return (point.z, normal) if point is not None and point.z > 4.8 else None

    def excluded(x, y, radius, role):
        rel = Vector((x, y)) - origin
        distance = (rel - span * max(0, min(1, rel.dot(span) / span.length_squared))).length
        if distance < 1.25 + radius:
            return True
        if role == "tree":
            return False
        return any(math.hypot(x - bx, y + bz) < br + radius for bx, bz, br in nav["obstacles"])

    plan = VegetationPlacement(surface, excluded, seed=357421)
    for old in sorted(scene.objects, key=lambda obj: obj.name):
        if not old.name.startswith("eco_tree_deciduous_a") or old.hide_render:
            continue
        x, y, z = old.location
        point = plan.candidate("eco_tree_deciduous_a", "tree", (x, y), radius=0.38, slope=25, align=0,
                               scale=(old.scale.x, old.scale.x), sink=0, yaw=old.rotation_euler.z, datum=z)
        assert point, old.name
        point["replaces"] = old.name
        plan.instances.append(point)
    patches = [
        ("foreground", ((3.4, 13.7), (8.7, 17.3)), 7),
        ("foreground", ((-0.6, 8.0), (4.0, 11.8)), 6),
        ("landmark", ((-12.8, 2.1), (-8.9, 5.7)), 10),
        ("landmark", ((-7.7, 2.3), (-4.6, 5.3)), 5),
    ]
    for role, box, count in patches:
        plan.patch("eco_turf_meadow_a", role, box, 1.22, count=count, radius=0.79, slope=28, align=0.86,
                   scale=(0.91, 1.09), sink=0.008)
    for i, (asset, role, center) in enumerate([
        ("eco_flower_daisy_clump", "landmark", (-11.2, 3.7)),
        ("eco_flower_violet_cushion", "landmark", (-8.6, 4.3)),
        ("eco_flower_daisy_clump", "flower", (2.2, 14.0)),
        ("eco_flower_violet_cushion", "flower", (4.1, 9.2)),
    ]):
        group = plan.cluster(asset, role, center, i, radius=0.36, scale=(1.10, 1.30), slope=30, sink=0.012)
        assert len(group) >= 2, center
    plan.patch("eco_grass_tuft_short", "accent", ((-5, 7.3), (8.8, 16.6)), 2.25, count=9,
               radius=0.26, scale=(0.77, 1.01))
    plan.patch("eco_grass_coastal_dune", "accent", ((-10.5, 1.3), (-5, 3.3)), 1.5, count=4, radius=0.36,
               yaw=math.atan2(-0.282, 0.959), slope=35, align=0.45)
    plan.patch("eco_shrub_round_a", "middle", ((-12.5, 10.0), (13, 24)), 4.6, count=9,
               radius=0.64, scale=(0.59, 0.81), slope=27)
    return plan.instances


def quaternion(instance):
    normal = Vector((0, 0, 1)).lerp(Vector(instance["normal"]), instance["align"]).normalized()
    return Vector((0, 0, 1)).rotation_difference(normal) @ Quaternion((0, 0, 1), instance["yaw"])


def install_instances(scene, assets, items):
    group = bpy.data.collections.new("ECO v2 | instanced roles")
    scene.collection.children.link(group)
    for obj in scene.objects:
        if obj.name.startswith(("eco_grass_", "eco_flower_", "eco_tree_")):
            obj.hide_render = True
            obj.hide_set(True)
    by_asset = {}
    for item in items:
        by_asset.setdefault(item["asset"], []).append(item)
    for asset, instances in by_asset.items():
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(V2 / assets[asset]["path"]))
        prototype, = [obj for obj in set(bpy.data.objects) - before if obj.type == "MESH"]
        for index, instance in enumerate(instances):
            obj = bpy.data.objects.new(f"{asset} v2 #{index + 1}", prototype.data)
            group.objects.link(obj)
            obj.location = (*instance["xy"], instance["height"] - instance["sink"])
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = quaternion(instance)
            obj.scale = (instance["scale"],) * 3
        bpy.data.objects.remove(prototype, do_unlink=True)


def blend_moss():
    names = ("Slate and weathered limestone", "Damp lower bedrock",
             "C9 CC0 | Wet boulders and talus", "Moss over loose coastal stones")
    textures = V2 / "textures"
    images = {}
    for channel in ("basecolor", "normal", "orm"):
        image = bpy.data.images.load(str(textures / f"moss_tile_{channel}.png"), check_existing=True)
        if channel != "basecolor":
            image.colorspace_settings.name = "Non-Color"
        images[channel] = image
    for name in names:
        mat = bpy.data.materials[name]
        tree = mat.node_tree
        nodes, links = tree.nodes, tree.links
        pbr = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
        base = pbr.inputs["Base Color"]
        if name.startswith("Moss over loose"):
            for link in list(base.links):
                links.remove(link)
            base.default_value = (0.16, 0.145, 0.125, 1)
        coord = nodes.new("ShaderNodeTexCoord")
        xyz = nodes.new("ShaderNodeVectorMath")
        xyz.operation = "SCALE"
        xyz.inputs["Scale"].default_value = 2
        links.new(coord.outputs["Object"], xyz.inputs[0])
        mapping = {}
        for channel, image in images.items():
            texture = nodes.new("ShaderNodeTexImage")
            texture.image = image
            texture.projection = "BOX"
            texture.projection_blend = 0.23
            links.new(xyz.outputs[0], texture.inputs[0])
            mapping[channel] = texture
        geometry_node = nodes.new("ShaderNodeNewGeometry")
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(geometry_node.outputs["Normal"], sep.inputs[0])
        face = nodes.new("ShaderNodeMapRange")
        face.interpolation_type = "SMOOTHSTEP"
        face.inputs["From Min"].default_value = 0.55
        face.inputs["From Max"].default_value = 0.80
        links.new(sep.outputs["Z"], face.inputs["Value"])
        cavity = nodes.new("ShaderNodeMapRange")
        cavity.inputs["From Min"].default_value = 0.42
        cavity.inputs["From Max"].default_value = 0.56
        cavity.inputs["To Min"].default_value = 0.88
        cavity.inputs["To Max"].default_value = 0.12
        links.new(geometry_node.outputs["Pointiness"], cavity.inputs["Value"])
        variability = nodes.new("ShaderNodeTexNoise")
        variability.inputs["Scale"].default_value = 1.15
        links.new(coord.outputs["Object"], variability.inputs["Vector"])
        mask = nodes.new("ShaderNodeMath")
        mask.operation = "MULTIPLY"
        links.new(face.outputs["Result"], mask.inputs[0])
        links.new(cavity.outputs["Result"], mask.inputs[1])
        coverage = nodes.new("ShaderNodeMath")
        coverage.operation = "MULTIPLY"
        links.new(mask.outputs[0], coverage.inputs[0])
        links.new(variability.outputs["Fac"], coverage.inputs[1])
        mix = nodes.new("ShaderNodeMixRGB")
        mix.label = "ECO v2 moss | slope and concavity"
        if base.is_linked:
            links.new(base.links[0].from_socket, mix.inputs[1])
        else:
            mix.inputs[1].default_value = base.default_value
        links.new(coverage.outputs[0], mix.inputs[0])
        links.new(mapping["basecolor"].outputs["Color"], mix.inputs[2])
        links.new(mix.outputs["Color"], base)
        orm = nodes.new("ShaderNodeSeparateColor")
        links.new(mapping["orm"].outputs["Color"], orm.inputs[0])
        rough = pbr.inputs["Roughness"]
        rough_mix = nodes.new("ShaderNodeMix")
        if rough.is_linked:
            links.new(rough.links[0].from_socket, rough_mix.inputs[2])
        else:
            rough_mix.inputs[2].default_value = rough.default_value
        links.new(coverage.outputs[0], rough_mix.inputs[0])
        links.new(orm.outputs["Green"], rough_mix.inputs[3])
        links.new(rough_mix.outputs[0], rough)
        # Normal-map texture is sampled as a scalar fine bump under the same mask.
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Distance"].default_value = 0.012
        links.new(coverage.outputs[0], bump.inputs["Strength"])
        links.new(mapping["normal"].outputs["Color"], bump.inputs["Height"])
        if pbr.inputs["Normal"].is_linked:
            links.new(pbr.inputs["Normal"].links[0].from_socket, bump.inputs["Normal"])
        links.new(bump.outputs["Normal"], pbr.inputs["Normal"])


def main():
    source = json.loads((V2 / "source.json").read_text())
    assert source["artifact_sha256"] == ARCHIVE_DIGEST
    assert sha(BASE) == source["base_blend_sha256"]
    assert sha(TARGET / "cliff.glb") == source["base_glb_sha256"]
    assert sha(TARGET / "navigation.json") == source["navigation_sha256"]
    assets = asset_inventory()
    open_base()
    scene = setup()
    items = placements()
    old = {obj.name: geometry(obj.data) for obj in scene.objects
           if obj.type == "MESH" and not obj.name.startswith(("eco_grass_", "eco_flower_", "eco_tree_"))}
    install_instances(scene, assets, items)
    blend_moss()
    assert all(geometry(bpy.data.objects[name].data) == digest for name, digest in old.items())
    assert all(assets[i["asset"]]["lod"] == 1 for i in items)
    manifest = {
        "schema": "vegetation-placement-v1", "units": "candidate BU; glTF metre authored as 1 BU before instance scale",
        "surface": "Z-up right-handed Blender; runtime copies X,Z,-Y",
        "assets": assets, "instances": items, "protected_geometry_sha256": old,
        "roles": {"foreground": {"range": 10}, "landmark": {"range": 20},
                  "flower": {"range": 15}, "accent": {"range": 14},
                  "middle": {"range": 32}, "tree": {"range": 55}},
        "full_overlay_triangles": sum(assets[i["asset"]]["triangles"] for i in items),
    }
    (V2 / "placement.json").write_text(json.dumps(manifest, indent=2) + "\n")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.file.pack_all()
    candidate = V2 / "cliff_eco_v2_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate), compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(candidate), load_ui=False)
    assert all(geometry(bpy.data.objects[name].data) == digest for name, digest in old.items())
    missing = [i.name for i in bpy.data.images if i.source == "FILE" and i.users and not i.packed_file]
    assert not missing, missing
    objects = list(bpy.data.collections["ECO v2 | instanced roles"].objects)
    assert len(objects) == len(items)
    reopen = {"matched_protected_meshes": len(old), "eco_instances": len(objects),
              "linked_prototype_meshes": len({o.data for o in objects}),
              "missing_packed_images": missing, "version": bpy.app.version_string}
    (V2 / "reopen-qa.json").write_text(json.dumps(reopen, indent=2) + "\n")
    if not os.environ.get("TWO_SKIP_RENDER"):
        render(setup(), "after")
        open_base()
        render(setup(), "before")


if __name__ == "__main__":
    main()
