"""Reopen cliff C7 and verify the body, outputs and reference provenance."""
import argparse
import hashlib
import json
import statistics
import struct
import math
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from mathutils.bvhtree import BVHTree

from build_windwaiting_cliff_C7 import BLOCKS, BODY, CG_SHA, COAST, DEEP, HEADLANDS, crest_height, crown_radius, make_section, shoreline


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


def seam_snapshot(mesh, side):
    result = {}
    for p in mesh.polygons:
        if len(p.vertices)!=4:
            continue
        for index in p.loop_indices:
            point = mesh.vertices[mesh.loops[index].vertex_index].co
            if abs(point.x-side)>1e-5:
                continue
            uv = mesh.uv_layers.active.uv[index].vector
            normal = mesh.corner_normals[index].vector
            key = (round(point.y,5),round(point.z,5))
            result.setdefault(key,set()).add(tuple(round(x,4) for x in (*uv,*normal)))
    return result


def variants_qa():
    objects = [bpy.data.objects[f"Cliff C7 {label} | joinable coastal segment"] for label in "ABC"]
    bounds = [v for v,_ in COAST]
    pairs = {}
    records = {}
    for label,obj in zip("ABC",objects):
        metrics = inspect_mesh(obj.data)
        assert metrics["connected_components"]==1
        for key in ("boundary_edges","nonmanifold_edges","intersecting_nonadjacent_triangle_pairs","zero_area_faces","inconsistent_edges"):
            assert metrics[key]==0, (label,key,metrics[key])
        h = hashlib.sha256()
        for vertex in obj.data.vertices:
            h.update(struct.pack("<3f",*vertex.co))
        for poly in obj.data.polygons:
            topology = tuple(poly.vertices)
            h.update(struct.pack("<I",len(topology)))
            h.update(struct.pack(f"<{len(topology)}I",*topology))
        # Check the plateau at a common Y using the reopened mesh. Span is
        # identical between variants, but the interior raster must differ.
        slope = 0.
        for edge,direction in ((bounds[0],1),(bounds[1],-1)):
            prior = None
            for j in range(81):
                x = edge+direction*(.0005+j*.1)
                hit,point,_,_ = obj.ray_cast(Vector((x,10,20)),Vector((0,0,-1)))
                assert hit
                if prior is not None:
                    slope=max(slope,math.degrees(math.atan(abs(point.z-prior)/.1)))
                prior=point.z
        assert slope <= 5, (label,slope)
        records[label] = {"geometry_sha256":h.hexdigest(),"max_8_unit_transition_slope_degrees_at_y10":slope,
                          "classification":"unapproved review candidate","mesh":metrics}
    assert len({r["geometry_sha256"] for r in records.values()})==3
    for tag,a,b in zip(("A-B","B-C"),objects,objects[1:]):
        left,right = seam_snapshot(a.data,bounds[1]),seam_snapshot(b.data,bounds[0])
        assert left.keys()==right.keys() and len(left)==85
        assert abs((b.location.x-a.location.x)-40)<1e-6
        max_angle=0.
        for key in left:
            for origins,targets,period in ((left[key],right[key],1),(right[key],left[key],-1)):
                for origin in origins:
                    compatible = [t for t in targets if abs(origin[0]-t[0]-period)<1e-4 and abs(origin[1]-t[1])<1e-4]
                    assert compatible
                    angle = min(math.degrees(Vector(origin[2:]).angle(Vector(t[2:]))) for t in compatible)
                    max_angle = max(max_angle,angle)
        assert max_angle < .3
        pairs[tag]={"paired_vertices":85,"max_normal_delta_degrees":max_angle,"u_period":1}
    return records,pairs


def inland_and_view(scene):
    land=bpy.data.objects["Independent inland heightfield"]
    rms=[]
    for y in (52,70,90):
        differences=[]
        for x in range(-45,22,3):
            p=[]
            for px in (x,x+40):
                hit,pt,_,_=land.ray_cast(Vector((px,y,20)),Vector((0,0,-1)))
                assert hit
                p.append(pt.z)
            differences.append(p[1]-p[0])
        rms.append(math.sqrt(statistics.mean(v*v for v in differences)))
    assert min(rms)>.10, rms
    camera=bpy.data.objects["cg_review"]
    local=[]
    for x in (-6.3,2.6,10.6):
        section=make_section(x)
        y,z=section[17]
        top=world_to_camera_view(scene,camera,Vector((x,y,z)))
        base=world_to_camera_view(scene,camera,Vector((x,y,0)))
        local.append({"x":x,"cliff_screen_height_fraction":abs(top.y-base.y),"crest_in_frame":0<top.x<1 and 0<top.y<1})
    assert any(v["crest_in_frame"] and v["cliff_screen_height_fraction"]>=.2 for v in local), local
    return {"inland_40_unit_shift_rms_by_y_52_70_90":rms,"cg_projected_cliff_heights":local,
            "shelf_designed_window_lengths_local":[11.4,12.5,13.3,11.1,14.7,16.1],
            "shelf_nominal_projection_local":.225,"shelf_legibility":"INDEPENDENT_REVIEW_PENDING"}


