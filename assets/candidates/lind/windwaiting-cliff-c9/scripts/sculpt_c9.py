"""Apply staged, editable local rock-face sculpts to the preserved C8 scene."""
import argparse
import hashlib
import sys
import math
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[5] / "tools/map_blender/lind"))
from build_windwaiting_cliff_C8 import aim, loose_rock, shoreline

C8_SHA = "4df39e97f2d216ba92408e0d881dedb59afef5bb00cfd5592af34a6a1895c3bc"
VIEWS = ("cg_review", "front", "left", "right", "elevated", "shore_detail", "sunset")

# (x, z, inland displacement). Asymmetric outlines mark the limits of
# individual failures. The interior vertices set the facets of the scar.
SCARS = (
    ((-10.2, 3.15, 1.27), ((-13.9, 1.12), (-12.8, .28), (-10.1, .51), (-8.7, 1.82), (-8.3, 3.73), (-9.12, 5.42), (-11.37, 5.24), (-12.4, 4.24))),
    ((-9.00, 3.77, -.53), ((-10.01, 3.20), (-9.65, 1.78), (-8.09, 1.03), (-7.95, 2.29), (-7.94, 4.98), (-8.13, 5.89), (-9.19, 5.14))),
    ((-4.15, 1.97, .97), ((-5.52, .94), (-4.64, .31), (-2.4, .53), (-2.17, 2.42), (-3.32, 4.72), (-4.43, 4.48))),
    ((4.36, 2.16, .68), ((3.35, .63), (3.66, .29), (5.31, .66), (5.51, 2.09), (4.32, 3.03), (4.15, 4.32), (3.36, 4.07))),
    ((10.12, 1.88, .58), ((8.52, .82), (9.48, .38), (11.15, .55), (11.57, 2.13), (10.38, 3.62), (9.45, 3.27))),
)


def displacement(x, z):
    result = 0.0
    for (cx, cz, depth), outline in SCARS:
        for i, (x1, z1) in enumerate(outline):
            x2, z2 = outline[(i + 1) % len(outline)]
            ax, az, bx, bz = x1 - cx, z1 - cz, x2 - cx, z2 - cz
            det = ax * bz - az * bx
            u = ((x - cx) * bz - (z - cz) * bx) / det
            v = (ax * (z - cz) - az * (x - cx)) / det
            if u >= 0 and v >= 0 and u + v <= 1:
                result += depth * min(1.0, (1 - u - v) * 1.36)
                break
    return result


def edit_carrier():
    body = next(obj for obj in bpy.data.objects if obj.get("variant") == "B")
    mesh = body.data
    original = [vert.co.copy() for vert in mesh.vertices]
    for vert in mesh.vertices:
        ring = vert.index % 85
        x, y, z = original[vert.index]
        if ring < 17 or ring > 81 or not -14 < x < 12:
            continue
        crest = original[vert.index - ring + 17].z
        fade = min(1.0, max(0.0, (crest - z) / .70))
        relief = displacement(x, z) * fade
        vert.co.y = y + relief
    mesh.update()
    body["c9_method"] = "Local asymmetric fracture scars with separate scar-derived waterline debris"
    body["source_sha256"] = C8_SHA
    group = body.vertex_groups.new(name="C9 edited rock face")
    edited = [vert.index for vert in mesh.vertices if (vert.co - original[vert.index]).length > 1e-6]
    group.add(edited, 1.0, "REPLACE")
    print(f"Edited {len(edited)} rock-face vertices", flush=True)

    debris = bpy.data.collections.new("C9 | New scar debris")
    bpy.context.scene.collection.children.link(debris)
    rock = mesh.materials[0]
    for index, (center, _) in enumerate(SCARS):
        x, _, depth = center
        if depth <= 0:
            continue
        for part, (offset, offshore, width, height) in enumerate((
            (-.64, .81, .62, .46), (.21, 1.48, .94, .72), (.93, 1.91, .44, .32),
        )):
            local_x = x + offset
            name = f"C9 Scar {index + 1:02d} debris {part + 1:02d}"
            loose_rock(debris, name, (local_x, shoreline(local_x) - offshore, -.24),
                       (width, width * .69, height), rock, 9010 + index * 3 + part, part)
            debris.objects[name]["collapse_site_x"] = x


def render(scene, camera, output):
    scene.camera = bpy.data.objects[camera]
    sun = bpy.data.objects["Grazing warm key"]
    if camera in ("sunset", "cg_review"):
        sun.location = (16, 9, 4)
        aim(sun, (0, 0, 1))
        sun.data.color = (1, .52, .23)
    else:
        sun.location = (9, -6, 6)
        aim(sun, (0, 0, 1))
        sun.data.color = (1, .82, .65)
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--save-only", action="store_true")
    args = parser.parse_args()
    assert tuple(bpy.app.version) == (5, 2, 4), bpy.app.version_string
    assert hashlib.sha256(args.source.read_bytes()).hexdigest() == C8_SHA
    bpy.ops.wm.open_mainfile(filepath=str(args.source))
    edit_carrier()
    scene = bpy.context.scene
    scene["candidate"] = "C9-A_UNAPPROVED"
    scene.render.threads = 8
    scene.render.resolution_percentage = 80
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output / "windwaiting_cliff_C9-A_UNAPPROVED.blend"), compress=True)
    if args.save_only:
        return
    for camera in VIEWS:
        render(scene, camera, args.output / f"{camera}.png")
    clay = bpy.data.materials.new("C9 neutral geometry review")
    clay.use_nodes = True
    shader = clay.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (.32, .32, .32, 1)
    shader.inputs["Roughness"].default_value = .82
    bpy.context.view_layer.material_override = clay
    render(scene, "cg_review", args.output / "cg_review_clay.png")


if __name__ == "__main__":
    main()
