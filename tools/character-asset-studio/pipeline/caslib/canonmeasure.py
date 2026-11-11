"""Read-only landmark measurement of the director-approved canon (4 views) -> unapproved candidates.

Outputs (all new files, never into protected paths):
  measurement_evidence.json   per view/landmark: visible | estimated | unmeasurable, px + n, method, confidence
  BASE_BODY_SPEC.candidate.json  BASE_BODY_SPEC v2.0, status candidate_not_canonical
  guide_<view>.png / guide_<view>_preview.png   measured points only (unmeasurable joints are listed, not drawn)
  qa_report.json              cas/qa-report/0.5 (adoptionReady is always false here)

Rules:
* The canon is opened read-only and its SHA-256 is checked before and after.
* Only ground/foot contacts are measured automatically (alpha/foreground at the sole). Other joints come from a
  separate observations file (AI visual inspection) with explicit status and method.
* Costume outlines (hat, capelet, robe) are recorded as costume, never as body dimensions.
* BASE_BODY_SPEC v2.0 needs a value for every landmark. Unmeasurable joints therefore keep the studio template
  value but are labelled source=template_default / confidence=provisional, are listed as UNMEASURABLE in the
  evidence, and are BLOCKED in the QA report — they are never reported as measured or PASS.
"""
from pathlib import Path

from .core import (js_round, LANDMARK_KEYS, REPO_ROOT, STUDIO_DIR, VIEWS, guard_write, load_json, placement, protected_list,
                   rel, sha256_file, stable_dumps, to_norm, to_pixel)
from .brief import TEMPLATE
from .report import Checks, make_report
from .schemas import validate

CANVAS = {"width": 1200, "height": 1600}
MIN_SPAN = 8          # px: a sole row must contain a run at least this wide
PROBE = 6             # px above the lowest row where contact spans are read (same as imageqa)
SIDE_VIEWS = ("left", "right")


def canon_files(character_id):
    files = [e for e in protected_list()["files"] if f"/{character_id}/" in e["path"] and e.get("role") == "director_approved_visual_canon_4view"]
    return {Path(e["path"]).stem: e for e in files}


def _load_on_canvas(path):
    from PIL import Image
    import numpy as np
    with Image.open(path) as im:
        mode, size = im.mode, im.size
        rgba = im.convert("RGBA")
    pl = placement(size[0], size[1], CANVAS)
    if not pl["exact"]:
        rgba = rgba.resize((round(pl["w"]), round(pl["h"])), Image.LANCZOS)
        base = Image.new("RGBA", (CANVAS["width"], CANVAS["height"]), (0, 0, 0, 0))
        base.alpha_composite(rgba, (round(pl["x"]), round(pl["y"])))
        rgba = base
    a = np.asarray(rgba)
    fg = a[..., 3] >= 128
    if "A" not in mode:                       # RGB on black: background = near-black pixels
        fg &= a[..., :3].max(axis=2) > 10
    return rgba, fg, {"sourceMode": mode, "sourceSize": list(size), "placement": pl,
                      "foreground": "alpha>=128" + ("" if "A" in mode else " and max(R,G,B)>10 (RGB on black)")}


def _spans(row, min_w):
    import numpy as np
    xs = np.where(row)[0]
    if not len(xs):
        return []
    out, start = [], xs[0]
    for i in range(1, len(xs)):
        if xs[i] != xs[i - 1] + 1:
            out.append((int(start), int(xs[i - 1])))
            start = xs[i]
    out.append((int(start), int(xs[-1])))
    return [s for s in out if s[1] - s[0] + 1 >= min_w]


