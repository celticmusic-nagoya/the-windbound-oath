"""Section-driven sculpt of the playable C8-B cap and seaward bedrock."""
import argparse
import hashlib
import json
from math import exp
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))

from build_windwaiting_cliff_C8 import crest_height, shoreline
import build_windwaiting_cliff_C8 as carrier

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "assets/candidates/lind/windwaiting-cliff-playable"
SOURCE = BASE / "composition-v1/composition_UNAPPROVED.blend"
OBJECT = "Cliff C8 B | joinable coastal segment"
# x, crest uplift, upper platform reach, middle bench reach, lower bench reach.
STATIONS = [
    (-15, 0, 0, 0, 0), (-12, .41, .20, .48, .54),
    (-10.4, .63, .26, .78, .97), (-9.2, .60, .23, .56, 1.02),
    (-8.25, .12, .06, .18, .56), (-7.45, .62, .62, .85, 1.10),
    (-6.45, .62, .62, 1.02, 1.19), (-5.45, .64, .56, .80, 1.02),
    (-4.65, .60, .34, .73, .92), (-3.65, .07, .02, .37, .61),
    (-2.60, -.21, -.04, .13, .28), (-1.55, -.32, -.11, .35, .52),
    (.25, .15, .14, .44, .67), (1.85, .42, .25, .63, .82),
    (3.0, .29, .20, .47, .61), (4.6, .02, .05, .19, .28),
    (6.8, 0, 0, 0, 0),
]


