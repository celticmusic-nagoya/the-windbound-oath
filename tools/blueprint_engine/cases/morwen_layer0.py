"""Character connection case: Morwen official Layer0 four views + VRoid native.

* Silhouette groups: recorded alpha-silhouette measurements (artifact 14602858760)
  are re-measured from the SHA-verified official PNGs through the #468 Factory
  read-only stage (OFFICIAL_SOURCE_MEASURED reproducibility).
* Face group: manual ESTIMATED projected face metrics (main precision_blueprint_v2)
  compiled as targets for the VRoid native; no qualified matched-camera VRoid
  measurement exists, so hand-off is BLOCKED (fail closed, no edit).
* A 3D value asserted from the 2D views is rejected by the blueprint guard.
Projection of the PNGs is UNKNOWN_FROM_PNG (no camera calibration).
"""
import argparse
import json
from pathlib import Path
import shutil

import PIL

from ..contract import OperationRegistry, compile_target, handoff
from ..evidence import ESTIMATED, OFFICIAL_SOURCE_MEASURED, UNDETERMINED
from ..export import ledger, scanline_svg, studio_record, write_json
from ..geometry import Blueprint, BlueprintError
from ..measure import ImageAlphaAdapter
from ..sources import file_sha256, register_source
from ._run import run_group

VIEWS = {"front": ("7809.png", "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"),
         "right": ("7807.png", "9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737"),
         "back": ("7810.png", "b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"),
         "left": ("7808.png", "69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa")}
# view -> file/SHA as registered in reference_verification.json and layer0_landmarks_v1.json
PX = "source pixels"
FACE_TOL = 6.0            # owner #427 blueprint-targets.json tolerance for face metrics
FACE_U = 3.0              # face_front_review stated point uncertainty


def cs(view):
    return f"Morwen Layer0 {view} original pixels, origin top-left, x right, y down"


def qualify(png, work):
    work.mkdir(parents=True, exist_ok=True)
    copy_path = work / "q.png"
    shutil.copyfile(png, copy_path)
    probe = ImageAlphaAdapter({"a": ("scan", 500, "left")}, "q")
    first, second = probe.raw(copy_path), probe.raw(copy_path)
    record = dict(operation="blueprint_engine.measure.image_alpha.v1", kind="read_only_measure",
                  native_sha256=file_sha256(copy_path), pillow=PIL.__version__,
                  repeat_identical=first == second, threshold=128,
                  definition="inclusive integer x/y bounds of alpha >= 128")
    record["qualified"] = record["repeat_identical"]
    shutil.rmtree(work)
    return record


