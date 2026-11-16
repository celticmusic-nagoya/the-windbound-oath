"""LIND-SPATIAL-01 non-destructive Blender scene assembler.
Never infers village positions: only consumes a director-reviewed layout JSON.
Run: blender -b --python tools/map_blender/lind_spatial_assemble.py -- --layout path.json --out scene.blend
"""
import argparse, hashlib, json, pathlib, sys
import bpy
from mathutils import Vector

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--layout", required=True)
    parser.add_argument("--out", required=True)
    args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    opt = parser.parse_args(args)
    path = pathlib.Path(opt.layout)
    raw = path.read_bytes()
    data = json.loads(raw)
    require(data.get("schema") == "lind-spatial-layout-v1", "Unknown layout schema")
    require(data.get("canon_review") == "PASS", "BLOCKED: map visual/canon review not PASS")
    require(data.get("source_map_sha256") == "83dd4ad1eb10103fdb7eb569e8b1b22cc92920d4c94d4eae85735125de87fe6c",
            "BLOCKED: source map hash mismatch")
    require(data.get("camera") and data.get("units_per_world_px"), "BLOCKED: verified camera/scale missing")
    require(isinstance(data.get("assets"), list) and data["assets"], "BLOCKED: verified asset placements missing")
    require(all(a.get("verified") is True for a in data["assets"]), "BLOCKED: unverified placement")
    ids = [a["id"] for a in data["assets"]]
    require(len(ids) == len(set(ids)), "Duplicate asset ids")
    for a in data["assets"]:
        require(len(a.get("position", [])) == 3, "Missing XYZ for "+a["id"])
        require(a.get("asset_path"), "Missing .blend asset path for "+a["id"])
        require(pathlib.Path(a["asset_path"]).is_file(), "Missing source asset: "+a["asset_path"])
        if a.get("sha256"):
            digest = hashlib.sha256(pathlib.Path(a["asset_path"]).read_bytes()).hexdigest()
            require(digest == a["sha256"], "Asset hash mismatch: "+a["id"])
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    collections = {}
    for a in data["assets"]:
        group = a.get("layer", "L2_architecture")
        if group not in collections:
            c = bpy.data.collections.new(group)
            bpy.context.scene.collection.children.link(c)
            collections[group] = c
        with bpy.data.libraries.load(a["asset_path"], link=False) as (src, dst):
            dst.objects = [name for name in src.objects if name is not None]
        root = bpy.data.objects.new("ROOT__"+a["id"], None)
        collections[group].objects.link(root)
        root.location = Vector(a["position"])
        root.rotation_euler[2] = float(a.get("rotation_z", 0.0))
        root.scale = (float(a.get("scale", 1.0)),)*3
        for obj in dst.objects:
            if obj is None:
                continue
            collections[group].objects.link(obj)
            if obj.parent is None:
                obj.parent = root
            obj["source_asset_id"] = a["id"]
        root["source_sha256"] = a.get("sha256", "")
        root["canon_status"] = "reviewed-placement"
    cam = data["camera"]
    camera = bpy.data.objects.new("LIND_MASTER_CAMERA", bpy.data.cameras.new("LIND_MASTER_CAMERA"))
    bpy.context.scene.collection.objects.link(camera)
    camera.location = Vector(cam["position"])
    camera.rotation_euler = cam["rotation_euler"]
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = float(cam["ortho_scale"])
    bpy.context.scene.camera = camera
    bpy.context.scene["layout_sha256"] = hashlib.sha256(raw).hexdigest()
    bpy.context.scene["map_source_sha256"] = data["source_map_sha256"]
    bpy.context.scene["units_per_world_px"] = float(data["units_per_world_px"])
    output = pathlib.Path(opt.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()))
    print("LIND_SPATIAL_ASSEMBLY_PASS", output)

if __name__ == "__main__":
    main()
