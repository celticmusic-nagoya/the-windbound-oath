"""Apply verified temporary Poly Haven PBR maps to Aidan house candidate.

Blender-side utility; candidate only. Uses SHA-256 manifest from intake.
"""
import hashlib
import json
import pathlib

import bpy

ASSIGNMENTS = {
    "Limestone": "medieval_blocks_05",
    "Oak": "medieval_wood",
    "Solid_oak_door": "dark_wooden_planks",
    "Individual_roof_slate": "reed_roof_03",
    "ROOF_UNDERLAY": "reed_roof_03",
    "Porch_canopy": "reed_roof_03",
}
def apply_candidate_pbr(texture_directory):
    root = pathlib.Path(texture_directory)
    data = json.loads((root / "download-manifest.json").read_text(encoding="utf-8"))
    assert data["status"] == "CANDIDATE_NOT_CANON"
    indexed = {}
    for row in data["textures"]:
        p = root / row["path"]
        if p.resolve().parent != root.resolve():
            raise ValueError("Texture path escapes candidate folder")
        if hashlib.sha256(p.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Texture SHA-256 mismatch: " + str(p))
        indexed[(row["asset_id"], row["channel"])] = p
    materials = {}
    for asset in set(ASSIGNMENTS.values()):
        mat = bpy.data.materials.new("CANDIDATE_PBR_" + asset)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        for channel in ("Diffuse", "Normal", "Rough"):
            path = indexed[(asset, channel)]
            image = bpy.data.images.load(str(path), check_existing=True)
            image.pack()
            image.colorspace_settings.name = "sRGB" if channel == "Diffuse" else "Non-Color"
            node = nodes.new("ShaderNodeTexImage")
            node.label = channel
            node.image = image
            if channel == "Diffuse":
                links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
            elif channel == "Rough":
                links.new(node.outputs["Color"], bsdf.inputs["Roughness"])
            else:
                normal = nodes.new("ShaderNodeNormalMap")
                links.new(node.outputs["Color"], normal.inputs["Color"])
                links.new(normal.outputs["Normal"], bsdf.inputs["Normal"])
        materials[asset] = mat
    assigned = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        asset = None
        if obj.name.startswith("Solid_oak_door"):
            asset = ASSIGNMENTS["Solid_oak_door"]
        elif obj.name.startswith("Individual_roof_slate") or obj.name.startswith("ROOF_UNDERLAY") or obj.name.startswith("Porch_canopy"):
            asset = ASSIGNMENTS["Individual_roof_slate"]
        elif obj.data.materials and obj.data.materials[0].name.startswith("Limestone"):
            asset = ASSIGNMENTS["Limestone"]
        elif obj.data.materials and obj.data.materials[0].name.startswith("Oak"):
            asset = ASSIGNMENTS["Oak"]
        if asset:
            obj.data.materials.clear()
            obj.data.materials.append(materials[asset])
            assigned += 1
    print("AIDAN_CANDIDATE_PBR_APPLIED", assigned)
    return assigned
