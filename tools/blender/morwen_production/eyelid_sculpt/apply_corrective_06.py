"""EYELID-06 Blender corrective-key *candidate* on the saved EYELID-05 .blend.

Run: blender -b MORWEN_EYELID_05_CANDIDATE.blend --python apply_corrective_06.py
Requires EYELID_06_TARGET_JSON and EYELID_06_OUTPUT_BLEND environment variables.
The script refuses to overwrite the input or any existing output. NOT an art/QA PASS.
"""
import hashlib
import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


def smoothstep(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)


def interp(points, u):
    i = min(int(u*(len(points)-1)), len(points)-2)
    t = u*(len(points)-1)-i
    return (1-t)*points[i]["y_px"]+t*points[i+1]["y_px"]


def main():
    target_path = Path(os.environ["EYELID_06_TARGET_JSON"]).resolve()
    output_path = Path(os.environ["EYELID_06_OUTPUT_BLEND"]).resolve()
    input_path = Path(bpy.data.filepath).resolve()
    if not input_path.is_file() or output_path == input_path or output_path.exists():
        raise RuntimeError("Input .blend required; output must be a new, nonexistent path")
    target = json.loads(target_path.read_text(encoding="utf-8"))
    if target["status"] != "UNREVIEWED_ART_PROPOSAL_NOT_CANON":
        raise RuntimeError("Unexpected target status")
    face = bpy.data.objects["Face"]
    me = face.data
    keys = me.shape_keys.key_blocks
    names_before = [k.name for k in keys]
    if len(keys) != 57 or names_before[1:] != [f"target_{i}" for i in range(56)]:
        raise RuntimeError("Unexpected 56-key VRoid order; refuse to modify")
    if "elm_patch" not in me.attributes:
        raise RuntimeError("Missing EYELID-05 patch provenance")
    attr = me.attributes["elm_patch"].data
    mw = face.matrix_world
    inv = mw.inverted()
    scale = 561.5300546448087  # EYELID-05 calibration, pixels per meter
    mid_x_px = 212.785
    mid_x_m = 0.00026
    eye_y_px = 127.62
    eye_z_m = 1.44589
    # The 05 mesh's margin is the skin boundary against eye opening, not every patch vertex.
    # Identify margin vertices via skin-face boundary edges; no topology or Basis edits.
    edge_count = {}
    for p in me.polygons:
        if p.material_index < 0:
            continue
        for e in p.edge_keys:
            edge_count.setdefault(tuple(sorted(e)), []).append(p.index)
    margin = set()
    for (a,b), adjacent in edge_count.items():
        if len(adjacent) == 1 and attr[a].value in (1,2) and attr[b].value in (1,2):
            margin.update((a,b))
    if not margin:
        raise RuntimeError("No unambiguous lid opening boundary: refuse modification")
    # Candidate deltas are bounded to the lid patch and taper toward its exterior.
    # We do NOT replace the old VRoid key here; separate corrective keys must be composed
    # only after an artist verifies which target_N represents Blink/Joy.
    deltas = {}
    for side, patch_id in (("R",1),("L",2)):
        pts = target["sides"][side]["points"]
        x0,x1 = pts[0]["x_px"],pts[-1]["x_px"]
        if abs(x1-x0) < 1e-6:
            raise RuntimeError("Degenerate eye width")
        patch = [v.index for v in me.vertices if attr[v.index].value == patch_id]
        for idx in patch:
            world = mw @ me.vertices[idx].co
            px = mid_x_px - (world.x-mid_x_m)*scale
            py = eye_y_px - (world.z-eye_z_m)*scale
            u = (px-x0)/(x1-x0)
            if not 0 <= u <= 1:
                continue
            target_y = interp(pts,u)
            # 0 at the canthi, full at centre, falloff with distance from opening edge.
            envelope = math.sin(math.pi*u)**2
            # No more than 12 px displacement; reject implausible mapping.
            dz = (py-target_y)/scale
            if abs(dz*scale)>12:
                raise RuntimeError(f"Candidate displacement too large: {idx}")
            # Spatial weight: vertices on margin get 1, others decay over 12 mm.
            nearest = min(((mw @ me.vertices[j].co)-world).length for j in margin if attr[j].value == patch_id)
            weight = 1-smoothstep(nearest/0.012)
            if weight > 0:
                deltas[idx] = Vector((0,0,dz*weight*envelope))
    if not deltas:
        raise RuntimeError("No mapped corrective vertices")
    # New key only: never mutate existing 56 keys or Basis.
    new_key = face.shape_key_add(name="EYELID06_CLOSED_ART_CANDIDATE", from_mix=False)
    for idx,dz_world in deltas.items():
        new_key.data[idx].co = keys[0].data[idx].co + inv.to_3x3() @ dz_world
    if [k.name for k in keys[:57]] != names_before:
        raise RuntimeError("Protected original key order changed")
    new_key.value = 0.0
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path), compress=True, copy=True)
    report = {"status":"UNREVIEWED_NOT_ADOPTED","input_blend":input_path.name,
              "input_sha256":hashlib.sha256(input_path.read_bytes()).hexdigest(),
              "target_sha256":hashlib.sha256(target_path.read_bytes()).hexdigest(),
              "blender_version":bpy.app.version_string,"corrective_vertices":len(deltas),
              "protected_original_keys":names_before,"G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"}
    output_path.with_suffix(".json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")


if __name__=="__main__":
    main()