def build(layer0_dir, silhouette_json, precision_json, vroid):
    layer0_dir = Path(layer0_dir)
    silhouette = json.loads(Path(silhouette_json).read_text())
    precision = json.loads(Path(precision_json).read_text())
    bp = Blueprint(blueprint_id="MORWEN.layer0-connection.v1", asset_id="MORWEN",
                   stage="blueprint-measurement-audit", status="ENGINE_CONNECTION_TEST",
                   canon_status="OFFICIAL_LAYER0_REFERENCE; targets provisional, not adopted")
    for view, (name, sha) in VIEWS.items():
        bp.add_source(register_source(
            layer0_dir / name, source_id=f"layer0.{view}", role="OFFICIAL_CANON",
            projection="image-2d-uncalibrated", coordinate_system=cs(view), units=PX,
            expected_sha256=sha, view=view,
            provenance="director-designated Layer0 four view (2026-11-16); artifact 14602858760",
            license="project-original; private, not for publication"))
    bp.add_source(register_source(
        silhouette_json, source_id="record.silhouette", role="VERIFICATION", projection="data",
        coordinate_system="per-view source pixels", units=PX,
        provenance="reference_silhouette_landmarks.json, artifact 14602858760",
        license="project-original"))
    bp.add_source(register_source(
        precision_json, source_id="record.precision_v2", role="REFERENCE", projection="data",
        coordinate_system="per-view source pixels", units=PX,
        provenance="main tools/morwen_authored_sculpt/precision_blueprint_v2.json "
                   f"({precision['status']})", license="project-original"))
    bp.add_source(register_source(
        vroid, source_id="native.vroid", role="NATIVE_WORKING", projection="native-3d",
        coordinate_system="VRoid native (opaque)", units="UNKNOWN",
        provenance="model.vroid, artifact 14754066570 (#427 morwen-native-editor-checkpoint-"
                   "not-adopted)", license="project-original; private"))
    selectors, rejected = {}, []
    for view, record in silhouette["source_views"].items():
        source = f"layer0.{view}"
        if (record["file"], record["sha256"]) != VIEWS[view]:
            raise BlueprintError(f"silhouette record {view} is bound to another source file")
        bbox = record["alpha_bbox_xyxy"]
        bp.add_element(element_id=f"{view}.alpha_bbox", kind="silhouette", module="body",
                       sources=[source], evidence=OFFICIAL_SOURCE_MEASURED,
                       coordinate_system=cs(view), units=PX, dims=2, value=bbox, uncertainty=0.0,
                       notes="alpha silhouette, not anatomy")
        metrics = {}
        for i, axis in enumerate(("x0", "y0", "x1", "y1")):
            metrics[f"bbox.{axis}"] = dict(element=f"{view}.alpha_bbox", select=i,
                                           value=float(bbox[i]), tolerance=0.0, uncertainty=0.0,
                                           evidence=OFFICIAL_SOURCE_MEASURED)
            selectors[(view, f"bbox.{axis}")] = ("bbox", i)
        for row in record["silhouette_scanlines"]:
            y = row["y"]
            eid = f"{view}.scan.{y}"
            bp.add_element(element_id=eid, kind="section", module="body", sources=[source],
                           evidence=OFFICIAL_SOURCE_MEASURED, coordinate_system=cs(view),
                           units=PX, dims=1, value=[row["left_x"], row["right_x"]],
                           uncertainty=0.0, notes="horizontal alpha section; anatomy UNDETERMINED")
            for i, side in enumerate(("left", "right")):
                key = f"scan.{y}.{side}"
                metrics[key] = dict(element=eid, select=i, value=float(row[f"{side}_x"]),
                                    tolerance=0.0, uncertainty=0.0,
                                    evidence=OFFICIAL_SOURCE_MEASURED)
                selectors[(view, key)] = ("scan", y, side)
        bp.add_group(target_id=f"morwen.layer0.{view}.silhouette",
                     measurement_id=f"alpha128.{view}", coordinate_system=cs(view), units=PX,
                     projection="image-2d-uncalibrated", metrics=metrics,
                     operation_id="blueprint_engine.measure.image_alpha.v1",
                     protection_scope_id=f"layer0.{view}.file",
                     tolerance_basis="exact reproducibility of recorded official measurement")
    face = precision["face_front_review"]
    for name, xy in face["points"].items():
        bp.add_element(element_id=f"front.face.{name}", kind="landmark", module="face",
                       sources=["layer0.front"], evidence=ESTIMATED, coordinate_system=cs("front"),
                       units=PX, dims=2, value=xy, uncertainty=FACE_U, visibility="visible",
                       method=face["method"])
    bp.add_element(element_id="front.face.hairline", kind="landmark", module="face",
                   sources=["layer0.front"], evidence=UNDETERMINED, coordinate_system=cs("front"),
                   units=PX, dims=2, value=None, visibility="occluded",
                   notes="covered by fringe (layer0_landmarks_v1)")
    try:   # guard demonstration on real sources: eye-socket depth from four 2D views
        bp.add_element(element_id="face.eye_socket_depth_3d", kind="landmark", module="face",
                       sources=["layer0.front", "layer0.right"], evidence=ESTIMATED,
                       coordinate_system=cs("front"), units=PX, dims=3, value=[188, 125, 12],
                       uncertainty=3.0)
    except BlueprintError as exc:
        rejected.append(dict(element="face.eye_socket_depth_3d", reason=str(exc)))
    pm = face["projected_metrics_px"]
    refs = dict(eye_width_left="left_outer_eye", eye_width_right="right_outer_eye",
                iris_center_distance="left_iris_center", inner_eye_gap="left_inner_eye",
                mouth_width="mouth_left", nose_to_chin_vertical="nose_tip")
    bp.add_group(target_id="morwen.face.front.projected", measurement_id="matched-front-render-px",
                 coordinate_system=cs("front"), units=PX, projection="image-2d-uncalibrated",
                 metrics={k: dict(element=f"front.face.{refs[k]}", value=float(v),
                                  tolerance=FACE_TOL, uncertainty=2 * FACE_U, evidence=ESTIMATED)
                          for k, v in pm.items()},
                 operation_id="morwen.vroid.matched_front_render_measure",
                 protection_scope_id="morwen.vroid.protected_modules",
                 tolerance_basis="owner #427 blueprint-targets.json (6 px); distance of two "
                                 "estimated points -> u = 2 x 3 px")
    bp.add_question("camera", "Layer0 PNG projection/camera calibration unknown; 3D targets "
                    "require reconstruction with a calibrated method.", ["3d targets"])
    bp.add_question("vroid-measure", "No qualified matched-camera VRoid render measurement; "
                    "face targets cannot be measured on the native.",
                    ["morwen.face.front.projected"])
    return bp, selectors, rejected


