"""Independent saved-blend checks; authored outside the two production workers.
No art judgement and no inference of metric or gameplay acceptance.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def evaluated_tree(objects):
    vertices, faces = [], []
    deps = bpy.context.evaluated_depsgraph_get()
    for o in objects:
        evaluated = o.evaluated_get(deps)
        mesh = evaluated.to_mesh()
        offset = len(vertices)
        vertices.extend(evaluated.matrix_world @ v.co for v in mesh.vertices)
        mesh.calc_loop_triangles()
        faces.extend([offset + i for i in t.vertices] for t in mesh.loop_triangles)
        evaluated.to_mesh_clear()
    return BVHTree.FromPolygons(vertices, faces, all_triangles=True) if faces else None


def hit_z(tree, p):
    if tree is None:
        return None
    hit = tree.ray_cast(Vector((p.x, p.y, 1000)), Vector((0, 0, -1)), 2000)[0]
    return hit.z if hit is not None else None


def points_on_mesh(o):
    m = o.data
    m.calc_loop_triangles()
    for t in m.loop_triangles:
        a, b, c = [o.matrix_world @ m.vertices[i].co for i in t.vertices]
        # All vertices, edge midpoints, centroid and three strictly interior locations.
        yield from [a, b, c, (a+b)*.5, (a+c)*.5, (b+c)*.5, (a+b+c)/3,
                    a*.6+b*.2+c*.2, a*.2+b*.6+c*.2, a*.2+b*.2+c*.6]


def check_mesh(o):
    m = o.data
    m.calc_loop_triangles()
    bm = bmesh.new()
    bm.from_mesh(m)
    bm.normal_update()
    open_edges = sum(not e.is_manifold for e in bm.edges)
    bad_winding = sum(e.is_manifold and not e.is_contiguous for e in bm.edges)
    vol = bm.calc_volume(signed=True) if open_edges == 0 else None
    bm.free()
    geometry = {'vertices': [list(v.co) for v in m.vertices], 'faces': [list(p.vertices) for p in m.polygons], 'matrix_world': [list(row) for row in o.matrix_world]}
    return {'name': o.name, 'geometry_sha256': hashlib.sha256(json.dumps(geometry, sort_keys=True).encode()).hexdigest(), 'vertices': len(m.vertices), 'faces': len(m.polygons),
            'finite': all(math.isfinite(x) for v in m.vertices for x in v.co),
            'degenerate_triangles': sum(t.area < 1e-10 for t in m.loop_triangles),
            'nonmanifold_edges': open_edges, 'inconsistent_winding_edges': bad_winding,
            'signed_volume': vol, 'material_slots': len(m.materials),
            'intentional_open_surface': bool(o.get('qa_surface_open', False))}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--unit', choices=['WORLD', 'ROUTE'], required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    cfg = json.loads((ROOT / 'tools/map_pipeline/production_tasks.json').read_text())
    errors = []
    all_mesh = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    owned = all_mesh if a.unit == 'WORLD' else [o for o in all_mesh if o.name.startswith('ROUTE_')]
    # Explicit owned object list is also allowed for independently authored names.
    iface = json.loads((a.out / 'interface.json').read_text())
    if iface.get('interface_contract_sha256', iface.get('shared_contract_sha256')) != digest(ROOT / cfg['interface']):
        errors.append('shared interface contract SHA mismatch')
    if not owned:
        names = iface.get('owned_objects', [])
        owned = [o for o in all_mesh if o.name in names]
    if not owned:
        errors.append('no independently identifiable owned meshes')
    mesh_rows = [check_mesh(o) for o in owned]
    for row in mesh_rows:
        if not row['finite'] or row['degenerate_triangles'] or not row['faces'] or row['inconsistent_winding_edges']:
            errors.append('invalid geometry: ' + row['name'])
        if row['nonmanifold_edges'] and not row['intentional_open_surface']:
            errors.append('unclassified open/nonmanifold surface: ' + row['name'])
        if row['signed_volume'] is not None and row['signed_volume'] <= 0:
            errors.append('nonpositive closed volume: ' + row['name'])
    packed = [hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file]
    if cfg['original_sha256'] not in packed:
        errors.append('packed original SHA mismatch')
    if digest(ROOT / cfg['source']) != cfg['source_sha256']:
        errors.append('protected candidate D modified')
    image_rows = {}
    for name in cfg['units'][a.unit]['images']:
        path = a.out / name
        if not path.exists():
            errors.append('missing image: ' + name)
            continue
        image = bpy.data.images.load(str(path.resolve()), check_existing=False)
        image_rows[name] = {'sha256': digest(path), 'size': list(image.size)}
        if min(image.size) < 200:
            errors.append('invalid image dimensions: ' + name)
        bpy.data.images.remove(image)
    manifest_path = a.out / 'manifest.json'
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        hashes = manifest.get('files', manifest.get('output_hashes', {}))
        for name, expected in hashes.items():
            target = a.out / name
            if not target.is_file() or digest(target) != expected:
                errors.append('producer manifest SHA mismatch: ' + name)
    else:
        errors.append('producer manifest not present (render stage incomplete)')
    measurements = {}
    if a.unit == 'WORLD':
        rock = [o for o in owned if o.name.startswith('WORLD_INCLINED_BEDROCK_')]
        soil = [o for o in owned if o.name.startswith('WORLD_ROOTED_SOIL_POCKET_')]
        rock_tree = evaluated_tree(rock)
        contacts = []
        if rock_tree:
            for o in soil:
                m = o.data
                m.calc_loop_triangles()
                gaps, raw_gaps, missing, boundary_correspondences = [], [], 0, 0
                source_name = o.get('source_rock')
                source_tree = evaluated_tree([bpy.data.objects[source_name]]) if source_name and source_name in bpy.data.objects else None
                for t in m.loop_triangles:
                    if t.normal.z >= -.1:
                        continue
                    va, vb, vc = [o.matrix_world @ m.vertices[i].co for i in t.vertices]
                    for pt in [va,vb,vc,(va+vb)*.5,(va+vc)*.5,(vb+vc)*.5,(va+vb+vc)/3]:
                        z = hit_z(rock_tree, pt)
                        raw_gap = pt.z-z if z is not None else None
                        if raw_gap is not None:
                            raw_gaps.append(raw_gap)
                        # Vertical rays on exact triangle boundaries can fall through.
                        # Corroborate only an exact offset-surface correspondence to
                        # the named actual bedrock; never smooth or lower a QA limit.
                        nearest = source_tree.find_nearest(pt + Vector((0,0,.025))) if source_tree else None
                        exact_contact = nearest is not None and nearest[0] is not None and nearest[3] <= .0001
                        if (raw_gap is None or raw_gap > .03) and exact_contact:
                            gaps.append(-.025)
                            boundary_correspondences += 1
                        elif raw_gap is None:
                            missing += 1
                        else:
                            gaps.append(raw_gap)
                contacts.append({'name': o.name,'bottom_samples':len(gaps)+missing,'missing_bedrock':missing,'max_unsupported_gap':max(gaps) if gaps else None,'raw_vertical_max_gap':max(raw_gaps) if raw_gaps else None,'ray_boundary_misses_with_exact_offset_surface_contact':boundary_correspondences,'source_rock':source_name})
                if missing or (gaps and max(gaps) > .03):
                    errors.append('soil pocket unsupported interior: ' + o.name)
        measurements = {'soil_bedrock_contact': contacts, 'contact_tolerance':'.03 candidate scene units; nonmetric study threshold', 'boundary_ray_policy':'raw misses retained; accepted only if point+.025Z is within .0001 of named actual source bedrock triangles (independent nearest-surface test)', 'unmeasured':'global rock interpenetrations are intentional assemblage contacts; external/unintended overlap search NOT_RUN'}
    if a.unit == 'ROUTE':
        routes = [o for o in all_mesh if o.name.startswith('Village_to_')]
        supports = [o for o in owned if o.name.startswith(('ROUTE_SUPPORT__', 'ROUTE_ABUTMENT__', 'ROUTE_JUNCTION__'))]
        terrain = [o for o in all_mesh if o.name == 'CONTINUOUS_TERRAIN_coast_river_upland']
        bridge = [o for o in all_mesh if o.name == 'East_bridge_candidate_single_arch']
        support_tree = evaluated_tree(supports)
        terrain_tree = evaluated_tree(terrain + bridge)
        if len(routes) != 4 or support_tree is None:
            errors.append('expected four routes and engineered support')
        rows = []
        for o in routes:
            gaps, burial, missing = [], [], 0
            for pt in points_on_mesh(o):
                z = hit_z(support_tree, pt)
                if z is None:
                    missing += 1
                else:
                    gaps.append(pt.z-z)
                z = hit_z(terrain_tree, pt)
                if z is not None:
                    burial.append(z-pt.z)
            vs = [o.matrix_world @ v.co for v in o.data.vertices]
            centers = [(vs[i]+vs[i+1])*.5 for i in range(0, len(vs)-1, 2)]
            grades = [math.degrees(math.atan2(abs((q-p).z), math.hypot((q-p).x, (q-p).y))) for p,q in zip(centers, centers[1:])]
            row = {'name': o.name, 'samples': len(gaps)+missing, 'missing_support': missing,
                   'min_support_gap': min(gaps) if gaps else None, 'max_support_gap': max(gaps) if gaps else None,
                   'max_terrain_burial': max(burial) if burial else None,
                   'max_candidate_grade_degrees': max(grades) if grades else None}
            rows.append(row)
            if missing or not gaps or min(gaps) < -.015 or max(gaps) > .02:
                errors.append('road support continuity fails: ' + o.name)
            if burial and max(burial) > .015:
                errors.append('road terrain burial: ' + o.name)
            if grades and max(grades) >= 25:
                errors.append('provisional grade exceeds 25 degrees: ' + o.name)
        crossings = []
        coplanar_interior_pairs = []
        for one, other in itertools.combinations(routes, 2):
            tree = evaluated_tree([other])
            diffs = []
            for pt in points_on_mesh(one):
                z = hit_z(tree, pt)
                if z is not None:
                    diffs.append(abs(z-pt.z))
            if diffs:
                crossings.append({'routes': [one.name,other.name], 'overlap_samples': len(diffs), 'max_height_discontinuity': max(diffs)})
            interiors = list(points_on_mesh(one))
            hits = []
            for i, pt in enumerate(interiors):
                if i % 10 < 6:
                    continue
                z = hit_z(tree, pt)
                if z is not None and abs(z-pt.z) < .0005:
                    hits.append(list(pt))
            if hits:
                coplanar_interior_pairs.append({'routes': [one.name, other.name], 'samples': len(hits), 'examples': hits[:3]})
        bad_crossings = [r for r in crossings if r['max_height_discontinuity'] > .03]
        if bad_crossings:
            errors.append('junction overlap height discontinuity > provisional .03')
        if coplanar_interior_pairs:
            errors.append('coplanar overlapping road interiors: visible z-fighting risk')
        joint_surfaces = [o for o in owned if o.name.startswith('ROUTE_JUNCTION__')]
        joint_tree = evaluated_tree(joint_surfaces)
        joint_contacts = []
        if joint_tree:
            for road in routes:
                differences = []
                for pt in points_on_mesh(road):
                    z = hit_z(joint_tree, pt)
                    if z is not None:
                        differences.append(abs(z-pt.z))
                joint_contacts.append({'route': road.name, 'shared_surface_samples': len(differences), 'max_difference': max(differences) if differences else None})
                if differences and max(differences) > .03:
                    errors.append('road/shared-junction seam mismatch: ' + road.name)
        abutments = [o for o in owned if o.name.startswith('ROUTE_ABUTMENT__')]
        bridge_tree = evaluated_tree(bridge)
        contact = [{'name': o.name, 'intersecting_triangle_pairs': len(evaluated_tree([o]).overlap(bridge_tree))} for o in abutments] if bridge_tree else []
        measurements = {'road_triangle_samples': rows, 'junction_overlaps': crossings,
                        'coplanar_road_interior_overlaps': coplanar_interior_pairs,
                        'shared_junction_contacts': joint_contacts,
                        'abutment_bridge_surface_intersections': contact,
                        'abutment_engineering_acceptance': 'NOT_RUN; intersection is not engineering approval',
                        'tolerances': {'support_gap': .02,'burial': .015,'junction_step': .03,'grade_degrees':25,'units':'unapproved candidate scene units'}}
    report = {'schema': 'lind-independent-production-qa/v1', 'reviewer': 'root (not either producer worker)',
              'unit': a.unit, 'blender': bpy.app.version_string, 'blend_sha256': digest(bpy.data.filepath),
              'G1': 'BLOCKED_FULL_SPATIAL_METRIC_EVENT_REVIEW', 'source_bytes': 'PASS' if cfg['original_sha256'] in packed else 'FAIL',
              'G2': 'FAIL_METHOD_FAMILY_STOPPED' if cfg['units'][a.unit].get('art_status', '').startswith('FAIL') else 'NOT_RUN_IMAGE_REVIEW_REQUIRED',
              'G2_evidence': cfg['units'][a.unit].get('art_review'),
              'this_render_image_review': 'NOT_RUN_BY_THIS_SCRIPT; inherited method failures remain locked',
              'G3': 'FAIL' if errors else 'PARTIAL_TESTED_SUBSETS_PASS',
              'technical_gate': 'FAIL' if errors else 'PASS', 'G4': 'NOT_RUN', 'errors': errors,
              'meshes': mesh_rows, 'images': image_rows, 'measurements': measurements,
              'NOT_RUN': ['formal metric/source placement acceptance','global unintended mesh intersection search',
                          'geotechnical/structural loading','collision/navmesh','runtime traversal','performance/Android'],
              'interface_sha256': digest(ROOT / cfg['interface'])}
    (a.out / 'qa.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'unit':a.unit,'technical_gate':report['technical_gate'],'errors':errors}))
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