def measure_view(view, fg):
    import numpy as np
    rows = np.where(fg.any(axis=1))[0]
    cols = np.where(fg.any(axis=0))[0]
    ground_y = None
    for y in range(int(rows[-1]), int(rows[0]), -1):
        if _spans(fg[y], MIN_SPAN):
            ground_y = y
            break
    probe = ground_y - PROBE
    spans = _spans(fg[probe], 4)
    res = {"costumeSilhouetteBBox": [int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])],
           "costumeNote": "outline of the whole costumed figure incl. hat, capelet and robe; NOT a body dimension",
           "groundRow": ground_y, "probeRow": probe, "probeSpans": spans,
           "groundUncertaintyPx": 3,
           "groundNote": "lowest row with a >=8 px foreground run; the sole edge fades into the background over ~3 px, so the row can move by about +-3 px with the threshold"}
    lm = {}
    if view in SIDE_VIEWS:
        # standing side view: both feet overlap; the spans at the probe row are toe/heel of the near boot
        x0, x1 = spans[0][0], spans[-1][1]
        cx = (x0 + x1) / 2
        lm["footLeft"] = {"status": "visible", "px": [cx, ground_y], "confidence": "high", "method": f"near-boot sole: outer span {x0}..{x1} at row {probe} (toe and heel of one boot), y = lowest sole row"}
        lm["footRight"] = {"status": "unmeasurable", "reason": "far foot hidden behind the near foot"}
        lm["ground"] = {"status": "visible", "px": [cx, ground_y], "confidence": "high", "method": "centre of the visible sole contact; y = lowest row with a >=8 px run"}
    elif len(spans) == 2:
        (a0, a1), (b0, b1) = spans
        lm["footLeft"] = {"status": "visible", "px": [(a0 + a1) / 2, ground_y], "confidence": "high", "method": f"screen-left sole span {a0}..{a1} at row {probe}"}
        lm["footRight"] = {"status": "visible", "px": [(b0 + b1) / 2, ground_y], "confidence": "high", "method": f"screen-right sole span {b0}..{b1} at row {probe}"}
        lm["ground"] = {"status": "visible", "px": [((a0 + a1) / 2 + (b0 + b1) / 2) / 2, ground_y], "confidence": "high", "method": "midpoint of the two sole contacts; y = lowest row with a >=8 px run"}
    else:
        for k in ("footLeft", "footRight", "ground"):
            lm[k] = {"status": "unmeasurable", "reason": f"expected two sole spans at row {probe}, found {len(spans)}"}
    return res, lm


def _finish(rec):
    """Add normalised coords (studio-core rounding) and the integer px the studio would show."""
    if rec.get("px") is not None:
        raw = list(rec["px"])
        rec["px"] = [int(js_round(raw[0])), int(js_round(raw[1]))]     # integer canvas pixel (JS rounding)
        if raw != rec["px"]:
            rec["pxRaw"] = raw
        n = to_norm(rec["px"], CANVAS)
        rec["n"] = n
        rec["pxFromN"] = to_pixel(n, CANVAS)
    return rec


