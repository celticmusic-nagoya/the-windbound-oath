#!/usr/bin/env python3
"""Create an isolated artist-directed facial plane blockout, NOT a final Morwen head.

Unlike the rejected ellipsoid/Gaussian technique, this is a deliberately authored
piecewise facial plane surface with explicit forehead, orbital, cheek, nose,
philtrum, lip, chin and mandibular stations. It is a *sculpt blockout* only:
no claim of approved anatomy, projection matching, or production quality.
"""
import argparse
import math
import sys
from pathlib import Path
import bpy

# Rows: (z, half_width, front_depth, cheek_width_fraction, cheek_depth,
#        center_nose_projection, center_mouth_projection)
# All positions are visualization coordinates, NOT measured anatomy.
STATIONS = [
    (1.885, .040, -.050, .75, -.048, 0, 0),
    (1.865, .090, -.082, .72, -.077, 0, 0),
    (1.830, .123, -.103, .72, -.099, 0, 0),
    (1.792, .139, -.111, .69, -.111, 0, 0),
    (1.763, .141, -.107, .68, -.113, .005, 0),
    (1.744, .140, -.093, .68, -.111, .013, 0),
    (1.729, .139, -.097, .68, -.113, .024, 0),
    (1.711, .137, -.105, .69, -.113, .036, 0),
    (1.692, .135, -.109, .70, -.116, .040, 0),
    (1.676, .132, -.106, .70, -.119, .023, 0),
    (1.663, .129, -.105, .70, -.116, .006, .002),
    (1.650, .124, -.102, .70, -.111, 0, .009),
    (1.637, .119, -.103, .70, -.110, 0, .006),
    (1.618, .108, -.103, .70, -.105, 0, 0),
    (1.600, .092, -.099, .70, -.099, 0, 0),
    (1.579, .060, -.079, .70, -.080, 0, 0),
    (1.568, .012, -.038, .70, -.040, 0, 0),
]
# Front facial stations are explicit longitudinal bands, including inner eye
# corners, nasal wings, cheek peaks and temporal transitions.
FRONT_U = [-1, -.90, -.76, -.64, -.50, -.38, -.27, -.19, -.12, -.07, 0,
           .07, .12, .19, .27, .38, .50, .64, .76, .90, 1]
BACK_U = [i / 12 for i in range(1, 12)]  # returns from right side around rear to left

def make_surface(coll):
    verts = []
    rings = []
    for z, width, front, cheek_fraction, cheek_depth, nose, mouth in STATIONS:
        ring = []
        for u in FRONT_U:
            x = width * u
            absu = abs(u)
            # Explicit cheek/orbit/nasal plane stations, not radial bump functions.
            if absu <= .12:
                depth = front - nose - mouth
            elif absu <= .19:
                depth = front - nose * .68 - mouth * .80
            elif absu <= .27:
                depth = front - nose * .16 - mouth * .42
            elif absu <= .38:
                depth = front + .005
            elif absu <= .50:
                depth = cheek_depth - .003
            elif absu <= cheek_fraction:
                depth = cheek_depth
            else:
                t = (absu - cheek_fraction) / (1 - cheek_fraction)
                depth = cheek_depth + .065 * t
            ring.append(len(verts))
            verts.append((x, depth, z))
        # The rear cranial arc has more depth than the face, tapering at jaw.
        for t in BACK_U:
            phi = math.pi * t
            x = width * math.cos(phi)
            depth = .080 * math.sin(phi) + .012 * (1 - math.sin(phi))
            ring.append(len(verts))
            verts.append((x, depth, z))
        rings.append(ring)
    faces = []
    n = len(rings[0])
    for lower, upper in zip(rings, rings[1:]):
        for i in range(n):
            nxt = (i + 1) % n
            faces.append((lower[i], lower[nxt], upper[nxt], upper[i]))
    faces.append(tuple(reversed(rings[0])))
    faces.append(tuple(rings[-1]))
    mesh = bpy.data.meshes.new("FACIAL_PLANES_CONTROL_CAGE")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new("MORWEN_FACIAL_PLANES_BLOCKOUT_UNAPPROVED", mesh)
    coll.objects.link(obj)
    obj["status"] = "ARTIST_SCULPT_CONTROL_CAGE_NOT_FINAL"
    obj["method"] = "HAND_AUTHORED_ANATOMICAL_STATIONS_NOT_GAUSSIAN_BUMPS"
    obj["projection_calibrated"] = False
    for p in mesh.polygons:
        p.use_smooth = True
    edge_counts = {}
    for face in mesh.polygons:
        vs = list(face.vertices)
        for i, a in enumerate(vs):
            edge = tuple(sorted((a, vs[(i + 1) % len(vs)])))
            edge_counts[edge] = edge_counts.get(edge, 0) + 1
    assert edge_counts and all(v == 2 for v in edge_counts.values()), "Non-manifold surface"
    return obj

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)
    out = args.output.resolve()
    if out.exists():
        raise RuntimeError("Refusing to overwrite output")
    if bpy.data.meshes:
        raise RuntimeError("Expected a reference-only workspace")
    coll = bpy.data.collections.new("05_FACIAL_PLANES_METHOD_B_UNAPPROVED")
    bpy.context.scene.collection.children.link(coll)
    obj = make_surface(coll)
    bpy.context.scene["status"] = "UNAPPROVED_FACIAL_PLANES_BLOCKOUT_NOT_A_CHARACTER"
    bpy.context.scene["head_art_qa"] = "NOT_RUN"
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    print("FACIAL_PLANES_BLOCKOUT_CREATED", len(obj.data.vertices), len(obj.data.polygons), out)

if __name__ == "__main__":
    main()
