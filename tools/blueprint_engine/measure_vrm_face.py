"""Read-only VRoid/VRM face measurement inside Blender 5.3.0 (bpy 5.3.0).

Usage: <python-with-bpy> measure_vrm_face.py NATIVE.blend SPEC.json OUT.json
Input: a .blend containing a VRoid-exported VRM imported into Blender (rest pose,
basis shape). Never saves. Material regions (VRoid naming) define the landmarks:
  EyeWhite  -> eye corners (x extent per side)      EyeIris -> iris bbox centre
  Face_*_SKIN centreline (|x| < band) -> chin (lowest) and nose tip (most forward)
  crown -> highest vertex of all meshes (hair included, like Layer0 'crown')
Projection: orthographic front, camera looking along +forward axis, image x = world
+X (image left = character right), image y = -Z. Units: metres, and ratios to
head height H = crown_z - chin_z (dimensionless) for comparison with Layer0 pixels.
"""
import json
import sys

import bpy

REGIONS = ("EyeWhite", "EyeIris", "FaceEyeline", "FaceMouth", "FaceBrow", "Face_00_SKIN")


def region_vertices(obj):
    mesh = obj.data
    slots = [s.material.name if s.material else "" for s in obj.material_slots]
    out = {r: set() for r in REGIONS}
    for poly in mesh.polygons:
        name = slots[poly.material_index] if poly.material_index < len(slots) else ""
        for region in REGIONS:
            if region in name:
                out[region].update(poly.vertices)
    world = obj.matrix_world
    return {r: [tuple(world @ mesh.vertices[i].co) for i in sorted(v)] for r, v in out.items()}


def ext(points, axis, pick):
    return pick(p[axis] for p in points)


def main(argv):
    native, spec_path, out = argv
    spec = json.load(open(spec_path))
    band = spec.get("centre_band_m", 0.005)
    bpy.ops.wm.open_mainfile(filepath=native, load_ui=False)
    faces = [o for o in bpy.context.scene.objects if o.type == "MESH" and any(
        s.material and "EyeWhite" in s.material.name for s in o.material_slots)]
    if len(faces) != 1:
        raise SystemExit(f"expected one VRoid face mesh, found {len(faces)}")
    face = faces[0]
    keys = face.data.shape_keys
    nonzero = [k.name for k in keys.key_blocks[1:] if k.value != 0] if keys else []
    poses = [o.name for o in bpy.context.scene.objects if o.type == "ARMATURE" and o.data.pose_position != "REST"
             and any(pb.matrix_basis != pb.matrix_basis.Identity(4) for pb in o.pose.bones)]
    regions = region_vertices(face)
    missing = [r for r in ("EyeWhite", "EyeIris", "Face_00_SKIN") if not regions[r]]
    if missing:
        raise SystemExit("missing VRoid regions: " + ", ".join(missing))
    skin = regions["Face_00_SKIN"]
    centre = [p for p in skin if abs(p[0]) < band]
    iris = regions["EyeIris"]
    # forward axis sign: irises sit in front of the skin centroid
    skin_y = sum(p[1] for p in skin) / len(skin)
    iris_y = sum(p[1] for p in iris) / len(iris)
    forward = -1 if iris_y < skin_y else 1
    crown = max(v[2] for o in bpy.context.scene.objects if o.type == "MESH"
                for v in (o.matrix_world @ x.co for x in o.data.vertices))
    chin = min(p[2] for p in centre)
    eye_z = sum(p[2] for p in iris) / len(iris)
    nose_pool = [p for p in centre if chin < p[2] < eye_z]
    nose = (min if forward < 0 else max)(nose_pool, key=lambda p: p[1])

    def side(points, sign):
        return [p for p in points if (p[0] < 0) == (sign < 0)]

    m = {}
    for label, sign in (("left", -1), ("right", 1)):          # image left = world -X
        white = side(regions["EyeWhite"], sign)
        line = side(regions["FaceEyeline"], sign)
        ir = side(iris, sign)
        m[f"eye_width_{label}"] = ext(white, 0, max) - ext(white, 0, min)
        m[f"eyeline_width_{label}"] = (ext(line, 0, max) - ext(line, 0, min)) if line else None
        m[f"iris_center_x_{label}"] = (ext(ir, 0, max) + ext(ir, 0, min)) / 2
        m[f"eye_inner_x_{label}"] = ext(white, 0, max) if sign < 0 else ext(white, 0, min)
    m["iris_center_distance"] = m["iris_center_x_right"] - m["iris_center_x_left"]
    m["inner_eye_gap"] = m["eye_inner_x_right"] - m["eye_inner_x_left"]
    mouth = regions["FaceMouth"]
    m["mouth_mesh_width"] = (ext(mouth, 0, max) - ext(mouth, 0, min)) if mouth else None
    m["nose_to_chin_vertical"] = nose[2] - chin
    head = crown - chin
    result = dict(bpy_version=bpy.app.version_string, build_hash=(bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes)
                              else str(bpy.app.build_hash)),
                  face_object=face.name, face_vertices=len(face.data.vertices),
                  region_vertex_counts={r: len(v) for r, v in regions.items()},
                  forward_axis="-Y" if forward < 0 else "+Y", nonzero_shape_keys=nonzero,
                  posed_armatures_ignored=poses,  # basis mesh data is read; pose not applied
 is_dirty=bpy.data.is_dirty,
                  crown_z=crown, chin_z=chin, nose_tip=list(nose), head_height_m=head,
                  metrics_m=m,
                  ratios={k: (v / head if v is not None else None) for k, v in m.items()
                          if not k.startswith(("iris_center_x", "eye_inner_x"))})
    with open(out, "w") as stream:
        json.dump(result, stream, sort_keys=True, indent=1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
