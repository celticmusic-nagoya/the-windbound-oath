"""P1-B: read-only VRoid face measurement method and comparability with Layer0.

Native substrate: M00.blend (artifact 14626143604; Blender import of
TWO_Morwen_Base_M00.vrm 3e980877...; MEASURED_COMPARATOR_ONLY, not the current
candidate). The current #427 candidate is a .vroid (opaque); the same adapter
applies once the owner exports it to VRM and imports it into Blender 5.3.0.

Comparison space: ratio to head height H (crown->chin) in an orthographic front
view. Layer0 side: manual ESTIMATED points (+-3 px), crown/chin from
layer0_landmarks_v1 (+-2/+-3 px). No 3D depth is taken from the 2D views; only
front-plane (x, z) quantities are compared.
"""
import argparse
import json
from pathlib import Path
import shutil

from ..contract import OperationRegistry
from ..evidence import ESTIMATED, NATIVE_MEASURED, UNDETERMINED
from ..export import ledger, studio_record, write_json
from ..geometry import Blueprint
from ..measure import VrmFaceAdapter
from ..official_face import remeasure
from ..sources import file_sha256, register_source
from ._run import run_group

M00_BLEND_SHA = "17f6c6b098560b90bc2b9f372dc713c7f81f3459e5d44891fba080e9b5055eb3"
FRONT_SHA = "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"
OWNER_TOL_PX = 6.0         # #427 blueprint-targets.json
POINT_U_PX = 3.0           # face_front_review stated point uncertainty
CS = "front orthographic plane, ratio to head height (crown->chin), image x right, y down"
COMPARABLE = ("eye_width_left", "eye_width_right", "iris_center_distance", "inner_eye_gap")
DEFINITION = {
    "mouth_width": "VRoid mouth line is texture-drawn on the FaceMouth mesh; mesh extent is "
                   "not the illustrated mouth line -> needs texture/render measurement",
    "nose_to_chin_vertical": "illustrated nose tip is a shading mark; mesh nose tip is the "
                             "geometric apex -> landmark definitions differ",
}


def official(precision, landmarks):
    pts = precision["face_front_review"]["points"]
    front = landmarks["views"]["front"]["landmarks"]
    crown, chin = front["crown"], front["chin"]
    head = chin["xy_px"][1] - crown["xy_px"][1]
    u_head = crown["uncertainty_px"] + chin["uncertainty_px"]
    px = dict(
        eye_width_left=pts["left_inner_eye"][0] - pts["left_outer_eye"][0],
        eye_width_right=pts["right_outer_eye"][0] - pts["right_inner_eye"][0],
        iris_center_distance=pts["right_iris_center"][0] - pts["left_iris_center"][0],
        inner_eye_gap=pts["right_inner_eye"][0] - pts["left_inner_eye"][0],
        mouth_width=pts["mouth_right"][0] - pts["mouth_left"][0],
        nose_to_chin_vertical=pts["chin"][1] - pts["nose_tip"][1])
    out = {}
    for key, d in px.items():
        u_d = 2 * POINT_U_PX
        out[key] = dict(px=d, ratio=d / head, u=u_d / head + abs(d) * u_head / head ** 2,
                        tolerance=OWNER_TOL_PX / head)
    return head, u_head, out


