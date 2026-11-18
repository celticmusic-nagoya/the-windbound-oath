#!/usr/bin/env python3
"""Build a sculptable, explicitly UNAPPROVED Morwen head study in a copy of the reference workspace.

This is an authored anatomical surface study, NOT a finished character, calibrated
reconstruction, accepted sculpt, or substitute for an artist's face/hair detailing.
No canonical images, landmarks, or source .blend files are modified.
"""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

def make_head(name, coll, longitude=96, latitude=64):
    # Closed, continuous quad surface: no overlapping primitive facial features.
    # Coordinate convention: face points toward -Y, Z is up.
    vertices = []
    faces = []
    for j in range(latitude + 1):
        theta = math.pi * (j + 0.0001) / (latitude + 0.0002)
        z = 1.71 + 0.175 * math.cos(theta)
        ring = math.sin(theta)
        for i in range(longitude):
            phi = 2 * math.pi * i / longitude
            x = 0.137 * ring * math.sin(phi)
            y = -0.118 * ring * math.cos(phi)
            # Rounded cranium, narrower jaw and subtly pointed chin.
            jaw = max(0.0, (1.67 - z) / 0.14)
            x *= 1.0 - 0.27 * min(1.0, jaw)
            # Face-only detail with localized smooth falloff; avoid disconnected
            # primitive spheres, zipper loops or eyelid annuli.
            front = max(0.0, math.cos(phi)) ** 8
            def bump(cx, cz, sx, sz):
                return math.exp(-((x - cx) / sx) ** 2 - ((z - cz) / sz) ** 2)
            nose = bump(0.0, 1.697, 0.023, 0.044)
            bridge = bump(0.0, 1.727, 0.025, 0.055)
            eye_l = bump(-0.052, 1.735, 0.032, 0.020)
            eye_r = bump(0.052, 1.735, 0.032, 0.020)
            cheek_l = bump(-0.073, 1.681, 0.040, 0.040)
            cheek_r = bump(0.073, 1.681, 0.040, 0.040)
            lips = bump(0.0, 1.650, 0.045, 0.013)
            chin = bump(0.0, 1.612, 0.046, 0.025)
            y -= front * (0.019 * nose + 0.010 * bridge
                          - 0.009 * (eye_l + eye_r)
                          + 0.010 * (cheek_l + cheek_r)
                          + 0.006 * lips + 0.007 * chin)
            vertices.append((x, y, z))
    for j in range(latitude):
        for i in range(longitude):
            a = j * longitude + i
            b = j * longitude + (i + 1) % longitude
            faces.append((a, b, b + longitude, a + longitude))
    faces.append(tuple(reversed(tuple(range(longitude)))))
    faces.append(tuple(latitude * longitude + i for i in range(longitude)))
    mesh = bpy.data.meshes.new(name + "_quad_surface")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    obj["approval"] = "UNAPPROVED_HEAD_STUDY_NOT_FINAL_ASSET"
    obj["scale"] = "UNVERIFIED_VISUALIZATION_UNITS"
    obj["source"] = "canonical Layer 0 four-view; no calibrated reconstruction"
    return obj

def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError("Refusing to overwrite existing output")
    if "02_AUTHOR_SCULPT_EMPTY" not in bpy.data.collections:
        raise RuntimeError("Open the verified Morwen reference workspace first")
    if bpy.data.meshes:
        raise RuntimeError("Expected reference-only workspace; refusing to alter existing meshes")
    coll = bpy.data.collections.new("04_HEAD_SCULPT_STUDY_UNAPPROVED")
    bpy.context.scene.collection.children.link(coll)
    head = make_head("MORWEN_HEAD_CONTINUOUS_QUAD_STUDY", coll)
    assert len(head.data.vertices) == 96 * 65
    assert len(head.data.polygons) == 96 * 64 + 2
    assert all(len(e.link_faces) == 2 for e in [])  # manifold verified below by edge counts
    edge_counts = {}
    for poly in head.data.polygons:
        ids = list(poly.vertices)
        for i, a in enumerate(ids):
            b = ids[(i + 1) % len(ids)]
            key = tuple(sorted((a, b)))
            edge_counts[key] = edge_counts.get(key, 0) + 1
    assert all(count == 2 for count in edge_counts.values()), "Nonmanifold edge"
    bpy.context.scene["status"] = "UNAPPROVED_HEAD_SURFACE_STUDY_NOT_A_CHARACTER"
    bpy.context.scene["head_art_qa"] = "NOT_RUN"
    bpy.context.scene["projection_calibrated"] = False
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print("MORWEN_HEAD_STUDY_SAVED", output, len(head.data.vertices), len(head.data.polygons))

if __name__ == "__main__":
    main()
