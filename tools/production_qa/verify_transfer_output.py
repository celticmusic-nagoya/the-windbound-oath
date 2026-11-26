"""Prepare a private VRM transfer receipt from actual worker outputs."""
from hashlib import sha256
import json
from pathlib import Path
import sys

from PIL import Image

from import_vrm_transfer import inspect_vrm

SOURCE = "acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a"
VIEWS = ("front", "left4", "left8", "right4")


def verify(out, model, source, export_provenance):
    if model.suffix != ".vrm" or model.is_symlink() or source.is_symlink():
        raise ValueError("require a regular VRM and native source copy")
    if sha256(source.read_bytes()).hexdigest() != SOURCE:
        raise ValueError("native source changed")
    for phase in ("before", "after-views", "after-export"):
        if (out / f"native-{phase}.txt").read_text().strip() != SOURCE:
            raise ValueError(f"native source receipt mismatch: {phase}")
    if (export_provenance.get("app_version") != "2.16.0"
            or export_provenance.get("source_sha256") != SOURCE
            or not export_provenance.get("license_review_ref")):
        raise ValueError("missing reviewed VRoid export provenance or license reference")
    views = {}
    for view in VIEWS:
        shot = out / f"{view}.png"
        with Image.open(shot) as image:
            if image.format != "PNG":
                raise ValueError("capture is not an original PNG")
            image.verify()
        views[view] = sha256(shot.read_bytes()).hexdigest()
    if len(set(views.values())) != len(VIEWS):
        raise ValueError("duplicate source captures")
    # Only capture margin evidence; never infer exact angles or visible feet from this heuristic.
    rows = []
    for line in (out / "frame-margin.txt").read_text().splitlines():
        view, attempt, action, xmin, ymin, xmax, ymax, count, margin, good = line.split()
        if view not in VIEWS or action not in {"default", "pan_up", "undo_reversed_pan"}:
            raise ValueError("unknown capture state")
        attempt, xmin, ymin, xmax, ymax, count, margin, good = map(
            int, (attempt, xmin, ymin, xmax, ymax, count, margin, good))
        if not (0 <= attempt <= 3 and 298 <= xmin <= xmax <= 725
                and 104 <= ymin <= ymax <= 705 and 0 <= count <= 428 * 602
                and margin == min(xmin - 298, 725 - xmax, ymin - 104, 705 - ymax)
                and good == int(count >= 1500 and ymax-ymin >= 120 and margin >= 12)):
            raise ValueError("invalid capture margin receipt")
        rows.append(dict(view=view, attempt=attempt, action=action,
                         bbox=[xmin,ymin,xmax,ymax], foreground_pixels=count,
                         margin=margin, margin_pass=bool(good)))
    final = {}
    for view in VIEWS:
        attempts = [r for r in rows if r["view"] == view]
        if not attempts or [r["attempt"] for r in attempts] != list(range(len(attempts))):
            raise ValueError("missing or unordered capture attempts")
        final[view] = attempts[-1]
    raw = model.read_bytes()
    return dict(scope="PRIVATE_TRANSFER_CANDIDATE_REVIEW_REQUIRED", native_sha256=SOURCE,
                capture_frame_status="MARGIN_HEURISTIC_ONLY" if all(r["margin_pass"] for r in final.values()) else "HOLD",
                capture_frame_measurements=final, capture_frame_attempts=rows,
                vrm_sha256=sha256(raw).hexdigest(), vrm_structure=inspect_vrm(raw),
                capture_sha256=views, export_provenance=export_provenance)


if __name__ == "__main__":
    captures, model, source, provenance, receipt = [Path(arg) for arg in sys.argv[1:]]
    result = verify(captures, model, source, json.loads(provenance.read_text()))
    with receipt.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
