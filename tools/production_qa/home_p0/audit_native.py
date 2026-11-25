"""Read-only identification and sampling on the approved HOME source."""
import hashlib
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def main():
    output = Path(sys.argv[sys.argv.index("--") + 1])
    obj = bpy.data.objects["GEO_AIDANHOUSE_INT_SOFT"]
    mesh = obj.data
    groups = {}
    for poly in mesh.polygons:
        for v in poly.vertices:
            groups.setdefault(v, set()).update(poly.vertices)
    components = []
    while groups:
        pending = [min(groups)]
        component = set()
        while pending:
            vertex = pending.pop()
            if vertex in groups:
                component.add(vertex)
                pending.extend(groups.pop(vertex) - component)
        components.append(component)
    blanket = set(range(142, 312))
    mattress = set(range(142))
    if blanket not in components or mattress not in components:
        raise ValueError("source bedding components differ from inspected native")
    points = [obj.matrix_world @ v.co for v in mesh.vertices]
    mesh.calc_loop_triangles()

    def report(ids):
        faces = [p for p in mesh.polygons if set(p.vertices) <= ids]
        mats = sorted({mesh.materials[p.material_index].name for p in faces})
        bounds = [[min(points[v][i] for v in ids), max(points[v][i] for v in ids)] for i in range(3)]
        return dict(vertices=len(ids), face_ids=[p.index for p in faces], materials=mats,
                    world_bounds_m=bounds, uv_layers=[layer.name for layer in mesh.uv_layers])

    def tree(ids):
        return BVHTree.FromPolygons(points, [tuple(t.vertices) for t in mesh.loop_triangles
                                           if set(t.vertices) <= ids], all_triangles=True)

    base = tree(mattress)
    cloth = tree(blanket)
    gaps = []
    for i in range(1, 41):
        for j in range(1, 21):
            x, y = -3.85 + i * 1.84 / 41, 1.76 + j * .88 / 21
            top = base.ray_cast(Vector((x, y, 2)), Vector((0, 0, -1)))[0]
            lower = cloth.ray_cast(Vector((x, y, 0)), Vector((0, 0, 1)))[0]
            if top is not None and lower is not None:
                gaps.append(lower.z - top.z)
    scene = bpy.context.scene
    result = dict(version=bpy.app.version_string, native_sha256=hashlib.file_digest(
        open(bpy.data.filepath, "rb"), "sha256").hexdigest(), object=obj.name,
        blanket=report(blanket), mattress=report(mattress), sample_count=len(gaps),
        sampling_pitch_m=[1.84 / 41, .88 / 21],
        signed_gap_m={"min": min(gaps), "max": max(gaps),
                      "negative_samples": sum(gap < 0 for gap in gaps)},
        shared_uv=report(blanket)["uv_layers"],
        cameras=[item.name for item in scene.objects if item.type == "CAMERA"],
        lights=[item.name for item in scene.objects if item.type == "LIGHT"],
        active_camera=scene.camera.name if scene.camera else None,
        images=[dict(name=item.name, packed=bool(item.packed_file), path=item.filepath)
                for item in bpy.data.images if item.source == "FILE"],
        contact_tolerance_status="OWNER_CONFIRMATION_REQUIRED")
    output.write_text(json.dumps(result, indent=2) + "\n")


main()
