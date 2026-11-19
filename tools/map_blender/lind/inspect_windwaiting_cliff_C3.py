"""Reopen cliff C3 and verify the body, outputs and reference provenance."""
import argparse
import hashlib
import json
import statistics
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from build_windwaiting_cliff_C3 import BLOCKS, BODY, CG_SHA, COAST, DEEP, HEADLANDS, crest_height, crown_radius, make_section, shoreline


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connected_components(surface):
    remaining = set(surface.verts)
    components = 0
    while remaining:
        components += 1
        queue = [remaining.pop()]
        while queue:
            vertex = queue.pop()
            for edge in vertex.link_edges:
                other = edge.other_vert(vertex)
                if other in remaining:
                    remaining.remove(other)
                    queue.append(other)
    return components


def inspect_mesh(mesh):
    surface = bmesh.new()
    try:
        surface.from_mesh(mesh)
        counts = {
            "vertices": len(surface.verts),
            "edges": len(surface.edges),
            "faces": len(surface.faces),
            "connected_components": connected_components(surface),
            "boundary_edges": sum(edge.is_boundary for edge in surface.edges),
            "nonmanifold_edges": sum(not edge.is_manifold for edge in surface.edges),
            "inconsistent_edges": sum(not edge.is_contiguous for edge in surface.edges),
            "zero_area_faces": sum(face.calc_area() < 1e-12 for face in surface.faces),
            "signed_volume": surface.calc_volume(signed=True),
        }
    finally:
        surface.free()

    mesh.calc_loop_triangles()
    triangles = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    triangle_vertices = [set(tri) for tri in triangles]
    vertices = [vert.co for vert in mesh.vertices]
    bvh = BVHTree.FromPolygons(vertices, triangles, all_triangles=True)
    counts["triangles"] = len(triangles)
    counts["intersecting_nonadjacent_triangle_pairs"] = sum(
        a < b and triangle_vertices[a].isdisjoint(triangle_vertices[b])
        for a, b in bvh.overlap(bvh)
    )
    counts["bounds"] = {
        "min": [min(v[axis] for v in vertices) for axis in range(3)],
        "max": [max(v[axis] for v in vertices) for axis in range(3)],
    }
    return counts


def exposure(mesh):
    # Clip each tessellated triangle at the provisional water plane. Winding
    # and the original triangle normal survive clipping.
    sums = dict(exposed=0., downward=0., total=0., downward_total=0., inland_steep=0., coast_steep=0.)
    for tri in mesh.loop_triangles:
        points = [mesh.vertices[index].co.copy() for index in tri.vertices]
        n = tri.normal
        sums["total"] += tri.area
        if n.z < -1e-5:
            sums["downward_total"] += tri.area
        clipped = []
        for a,b in zip(points,points[1:]+points[:1]):
            if a.z >= 0:
                clipped.append(a)
            if (a.z >= 0) != (b.z >= 0):
                clipped.append(a.lerp(b,a.z/(a.z-b.z)))
        if len(clipped) < 3:
            continue
        area = sum((clipped[i]-clipped[0]).cross(clipped[i+1]-clipped[0]).length * .5
                   for i in range(1,len(clipped)-1))
        sums["exposed"] += area
        if n.z < -1e-5:
            sums["downward"] += area
        if math.cos(math.radians(100)) <= n.z <= math.cos(math.radians(60)):
            sums["inland_steep" if n.y > 0 else "coast_steep"] += area
    sums["inland_steep_over_coast_steep"] = sums["inland_steep"]/sums["coast_steep"]
    sums["exposed_downward_fraction"] = sums["downward"]/sums["exposed"]
    sums["whole_solid_downward_fraction"] = sums["downward_total"]/sums["total"]
    return sums


