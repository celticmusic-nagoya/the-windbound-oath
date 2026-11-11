"""Per-view working-coordinate normalisation (TASK A, v0.7).

Each protected canonical view is mapped onto the shared 1200x1600 canvas so that its MEASURED ground contact
(from the v0.6 measurement evidence, never a guessed constant) lands on the reference contact (600, 1540).

  canvas_point = placement(source) then integer translation (dx, dy)
  dx, dy = reference - measured contact   (both in canvas pixels, JS rounding)

* Sources are read-only (SHA-256 checked before/after); outputs go to a separate directory.
* The translation is an integer shift: every placed pixel is copied unchanged (no resampling in this step).
  The placement step is the studio's uniform scale (only for 1152x1536 sources), deterministic LANCZOS.
* RGB sources stay RGB (no alpha is invented; exposed area = the source's black background);
  RGBA sources stay RGBA (exposed area = alpha 0).
* Aligning the ground contact is NOT skeleton alignment. Body proportions are not evaluated here.
"""
from pathlib import Path

from .core import REPO_ROOT, guard_write, js_round, load_json, rel, sha256_file, stable_dumps
from .canonmeasure import CANVAS, _load_on_canvas, measure_view
from .report import Checks, make_report

REFERENCE_CONTACT = [600, 1540]
SCHEMA = "cas/view-transforms/0.7"


def transforms_from_evidence(evidence_path, reference=REFERENCE_CONTACT):
    ev = load_json(evidence_path)
    out = {}
    for v, d in ev["views"].items():
        g = d["landmarks"]["ground"]
        if g["status"] == "unmeasurable" or not g.get("px"):
            raise ValueError(f"{v}: ground contact was not measured; refusing to guess a transform")
        gx, gy = g["px"]
        dx, dy = int(js_round(reference[0] - gx)), int(js_round(reference[1] - gy))
        pl = d["source"]["placement"]
        out[v] = {"source": {"path": d["source"]["path"], "sha256": d["source"]["sha256"], "mode": d["source"]["sourceMode"], "size": d["source"]["sourceSize"]},
                  "measuredContact": {"px": [gx, gy], "pxRaw": g.get("pxRaw", [gx, gy]), "method": g["method"]},
                  "placement": pl, "translate": [dx, dy],
                  "affine": [[pl["scale"], 0, pl["x"] + dx], [0, pl["scale"], pl["y"] + dy]],
                  "fill": "black opaque (source background, RGB)" if "A" not in d["source"]["sourceMode"] else "alpha 0 (RGBA)"}
    return out


def _shift(img, dx, dy, fill):
    from PIL import Image
    out = Image.new(img.mode, img.size, fill)
    out.paste(img, (dx, dy))
    return out


def run(evidence_path, out_dir, overwrite=False, repo_root=REPO_ROOT):
    from PIL import Image
    import numpy as np
    out_dir = Path(out_dir)
    tf = transforms_from_evidence(evidence_path)
    targets = [out_dir / "view_transforms.json", out_dir / "normalize_qa.json"] + [out_dir / f"{v}.png" for v in tf]
    for t in targets:
        guard_write(t, repo_root, overwrite)
    out_dir.mkdir(parents=True, exist_ok=True)
    ck = Checks()
    doc = {"schema": SCHEMA, "status": "UNAPPROVED_REFERENCE", "canvas": CANVAS, "referenceContact": REFERENCE_CONTACT,
           "derivedFrom": {"path": rel(evidence_path, repo_root), "sha256": sha256_file(evidence_path)},
           "policy": "Working copies for production guides only — not canon, not adoptable. Ground-contact alignment only; skeleton/proportion consistency is NOT evaluated by this transform.",
           "skeletonConsistency": "NOT_EVALUATED", "views": {}}
    for v, t in tf.items():
        src = Path(repo_root) / t["source"]["path"]
        before = sha256_file(src)
        ck.add("source_sha256_before", v, "PASS" if before == t["source"]["sha256"] else "FAIL")
        rgba, fg, meta = _load_on_canvas(src)
        rgb_src = "A" not in meta["sourceMode"]
        placed = rgba.convert("RGB") if rgb_src else rgba
        dx, dy = t["translate"]
        fill = (0, 0, 0) if rgb_src else (0, 0, 0, 0)
        out = _shift(placed, dx, dy, fill)
        # pixel/alpha preservation: every in-bounds placed pixel is copied unchanged; no foreground pixel is clipped
        a, b = np.asarray(placed), np.asarray(out)
        H, W = a.shape[:2]
        ys, xs = slice(max(0, -dy), min(H, H - dy)), slice(max(0, -dx), min(W, W - dx))
        yd, xd = slice(ys.start + dy, ys.stop + dy), slice(xs.start + dx, xs.stop + dx)
        same = bool((a[ys, xs] == b[yd, xd]).all())
        keep = np.zeros_like(fg); keep[ys, xs] = True
        clipped = int((fg & ~keep).sum())
        ck.add("pixels_alpha_preserved", v, "PASS" if same and clipped == 0 else "FAIL",
               detail={"mode": out.mode, "translate": [dx, dy], "copiedRegionIdentical": same, "clippedForegroundPixels": clipped})
        p = out_dir / f"{v}.png"
        out.save(p, optimize=False, compress_level=9)
        # re-measure on the normalised image with the same rules as v0.6
        _, fg2, _ = _load_on_canvas(p)
        auto, lm = measure_view(v, fg2)
        g = lm["ground"]
        got = [int(js_round(g["px"][0])), g["px"][1]] if g.get("px") else None
        ck.add("contact_on_reference", v, "PASS" if got == REFERENCE_CONTACT else "FAIL", detail={"measuredAfter": got, "raw": g.get("px"), "reference": REFERENCE_CONTACT})
        after = sha256_file(src)
        ck.add("source_sha256_after", v, "PASS" if after == before == t["source"]["sha256"] else "FAIL")
        t["output"] = {"path": rel(p, repo_root), "sha256": sha256_file(p), "mode": out.mode}
        t["measuredAfter"] = {"px": got, "raw": g.get("px")}
        doc["views"][v] = t
    after_xy = {v: tuple(d["measuredAfter"]["px"]) for v, d in doc["views"].items() if d["measuredAfter"]["px"]}
    ck.add("contacts_identical_4views", "all", "PASS" if len(set(after_xy.values())) == 1 and len(after_xy) == 4 else "FAIL", detail={k: list(x) for k, x in after_xy.items()})
    ck.add("skeleton_consistency", "all", "NOT_RUN", "human", reason="contact alignment does not show that body proportions match across views")
    rep = make_report({"kind": "view-normalisation", "path": rel(out_dir, repo_root)}, ck.rows, adoption_subject=False)
    (out_dir / "view_transforms.json").write_text(stable_dumps(doc), encoding="utf-8")
    (out_dir / "normalize_qa.json").write_text(stable_dumps(rep), encoding="utf-8")
    return doc, rep
