#!/usr/bin/env python3
"""Build a NON-METRIC Rilde source-review .blend, not a production terrain.

Run with Blender 4.x: blender -b -t 2 --python tools/map_blender/build_lind_source_review.py -- --image /absolute/path/original.png --output /absolute/path/review.blend
No world geometry or placement is inferred from the illustration.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

APPROVED_SHA = "abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620"
COLLECTIONS = ("LIND_TERRAIN", "LIND_WATER", "LIND_ROADS", "LIND_HERO_HOME",
               "LIND_BUILDINGS", "LIND_ECOLOGY", "LIND_STORY_MARKERS")
REQUIRED = ("village_center", "harbor_sw", "windward_cliffs_wnw",
            "north_farms", "road_to_dunvall", "east_river_bridge",
            "raid_riverside_cliff", "downstream_landing", "moss_forest", "ancient_altar")

def validate_inputs(image, graph):
    if hashlib.sha256(image.read_bytes()).hexdigest() != APPROVED_SHA:
        raise ValueError("G1 BLOCKED: source image bytes differ from director-approved PNG")
    data = json.loads(graph.read_text(encoding="utf-8"))
    if data["source"]["sha256"] != APPROVED_SHA:
        raise ValueError("G1 BLOCKED: topology source hash differs")
    if any(value is not None for value in data["metric"].values()):
        raise ValueError("G1 BLOCKED: unapproved world metric")
    ids = {n["id"] for n in data["nodes"]}
    if not set(REQUIRED).issubset(ids):
        raise ValueError("G1 BLOCKED: required semantic node missing")
    jumps = [e for e in data["edges"] if e["kind"] == "story_jump"]
    if len(jumps) != 1 or (jumps[0]["from"], jumps[0]["to"], jumps[0]["bidirectional"]) != (
            "raid_riverside_cliff", "downstream_landing", False):
        raise ValueError("G1 BLOCKED: river raid transition incorrect")
    return data

def build(image, graph, output):
    import bpy
    data = validate_inputs(image, graph)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for col in list(bpy.data.collections):
        if col.users == 0:
            bpy.data.collections.remove(col)
    scene = bpy.context.scene
    scene["asset_status"] = "SOURCE_REVIEW_ONLY_NOT_PRODUCTION"
    scene["approved_source_sha256"] = APPROVED_SHA
    scene["metric_approval"] = "BLOCKED"
    scene["art_qa"] = "NOT_RUN"
    scene["game_qa"] = "NOT_RUN"
    scene["topology_schema"] = data["schema"]
    scene["blender_version"] = bpy.app.version_string
    for name in COLLECTIONS:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
        col["source_sha256"] = APPROVED_SHA
        col["geometry_status"] = "NOT_STARTED"
    # The approved image is a reference in the Image Editor, NOT a textured
    # terrain plane. This prevents mistaking illustration pixels for meters.
    ref = bpy.data.images.load(str(image.resolve()), check_existing=True)
    ref.pack()
    ref["source_sha256"] = APPROVED_SHA
    ref["role"] = "APPROVED_VISUAL_REFERENCE_NOT_METRIC"
    for node in data["nodes"]:
        marker = bpy.data.objects.new("SEMANTIC_" + node["id"], None)
        marker.empty_display_type = "PLAIN_AXES"
        marker.hide_viewport = True
        marker.hide_render = True
        marker["node_id"] = node["id"]
        marker["zone"] = node["zone"]
        marker["world_transform_approved"] = False
        marker["position_status"] = "UNPLACED"
        marker["source_sha256"] = APPROVED_SHA
        scene.collection.children["LIND_STORY_MARKERS"].objects.link(marker)
    scene["directed_edges_json"] = json.dumps(data["edges"], ensure_ascii=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output.resolve()))
    print("SOURCE_REVIEW_PASS: packed PNG, 7 modular collections, semantic nodes, no approved geometry")
    print("OUTPUT:", output.resolve())

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--graph", type=Path, default=Path(__file__).resolve().parents[2] / "docs/production/lind-new-world-topology.v1.json")
    parser.add_argument("--output", required=True, type=Path)
    ns = parser.parse_args(args)
    build(ns.image, ns.graph, ns.output)

if __name__ == "__main__":
    main()
