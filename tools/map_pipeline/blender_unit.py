"""Read-only candidate partition. No terrain/route generation or art judgement."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--unit', choices=['WORLD', 'ROUTE'], required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    cfg = json.loads(Path('tools/map_pipeline/tasks.json').read_text())
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    routes = sorted((o for o in scene.objects if o.type == 'MESH' and o.name.startswith('Village_to_')), key=lambda o: o.name)
    assert len(routes) == 4, 'expected four baseline routes'
    meshes = [o for o in scene.objects if o.type == 'MESH']
    owned = routes if a.unit == 'ROUTE' else [o for o in meshes if o not in routes]
    assert owned
    assert all(len(o.data.vertices) and len(o.data.polygons) for o in owned)
    assert all(math.isfinite(c) for o in meshes for v in o.data.vertices for c in v.co), 'nonfinite vertex'
    packed = [hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file]
    assert cfg['original_sha256'] in packed, 'packed original SHA mismatch'
    rows = []
    if a.unit == 'ROUTE':
        supports = [bpy.data.objects[n] for n in ['CONTINUOUS_TERRAIN_coast_river_upland', 'East_bridge_candidate_single_arch']]
        trees = [BVHTree.FromPolygons([o.matrix_world @ v.co for v in o.data.vertices], [list(p.vertices) for p in o.data.polygons]) for o in supports]
        for o in routes:
            vs = [o.matrix_world @ v.co for v in o.data.vertices]
            assert len(vs) % 2 == 0
            centers = [(vs[i] + vs[i+1]) * .5 for i in range(0, len(vs), 2)]
            angles = [math.degrees(math.atan2(abs((b-a).z), math.hypot((b-a).x, (b-a).y))) for a, b in zip(centers, centers[1:])]
            gaps = []
            for i in range(0, len(vs), 2):
                for pt in (vs[i], centers[i//2], vs[i+1]):
                    hits = [t.ray_cast(Vector((pt.x, pt.y, 100)), Vector((0, 0, -1)), 200)[0] for t in trees]
                    heights = [h.z for h in hits if h is not None]
                    assert heights, 'missing support sample'
                    gaps.append(pt.z - max(heights))
            row = {'route': o.name, 'samples': len(gaps), 'min_gap': min(gaps), 'max_gap': max(gaps), 'max_grade_degrees': max(angles)}
            rows.append(row)
            assert min(gaps) >= -cfg['limits']['burial_tolerance'], str(row)
            assert max(angles) < cfg['limits']['grade_degrees'], str(row)
    # WORLD artifact contains no route mesh; ROUTE retains WORLD as explicit QA/render context.
    if a.unit == 'WORLD':
        for o in routes:
            bpy.data.objects.remove(o, do_unlink=True)
    scene.camera = bpy.data.objects[cfg['render']['camera']]
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.use_denoising = False
    scene.cycles.samples = cfg['render']['samples']
    scene.cycles.seed = 0
    scene.render.resolution_x = cfg['render']['width']
    scene.render.resolution_y = cfg['render']['height']
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = str(out / 'preview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'unit.blend'))
    bpy.ops.render.render(write_still=True)
    assert (out / 'preview.png').read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
    report = {'unit': a.unit, 'blender': bpy.app.version_string, 'G1': 'SOURCE_BYTES_PASS_FULL_REVIEW_BLOCKED', 'G2': 'FAIL_INHERITED_CANDIDATE_D_NO_NEW_IMAGE_EVALUATION', 'G3': 'PASS', 'G3_scope': 'finite mesh, packed source, render; ROUTE sampled clearance and provisional grade only', 'G4': 'NOT_RUN', 'owned_objects': [o.name for o in owned], 'routes': rows, 'limits': ['unscaled candidate', 'support engineering, junctions, unsampled interiors, collision/navmesh unverified', 'ROUTE blend includes immutable WORLD context; do not append both complete scenes']}
    (out / 'qa.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