def check_outputs(root):
    files = {}
    for name in ("windwaiting_cliff_C3_UNAPPROVED.blend", "front.png", "left.png", "right.png",
                 "elevated.png", "sunset.png", "comparison.png"):
        path = root / name
        assert path.stat().st_size > 0, path
        entry = {"bytes": path.stat().st_size, "sha256": digest(path)}
        if path.suffix == ".png":
            image = bpy.data.images.load(str(path.resolve()), check_existing=False)
            try:
                width, height = image.size
                assert len(image.pixels) == width * height * 4
                if name != "comparison.png":
                    assert (width, height) == (1200, 760), (name, width, height)
                    center = ((height // 2) * width + width // 2) * 4
                    assert image.pixels[0:4] != image.pixels[center:center + 4]
                entry["size"] = [width, height]
            finally:
                bpy.data.images.remove(image)
        files[name] = entry
    return files


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument("--out", type=Path, required=True)
    arguments.add_argument("--reference", type=Path, required=True)
    args = arguments.parse_args()
    assert tuple(bpy.app.version) == (5, 2, 4)
    assert digest(args.reference) == CG_SHA
    root = args.out.resolve()
    blend = root / "windwaiting_cliff_C3_UNAPPROVED.blend"
    assert bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False) == {"FINISHED"}
    scene = bpy.context.scene
    assert scene["coordinate_space"] == "asset-local-provisional"
    assert scene["unit_scale_status"] == "UNAPPROVED"
    source = Path(__file__).with_name("build_windwaiting_cliff_C3.py")
    assert scene["producer_script_sha256"] == digest(source)
    obj = bpy.data.objects[BODY]
    assert len(obj.modifiers) == 0 and obj.type == "MESH"
    mesh = inspect_mesh(obj.data)
    separate = {
        name: len(bpy.data.collections[name].objects)
        for name in ("02 | Detached sea stacks", "03 | Talus modules", "05 | Waterline reef modules")
    }
    assert all(separate.values())
    height = mesh["bounds"]["max"][2]
    widths = [hi-lo for lo,hi,_,_,_ in BLOCKS]
    gaps = [b-a for a,b in zip(DEEP, DEEP[1:])]
    headlands = [dict(x=x, width=width, radius=crown_radius(x), height=crest_height(x)) for x,_,_,width in HEADLANDS]
    coast = {
        "headlands": headlands,
        "surface_area": exposure(obj.data),
        "principal_facet_widths_local": widths,
        "minimum_facet_width_over_cliff_height": min(widths)/height,
        "deep_joint_fraction": len(DEEP)/(len(BLOCKS)-1),
        "deep_joint_spacing_cv_population": statistics.pstdev(gaps)/statistics.mean(gaps),
        "cove_recession": shoreline(-1.8)-max(shoreline(-6.3),shoreline(2.6)),
        "highest_cap_z": max(z for x in (COAST[0][0],COAST[-1][0]) for _, z in make_section(x)),
        "maximum_foreshore_projection": max(shoreline(x)-make_section(x)[-3][0] for x in (COAST[0][0] + i*.1 for i in range(401))),
    }
    assert min(widths)>=1.5 and max(widths)<=3.5
    assert coast["minimum_facet_width_over_cliff_height"]>=.2
    assert .2 <= coast["deep_joint_fraction"] <= .3 and coast["deep_joint_spacing_cv_population"]>=.5
    assert coast["cove_recession"] > 1 and coast["highest_cap_z"] < 0
    assert len(headlands) >= 3 and all(h["radius"]/h["width"] >= .3 for h in headlands)
    assert all(a["height"] > b["height"] for a,b in zip(headlands,headlands[1:]))
    assert coast["maximum_foreshore_projection"] <= .36
    contacts = {}
    rock_families = set()
    for name in ("02 | Detached sea stacks", "03 | Talus modules"):
        for module in bpy.data.collections[name].objects:
            rock_families.add(module["shape_family"])
            zs = [(module.matrix_world @ vertex.co).z for vertex in module.data.vertices]
            lower, upper = min(zs), max(zs)
            if name.startswith("02"):
                ratio = (upper-lower)/height
                assert lower < 0 < upper and ratio >= .4
                contacts[module.name] = {"mode":"crosses_provisional_sea_datum","min_z":lower,"height_ratio":ratio}
            else:
                x,y = module.location.xy
                seed = module["support_z"]
                hit, point, normal, _ = obj.ray_cast(Vector((x,y,seed+.04)),Vector((0,0,-1)),distance=.1)
                assert hit and normal.z >= .5 and -.06 <= point.z <= .34 and lower <= point.z < upper and upper > .05, (module.name, lower, upper, point.z)
                contacts[module.name] = {"mode":"body_ray_hit_inside_vertical_rock_span","support_z":point.z,"support_normal_z":normal.z,"min_z":lower,"max_z":upper}
    assert len(contacts) == 17 and len(rock_families) >= 3
    for module in bpy.data.collections["05 | Waterline reef modules"].objects:
        zs = [(module.matrix_world @ vertex.co).z for vertex in module.data.vertices]
        assert min(zs) < 0 < max(zs)
        contacts[module.name] = {"mode":"reef_crosses_provisional_sea_datum","min_z":min(zs),"max_z":max(zs)}
    assert len(contacts) == 29
    report = {
        "blender": bpy.app.version_string,
        "runtime": "PyPI bpy wheel, CPU Cycles",
        "coordinate_space": scene["coordinate_space"],
        "unit_scale_status": scene["unit_scale_status"],
        "source_cg_sha256": CG_SHA,
        "producer_script_sha256": digest(source),
        "mesh": mesh,
        "coast": coast,
        "module_contacts": contacts,
        "shape_families": sorted(rock_families),
        "separate_module_counts": separate,
        "files": check_outputs(root),
        "reopen": "PASS",
        "png_decode": "PASS",
        "G1": "BLOCKED",
        "G2": "NOT_RUN",
        "G4": "NOT_RUN",
    }
    for key in ("boundary_edges", "nonmanifold_edges", "inconsistent_edges", "zero_area_faces",
                "intersecting_nonadjacent_triangle_pairs"):
        assert mesh[key] == 0, (key, mesh[key])
    assert mesh["connected_components"] == 1 and mesh["signed_volume"] > 0
    area = coast["surface_area"]
    report["art_numeric_proxies"] = {
        "inland_steep_below_ten_percent": area["inland_steep_over_coast_steep"] < .10,
        "exposed_downward_at_most_fifteen_percent": area["exposed_downward_fraction"] <= .15,
        "whole_solid_downward_at_most_fifteen_percent": area["whole_solid_downward_fraction"] <= .15,
    }
    report["G3_structural_subset"] = "PASS"
    report["G3"] = "NOT_RUN"
    (root / "qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