def headland_visibility(scene, body):
    camera = bpy.data.objects["cg_review"]
    origin = camera.matrix_world.translation
    graph = bpy.context.evaluated_depsgraph_get()
    output = []
    for label, x in (("near",-6.8),("middle",2.6),("far",9.2)):
        samples, in_frame, visible = 0, 0, 0
        for dx in (-.5,-.25,0,.25,.5):
            for z in (.9,1.8,2.9,4.1):
                found, point, _, _ = body.ray_cast(Vector((x+dx,-29,z)),Vector((0,1,0)),distance=55)
                if not found:
                    continue
                samples += 1
                xy = world_to_camera_view(scene,camera,point)
                if xy.z<=0 or not 0<xy.x<1 or not 0<xy.y<1:
                    continue
                in_frame += 1
                delta = point-origin
                hit, obstruction, _, _, obj, _ = scene.ray_cast(
                    graph,origin,delta.normalized(),distance=delta.length+.075)
                visible += int(hit and obj.original==body and (obstruction-point).length<.12)
        output.append({"zone":label,"x":x,"face_samples":samples,"in_frame":in_frame,
                       "unoccluded_face_samples":visible})
    assert all(v["unoccluded_face_samples"] > 0 for v in output), output
    return output


def end_slope_proxy(mesh, exposed_area):
    area = 0.
    for tri in mesh.loop_triangles:
        if abs(tri.center.x-COAST[0][0]) > 2 and abs(tri.center.x-COAST[-1][0]) > 2:
            continue
        if tri.center.z > 0 and .5 <= tri.normal.z <= math.cos(math.radians(20)):
            area += tri.area
    return area/exposed_area


def check_outputs(root):
    files = {}
    for name in ("windwaiting_cliff_C7_UNAPPROVED.blend", "front.png", "left.png", "right.png",
                 "elevated.png", "sunset.png", "shore_detail.png", "cg_review.png", "comparison.png"):
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
    blend = root / "windwaiting_cliff_C7_UNAPPROVED.blend"
    assert bpy.ops.wm.open_mainfile(filepath=str(blend), use_scripts=False) == {"FINISHED"}
    scene = bpy.context.scene
    assert scene["coordinate_space"] == "asset-local-provisional"
    assert scene["unit_scale_status"] == "UNAPPROVED"
    source = Path(__file__).with_name("build_windwaiting_cliff_C7.py")
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
    assert coast["cove_recession"] >= 3
    assert len(headlands) == 3
    assert all(a["height"] > b["height"] for a,b in zip(headlands,headlands[1:]))
    assert coast["maximum_foreshore_projection"] <= .36
    coast["end_slope_geometric_proxy_fraction"] = end_slope_proxy(obj.data,coast["surface_area"]["exposed"])
    assert coast["end_slope_geometric_proxy_fraction"] <= .05
    variants,boundary = variants_qa()
    inland = inland_and_view(scene)
    # Compare the actual cliff intercept to the plan edge at each height.
    # Orthogonal seaward rays reach the front without touching the inland skirt.
    sculpt = []
    for center,_,_,_ in HEADLANDS:
        levels = []
        for z in (1.05,2.15,3.35,4.35):
            offsets = []
            for sample in range(17):
                x = center-1.6+.2*sample
                hit, point, _, _ = obj.ray_cast(Vector((x,-26,z)),Vector((0,1,0)),distance=42)
                assert hit
                offsets.append(point.y-shoreline(x))
            levels.append({"z":z,"face_offsets_local":offsets,
                           "relief_range_local":max(offsets)-min(offsets)})
        sculpt.append({"headland_x":center,"reopened_ray_levels":levels})
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
                assert hit and normal.z >= .5 and -.06 <= point.z <= .91 and lower <= point.z < upper and upper > .05, (module.name, lower, upper, point.z)
                contacts[module.name] = {"mode":"body_ray_hit_inside_vertical_rock_span","support_z":point.z,"support_normal_z":normal.z,"min_z":lower,"max_z":upper}
    assert len(contacts) == 17 and len(rock_families) >= 3
    for module in bpy.data.collections["05 | Waterline reef modules"].objects:
        zs = [(module.matrix_world @ vertex.co).z for vertex in module.data.vertices]
        assert min(zs) < 0
        contacts[module.name] = {"mode":"reef_crosses_provisional_sea_datum" if max(zs)>0 else "reef_submerged","min_z":min(zs),"max_z":max(zs)}
    assert len(contacts) == 61 and any(x["mode"]=="reef_submerged" for x in contacts.values())
    report = {
        "blender": bpy.app.version_string,
        "runtime": "PyPI bpy wheel, CPU Cycles",
        "coordinate_space": scene["coordinate_space"],
        "unit_scale_status": scene["unit_scale_status"],
        "source_cg_sha256": CG_SHA,
        "producer_script_sha256": digest(source),
        "mesh": mesh,
        "coast": coast,
        "sculpt_samples": sculpt,
        "cg_review_visibility_samples": headland_visibility(scene,obj),
        "module_boundary": boundary,
        "variants": variants,
        "inland_and_view": inland,
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
        "end_slope_geometric_proxy_at_most_five_percent": coast["end_slope_geometric_proxy_fraction"] <= .05,
    }
    assert area["exposed_downward_fraction"] <= .15
    report["G3_structural_subset"] = "PASS"
    report["G3"] = "NOT_RUN"
    (root / "qa.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
