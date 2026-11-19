"""Install SHA-verified packed CC0 maps and render fixed-camera controls."""
import hashlib
import json
import sys
from pathlib import Path

import bpy

from sculpt_c9 import render

ONLY = sys.argv.pop(1)[2:] if sys.argv[1] in ("--skip-control", "--C") else ""

source, c8, c9, output = map(Path, sys.argv[1:])
manifest = json.loads((source / "source_provenance.json").read_text())
assert tuple(bpy.app.version) == (5, 2, 4)


def install(material, asset, role):
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    coord = nodes.new("ShaderNodeTexCoord")
    uv = nodes.new("ShaderNodeVectorMath")
    uv.operation = "MULTIPLY"
    uv.inputs[1].default_value = (8, 3, 1)
    links.new(coord.outputs["UV"], uv.inputs[0])
    geometry = nodes.new("ShaderNodeNewGeometry")
    mapping = nodes.new("ShaderNodeVectorMath")
    mapping.operation = "MULTIPLY"
    mapping.inputs[1].default_value = (.29, .31, .37)
    links.new(geometry.outputs["Position"], mapping.inputs[0])
    position_z = nodes.new("ShaderNodeSeparateXYZ")
    links.new(geometry.outputs["Position"], position_z.inputs[0])

    def map_range(socket, low, high, bottom, top):
        node = nodes.new("ShaderNodeMapRange")
        node.clamp = True
        node.interpolation_type = "SMOOTHSTEP"
        for key, value in zip(("From Min", "From Max", "To Min", "To Max"), (low, high, bottom, top)):
            node.inputs[key].default_value = value
        links.new(socket, node.inputs["Value"])
        return node.outputs[0]

    def color_mix(first, second, factor, operation="MIX"):
        node = nodes.new("ShaderNodeMixRGB")
        node.blend_type = operation
        for slot, value in enumerate((factor, first, second)):
            if isinstance(value, bpy.types.NodeSocket):
                links.new(value, node.inputs[slot])
            else:
                node.inputs[slot].default_value = value
        return node.outputs[0]

    textures = {}
    for record in asset["dependencies"]:
        image_path = source / record["file"]
        if image_path.suffix != ".jpg":
            continue
        kind = record["uri"].split("_")[-2]
        if "nor_gl" in record["uri"]:
            kind = "normal"
        if kind == "normal" and role == "debris":
            continue
        assert hashlib.sha256(image_path.read_bytes()).hexdigest() == record["sha256"]
        img = bpy.data.images.load(str(image_path), check_existing=True)
        img.colorspace_settings.name = "sRGB" if kind == "diff" else "Non-Color"
        assert tuple(img.size) == (1024, 1024) and img.has_data
        img.pack()
        img.filepath = "//packed_cc0/" + image_path.name
        tex = nodes.new("ShaderNodeTexImage")
        tex.label = kind
        tex.image = img
        if kind == "normal":
            links.new(uv.outputs["Vector"], tex.inputs["Vector"])
        else:
            tex.projection = "BOX"
            tex.projection_blend = .24
            links.new(mapping.outputs[0], tex.inputs["Vector"])
        textures[kind] = tex.outputs["Color"]

    channels = nodes.new("ShaderNodeSeparateColor")
    links.new(textures["arm"], channels.inputs[0])
    wet = map_range(position_z.outputs["Z"], .12, .91, 1, 0)
    neutral = (.17, .153, .137, 1)
    base = color_mix(neutral, textures["diff"], .42 if role == "carrier" else .61)
    base = color_mix(base, channels.outputs["Red"], .13, "MULTIPLY")
    base = color_mix(base, (.34, .44, .50, 1), wet, "MULTIPLY")
    dry_roughness = map_range(channels.outputs["Green"], 0, 1, .53, .94)
    roughness = color_mix(dry_roughness, (.34, .34, .34, 1), wet)

    if role == "carrier":
        old = shader.inputs["Base Color"].links[0].from_node
        grass_factor = old.inputs[0].links[0].from_socket
        grass_tones = old.inputs[2].links[0].from_socket
        soil_noise = nodes.new("ShaderNodeTexNoise")
        soil_noise.inputs["Scale"].default_value = .72
        soil_noise.inputs["Detail"].default_value = 2
        links.new(geometry.outputs["Position"], soil_noise.inputs["Vector"])
        soil = map_range(soil_noise.outputs["Fac"], .23, .44, .55, 0)
        mixed_ground = color_mix(grass_tones, (.14, .10, .058, 1), soil)
        base = color_mix(base, mixed_ground, grass_factor)
        turf_roughness = map_range(soil_noise.outputs["Fac"], .22, .74, .77, .94)
        roughness = color_mix(roughness, turf_roughness, grass_factor)
        normal = nodes.new("ShaderNodeNormalMap")
        links.new(textures["normal"], normal.inputs["Color"])
        normal.inputs["Strength"].default_value = .20
        normal.uv_map = "Coast tile | U periodic"
        links.new(normal.outputs["Normal"], shader.inputs["Normal"])
    elif role == "debris":
        height = nodes.new("ShaderNodeBump")
        height.inputs["Strength"].default_value = .20
        height.inputs["Distance"].default_value = .024
        links.new(channels.outputs["Red"], height.inputs["Height"])
        links.new(height.outputs["Normal"], shader.inputs["Normal"])
    else:
        normal = nodes.new("ShaderNodeNormalMap")
        normal.inputs["Strength"].default_value = .25
        links.new(textures["normal"], normal.inputs["Color"])
        links.new(normal.outputs["Normal"], shader.inputs["Normal"])

    links.new(base, shader.inputs["Base Color"])
    links.new(roughness, shader.inputs["Roughness"])


for label, path in (("A", c8), ("B", c8), ("C", c9)):
    if (label == "A" and ONLY == "skip-control") or (label != "C" and ONLY == "C"):
        continue
    bpy.ops.wm.open_mainfile(filepath=str(path))
    scene = bpy.context.scene
    scene.render.resolution_percentage = 80
    scene.render.threads = 8
    bpy.context.preferences.filepaths.save_version = 0
    if label != "A":
        rock = bpy.data.materials["Slate and weathered limestone"]
        debris = rock.copy()
        debris.name = "C9 CC0 | Wet boulders and talus"
        for obj in bpy.data.objects:
            if obj.type == "MESH" and not obj.get("variant") and obj.data.materials and obj.data.materials[0] == rock:
                obj.data.materials[0] = debris
        # Inland review context keeps the original turf material mix.
        for obj in bpy.data.objects:
            if obj.type == "MESH" and any(col.name.startswith("06 |") for col in obj.users_collection):
                for index, mat in enumerate(obj.data.materials):
                    if mat == debris or mat == rock:
                        obj.data.materials[index] = rock.copy()
        install(rock, manifest["assets"][0], "carrier")
        install(debris, manifest["assets"][1], "debris")
        scene["candidate"] = "C9-B_UNAPPROVED" if label == "B" else "C9-A+B_UNAPPROVED"
        bpy.ops.wm.save_as_mainfile(filepath=str(output / f"{label}_UNAPPROVED.blend"), compress=True)
    for view in ("cg_review", "shore_detail"):
        render(scene, view, output / f"{label}_{view}.png")