def draw_guides(view, rgba, lms, out_dir, overwrite, repo_root):
    from PIL import Image, ImageDraw, ImageFont
    W, H = CANVAS["width"], CANVAS["height"]
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    gy = lms["ground"]["px"][1] if lms["ground"].get("px") else None
    if gy is not None:
        d.line([0, gy, W, gy], fill=(240, 120, 60, 255), width=3)
    d.line([600, 0, 600, H], fill=(255, 255, 255, 90), width=1)
    colors = {"visible": (80, 230, 120, 255), "estimated": (255, 210, 60, 255)}
    for k in LANDMARK_KEYS:
        r = lms[k]
        if r["status"] == "unmeasurable" or not r.get("px"):
            continue
        x, y = r["px"]
        c = colors[r["status"]]
        if r["status"] == "visible":
            d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=c, width=3)
        else:
            d.rectangle([x - 9, y - 9, x + 9, y + 9], outline=c, width=3)
        dx, dy = {"kneeLeft": (-12, -40), "kneeRight": (12, 14), "footLeft": (-12, -66), "footRight": (12, -40), "ground": (12, 14)}.get(k, (12, -11))
        label = f"{k} ({r['status']}, {r['confidence']})"
        tx = x + dx - (font.getlength(label) if dx < 0 else 0)
        d.text((tx, y + dy), label, fill=c, font=font)
    um = [k for k in LANDMARK_KEYS if lms[k]["status"] == "unmeasurable"]
    lines = [f"morwen final canon · {view} · MEASUREMENT CANDIDATE (UNAPPROVED)", "circle = visible   square = estimated",
             "UNMEASURABLE (not drawn; never reported as measured):"] + [", ".join(um[i:i + 4]) for i in range(0, len(um), 4)]
    for i, t in enumerate(lines):
        d.text((40, 40 + i * 26), t, fill=(255, 255, 255, 235), font=font)
    gp = guard_write(Path(out_dir) / f"guide_{view}.png", repo_root, overwrite)
    g.save(gp, optimize=True)
    bg = Image.new("RGBA", (W, H), (58, 62, 70, 255))
    faint = rgba.copy()
    faint.putalpha(faint.getchannel("A").point(lambda a: a * 110 // 255))
    bg.alpha_composite(faint)
    bg.alpha_composite(g)
    pp = guard_write(Path(out_dir) / f"guide_{view}_preview.png", repo_root, overwrite)
    bg.convert("RGB").save(pp, optimize=True)
    return {"guide": {"path": rel(gp, repo_root), "sha256": sha256_file(gp)}, "guidePreview": {"path": rel(pp, repo_root), "sha256": sha256_file(pp)}}


def run(character_id, observations_path, out_dir, overwrite=False, repo_root=REPO_ROOT):
    obs = load_json(observations_path)
    canon = canon_files(character_id)
    out_dir = Path(out_dir)
    targets = [out_dir / n for n in ("measurement_evidence.json", "BASE_BODY_SPEC.candidate.json", "qa_report.json")]
    targets += [out_dir / f"guide_{v}{s}.png" for v in VIEWS for s in ("", "_preview")]
    for t in targets:                                   # check every output before writing anything
        guard_write(t, repo_root, overwrite)
    out_dir.mkdir(parents=True, exist_ok=True)
    ck = Checks()
    before = {}
    for v in VIEWS:
        e = canon.get(v)
        if not e:
            ck.add("canon_present", v, "BLOCKED", reason="no protected canonical image for this view")
            continue
        sha = sha256_file(Path(repo_root) / e["path"])
        before[v] = sha
        ck.add("canon_sha256_before", v, "PASS" if sha == e["sha256"] else "FAIL", detail=e["path"])
    if len(before) != 4 or any(r["result"] != "PASS" for r in ck.rows):
        return None, make_report({"kind": "canon-measurement", "characterId": character_id}, ck.rows)

    evidence = {"schema": "cas/canon-measurement/0.5", "status": "UNAPPROVED_REFERENCE", "characterId": character_id,
                "canvas": CANVAS, "observations": {"path": rel(observations_path, repo_root), "sha256": sha256_file(observations_path), "observer": obs["observer"]},
                "sideConvention": obs["sideConvention"],
                "policy": "Read-only measurement of the protected canon. visible = located on visible body; estimated = inferred from nearby visible evidence (needs human review); unmeasurable = no body evidence (costume covers it). Costume outlines are not body dimensions. Nothing here is adopted.",
                "views": {}}
    spec_lm, guides = {}, {}
    for v in VIEWS:
        e = canon[v]
        rgba, fg, meta = _load_on_canvas(Path(repo_root) / e["path"])
        auto, lm_auto = measure_view(v, fg)
        lms = {}
        for k in LANDMARK_KEYS:
            if k in lm_auto:
                rec = dict(lm_auto[k], origin="automated_alpha")
            elif k in obs["landmarks"][v]:
                rec = dict(obs["landmarks"][v][k], origin="observation")
            else:
                rec = {"status": "unmeasurable", "reason": "no observation recorded", "origin": "none"}
            lms[k] = _finish(rec)
        evidence["views"][v] = {"source": {"path": e["path"], "sha256": e["sha256"], **meta}, "automated": auto, "landmarks": lms}
        spec_lm[v] = {}
        for k in LANDMARK_KEYS:
            r = lms[k]
            if r["status"] == "unmeasurable":
                n = list(TEMPLATE[k])
                spec_lm[v][k] = {"n": n, "px": to_pixel(n, CANVAS), "confidence": "provisional", "source": "template_default"}
            else:
                conf = r["confidence"] if r["status"] == "visible" else "low"
                spec_lm[v][k] = {"n": r["n"], "px": r["pxFromN"], "confidence": conf, "source": "measured_reference"}
        guides[v] = draw_guides(v, rgba, lms, out_dir, overwrite, repo_root)
        evidence["views"][v]["guides"] = guides[v]

    # ---------- QA ----------
    ground = {v: evidence["views"][v]["landmarks"]["ground"] for v in VIEWS}
    gys = {v: g["px"][1] for v, g in ground.items() if g.get("px")}
    gxs = {v: g["px"][0] for v, g in ground.items() if g.get("px")}
    tol_y, tol_x = 6, 24
    ck.add("ground_measured_4views", "all", "PASS" if len(gys) == 4 else "FAIL", detail=gys)
    spread = max(gys.values()) - min(gys.values())
    ck.add("ground_y_consistency_4views", "all", "PASS" if spread <= tol_y else "FAIL", detail={"groundRowPx": gys, "spreadPx": spread, "tolPx": tol_y},
           reason=None if spread <= tol_y else "the four canonical images put the soles at different heights on the shared canvas; reported, not corrected (canon is protected)")
    dev = {v: round(x - 600, 1) for v, x in gxs.items()}
    bad = {v: d for v, d in dev.items() if abs(d) > tol_x}
    ck.add("ground_x_vs_anchor_4views", "all", "PASS" if not bad else "FAIL", detail={"contactX": gxs, "deltaFromAnchor600": dev, "tolPx": tol_x},
           reason=None if not bad else "contact centre is off the shared anchor x=600 in: " + ", ".join(bad))
    for v in VIEWS:
        for k in LANDMARK_KEYS:
            r = evidence["views"][v]["landmarks"][k]
            scope = f"{v}/{k}"
            if r.get("px") is not None:
                ok = r["pxFromN"] == r["px"] and to_norm(r["pxFromN"], CANVAS) == r["n"]
                ck.add("px_norm_consistency", scope, "PASS" if ok else "FAIL", detail={"px": r["px"], "n": r["n"], "pxFromN": r["pxFromN"]})
            if r["status"] == "unmeasurable":
                ck.add("landmark_measured", scope, "BLOCKED", reason="UNMEASURABLE: " + r.get("reason", ""))
                s = spec_lm[v][k]
                ck.add("unmeasured_not_promoted", scope, "PASS" if (s["source"], s["confidence"]) == ("template_default", "provisional") else "FAIL")
            elif r["origin"] == "automated_alpha":
                ck.add("landmark_measured", scope, "PASS", detail={"px": r["px"], "method": r["method"]})
            else:
                ck.add("landmark_visual_review", scope, "NOT_RUN", "human", reason=f"{r['status']} by AI visual inspection ({r['confidence']}); needs human/director confirmation")
    spec = {"schemaVersion": "2.0", "status": "candidate_not_canonical", "characterId": character_id, "presetId": "MORWEN_REAL_1200x1600",
            "canvas": CANVAS, "groundNormalized": [0.5, 0.9625], "worldScale": {"pixelsPerUnit": None},
            "coordinateSpace": "normalized canvas (0..1, origin top-left, y down); px = n * canvas size",
            "views": list(VIEWS), "landmarks": spec_lm,
            "referenceBody": [{"id": r["id"], "status": r["status"]} for r in load_json(STUDIO_DIR / "profiles" / "reference_bodies.json")["references"]]
                             + [{"id": "MORWEN_FINAL_CANON_MEASUREMENT_20261111", "status": "UNAPPROVED_PARTIAL_MEASUREMENT",
                                 "path": rel(out_dir / "measurement_evidence.json", repo_root)}],
            "assets": [{"name": Path(canon[v]["path"]).name, "view": v, "layer": "reference", "frame": 0, "sha256": canon[v]["sha256"],
                        "dimensions": evidence["views"][v]["source"]["sourceSize"], "canonical": True} for v in VIEWS],
            "notes": "UNAPPROVED measurement candidate from the final canon (read-only). Entries with source=template_default/confidence=provisional were UNMEASURABLE (covered by costume) and are template placeholders only, NOT measurements. See measurement_evidence.json. Not for adoption without director approval."}
    vs = validate(spec)
    ck.add("spec_schema_v2", "BASE_BODY_SPEC.candidate.json", vs["result"], detail=vs["errors"] or None)
    ck.add("spec_status_unapproved", "BASE_BODY_SPEC.candidate.json", "PASS" if spec["status"] == "candidate_not_canonical" else "FAIL")
    r21 = [r for r in load_json(STUDIO_DIR / "profiles" / "reference_bodies.json")["references"] if r["id"] == "MORWEN_BASE_BODY_R2.1"]
    ck.add("r21_still_blocked", "profiles/reference_bodies.json", "PASS" if r21 and r21[0]["status"] == "BLOCKED_FOR_FINAL_CANON" else "FAIL")
    for v in VIEWS:
        sha = sha256_file(Path(repo_root) / canon[v]["path"])
        ck.add("canon_sha256_after", v, "PASS" if sha == before[v] == canon[v]["sha256"] else "FAIL")
    for cid, label in (("director_confirms_landmarks", "director confirms visible/estimated landmarks"),
                       ("director_decides_unmeasurable_handling", "decide how unmeasurable joints (head top, shoulders, pelvis, neck) get a body reference, e.g. a separate base-body drawing")):
        ck.add(cid, "all", "NOT_RUN", "human", reason=label)
    rep = make_report({"kind": "canon-measurement", "characterId": character_id, "path": rel(out_dir, repo_root)}, ck.rows)
    counts = {s: sum(1 for v in VIEWS for k in LANDMARK_KEYS if evidence["views"][v]["landmarks"][k]["status"] == s) for s in ("visible", "estimated", "unmeasurable")}
    evidence["summary"] = {"landmarkStatusCounts": counts, "groundRowPx": gys, "groundSpreadPx": spread, "contactXDeltaFromAnchor": dev}
    (out_dir / "measurement_evidence.json").write_text(stable_dumps(evidence), encoding="utf-8")
    (out_dir / "BASE_BODY_SPEC.candidate.json").write_text(stable_dumps(spec), encoding="utf-8")
    (out_dir / "qa_report.json").write_text(stable_dumps(rep), encoding="utf-8")
    return evidence, rep
