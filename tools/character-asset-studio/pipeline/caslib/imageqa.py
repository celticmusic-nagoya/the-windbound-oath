"""Automated image QA for an asset set: dimensions, real alpha, anchors, frame integrity.

Everything a script can measure is classified PASS/FAIL; anything that needs a person (design match,
anatomy, age-appropriateness, costume structure) is NOT_RUN unless the asset set carries a human review
record. Missing prerequisites are BLOCKED. Nothing here edits or adopts an image.
"""
from pathlib import Path

from .core import REPO_ROOT, STUDIO_DIR, VIEWS, load_json, sha256_file, is_protected, to_norm
from .report import Checks, make_report
from .schemas import validate

DEFAULT_TOL = {"groundPx": None, "anchorXPx": None, "bboxHeightRatio": 0.08, "groundSpreadPx": None, "borderAlphaPixels": 0}
HUMAN_CHECKS = [
    ("design_matches_protected_reference", "Design matches the protected canonical reference (hair, hat, uniform, palette)"),
    ("anatomy_and_proportion", "Anatomy, head-to-body ratio and joint placement are plausible and unchanged"),
    ("age_appropriate_no_sexualisation", "Character age/body unchanged; no sexualised emphasis (Morwen is 17)"),
    ("costume_structure_not_guessed", "No unconfirmed equipment/costume structure was invented"),
]


def _tol(doc):
    c = doc["canvas"]
    t = dict(DEFAULT_TOL)
    t.update(doc.get("tolerances", {}))
    if t["groundPx"] is None:
        t["groundPx"] = max(2, round(c["height"] * 0.004))
    if t["anchorXPx"] is None:
        t["anchorXPx"] = max(2, round(c["width"] * 0.02))
    if t["groundSpreadPx"] is None:
        t["groundSpreadPx"] = max(2, round(c["height"] * 0.004))
    return t


def measure(path_or_image):
    """Alpha measurements of one PNG path or PIL image (alpha >= 128 counts as body)."""
    from PIL import Image
    import numpy as np
    if isinstance(path_or_image, Image.Image):
        im = path_or_image
    else:
        with Image.open(path_or_image) as f:
            f.load()
            im = f.copy()
            im.format = f.format
    info = {"width": im.width, "height": im.height, "mode": im.mode, "format": im.format}
    has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
    info["hasAlphaChannel"] = bool(has_alpha)
    if not has_alpha:
        return info
    a = np.asarray(im.convert("RGBA").getchannel("A"))
    info["transparentPixels"] = int((a == 0).sum())
    info["semiPixels"] = int(((a > 0) & (a < 255)).sum())
    border = np.concatenate([a[0, :], a[-1, :], a[:, 0], a[:, -1]])
    info["borderNonZero"] = int((border > 0).sum())
    body = a >= 128
    rows = np.where(body.any(axis=1))[0]
    cols = np.where(body.any(axis=0))[0]
    if not len(rows):
        info["bbox"] = None
        return info
    info["bbox"] = [int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])]
    bottom = int(rows[-1])
    probe = max(int(rows[0]), bottom - 6)          # contact x = outer sole span at bottom-6
    xs = np.where(body[probe])[0]
    info["contact"] = {"bottomRow": bottom, "probeRow": probe, "span": [int(xs[0]), int(xs[-1])], "x": (int(xs[0]) + int(xs[-1])) / 2}
    return info