def run(layer0_front, precision_json, landmarks_json, m00_blend, out, python=None):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    precision = json.loads(Path(precision_json).read_text())
    landmarks = json.loads(Path(landmarks_json).read_text())
    head, u_head, off = official(precision, landmarks)
    bp = Blueprint(blueprint_id="MORWEN.face-front-ratio.v1", asset_id="MORWEN",
                   stage="face-measurement-method", status="METHOD_RESEARCH",
                   canon_status="Layer0 official reference; targets ESTIMATED, not adopted")
    bp.add_source(register_source(layer0_front, source_id="layer0.front", role="OFFICIAL_CANON",
                                  projection="image-2d-uncalibrated",
                                  coordinate_system="Layer0 front px", units="px",
                                  expected_sha256=FRONT_SHA, view="front",
                                  provenance="artifact 14602858760",
                                  license="project-original; private"))
    for sid, path in (("record.precision_v2", precision_json), ("record.landmarks_v1", landmarks_json)):
        bp.add_source(register_source(path, source_id=sid, role="REFERENCE", projection="data",
                                      coordinate_system="Layer0 front px", units="px",
                                      provenance="main tools/morwen_authored_sculpt",
                                      license="project-original"))
    bp.add_source(register_source(m00_blend, source_id="native.m00", role="VERIFICATION",
                                  projection="native-3d", coordinate_system="Blender world, Z-up",
                                  units="m", expected_sha256=M00_BLEND_SHA,
                                  provenance="M00.blend, artifact 14626143604 (VRM 3e980877...; "
                                             "comparator only, NOT_ADOPTED)",
                                  license="VRM meta: allowRedistribution=false; private"))
    metrics = {}
    for key, rec in off.items():
        evidence = ESTIMATED if key in COMPARABLE else UNDETERMINED
        bp.add_element(element_id=f"official.{key}", kind="dimension", module="face",
                       sources=["layer0.front", "record.precision_v2", "record.landmarks_v1"],
                       evidence=ESTIMATED, coordinate_system=CS, units="ratio", dims=1,
                       value=rec["ratio"], uncertainty=rec["u"],
                       notes=f"{rec['px']} px / H {head} px; u = 2x{POINT_U_PX}/H + d*{u_head}/H^2")
        if key in COMPARABLE:
            metrics[key] = dict(element=f"official.{key}", value=rec["ratio"],
                                tolerance=rec["tolerance"], uncertainty=rec["u"], evidence=evidence)
    bp.add_group(target_id="morwen.face.front.ratio", measurement_id="vroid-region-front-ortho",
                 coordinate_system=CS, units="ratio", projection="image-2d-uncalibrated",
                 metrics=metrics, operation_id="blueprint_engine.measure.vrm_face_front.v1",
                 protection_scope_id="native.file",
                 tolerance_basis=f"owner 6 px / H {head} px")
    for key, why in DEFINITION.items():
        bp.add_question(f"definition.{key}", why, ["morwen.face.front.ratio"])
    bp.add_question("orthographic-assumption", "Layer0 camera unknown; head region treated as "
                    "orthographic (unverified, no numeric term).", ["morwen.face.front.ratio"])
    adapter = VrmFaceAdapter({k: k for k in metrics}, "native.file", python=python)
    work = out / "qual"
    work.mkdir()
    shutil.copyfile(m00_blend, work / "n.blend")
    first, second = adapter.raw(work / "n.blend"), adapter.raw(work / "n.blend")
    qual = dict(operation="blueprint_engine.measure.vrm_face_front.v1", kind="read_only_measure",
                native_sha256=file_sha256(work / "n.blend"), repeat_identical=first == second,
                regions=first["region_vertex_counts"], forward_axis=first["forward_axis"],
                script_sha256=file_sha256(VrmFaceAdapter.script), bpy=first["bpy_version"],
                build_hash=first["build_hash"])
    qual["qualified"] = qual["repeat_identical"] and all(first["region_vertex_counts"][r] > 0 for r in
                                                         ("EyeWhite", "EyeIris", "Face_00_SKIN"))
    shutil.rmtree(work)
    write_json(out / "qualification.json", qual)
    registry = OperationRegistry()
    registry.register("blueprint_engine.measure.vrm_face_front.v1", kind="read_only_measure",
                      qualified=qual["qualified"],
                      evidence_sha256=file_sha256(out / "qualification.json"))
    write_json(out / "blueprint.json", bp.to_dict())
    deps = {"blueprint": bp.digest(), "script": qual["script_sha256"]}
    result, target, report = run_group(bp, "morwen.face.front.ratio", registry, adapter,
                                       native=m00_blend, native_sha=M00_BLEND_SHA,
                                       baseline=M00_BLEND_SHA, dependencies=deps, out=out)
    comparability = {}
    for key, rec in off.items():
        native_value = first["ratios"].get("mouth_mesh_width" if key == "mouth_width" else key)
        reachable = rec["u"] <= rec["tolerance"]
        comparability[key] = dict(
            official_px=rec["px"], official_ratio=rec["ratio"], official_u=rec["u"],
            tolerance=rec["tolerance"], native_ratio=native_value,
            status=("COMPARABLE" if key in COMPARABLE else "DEFINITION_MISMATCH"),
            pass_reachable=reachable, state=report["metrics"].get(key, {}).get("state", "NOT_TARGET"),
            note=DEFINITION.get(key))
    research = remeasure(layer0_front, precision["face_front_review"]["points"])
    native_key = dict(eye_width_left="eyeline_width_left", eye_width_right="eyeline_width_right",
                      inner_eye_gap="eyeline_inner_gap", iris_center_distance="iris_center_distance",
                      sclera_width_left="eye_width_left", sclera_width_right="eye_width_right")
    definition = {
        "eye_width_left": "eyeline (upper lash line) extent <-> VRoid FaceEyeline extent",
        "eye_width_right": "eyeline extent <-> FaceEyeline; inner corner has a faint taper",
        "inner_eye_gap": "eyeline inner ends <-> FaceEyeline inner ends",
        "iris_center_distance": "iris centroid <-> VRoid EyeIris bbox centre",
        "sclera_width_left": "sclera+iris opening <-> VRoid EyeWhite (not the manual points)",
        "sclera_width_right": "sclera+iris opening <-> VRoid EyeWhite (not the manual points)"}
    pts = research["points"]
    ambiguous = {"eye_width_right": "right" if "left" in pts["right_eyeline"]["ambiguous"] else None,
                 "inner_eye_gap": "right" if "left" in pts["right_eyeline"]["ambiguous"] else None,
                 "eye_width_left": "left" if pts["left_eyeline"]["ambiguous"] else None}
    research_rows = {}
    for key, rec in research["ratios"].items():
        tol = OWNER_TOL_PX / research["head_px"]
        nat = first["ratios"].get(native_key[key])
        u = rec["u"] + 2.0 ** -22 * 4
        if ambiguous.get(key):
            state = "DEFINITION_AMBIGUOUS"
        elif key.startswith("sclera"):
            state = "NOT_COMPARED (different definition from manual points)"
        else:
            r = nat - rec["ratio"]
            state = "PASS" if abs(r) + u <= tol else "OUTSIDE" if abs(r) - u > tol else "HOLD"
        research_rows[key] = dict(manual_px=off.get(key, {}).get("px"),
                                  manual_u_ratio=off.get(key, {}).get("u"),
                                  algorithmic_px=rec["px"], algorithmic_u_px=rec["u_px"],
                                  algorithmic_ratio=rec["ratio"], algorithmic_u_ratio=rec["u"],
                                  tolerance_ratio=tol, pass_reachable=rec["u"] < tol,
                                  m00_native_key=native_key[key], m00_ratio=nat,
                                  m00_state_if_adopted=state, definition=definition[key])
    research_record = dict(
        status="RESEARCH_ONLY_NOT_A_TARGET (official targets and owner tolerance unchanged)",
        method="official_face.py: deterministic pixel segmentation; u = half range of a fixed "
               "parameter sweep + 0.5 px; manual points used only as search windows",
        head=dict(manual_px=head, manual_u_px=u_head, algorithmic_px=research["head_px"],
                  algorithmic_u_px=research["head_u_px"],
                  crown=research["points"]["crown"], chin=research["points"]["chin"]),
        metrics=research_rows,
        corner_candidates=dict(left=pts["left_eyeline"], right=pts["right_eyeline"]),
        conclusion=["crown/chin: head-height uncertainty 5 px -> ~1.5 px",
                    "iris centre distance: 6 px -> ~2.7 px",
                    "left eye width (eyeline): 6 px -> ~1 px; matches the manual 32 px",
                    "right eye inner corner is bimodal (faint taper vs main stroke end, "
                    "~10 px apart): a definition decision for the owner, not noise",
                    "sclera opening is a different definition from the manual points"],
        owner_decisions=["eye corner = end of faint taper or end of main stroke",
                         "adopt algorithmic official points (OFFICIAL_SOURCE_MEASURED) as "
                         "targets, with independent review", "tolerance basis (6 px)"])
    write_json(out / "official_remeasure_research.json", research_record)
    summary = dict(case="morwen.face.front.ratio", substrate="M00 comparator (not current candidate)",
                   head_px=head, head_u_px=u_head, native_head_m=first["head_height_m"],
                   qualification=qual, result=result, comparability=comparability,
                   finding=("PASS is unreachable while official u > owner tolerance: improve "
                            "Layer0 landmark precision (sub-pixel, independent double annotation) "
                            "or re-base tolerance with the owner" if not all(
                                c["pass_reachable"] for c in comparability.values()) else None),
                   unblock=["#427 owner exports current .vroid to VRM (VRoid GUI) and imports it "
                            "in Blender 5.3.0; register SHA; rerun this adapter read-only",
                            "texture/render adapter for mouth line and nose shading mark"])
    write_json(out / "case_summary.json", summary)
    files = ledger(out)
    write_json(out / "studio.json", studio_record(
        asset_id="MORWEN", case_id="morwen.face.front.ratio", blueprint_summary=bp.summary(),
        groups=[result], readiness="METHOD_ISOLATED (comparator substrate)",
        qa=dict(G1="NOT_RUN", G2="NOT_RUN", G3="NOT_RUN", G4="NOT_RUN"),
        files={k: v["sha256"] for k, v in files.items() if not k.startswith("factory/")},
        limitations=["M00 is a comparator, not the current #427 candidate",
                     "front-plane ratios only; no depth from 2D",
                     "orthographic assumption for Layer0 head region unverified"]))
    ledger(out)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--front", required=True)
    parser.add_argument("--precision", required=True)
    parser.add_argument("--landmarks", required=True)
    parser.add_argument("--m00", required=True)
    parser.add_argument("--out", required=True)
    a = parser.parse_args()
    s = run(a.front, a.precision, a.landmarks, a.m00, a.out)
    print(json.dumps(dict(result={k: s["result"].get(k) for k in ("residual", "counts", "factory",
                                                                   "factory_reason")},
                          comparability=s["comparability"], finding=s["finding"]), indent=1))


if __name__ == "__main__":
    main()
