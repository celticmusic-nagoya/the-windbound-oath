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
    raw = model.read_bytes()
    return dict(scope="PRIVATE_TRANSFER_CANDIDATE_REVIEW_REQUIRED", native_sha256=SOURCE,
                vrm_sha256=sha256(raw).hexdigest(), vrm_structure=inspect_vrm(raw),
                capture_sha256=views, export_provenance=export_provenance)


if __name__ == "__main__":
    captures, model, source, provenance, receipt = [Path(arg) for arg in sys.argv[1:]]
    result = verify(captures, model, source, json.loads(provenance.read_text()))
    with receipt.open("x", encoding="utf-8") as output:
        json.dump(result, output, indent=2)
