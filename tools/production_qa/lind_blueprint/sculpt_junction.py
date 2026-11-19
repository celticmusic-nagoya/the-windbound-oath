"""Carve a continuous bedrock junction on a separate C10 candidate copy."""
import argparse
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_blueprint import sha, write

SOURCE_SHA = "8d0618ddd9db7562492e94477503ed53b621e908d88ab34c7bd07afb0c159223"
TARGET = "Cliff C8 B | joinable coastal segment"
DETACHED = ("C10 large rock 02", "C10 large rock 03")
# Authored angled fracture rails anchored to measured landmarks of rocks 02/03.
# bottom to top: X, Z, half-width, inland cut depth.
RAILS = (
    ((-7.35, 0.95, .09, .32), (-7.47, 2.35, .19, .59), (-7.98, 4.80, .28, .87),
     (-8.24, 6.95, .36, .80)),
    ((-5.42, 2.30, .10, .30), (-5.72, 3.62, .18, .65), (-5.97, 5.05, .27, .69),
     (-5.67, 6.80, .21, .64)),
)
GUARD = (-9.0, -4.9)


def cutter(scene, carrier, number, rail):
    """V-notch tool with a narrow floor and uneven vertical return."""
    positions = [carrier.matrix_world @ vert.co for vert in carrier.data.vertices]
    tree = KDTree(len(positions))
    for index, point in enumerate(positions):
        tree.insert((point.x, 0, point.z), index)
    tree.balance()
    vertices = []
    for x, z, half, depth in rail:
        lookup_z = min(z, 5.4)
        neighbors = tree.find_n((x, 0, lookup_z), 12)
        surface = min(positions[index].y for _, index, _ in neighbors)
        vertices.extend(((x-half, surface-1.7, z), (x+half, surface-1.7, z),
                         (x+half*.13, surface+depth, z), (x-half*.26, surface+depth*.82, z)))
    faces = [(3, 2, 1, 0), (12, 13, 14, 15)]
    faces.extend((4*i+j, 4*i+(j+1)%4, 4*(i+1)+(j+1)%4, 4*(i+1)+j)
                 for i in range(3) for j in range(4))
    mesh = bpy.data.meshes.new(f"Junction fracture {number} cutter")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    cut = bpy.data.objects.new(mesh.name, mesh)
    scene.collection.objects.link(cut)
    return cut


def mesh_stats(obj):
    mesh = obj.data
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        result = {"vertices": len(bm.verts), "faces": len(bm.faces),
                  "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
                  "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
                  "degenerate_faces": sum(face.calc_area() <= 1e-12 for face in bm.faces)}
    finally:
        bm.free()
    mesh.calc_loop_triangles()
    world = [tuple(obj.matrix_world @ v.co) for v in mesh.vertices]
    tris = [tuple(tri.vertices) for tri in mesh.loop_triangles
            if min(world[i][0] for i in tri.vertices) < GUARD[1]
            and max(world[i][0] for i in tri.vertices) > GUARD[0]]
    bvh = BVHTree.FromPolygons(world, tris, all_triangles=True)
    result["local_self_contacts"] = sum(
        a < b and not set(tris[a]).intersection(tris[b]) for a, b in bvh.overlap(bvh))
    return result, {point for point in world if not GUARD[0] <= point[0] <= GUARD[1]}


def render_views(scene, output):
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 65
    scene.render.image_settings.file_format = "PNG"
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 4
    for name in ("cg_review", "front", "shore_detail"):
        scene.camera = scene.objects[name]
        scene.render.filepath = str(output / f"{name}.png")
        bpy.ops.render.render(write_still=True)
    clay = bpy.data.materials.new("Junction review clay")
    clay.diffuse_color = (.34, .34, .34, 1)
    bpy.context.view_layer.material_override = clay
    scene.camera = scene.objects["cg_review"]
    scene.render.filepath = str(output / "cg_review_clay.png")
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("repository", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = args.source.resolve()
    out = args.output.resolve()
    if bpy.app.version != (5, 3, 0) or sha(source) != SOURCE_SHA or out in source.parents:
        raise ValueError("Invalid locked source, output, or runtime")
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    carrier = scene.objects[TARGET]
    before, outside_before = mesh_stats(carrier)
    for name in DETACHED:
        scene.objects[name].hide_render = True
        scene.objects[name].hide_set(True)
    for number, rail in enumerate(RAILS, start=1):
        tool = cutter(scene, carrier, number, rail)
        mod = carrier.modifiers.new(f"Authored fracture {number}", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.solver = "EXACT"
        mod.object = tool
        bpy.context.view_layer.objects.active = carrier
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(tool, do_unlink=True)
    bpy.context.view_layer.update()
    after, outside_after = mesh_stats(carrier)
    sys.path.insert(0, str(args.repository / "tools/map_blender/lind"))
    from inspect_windwaiting_cliff_C8 import headland_visibility
    try:
        visibility = headland_visibility(scene, carrier)
    except AssertionError as error:
        visibility = error.args[0]
    changed_outside = len(outside_before.symmetric_difference(outside_after))
    h = [row["unoccluded_face_samples"] for row in visibility]
    checks = {"boundary_vertices_unchanged": not changed_outside,
              "closed_carrier": not (after["nonmanifold_edges"] or after["boundary_edges"]),
              "no_degenerate_faces": not after["degenerate_faces"],
              "no_new_local_self_contacts": after["local_self_contacts"] <= before["local_self_contacts"],
              "near_middle_far_visibility": len(h) == 3 and all(a >= b for a, b in zip(h, (10, 4, 13))),
              "changed_topology": after["faces"] != before["faces"],
              "original_sha_intact": sha(source) == SOURCE_SHA}
    scene["candidate"] = "C10_JUNCTION_SUBTRACTIVE_FRACTURE_UNAPPROVED"
    scene["junction_source_sha256"] = SOURCE_SHA
    destination = out / "junction_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    write(out / "qa.json", {"source_sha256": SOURCE_SHA, "candidate_sha256": sha(destination),
                            "target": TARGET, "hidden_candidate_objects": DETACHED,
                            "fractures": RAILS, "guard_x": GUARD, "before": before, "after": after,
                            "changed_outside_vertices": changed_outside, "visibility": visibility,
                            "checks": checks, "G1": "BLOCKED", "G2": "NOT_RUN",
                            "G3": "BLOCKED" if all(checks.values()) else "FAIL", "G4": "NOT_RUN"})
    print("JUNCTION_CHECKS", json.dumps(checks, sort_keys=True), flush=True)
    render_views(scene, out)
    if not all(checks.values()):
        raise RuntimeError("Junction stop condition met; candidate and renders retained for diagnosis")


if __name__ == "__main__":
    main()