def run(doc, doc_path=None, repo_root=REPO_ROOT):
    ck = Checks()
    subject = {"kind": "asset-set", "characterId": doc.get("characterId", "?")}
    if doc_path:
        subject["path"] = Path(doc_path).as_posix()
        subject["sha256"] = sha256_file(doc_path)
    v = validate(doc)
    ck.add("schema_valid", "asset-set", v["result"], detail=v["errors"] or None)
    if v["result"] != "PASS":
        for cid, _ in HUMAN_CHECKS:
            ck.add(cid, "asset-set", "BLOCKED", "human", reason="asset set is not schema-valid")
        return make_report(subject, ck.rows)
    try:
        import numpy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as e:
        ck.add("image_libraries", "asset-set", "BLOCKED", reason=f"missing dependency: {e.name}")
        return make_report(subject, ck.rows)

    canvas, anchor, kind = doc["canvas"], doc["anchor"], doc["kind"]
    ax, ay = anchor["px"]
    tol = _tol(doc)
    slot = doc.get("layer", {}).get("slot")
    has_feet = kind in ("base_body", "walk_frames", "reference") or slot in ("base", "footwear")

    # status / approval integrity
    status = doc["status"]
    if status == "DIRECTOR_APPROVED" and not any(a.get("decision") == "approved" for a in doc.get("approvals", [])):
        ck.add("approval_record", "asset-set", "FAIL", reason="DIRECTOR_APPROVED without a director approval record")
    elif status == "DIRECTOR_APPROVED":
        ck.add("approval_record", "asset-set", "PASS", "human", detail=doc["approvals"])
    else:
        ck.add("status_unapproved", "asset-set", "PASS", detail=status)
    ck.add("anchor_inside_canvas", "asset-set", "PASS" if 0 <= ax < canvas["width"] and 0 <= ay < canvas["height"] else "FAIL", detail=anchor["px"])
    n = to_norm(anchor["px"], canvas)
    ck.add("anchor_px_norm_consistent", "asset-set", "PASS" if all(abs(n[i] - anchor["n"][i]) <= 1e-4 for i in range(2)) else "FAIL", detail={"px": anchor["px"], "n": anchor["n"], "expectedN": n})

    blocked_refs = {r["path"]: r for r in load_json(STUDIO_DIR / "profiles" / "reference_bodies.json")["references"] if r["status"].startswith("BLOCKED")}
    for r in doc.get("references", []):
        p = repo_root / r["path"]
        if r["path"] in blocked_refs:
            ck.add("reference_usable", r["path"], "BLOCKED", reason=blocked_refs[r["path"]]["reason"][:200])
        elif not p.exists():
            ck.add("reference_present", r["path"], "BLOCKED", reason="reference file not found")
        else:
            ok = sha256_file(p) == r["sha256"]
            ck.add("reference_sha256", r["path"], "PASS" if ok else "FAIL", detail=None if ok else "SHA-256 differs from the recorded reference")

    for view in VIEWS:
        frames = doc["views"].get(view)
        if frames is None:
            if kind == "base_body":
                ck.add("view_present", view, "FAIL", reason="base body needs all four views")
            continue
        nums = [f["frame"] for f in frames]
        expected = list(range(doc["frameCount"]))
        missing = [i for i in expected if i not in nums]
        extra = sorted({i for i in nums if i not in expected})
        dup = sorted({i for i in nums if nums.count(i) > 1})
        ck.add("frame_set_complete", view, "PASS" if not (missing or extra or dup) else "FAIL",
               detail={"expected": doc["frameCount"], "missing": missing, "extra": extra, "duplicates": dup})
        meas = {}
        for fr in sorted(frames, key=lambda f: f["frame"]):
            scope = f"{view}/f{fr['frame']:02d}"
            p = repo_root / fr["file"]["path"]
            if not p.exists():
                ck.add("file_present", scope, "FAIL", reason=f"missing file {fr['file']['path']}")
                continue
            sha = sha256_file(p)
            if "sha256" in fr["file"]:
                ck.add("file_sha256", scope, "PASS" if sha == fr["file"]["sha256"] else "FAIL", detail=None if sha == fr["file"]["sha256"] else {"recorded": fr["file"]["sha256"], "actual": sha})
            if is_protected(fr["file"]["path"]) and kind != "reference":
                ck.add("not_a_protected_asset", scope, "FAIL", reason="candidate entry points at a protected canonical asset")
            try:
                m = measure(p)
            except Exception as e:  # unreadable image
                ck.add("image_readable", scope, "FAIL", reason=str(e)[:200])
                continue
            m["sha256"] = sha
            meas[fr["frame"]] = m
            ck.add("dimensions", scope, "PASS" if (m["width"], m["height"]) == (canvas["width"], canvas["height"]) else "FAIL",
                   detail={"actual": [m["width"], m["height"]], "expected": [canvas["width"], canvas["height"]]})
            ck.add("alpha_channel", scope, "PASS" if m["hasAlphaChannel"] else "FAIL", detail=m["mode"])
            if not m["hasAlphaChannel"]:
                continue
            ck.add("real_transparency", scope, "PASS" if m["transparentPixels"] > 0 else "FAIL", detail={"alpha0": m["transparentPixels"]},
                   reason=None if m["transparentPixels"] else "no alpha=0 pixels (baked background or checkerboard?)")
            ck.add("transparent_border", scope, "PASS" if m["borderNonZero"] <= tol["borderAlphaPixels"] else "FAIL", detail={"nonZeroBorderPixels": m["borderNonZero"]})
            if m.get("bbox") is None:
                ck.add("content_present", scope, "FAIL", reason="no pixels with alpha >= 128")
                continue
            ck.add("content_present", scope, "PASS", detail={"bbox": m["bbox"]})
            if has_feet:
                dy = m["contact"]["bottomRow"] - ay
                ck.add("ground_contact", scope, "PASS" if abs(dy) <= tol["groundPx"] else "FAIL",
                       detail={"bottomRow": m["contact"]["bottomRow"], "anchorY": ay, "deltaPx": dy, "tolPx": tol["groundPx"]})
                if kind != "walk_frames":
                    dx = m["contact"]["x"] - ax
                    ck.add("anchor_x_at_contact", scope, "PASS" if abs(dx) <= tol["anchorXPx"] else "FAIL",
                           detail={"contactSpan": m["contact"]["span"], "contactX": m["contact"]["x"], "anchorX": ax, "deltaPx": dx, "tolPx": tol["anchorXPx"]})
            for name, nxy in fr.get("anchors", {}).items():
                ck.add("frame_anchor_in_range", f"{scope}/{name}", "PASS" if all(0 <= c <= 1 for c in nxy) else "FAIL", detail=nxy)
        # frame-to-frame consistency
        if len(meas) >= 2:
            sizes = {(m["width"], m["height"]) for m in meas.values()}
            ck.add("frame_size_consistency", view, "PASS" if len(sizes) == 1 else "FAIL", detail=sorted(sizes))
            withbox = {f: m for f, m in meas.items() if m.get("bbox")}
            if has_feet and len(withbox) >= 2:
                bottoms = [m["contact"]["bottomRow"] for m in withbox.values()]
                ck.add("ground_consistency", view, "PASS" if max(bottoms) - min(bottoms) <= tol["groundSpreadPx"] else "FAIL",
                       detail={"min": min(bottoms), "max": max(bottoms), "tolPx": tol["groundSpreadPx"]})
            if len(withbox) >= 2:
                hs = [m["bbox"][3] - m["bbox"][1] + 1 for m in withbox.values()]
                ratio = (max(hs) - min(hs)) / max(hs)
                ck.add("bbox_height_consistency", view, "PASS" if ratio <= tol["bboxHeightRatio"] else "FAIL",
                       detail={"min": min(hs), "max": max(hs), "ratio": round(ratio, 4), "tol": tol["bboxHeightRatio"]})
            if kind == "walk_frames":
                shas = [meas[f]["sha256"] for f in sorted(meas)]
                same = [sorted(meas)[i] for i in range(1, len(shas)) if shas[i] == shas[i - 1]]
                ck.add("no_identical_consecutive_frames", view, "PASS" if not same else "FAIL", detail={"repeatedAt": same},
                       reason=None if not same else "consecutive frames are byte-identical (reuse is not animation material)")
        elif len(meas) == 1 and doc["frameCount"] > 1:
            ck.add("frame_size_consistency", view, "NOT_RUN", reason="only one readable frame")

    # human-only checks
    reviews = doc.get("humanReviews", {})
    cons = STUDIO_DIR / "profiles" / f"{doc['characterId']}_constraints.json"
    human = list(HUMAN_CHECKS)
    if cons.exists():
        human += [(f"constraint:{c['id']}", c["label"]) for c in load_json(cons)["constraints"]]
    for cid, label in human:
        r = reviews.get(cid)
        if r:
            ck.add(cid, "asset-set", r["result"], "human", detail={"by": r["by"], "date": r["date"], "note": r.get("note")})
        else:
            ck.add(cid, "asset-set", "NOT_RUN", "human", reason="needs a human/director review: " + label)
    return make_report(subject, ck.rows)
