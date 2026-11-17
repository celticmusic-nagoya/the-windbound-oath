"""Create reopenable, unplaced Blender source scenes for SHA-verified CC0 rock candidates.

Candidate-only library assets; not a LIND world placement or adopted cliff.
"""
import argparse
import bpy
import hashlib
import json
import sys
from pathlib import Path


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = Path(args.source).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((source / "source_provenance.json").read_text())
    report = []

    for asset in manifest["assets"]:
        assert asset["status"] == "DOWNLOADED_UNREVIEWED"
        gltf_file = source / asset["file"]
        assert sha256(gltf_file) == asset["sha256"]
        for dep in asset["dependencies"]:
            assert sha256(source / dep["file"]) == dep["sha256"]

        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(gltf_file))
        meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        assert meshes, "No geometry in source glTF"
        materials = {m for obj in meshes for m in obj.data.materials if m}
        assert materials, "No source materials"

        images = json.loads(gltf_file.read_text()).get("images", [])
        dependencies = {dep["uri"]: dep for dep in asset["dependencies"]}
        nodes = [(mat, node) for mat in materials if mat.use_nodes
                 for node in mat.node_tree.nodes if node.type == "TEX_IMAGE" and node.image]
        assert len(nodes) >= 3, "Expected PBR material texture nodes"
        verified = []
        for mat, node in nodes:
            imported = node.image
            candidates = [im for im in images if "uri" in im and (
                imported.name.lower().split(".")[0] in
                (Path(im["uri"]).stem.lower(), im.get("name", "").lower())
                or Path(im["uri"]).stem.lower() in imported.name.lower())]
            assert len(candidates) == 1, "Ambiguous image source for " + imported.name
            uri = candidates[0]["uri"]
            dep = dependencies[uri]
            disk = source / dep["file"]
            assert sha256(disk) == dep["sha256"]
            fresh = bpy.data.images.load(str(disk), check_existing=False)
            assert len(fresh.pixels[:4]) == 4 and fresh.has_data
            fresh.colorspace_settings.name = imported.colorspace_settings.name
            node.image = fresh
            fresh.pack()
            assert fresh.packed_file is not None, "Texture not packed"
            verified.append({"material": mat.name, "image": fresh.name,
                             "uri": uri, "sha256": dep["sha256"],
                             "colorspace": fresh.colorspace_settings.name})

        # Preserve original imported transforms and geometry; never invent world meters.
        for obj in meshes:
            obj["asset_status"] = "CC0_CANDIDATE_NOT_ADOPTED"
            obj["source_sha256"] = asset["sha256"]
        scene = bpy.context.scene
        scene["asset_status"] = "UNPLACED_CANDIDATE"
        scene["official_world_metric"] = "UNAPPROVED"
        scene["source_sha256"] = asset["sha256"]
        scene["source_license"] = "CC0"
        path = out / (asset["id"] + "_candidate_source.blend")
        bpy.ops.wm.save_as_mainfile(filepath=str(path), compress=True)
        assert path.is_file() and path.stat().st_size > 0
        report.append({"id": asset["id"], "blend": path.name,
                       "blend_sha256": sha256(path), "source_sha256": asset["sha256"],
                       "meshes": len(meshes), "materials": len(materials),
                       "verified_packed_nodes": verified, "G1": "BLOCKED",
                       "G2": "NOT_RUN", "G3": "SOURCE_PACKAGING_PASS",
                       "G4": "NOT_RUN"})
    (out / "editable_source_manifest.json").write_text(
        json.dumps({"candidates": report, "official_placement": "NOT_RUN"},
                   indent=2) + "\n")
    print("LIND_EDITABLE_SOURCE_PASS", json.dumps(report), flush=True)


if __name__ == "__main__":
    main()