def smooth(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def profile(x):
    for a, b in zip(STATIONS, STATIONS[1:]):
        if a[0] <= x <= b[0]:
            t = smooth((x - a[0]) / (b[0] - a[0]))
            return [u + (v - u) * t for u, v in zip(a[1:], b[1:])]
    return [0] * 4


def edit(point, protected):
    x, y, z = point
    if not STATIONS[0][0] < x < STATIONS[-1][0] or z < .1:
        return point.copy()
    inland = y - shoreline(x)
    distance = protected.find((x, y, 0))[2]
    weight = (1 - smooth((inland - .25) / 2.7)) * smooth((distance - .54) / 1.35)
    height = z / crest_height(x)
    # Retreat at the overhangs, widening into two bedding shelves below.
    rise, cap, middle, toe = profile(x + .54 * (.5 - height))
    upper = smooth((height - .57) / .3)
    mid_shelf = smooth((height - .37) / .10) * (1 - smooth((height - .53) / .11))
    basal_shelf = smooth((height - .08) / .11) * (1 - smooth((height - .28) / .09))
    strata = cap * upper + middle * mid_shelf + toe * basal_shelf
    # Three inclined discontinuities keep the new bedding from reading as a ribbon.
    relief = sum(a * exp(-((x - c - lean * (height - .5)) / width) ** 2)
                 for c, a, width, lean in [(-9.85, .19, .62, .8), (-6.86, .23, .55, -.92), (-4.16, .24, .53, 1.1)])
    y -= weight * (strata - relief * smooth((height - .15) / .18))
    z += weight * rise * smooth((height - .41) / .58)
    return Vector((x, y, z))


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def make_bvh(points, triangles):
    return BVHTree.FromPolygons(points, triangles, all_triangles=True)


def self_contacts(bvh, ids):
    return {(a, b) for a, b in bvh.overlap(bvh) if a < b and not ids[a].intersection(ids[b])}


def section(bvh, x):
    rows = []
    for i in range(1, 84):
        z = i * .1
        p, *_ = bvh.ray_cast(Vector((x, -25, z)), Vector((0, 1, 0)))
        if p is not None:
            rows.append([round(p.y, 5), round(z, 3)])
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    out = parser.parse_args(sys.argv[sys.argv.index("--") + 1:]).output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "hero-cliff_UNAPPROVED.blend").exists()
    assert bpy.app.version == (5, 3, 0)
    carrier.ACTIVE = "B"
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE), load_ui=False)
    obj = bpy.data.objects[OBJECT]
    mesh = obj.data
    mesh.calc_loop_triangles()
    triangles = [tuple(t.vertices) for t in mesh.loop_triangles]
    ids = [set(t) for t in triangles]
    original = [v.co.copy() for v in mesh.vertices]
    nav = json.loads((BASE / "navigation.json").read_text())
    valid = [(nav["origin"][0] + (i % nav["width"]) * nav["stride"],
              -(nav["origin"][1] + (i // nav["width"]) * nav["stride"]))
             for i, level in enumerate(nav["levels"]) if level is not None]
    protected = KDTree(len(valid))
    for i, (x, y) in enumerate(valid):
        protected.insert((x, y, 0), i)
    protected.balance()
    incoming = make_bvh(original, triangles)
    rays = [Vector((x, y, 18)) for x, y in valid]
    down = Vector((0, 0, -1))
    hits = [incoming.ray_cast(ray, down) for ray in rays]
    assert all(hit[0] is not None for hit in hits)
    protected_vertices = {vertex for hit in hits for vertex in triangles[hit[2]]}
    new = [point.copy() if i in protected_vertices else edit(point, protected)
           for i, point in enumerate(original)]
    outgoing = make_bvh(new, triangles)
    contacts_in, contacts_out = self_contacts(incoming, ids), self_contacts(outgoing, ids)
    errors = []
    for ray, hit in zip(rays, hits):
        result, *_ = outgoing.ray_cast(ray, down)
        assert result is not None
        errors.append(abs(hit[0].z - result.z))
    offsets = [b - a for a, b in zip(original, new)]
    assert max(errors) < 1e-5, max(errors)
    assert not contacts_out - contacts_in, len(contacts_out - contacts_in)
    assert not mesh.color_attributes, "The carrier export contract has no vertex colors"
    tessellated = bpy.data.meshes.new("C8-B | terraced promontory")
    tessellated.from_pydata(new, [], triangles)
    for mat in mesh.materials:
        tessellated.materials.append(mat)
    for face, tri in zip(tessellated.polygons, mesh.loop_triangles):
        source_face = mesh.polygons[tri.polygon_index]
        face.material_index = source_face.material_index
        face.use_smooth = source_face.use_smooth
    source_loops = [loop for tri in mesh.loop_triangles for loop in tri.loops]
    for source in mesh.uv_layers:
        uv = tessellated.uv_layers.new(name=source.name)
        for dest_loop, source_loop in zip(uv.data, source_loops):
            dest_loop.uv = source.data[source_loop].uv
    tessellated.update()
    tessellated.normals_split_custom_set([
        mesh.corner_normals[source_loop].vector.copy() if offsets[new_loop.vertex_index].length <= 1e-5
        else (0, 0, 0) for new_loop, source_loop in zip(tessellated.loops, source_loops)
    ])
    obj.data = tessellated

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out / "hero-cliff.glb"), use_selection=True,
                              export_extras=True, export_tangents=True, export_animations=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(out / "hero-cliff_UNAPPROVED.blend"), compress=True)
    QA = {
        "source_sha256": sha(SOURCE), "status": "UNAPPROVED",
        "points": len(new), "triangles": len(triangles),
        "changed_points": sum(d.length > 1e-5 for d in offsets),
        "max_horizontal_change_BU": max(abs(d.y) for d in offsets),
        "max_height_increase_BU": max(d.z for d in offsets), "max_height_decrease_BU": min(d.z for d in offsets),
        "station_columns": ["X", "crest_uplift", "cap_reach", "middle_reach", "basal_reach"],
        "stations": STATIONS,
        "sections": {str(x): {"before": section(incoming, x), "after": section(outgoing, x)}
                     for x in (-10.4, -7.45, -6.45, -4.65, -1.55, 1.85)},
        "protected_walkable_vertices": len(protected_vertices), "walkable_probes": len(errors), "max_ground_delta_BU": max(errors),
        "baseline_nonadjacent_self_contacts": len(contacts_in), "new_nonadjacent_self_contacts": len(contacts_out - contacts_in),
    }
    (out / "geometry-qa.json").write_text(json.dumps(QA, indent=2) + "\n")


if __name__ == "__main__":
    main()
