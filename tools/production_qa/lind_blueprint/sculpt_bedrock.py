"""Shape contiguous, oblique bedrock panels on the verified C10 carrier."""
import argparse
import json
from pathlib import Path
import sys

import bpy

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent), str(Path.cwd() / "tools/map_blender/lind")]
from build_windwaiting_cliff_C8 import shoreline, crest_height
from export_blueprint import scene_record, sha, write
from inspect_windwaiting_cliff_C8 import headland_visibility
from junction_contact_faces import TARGET, audit
import sculpt_junction

SOURCE_SHA = "056ba4a3f672dde75a9f129af8486f547c3971ad41cd6cee1dc360b275591f2c"
GUARD = (-13.0, 1.15)
# Alongshore stations at mid-height. Each station carries a set-back and a
# bedding elevation; adjacent stations define a continuous rock plane.
# Narrow station intervals are the oblique, recessed returns between blocks.
STATIONS = (
    (-13.0, 0.0, 0.0), (-12.0, -.12, .07), (-11.15, -.40, .23),
    (-10.55, -.28, .31), (-10.18, .30, -.11), (-9.88, .52, -.25),
    (-9.43, -.15, -.13), (-8.76, -.29, .13), (-8.18, 0.0, 0.0),
    (-7.42, 0.0, 0.0), (-6.90, -.14, -.09), (-5.91, -.32, .18),
    (-5.18, -.09, .31), (-4.87, .44, -.16), (-4.48, .27, -.24),
    (-4.00, -.22, -.05), (-2.89, -.38, .23), (-2.48, -.26, .34),
    (-2.12, .31, -.15), (-1.78, .39, -.20), (-1.35, -.12, -.08),
    (-.47, -.21, .12), (1.15, 0.0, 0.0),
)
# At the validated fracture, keep all original wall vertices and a collar.
LOCKED_X = (-8.10, -7.50)


def smooth(t):
    t = min(1., max(0., t))
    return t*t*(3.-2.*t)


def profile(x):
    for (left, a, b), (right, c, d) in zip(STATIONS, STATIONS[1:]):
        if left <= x <= right:
            t = (x-left)/(right-left)
            return a+t*(c-a), b+t*(d-b)
    return 0.0, 0.0


def deformation(point):
    x, y, z = point
    if not GUARD[0] < x < GUARD[1] or LOCKED_X[0] <= x <= LOCKED_X[1]:
        return 0., 0.
    edge, crown = shoreline(x), crest_height(x)
    height = min(1., max(0., z/max(crown, .1)))
    from_lock = min(abs(x-LOCKED_X[0]), abs(x-LOCKED_X[1]))
    weight = (smooth((x-GUARD[0])/.70)*smooth((GUARD[1]-x)/.70)
              *smooth(from_lock/.45)*smooth((z+.05)/.85)
              *(1.-smooth((y-edge-.25)/3.25)))
    # Incline the discontinuities in opposite directions across the two beds.
    obliquity = .54 if x < LOCKED_X[0] else -.71
    retreat, shift = profile(x-obliquity*(height-.48))
    face_weight = 1.-.70*smooth((height-.80)/.20)
    # Round the inland shoulder into the new crown while keeping the toe
    # connected to the original closed mesh.
    crest_weight = smooth((height-.69)/.31)
    crest_lowering = -.21*crest_weight*(1.-smooth(abs(x+10.6)/2.15))
    return (weight*retreat*face_weight,
            weight*(shift*(.55+.45*height)+crest_lowering))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args(sys.argv[sys.argv.index("--")+1:])
    source, out = args.source.resolve(), args.output.resolve()
    if bpy.app.version != (5,3,0) or sha(source) != SOURCE_SHA or out in source.parents:
        raise ValueError("Expected Blender 5.3.0 and the locked retopology candidate")
    out.mkdir(parents=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    obj = scene.objects[TARGET]
    mesh = obj.data
    sculpt_junction.GUARD = GUARD
    baseline, _ = sculpt_junction.mesh_stats(obj)
    before_scene = scene_record(scene)
    points = [tuple(v.co) for v in mesh.vertices]
    world, inverse = obj.matrix_world, obj.matrix_world.inverted()
    changed = []
    protected = []
    for v in mesh.vertices:
        p = world @ v.co
        dy, dz = deformation(p)
        if not (dy or dz):
            protected.append(v.index)
            continue
        p.y += dy
        p.z += dz
        v.co = inverse @ p
        if tuple(v.co) != points[v.index]:
            changed.append({"vertex_id":v.index,"before_local":points[v.index],"after_local":list(v.co)})
    mesh.update()
    bpy.context.view_layer.update()
    after, _ = sculpt_junction.mesh_stats(obj)
    try:
        visibility = headland_visibility(scene, obj)
    except AssertionError as error:
        visibility = error.args[0]
    visible = [row["unoccluded_face_samples"] for row in visibility]
    checks = {
        "protected_vertices_unchanged": all(tuple(mesh.vertices[i].co) == points[i] for i in protected),
        "original_fracture_collar_unchanged": all(tuple(v.co) == points[v.index] for v in mesh.vertices
                      if LOCKED_X[0] <= (world @ v.co).x <= LOCKED_X[1]),
        "no_self_contacts_in_sculpt_guard": not after["local_self_contacts"],
        "valid_closed_carrier": not any(after[k] for k in ("boundary_edges","degenerate_faces","nonmanifold_edges")),
        "visibility_at_least_10_4_13": len(visible) == 3 and all(x >= y for x,y in zip(visible,(10,4,13))),
        "scene_settings_unchanged": before_scene == scene_record(scene),
        "original_input_sha_unchanged": sha(source) == SOURCE_SHA,
        "geometry_changed": bool(changed),
    }
    scene["candidate"] = "C10_BEDROCK_WALL_UNAPPROVED"
    scene["bedrock_source_sha256"] = SOURCE_SHA
    destination = out/"bedrock_wall_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination),compress=True)
    write(out/"bedrock_vertex_diff.json", {"axis":"+X along coast, +Y inland, +Z up", "units":"provisional BU",
          "scope_x":GUARD,"locked_x":LOCKED_X,"authored_stations":STATIONS,"vertices":changed})
    write(out/"local_qa.json",{"source_sha256":SOURCE_SHA,"candidate_sha256":sha(destination),
          "checks":checks,"before":baseline,"after":after,"visibility":visibility,
          "changed_vertices":len(changed),"protected_vertices":len(protected),"junction_audit":audit(obj),
          "G1":"BLOCKED","G2":"NOT_RUN","G3":"BLOCKED" if all(checks.values()) else "FAIL","G4":"NOT_RUN"})
    print("BEDROCK_QA",json.dumps(checks,sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
