"""Import a verified VRoid VRM into Blender 5.3.0 and reopen an editable copy.

Run with: blender -b --python-exit-code 1 --python import_vrm_transfer.py --
          SOURCE.vrm EXPECTED_VRM_SHA256 NEW.blend NEW.receipt.json
The qualified VRM add-on must already be enabled in this isolated Blender profile.
"""
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import struct
import sys


def validate_embedded_geometry(model, raw, json_length):
    """Strict embedded GLB framing and reference/range preflight, not full schema QA."""
    def require(ok, reason):
        if not ok:
            raise ValueError(reason)

    def uint(value):
        return type(value) is int and value >= 0

    def index(items, value, label):
        require(uint(value) and value < len(items), f"invalid {label} index")
        return items[value]

    start = 20 + json_length
    require(json_length > 0 and json_length % 4 == 0 and start + 8 <= len(raw), "missing or misaligned BIN chunk")
    size, kind = struct.unpack_from("<I4s", raw, start)
    require(kind == b"BIN\0" and size > 0 and size % 4 == 0 and start + 8 + size == len(raw), "invalid BIN chunk length or trailing bytes")
    buffers = model.get("buffers", [])
    require(len(buffers) == 1 and "uri" not in buffers[0], "expected one embedded buffer")
    length = buffers[0].get("byteLength")
    require(uint(length) and 0 < length <= size and size - length <= 3, "invalid embedded buffer length")
    require(not any(raw[start + 8 + length:]), "nonzero BIN padding")
    views = model.get("bufferViews", [])
    accessors = model.get("accessors", [])
    nodes = model.get("nodes", [])
    meshes = model.get("meshes", [])
    skins = model.get("skins", [])
    materials = model.get("materials", [])
    for view in views:
        require(type(view.get("buffer")) is int and view["buffer"] == 0, "invalid bufferView buffer")
        off, count = view.get("byteOffset", 0), view.get("byteLength")
        require(uint(off) and uint(count) and count > 0 and off + count <= length, "bufferView range exceeds embedded buffer")
    component_bytes = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
    dimensions = {"SCALAR": (1, 1), "VEC2": (2, 1), "VEC3": (3, 1), "VEC4": (4, 1), "MAT2": (2, 2), "MAT3": (3, 3), "MAT4": (4, 4)}
    for accessor in accessors:
        width = component_bytes.get(accessor.get("componentType"))
        shape = dimensions.get(accessor.get("type"))
        count, off = accessor.get("count"), accessor.get("byteOffset", 0)
        require(width is not None and shape is not None and uint(count) and count > 0 and uint(off), "invalid accessor format")
        require("sparse" not in accessor, "sparse accessor requires separate qualification")
        view = index(views, accessor.get("bufferView"), "accessor bufferView")
        rows, cols = shape
        column = rows * width
        element = ((column + 3) // 4 * 4 if cols > 1 else column) * cols
        stride = view.get("byteStride", element)
        require(uint(stride) and stride >= element and stride % width == 0 and off % width == 0 and (view.get("byteOffset", 0) + off) % width == 0, "invalid accessor alignment or stride")
        require(off + (count - 1) * stride + element <= view["byteLength"], "accessor range exceeds bufferView")
    for image in model.get("images", []):
        require("uri" not in image, "expected embedded image bufferView")
        index(views, image.get("bufferView"), "image bufferView")
    for skin in skins:
        require(bool(skin.get("joints")), "skin has no joints")
        for joint in skin["joints"]:
            index(nodes, joint, "joint node")
        if "skeleton" in skin:
            index(nodes, skin["skeleton"], "skeleton node")
        if "inverseBindMatrices" in skin:
            index(accessors, skin["inverseBindMatrices"], "inverse bind accessor")
    for node in nodes:
        for child in node.get("children", []):
            index(nodes, child, "child node")
        if "mesh" in node:
            index(meshes, node["mesh"], "node mesh")
        if "skin" in node:
            index(skins, node["skin"], "node skin")
    for mesh in meshes:
        for primitive in mesh.get("primitives", []):
            for attribute in primitive.get("attributes", {}).values():
                index(accessors, attribute, "primitive attribute accessor")
            for target in primitive.get("targets", []):
                for attribute in target.values():
                    index(accessors, attribute, "morph accessor")
            if "indices" in primitive:
                index(accessors, primitive["indices"], "primitive indices accessor")
            if "material" in primitive:
                index(materials, primitive["material"], "primitive material")
    ext = model.get("extensions", {})
    if "VRMC_vrm" in ext:
        for bone in ext["VRMC_vrm"].get("humanoid", {}).get("humanBones", {}).values():
            index(nodes, bone.get("node"), "humanoid node")
    elif "VRM" in ext:
        for bone in ext["VRM"].get("humanoid", {}).get("humanBones", []):
            index(nodes, bone.get("node"), "humanoid node")


def inspect_vrm(raw):
    if len(raw) < 20 or struct.unpack_from("<4sII", raw) != (b"glTF", 2, len(raw)):
        raise ValueError("expected a complete GLB v2 container")
    length, kind = struct.unpack_from("<I4s", raw, 12)
    if kind != b"JSON" or length > len(raw) - 20:
        raise ValueError("invalid JSON chunk")
    model = json.loads(raw[20:20+length])
    validate_embedded_geometry(model, raw, length)
    extensions = model.get("extensions", {})
    if "VRMC_vrm" in extensions:
        vrm = extensions["VRMC_vrm"]
        humanoid = vrm.get("humanoid", {}).get("humanBones", {})
        expressions = vrm.get("expressions", {})
        names = sorted(set(expressions.get("preset", {})) | set(expressions.get("custom", {})))
        version = vrm.get("specVersion")
    elif "VRM" in extensions:
        vrm = extensions["VRM"]
        humanoid = {entry["bone"]: entry["node"] for entry in vrm.get("humanoid", {}).get("humanBones", [])}
        names = sorted(group["name"] for group in vrm.get("blendShapeMaster", {}).get("blendShapeGroups", []))
        version = vrm.get("specVersion")
    else:
        raise ValueError("file is GLB but lacks a VRM extension")
    for key in ("buffers", "images"):
        if any("uri" in item and not item["uri"].startswith("data:") for item in model.get(key, [])):
            raise ValueError("external VRM resource is outside the transfer contract")
    primitives = [p for mesh in model.get("meshes", []) for p in mesh.get("primitives", [])]
    result = dict(version=version, exporter=vrm.get("exporterVersion") or model.get("asset", {}).get("generator"),
                  meta=vrm.get("meta", {}), humanoid_bones=sorted(humanoid), expressions=names,
                  skins=len(model.get("skins", [])), primitives=len(primitives),
                  uv_primitives=sum("TEXCOORD_0" in p["attributes"] for p in primitives),
                  skin_primitives=sum({"JOINTS_0","WEIGHTS_0"} <= p["attributes"].keys() for p in primitives),
                  morph_targets=sum(len(p.get("targets", [])) for p in primitives),
                  materials=len(model.get("materials", [])), images=len(model.get("images", [])),
                  spring_bone_extension="VRMC_springBone" in extensions or bool(vrm.get("secondaryAnimation")))
    if not all(result[k] for k in ("version", "meta", "humanoid_bones", "expressions", "skins",
                                   "uv_primitives", "skin_primitives", "materials", "images")):
        raise ValueError("source VRM is missing a required transfer category")
    return result


def inventory(bpy):
    meshes = {}
    armatures = {}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            mesh = obj.data
            shape_keys = mesh.shape_keys
            meshes[obj.name] = dict(vertices=len(mesh.vertices), polygons=len(mesh.polygons),
                uv_layers=[layer.name for layer in mesh.uv_layers],
                materials=[slot.material.name if slot.material else None for slot in obj.material_slots],
                morphs=[key.name for key in shape_keys.key_blocks][1:] if shape_keys else [],
                skin_groups=[group.name for group in obj.vertex_groups],
                weighted_vertices=sum(any(g.weight > 0 for g in v.groups) for v in mesh.vertices),
                rigs=[m.object.name for m in obj.modifiers if m.type == "ARMATURE" and m.object])
        elif obj.type == "ARMATURE":
            ext = getattr(obj.data, "vrm_addon_extension", None)
            armatures[obj.name] = dict(bones=sorted(obj.data.bones.keys()),
                                      vrm_extension=ext.spec_version if ext else None)
    images = {im.name: dict(size=list(im.size), packed_sha256=sorted(
                   sha256(p.packed_file.data).hexdigest() for p in im.packed_files))
              for im in bpy.data.images if im.source not in {"GENERATED", "VIEWER"}}
    return dict(meshes=meshes, armatures=armatures, images=images)


def main():
    import bpy

    source, expected, blend, report = sys.argv[sys.argv.index("--")+1:]
    source, blend, report = (Path(p).resolve() for p in (source, blend, report))
    if blend.exists() or report.exists() or blend.suffix != ".blend" or source.suffix != ".vrm":
        raise ValueError("require a VRM and unique .blend and receipt paths")
    if tuple(bpy.app.version) != (5, 3, 0):
        raise RuntimeError("requires Blender 5.3.0")
    modules = [name for name in bpy.context.preferences.addons.keys() if name.endswith(".vrm")]
    if len(modules) != 1:
        raise RuntimeError("profile must have exactly one qualified VRM add-on")
    module = import_module(modules[0])
    from tomllib import loads
    manifest = Path(module.__file__).parent / "blender_manifest.toml"
    if loads(manifest.read_text()).get("version") != "4.10.5":
        raise RuntimeError("requires qualified VRM add-on v4.10.5")
    raw = source.read_bytes()
    if sha256(raw).hexdigest() != expected:
        raise ValueError("source VRM SHA mismatch")
    metadata = inspect_vrm(raw)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    operator = bpy.ops.import_scene.vrm if 'vrm' in dir(bpy.ops.import_scene) else bpy.ops.wm.vrm_import
    if operator(filepath=str(source)) != {"FINISHED"}:
        raise RuntimeError("VRM import did not finish")
    bpy.ops.file.pack_all()
    before = inventory(bpy)
    if not (before["armatures"] and before["meshes"] and before["images"]
            and any(m["uv_layers"] and m["rigs"] and m["weighted_vertices"] for m in before["meshes"].values())
            and all(i["packed_sha256"] for i in before["images"].values())):
        raise RuntimeError("import lacks essential editable or packed resources")
    if bpy.ops.wm.save_as_mainfile(filepath=str(blend)) != {"FINISHED"}:
        raise RuntimeError("blend save did not finish")
    if bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False) != {"FINISHED"}:
        raise RuntimeError("blend reopen did not finish")
    after = inventory(bpy)
    if before != after or sha256(source.read_bytes()).hexdigest() != expected:
        raise RuntimeError("inventory or source bytes changed on reopen")
    with report.open("x", encoding="utf-8") as output:
        json.dump(dict(scope="STRUCTURAL_IMPORT_AND_REOPEN_NOT_ART_ACCEPTANCE",
                       blender=bpy.app.version_string, addon="4.10.5",
                       vrm_sha256=expected, blend_sha256=sha256(blend.read_bytes()).hexdigest(),
                       source=metadata, saved_and_reopened=after,
                       pending=["source-to-import exact humanoid/expression/hair correspondence",
                                "matched renders and deformation test"]),
                  output, indent=2)


if __name__ == "__main__":
    main()