def run(layer0_dir, silhouette_json, precision_json, vroid, out):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    bp, selectors, rejected = build(layer0_dir, silhouette_json, precision_json, vroid)
    qual = qualify(Path(layer0_dir) / VIEWS["front"][0], out / "qual")
    write_json(out / "qualification.json", qual)
    registry = OperationRegistry()
    registry.register("blueprint_engine.measure.image_alpha.v1", kind="read_only_measure",
                      qualified=qual["qualified"],
                      evidence_sha256=file_sha256(out / "qualification.json"))
    registry.register("morwen.vroid.matched_front_render_measure", kind="native_measure",
                      qualified=False, notes="requires calibrated VRoid camera + render")
    write_json(out / "blueprint.json", bp.to_dict())
    deps = {"silhouette_record": bp.data["sources"]["record.silhouette"]["sha256"],
            "blueprint": bp.digest()}
    results = []
    for view, (name, sha) in VIEWS.items():
        target_id = f"morwen.layer0.{view}.silhouette"
        keys = bp.data["groups"][target_id]["metrics"]
        adapter = ImageAlphaAdapter({k: selectors[(view, k)] for k in keys}, f"layer0.{view}.file")
        result, target, report = run_group(bp, target_id, registry, adapter,
                                           native=Path(layer0_dir) / name, native_sha=sha,
                                           baseline=sha, dependencies=deps, out=out)
        results.append(result)
        rows = [(int(k.split(".")[1]), (report["metrics"][k]["target"],
                                         report["metrics"][k.replace("left", "right")]["target"]),
                 (report["metrics"][k]["actual"],
                  report["metrics"][k.replace("left", "right")]["actual"]),
                 "PASS" if report["metrics"][k]["state"] == report["metrics"][
                     k.replace("left", "right")]["state"] == "PASS" else "OUTSIDE")
                for k in keys if k.startswith("scan.") and k.endswith(".left")]
        scanline_svg(out / f"preview_{view}_sections.svg",
                     f"Morwen Layer0 {view}: alpha sections target vs measured", [384, 1024], rows)
    vroid_sha = bp.data["sources"]["native.vroid"]["sha256"]
    target, request, issues = compile_target(
        bp, "morwen.face.front.projected", registry, native_sha256=vroid_sha,
        protected_baseline_sha256="0" * 64, dependency_hashes=deps)
    gate = handoff(target, request, issues)
    gate["unblock"].append("supply a calibrated front camera for the VRoid native and a "
                           "qualified render-measurement adapter; protected module fingerprint "
                           "baseline is UNKNOWN (placeholder all-zero, fail closed)")
    write_json(out / "targets" / "morwen.face.front.projected.json",
               dict(target=target, request=request))
    write_json(out / "handoff" / "morwen.face.front.projected.json", gate)
    results.append(dict(target_id="morwen.face.front.projected", residual="NOT_RUN",
                        factory_ready=gate["factory_ready"], handoff_issues=gate["issues"],
                        factory="BLOCKED", factory_reason="handoff: " + ", ".join(gate["issues"])))
    summary = dict(case="morwen-layer0", qualification=qual, results=results,
                   rejected_elements=rejected, open_questions=bp.data["open_questions"])
    write_json(out / "case_summary.json", summary)
    files = ledger(out)
    write_json(out / "studio.json", studio_record(
        asset_id="MORWEN", case_id="morwen.layer0-connection", blueprint_summary=bp.summary(),
        groups=results, readiness="ISOLATED_PASS (official-source measurement only)",
        qa=dict(G1="NOT_RUN", G2="NOT_RUN", G3="NOT_RUN", G4="NOT_RUN"),
        files={k: v["sha256"] for k, v in files.items() if not k.startswith("factory/")},
        limitations=["official PNGs are private; previews embed no source pixels",
                     "VRoid native measurement BLOCKED (no qualified adapter)",
                     "no 3D values inferred from 2D views"]))
    ledger(out)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layer0", required=True)
    parser.add_argument("--silhouette", required=True)
    parser.add_argument("--precision", required=True)
    parser.add_argument("--vroid", required=True)
    parser.add_argument("--out", required=True)
    a = parser.parse_args()
    s = run(a.layer0, a.silhouette, a.precision, a.vroid, a.out)
    print(json.dumps([{k: r.get(k) for k in ("target_id", "residual", "counts", "factory",
                                              "handoff_issues")} for r in s["results"]], indent=1))
    print(json.dumps(s["rejected_elements"], indent=1))


if __name__ == "__main__":
    main()
