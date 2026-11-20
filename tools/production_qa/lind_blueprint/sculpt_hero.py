"""Replace the foreground shelf profile with joined rock planes on C10."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sculpt_bedrock import TARGET, crest_height, headland_visibility, scene_record, sha, shoreline, smooth, write
import junction_contact_faces
import sculpt_junction

SOURCE_SHA = "a88fd51546a31242e2e63a423988548ed253e4831c501aae430713eac406d334"
GUARD = (-7.48, -3.65)
# The two seaward planes have opposing strike and dip. Their roots share
# the carrier surface; the intervening return runs obliquely down the wall.
PLANES = ((-6.78, -.38, .21, -.07), (-4.90, .29, -.16, -.24))


def freeze_faces(mesh):
    """Keep the source tessellation of every edited non-triangular wall face."""
    mesh.calc_loop_triangles()
    targets = {face.index for face in mesh.polygons if len(face.vertices) > 4
               and any(GUARD[0] < mesh.vertices[i].co.x < GUARD[1] for i in face.vertices)}
    triangles = {i: [] for i in targets}
    for tri in mesh.loop_triangles:
        if tri.polygon_index in targets:
            triangles[tri.polygon_index].append(tuple(tri.vertices))
    # A native shared triangle can occur across more than one polygon in the
    # input tessellation. Keep those polygons native to retain both UV loops.
    uses = Counter(frozenset(tri.vertices) for tri in mesh.loop_triangles)
    retained = {i for i, faces in triangles.items()
                if any(uses[frozenset(ids)] > 1 for ids in faces)}
    targets -= retained
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        handles = [bm.verts[i] for i in range(len(mesh.vertices))]
        faces = {i: bm.faces[i] for i in targets}
        layers = list(bm.loops.layers.uv.values())
        for i, face in sorted(faces.items()):
            material, smooth_face = face.material_index, face.smooth
            uv = {loop.vert.index: [loop[layer].uv.copy() for layer in layers] for loop in face.loops}
            bm.faces.remove(face)
            for ids in triangles[i]:
                new = bm.faces.new([handles[k] for k in ids])
                new.material_index, new.smooth = material, smooth_face
                for loop in new.loops:
                    for layer, coords in zip(layers, uv[loop.vert.index]):
                        loop[layer].uv = coords
        bm.to_mesh(mesh)
        mesh.update()
    finally:
        bm.free()
    return sorted(targets), sorted(retained)


def sculpt_delta(point, anchors):
    x, y, z = point
    if not GUARD[0] < x < GUARD[1] or z <= -.12:
        return 0., 0.
    edge, crown = shoreline(x), crest_height(x)
    weight = smooth((x-GUARD[0])/.70)*smooth((GUARD[1]-x)/.80)
    weight *= smooth((z+.12)/.55)*(1.-smooth((y-edge-.25)/2.85))
    # The return has separate left and right shoulders, an inland trough,
    # and a slight rake. It replaces the existing horizontal convex profile.
    seam = -5.95 + .065*(z-2.8)
    u = smooth((x-seam+.19)/.47)
    left, right = [anchor + strike*(x-center) + dip*(z-3.) + setback
                   for anchor,(center,strike,dip,setback) in zip(anchors,PLANES)]
    recess = .66 * max(0., 1.-abs(x-seam-.035)/.27)
    target = (1.-u)*left + u*right + recess
    delta_y = max(-.95,min(.90,target-y))
    crest_weight = smooth((z-(crown-.85))/1.05)
    tip_lowering = -.48*(1.-smooth(abs(x+6.76)/.78))
    notch = -.32*max(0.,1.-abs(x-seam-.04)/.39)
    return .83*weight*delta_y, weight*crest_weight*(tip_lowering+notch)


def fit_without_contacts(obj, original, offsets):
    """Constrain only the contact neighborhoods, measuring after every solve."""
    mesh = obj.data
    junction_contact_faces.GUARD = GUARD
    weights = [1.0] * len(original)
    neighbors = [set() for _ in original]
    for edge in mesh.edges:
        a,b = edge.vertices
        neighbors[a].add(b)
        neighbors[b].add(a)
    trace = []
    for _ in range(7):
        for vertex, base, (dy,dz), weight in zip(mesh.vertices,original,offsets,weights):
            if dy or dz:
                vertex.co = (base[0],base[1]+weight*dy,base[2]+weight*dz)
        mesh.update()
        bpy.context.view_layer.update()
        result = junction_contact_faces.audit(obj)
        trace.append({"pairs":result["nonadjacent_bvh_pairs"],
                      "face_ids": [item["face_ids"] for item in result["pairs"] if "face_ids" in item]})
        if not result["pairs"]:
            break
        core = set()
        for pair in result["pairs"]:
            for face_id in pair["face_ids"]:
                core.update(mesh.polygons[face_id].vertices)
        ring = set().union(*(neighbors[i] for i in core)) - core
        outer = set().union(*(neighbors[i] for i in ring)) - core - ring
        for ids, cap in ((core,0.0),(ring,.22),(outer,.60)):
            for i in ids:
                weights[i] = min(weights[i],cap)
    return trace, weights


def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args(sys.argv[sys.argv.index("--")+1:])
    source, out = args.source.resolve(), args.output.resolve()
    if bpy.app.version != (5,3,0) or sha(source) != SOURCE_SHA or out in source.parents:
        raise ValueError("Expected Blender 5.3.0 and the locked bedrock source")
    out.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    obj = scene.objects[TARGET]
    if obj.matrix_world != Matrix.Identity(4):
        raise ValueError("Measured carrier coordinates require its unchanged identity transform")
    mesh = obj.data
    sculpt_junction.GUARD = GUARD
    before, _ = sculpt_junction.mesh_stats(obj)
    before_scene = scene_record(scene)
    original = [tuple(v.co) for v in mesh.vertices]
    anchors = []
    for center,*_ in PLANES:
        hit, point, _, _ = obj.ray_cast(Vector((center,-30,3.)), Vector((0,1,0)), distance=60)
        if not hit:
            raise RuntimeError(f"Source plane anchor did not hit at X={center}")
        anchors.append(point.y)
    offsets = [sculpt_delta(v,anchors) for v in original]
    # Check the source triangulation alone before applying any deformation.
    native = mesh.copy()
    fixed_triangles, retained_faces = freeze_faces(mesh)
    if original != [tuple(v.co) for v in mesh.vertices]:
        raise ValueError("Source tessellation did not preserve vertex correspondence")
    pinned_baseline,_ = sculpt_junction.mesh_stats(obj)
    if pinned_baseline["local_self_contacts"]:
        original_name = mesh.name
        mesh.name = original_name + " (rejected tessellation check)"
        obj.data = native
        mesh = obj.data
        mesh.name = original_name
        fixed_triangles = []
    trace, weights = fit_without_contacts(obj, original, offsets)
    protected, changed = [], []
    for vertex, base in zip(mesh.vertices,original):
        if tuple(vertex.co) == base:
            protected.append(vertex.index)
        else:
            changed.append({"vertex_id":vertex.index,"before_local":base,"after_local":list(vertex.co)})
    after,_ = sculpt_junction.mesh_stats(obj)
    try:
        visibility = headland_visibility(scene,obj)
    except AssertionError as error:
        visibility = error.args[0]
    visible = [row["unoccluded_face_samples"] for row in visibility]
    checks = {
        "scope_and_original_collar_preserved": all(tuple(v.co) == original[v.index]
                    for v in mesh.vertices if not GUARD[0] < original[v.index][0] < GUARD[1]),
        "local_self_contacts_zero": after["local_self_contacts"] == 0,
        "valid_closed_carrier": not any(after[k] for k in ("boundary_edges","degenerate_faces","nonmanifold_edges")),
        "visibility_at_least_10_4_13": len(visible)==3 and all(x>=y for x,y in zip(visible,(10,4,13))),
        "scene_settings_unchanged": before_scene==scene_record(scene),
        "source_sha_preserved": sha(source)==SOURCE_SHA,
        "at_least_60_percent_of_target_vertices_changed": len(changed) >= .60*sum(bool(y or z) for y,z in offsets),
    }
    scene["candidate"] = "C10_HERO_FRACTURE_UNAPPROVED"
    scene["hero_source_sha256"] = SOURCE_SHA
    destination = out/"hero_fracture_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    write(out/"hero_vertex_diff.json",{"scope_x":GUARD,"units":"provisional local BU",
          "source_front_y":anchors,"planes":PLANES,"protected_count":len(protected),
          "source_faces_with_locked_tessellation":fixed_triangles,
          "native_faces_with_shared_tessellation":retained_faces,"vertices":changed})
    write(out/"local_qa.json",{"source_sha256":SOURCE_SHA,"candidate_sha256":sha(destination),
          "checks":checks,"before":before,"after":after,"visibility":visibility,
          "pinned_source_mesh_check":pinned_baseline,"contact_solver_trace":trace,
          "constrained_vertices":sum(w<1 for w in weights),
          "changed_vertices":len(changed),"protected_vertices":len(protected),
          "G1":"BLOCKED","G2":"NOT_RUN","G3":"BLOCKED" if all(checks.values()) else "FAIL","G4":"NOT_RUN"})
    print("HERO_QA",json.dumps(checks,sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
