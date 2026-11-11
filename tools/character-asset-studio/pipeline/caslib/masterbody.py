"""Layer 0 master-body CANDIDATE (v0.8): one shared 3D skeleton projected into the four views.

* Every parameter carries a status: VERIFIED (automated canon measurement), ESTIMATED (AI visual observation),
  DESIGNED_CANDIDATE (new design value derived by a stated rule), UNKNOWN. Designed values are never presented
  as measurements.
* Front/back use a left-right symmetric skeleton; side views are the SAME 3D joints projected sideways.
* Structure guides are neutral mannequin shapes (head, ribcage, pelvis, limb capsules) — no anatomical detail.
  Guide PNGs contain no canon pixels; the *_overlay.png comparison images are separate.
* Nothing is adopted; final design/skeleton adoption stays NOT_RUN.
"""
import math
from pathlib import Path

from .core import REPO_ROOT, VIEWS, guard_write, js_round, load_json, protected_list, rel, sha256_file, stable_dumps, to_norm
from .imageqa import design_protection_checks, measure
from .report import Checks, make_report
from .schemas import validate

CANVAS = {"width": 1200, "height": 1600}
CX, GROUND = 600, 1540
R = lambda v: int(js_round(v))  # noqa: E731


def design_parameters(obs, layer0_evidence):
    """All shared parameters with status and derivation (rules are explicit; nothing is guessed silently)."""
    o = {k: v["value"] for k, v in obs["observations"].items()}
    P = {}

    def put(name, value, status, derivation):
        P[name] = {"value": value, "unit": "px", "status": status, "derivation": derivation}
    put("groundY", GROUND, "VERIFIED", "normalised sole contact, identical in all four views (v0.7 TASK A)")
    put("centerX", CX, "VERIFIED", "normalised contact x, identical in all four views")
    eye, chin = o["front.eyeLineY"], o["front.chinY"]
    put("chinY", chin, "ESTIMATED", "front observation (AI visual)")
    eye_ratio = 0.58
    hh = R((chin - eye) / (1 - eye_ratio))
    put("headHeight", hh, "DESIGNED_CANDIDATE", f"(chinY - eyeLineY) / (1 - {eye_ratio}): eye line placed at 58% of the head height from the top")
    put("headTopY", chin - hh, "DESIGNED_CANDIDATE", "chinY - headHeight; skull top is hidden by the hat (UNKNOWN in the canon); range for review 167..186 (eye ratio 0.55..0.60)")
    hw = R(o["front.faceWidthAtEyes"] * 1.08)
    put("headWidth", hw, "DESIGNED_CANDIDATE", "faceWidthAtEyes x 1.08 (skull slightly wider than the cheeks)")
    put("headDepth", R(hh * 0.9), "DESIGNED_CANDIDATE", "0.9 x headHeight (side profile of the skull)")
    put("neckBaseY", chin + R(0.375 * hh), "DESIGNED_CANDIDATE", "chinY + 0.375 x headHeight")
    put("shoulderY", max(o["front.capeletRidgeY"] + 12, chin + R(0.375 * hh) + 35), "DESIGNED_CANDIDATE",
        "max(capelet ridge + 12, neckBase + 35): joint stays under the capelet surface (the capelet itself is NOT a body dimension)")
    put("shoulderHalfWidth", R(0.92 * hw), "DESIGNED_CANDIDATE", "0.92 x headWidth (shoulder width = 1.84 head widths)")
    wl, wr = o["front.wristLeft"], o["front.wristRight"]
    wy = (wl[1] + wr[1]) / 2
    wx = ((CX - wl[0]) + (wr[0] - CX)) / 2
    put("wristHalfSpanFront", R(wx), "ESTIMATED", "mean of the two front wrist observations (arms slightly abducted)")
    put("wristYFront", R(wy), "ESTIMATED", "mean of the two front wrist observations")
    dx, dy = R(wx) - P["shoulderHalfWidth"]["value"], R(wy) - P["shoulderY"]["value"]
    put("armLength", R(math.hypot(dx, dy)), "DESIGNED_CANDIDATE", "distance shoulder joint -> observed front wrist; elbow at the midpoint")
    put("ribcageBottomY", R(o["front.waistbandY"] - 0.25 * hh), "DESIGNED_CANDIDATE", "waistband - 0.25 x headHeight (waistband is costume; used only as a reference line)")
    put("pelvisY", R(o["front.waistbandY"] + 0.65 * hh), "DESIGNED_CANDIDATE", "waistband + 0.65 x headHeight: hip-joint centre below the skirt waistband")
    put("hipHalfWidth", R(0.4 * hw), "DESIGNED_CANDIDATE", "0.4 x headWidth (hip joints)")
    put("pelvisHalfWidth", R(0.62 * hw), "DESIGNED_CANDIDATE", "0.62 x headWidth (pelvis block, inside the skirt)")
    put("kneeY", layer0_evidence["designedCandidates"]["commonKneeHeight"]["y"], "DESIGNED_CANDIDATE",
        "v0.7 common knee height (mean of ESTIMATED knees 1059..1093, kept as unapproved observations)")
    knees = []
    for v in ("front", "back"):
        lm = layer0_evidence["views"][v]["landmarks"]
        knees += [abs(lm[k]["px"][0] - CX) for k in ("kneeLeft", "kneeRight") if "px" in lm[k]]
    put("kneeHalfWidth", R(sum(knees) / len(knees)), "DESIGNED_CANDIDATE", f"mean |x - 600| of the ESTIMATED front/back knees {knees}")
    put("ankleY", GROUND - R(0.44 * hh), "DESIGNED_CANDIDATE", "groundY - 0.44 x headHeight (ankle hidden by the boot; heel and sole included)")
    put("footHalfWidth", P["kneeHalfWidth"]["value"], "DESIGNED_CANDIDATE", "= kneeHalfWidth (straight legs)")
    heel = []
    for v, sign in (("left", 1), ("right", -1)):   # left view faces screen-left: heel lies at +x
        sp = layer0_evidence["_v06"][v]["automated"]["probeSpans"]
        dx = layer0_evidence["views"][v]["translate"][0]
        h = max(sp, key=lambda s: s[0]) if sign > 0 else min(sp, key=lambda s: s[0])
        heel.append(abs((h[0] + h[1]) / 2 + dx - CX))
    put("ankleDepthOffset", -R(0.6 * sum(heel) / len(heel)), "DESIGNED_CANDIDATE",
        f"ankle above the heel: -0.6 x mean heel-centre offset {[round(x, 1) for x in heel]} px from the sole contact centre (VERIFIED side sole spans)")
    put("statureWithFootwear", GROUND - P["headTopY"]["value"], "DESIGNED_CANDIDATE", "groundY - headTopY")
    put("headsTall", round(P["statureWithFootwear"]["value"] / hh, 2), "DESIGNED_CANDIDATE", "stature / headHeight (unitless)")
    P["headsTall"]["unit"] = "ratio"
    return P


def joints3d(P):
    """Shared 3D joints (x lateral +right of the character's centre, y down, z depth +forward). Anatomical L/R."""
    v = {k: p["value"] for k, p in P.items()}
    hx, sx, kx, fx = v["hipHalfWidth"], v["shoulderHalfWidth"], v["kneeHalfWidth"], v["footHalfWidth"]
    wx, wy = v["wristHalfSpanFront"], v["wristYFront"]
    J = {"headTop": (0, v["headTopY"], 0), "headCenter": (0, v["headTopY"] + v["headHeight"] / 2, 0), "chin": (0, v["chinY"], 0),
         "neckBase": (0, v["neckBaseY"], 0), "pelvis": (0, v["pelvisY"], 0), "ground": (0, v["groundY"], 0)}
    for side, s in (("R", -1), ("L", 1)):   # character's right = -x
        J[f"shoulder{side}"] = (s * sx, v["shoulderY"], 0)
        J[f"wrist{side}"] = (s * wx, wy, 0)
        J[f"elbow{side}"] = (s * (sx + wx) / 2, (v["shoulderY"] + wy) / 2, 0)
        J[f"hip{side}"] = (s * hx, v["pelvisY"], 0)
        J[f"knee{side}"] = (s * kx, v["kneeY"], 0)
        J[f"ankle{side}"] = (s * fx, v["ankleY"], v["ankleDepthOffset"])
        J[f"foot{side}"] = (s * fx, v["groundY"], 0)
    return J


def project(J, view):
    """front: viewer sees the character's right on screen-left; back: mirrored; left/right: side projections
    (screen x = centre -/+ depth), so lateral offsets collapse onto the profile line."""
    out = {}
    for k, (x, y, z) in J.items():
        sx = {"front": CX + x, "back": CX - x, "left": CX - z, "right": CX + z}[view]
        out[k] = [R(sx), R(y)]
    return out


V2_MAP = {"headTop": "headTop", "neck": "neckBase", "pelvis": "pelvis", "ground": "ground"}


def v2_landmarks(PJ, P):
    """BASE_BODY_SPEC v2.0-compatible landmarks (screen-left/right convention)."""
    out = {}
    for view, pts in PJ.items():
        sl, sr = ("R", "L") if view in ("front", "left", "right") else ("L", "R")
        m = dict(V2_MAP, shoulderLeft=f"shoulder{sl}", shoulderRight=f"shoulder{sr}", kneeLeft=f"knee{sl}", kneeRight=f"knee{sr}",
                 footLeft=f"foot{sl}", footRight=f"foot{sr}")
        out[view] = {}
        for k, j in m.items():
            verified = j == "ground"
            out[view][k] = {"n": to_norm(pts[j], CANVAS), "px": pts[j], "confidence": "high" if verified else "provisional",
                            "source": "measured_reference" if verified else "manual_edit"}
    return out


def _capsule(d, a, b, r, fill):
    d.line([tuple(a), tuple(b)], fill=fill, width=int(2 * r))
    for p in (a, b):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill)


def render(view, P, PJ, font, with_labels=True):
    from PIL import Image, ImageDraw
    v = {k: p["value"] for k, p in P.items()}
    im = Image.new("RGBA", (CANVAS["width"], CANVAS["height"]), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = (176, 180, 188, 255)
    j = PJ[view]
    side = view in ("left", "right")
    fwd = -1 if view == "left" else 1
    # head
    hw = v["headDepth"] if side else v["headWidth"]
    hc = j["headCenter"]
    d.ellipse([hc[0] - hw / 2, v["headTopY"], hc[0] + hw / 2, v["headTopY"] + v["headHeight"]], fill=body)
    # neck
    nw = 0.36 * v["headWidth"]
    d.rectangle([CX - nw / 2, v["chinY"] - 20, CX + nw / 2, v["neckBaseY"] + 10], fill=body)
    # ribcage + pelvis blocks
    if side:
        rd, pd = 0.95 * v["headDepth"], 0.9 * v["headDepth"]
        d.rounded_rectangle([CX - rd / 2, v["neckBaseY"], CX + rd / 2, v["ribcageBottomY"]], radius=40, fill=body)
        d.rounded_rectangle([CX - pd / 2, v["ribcageBottomY"] - 10, CX + pd / 2, v["pelvisY"] + 45], radius=36, fill=body)
    else:
        sw = v["shoulderHalfWidth"]
        d.polygon([(CX - sw, v["shoulderY"] - 10), (CX + sw, v["shoulderY"] - 10), (CX + 0.62 * sw, v["ribcageBottomY"]), (CX - 0.62 * sw, v["ribcageBottomY"])], fill=body)
        d.ellipse([CX - sw - 12, v["shoulderY"] - 22, CX - sw + 28, v["shoulderY"] + 18], fill=body)
        d.ellipse([CX + sw - 28, v["shoulderY"] - 22, CX + sw + 12, v["shoulderY"] + 18], fill=body)
        pw = v["pelvisHalfWidth"]
        d.polygon([(CX - 0.6 * pw, v["ribcageBottomY"] - 10), (CX + 0.6 * pw, v["ribcageBottomY"] - 10), (CX + pw, v["pelvisY"] + 20), (CX, v["pelvisY"] + 50), (CX - pw, v["pelvisY"] + 20)], fill=body)
    # limbs (far limbs slightly darker in side views)
    for s in ("R", "L"):
        col = body
        if side:
            near = "L" if view == "left" else "R"
            col = body if s == near else (140, 144, 152, 255)
        _capsule(d, j[f"shoulder{s}"], j[f"elbow{s}"], 17, col)
        _capsule(d, j[f"elbow{s}"], j[f"wrist{s}"], 14, col)
        _capsule(d, j[f"hip{s}"], j[f"knee{s}"], 28, col)
        _capsule(d, j[f"knee{s}"], j[f"ankle{s}"], 21, col)
        a, f = j[f"ankle{s}"], j[f"foot{s}"]
        if side:
            d.polygon([(a[0] - 16, a[1]), (a[0] + 16, a[1]), (f[0] + 50 * fwd, f[1] - 22), (f[0] + 50 * fwd, f[1]), (f[0] - 50 * fwd, f[1])], fill=col)
        else:
            d.rounded_rectangle([f[0] - 22, a[1], f[0] + 22, f[1]], radius=10, fill=col)
    if not with_labels:
        return im
    # reference lines + joints
    for y, name, col in ((v["groundY"], "ground", (240, 120, 60, 255)), (v["headTopY"], "headTop (DESIGNED)", (80, 210, 255, 230)),
                         (v["kneeY"], "knee (DESIGNED)", (80, 210, 255, 230)), (v["pelvisY"], "pelvis (DESIGNED)", (80, 210, 255, 230))):
        for x in range(0, CANVAS["width"], 24):
            d.line([x, y, x + 12, y], fill=col, width=2)
        d.text((CANVAS["width"] - 40 - font.getlength(name), y - 24), name, fill=col, font=font)
    for k, p in j.items():
        if k in ("headCenter",):
            continue
        c = (80, 230, 120, 255) if k == "ground" else (255, 210, 60, 255)
        d.ellipse([p[0] - 6, p[1] - 6, p[0] + 6, p[1] + 6], outline=c, width=3)
    lines = [f"morwen LAYER 0 MASTER BODY · {view} · CANDIDATE (UNAPPROVED)", "neutral mannequin structure guide (minor_neutral_structure)",
             "one shared skeleton; green = VERIFIED, yellow = DESIGNED_CANDIDATE joints"]
    for i, t in enumerate(lines):
        d.text((40, 40 + i * 26), t, fill=(255, 255, 255, 235), font=font)
    return im


def fit_generated(path, spec, view):
    """Numeric anchor check for an image-generation result + deterministic correction parameters
    (uniform scale about the contact, then integer translation). Returns residuals and the transform."""
    m = measure(path)
    if not m.get("bbox"):
        return {"result": "FAIL", "reason": "no opaque content"}
    top, bottom, cx = m["bbox"][1], m["contact"]["bottomRow"], m["contact"]["x"]
    want_top, want_bottom = spec["parameters"]["headTopY"]["value"], GROUND
    s = (want_bottom - want_top) / max(1, bottom - top)
    res = {"measured": {"top": top, "bottom": bottom, "contactX": cx}, "scale": round(s, 6),
           "translate": [R(CX - cx * s), R(GROUND - bottom * s)],
           "residualBefore": {"top": top - want_top, "bottom": bottom - want_bottom, "contactX": round(cx - CX, 2)}}
    res["result"] = "PASS" if max(abs(res["residualBefore"]["top"]), abs(res["residualBefore"]["bottom"]), abs(res["residualBefore"]["contactX"])) <= 2 else "NEEDS_CORRECTION"
    return res


def apply_fit(src, dst, fit, repo_root=REPO_ROOT):
    """Deterministic correction: uniform scale (LANCZOS) about the origin, then integer translation. New file only."""
    from PIL import Image
    o = guard_write(dst, repo_root)
    with Image.open(src) as im:
        im = im.convert("RGBA")
        if abs(fit["scale"] - 1) > 1e-9:
            im = im.resize((R(im.width * fit["scale"]), R(im.height * fit["scale"])), Image.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS["width"], CANVAS["height"]), (0, 0, 0, 0))
    canvas.paste(im, tuple(fit["translate"]), im)
    o.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(o, compress_level=9)
    return {"path": rel(o, repo_root), "sha256": sha256_file(o)}


def run(character_id, observations, layer0_evidence_path, transforms_path, out_dir, overwrite=False, repo_root=REPO_ROOT):
    from PIL import Image, ImageFont
    import numpy as np
    obs, lev, tf = load_json(observations), load_json(layer0_evidence_path), load_json(transforms_path)
    lev["_v06"] = load_json(Path(repo_root) / lev["inputs"]["measurementEvidence"]["path"])["views"]
    out_dir = Path(out_dir)
    names = ["MASTER_BODY_SPEC.candidate.json", "BODY_CONSISTENCY_QA.json", "production_brief.json"]
    names += [f"{v}_structure_guide.png" for v in VIEWS] + [f"{v}_structure_overlay.png" for v in VIEWS]
    for n in names:
        guard_write(out_dir / n, repo_root, overwrite)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    canon_before = {e["path"]: sha256_file(Path(repo_root) / e["path"]) for e in protected_list()["files"]}

    P = design_parameters(obs, lev)
    J = joints3d(P)
    PJ = {v: project(J, v) for v in VIEWS}
    guides, overlays, contain = {}, {}, {}
    for v in VIEWS:
        g = render(v, P, PJ, font)
        gp = out_dir / f"{v}_structure_guide.png"
        g.save(gp, compress_level=9)
        guides[v] = {"path": rel(gp, repo_root), "sha256": sha256_file(gp), "width": 1200, "height": 1600, "mode": "RGBA"}
        shape = np.asarray(render(v, P, PJ, font, with_labels=False))[..., 3] > 0
        src = Path(repo_root) / tf["views"][v]["output"]["path"]
        with Image.open(src) as cim:
            ca = np.asarray(cim.convert("RGBA"))
        fg = (ca[..., 3] >= 128) & (ca[..., :3].max(axis=2) > 10) if tf["views"][v]["source"]["mode"] != "RGBA" else ca[..., 3] >= 128
        from scipy import ndimage
        fg = ndimage.binary_fill_holes(fg)        # near-black hair/shadow pixels inside the figure count as inside
        inside = int((shape & fg).sum()); total = int(shape.sum())
        outside = shape & ~fg
        contain[v] = {"bodyPixels": total, "insideCanonFigure": inside, "ratio": round(inside / total, 4), "outsidePixels": int(outside.sum())}
        bg = Image.new("RGBA", (1200, 1600), (58, 62, 70, 255))
        faint = Image.fromarray(np.dstack([ca[..., :3], np.where(fg, 120, 0).astype(np.uint8)]), "RGBA")
        bg.alpha_composite(faint)
        bod = render(v, P, PJ, font, with_labels=False)
        bod.putalpha(bod.getchannel("A").point(lambda a: a * 150 // 255))
        bg.alpha_composite(bod)
        red = np.zeros((1600, 1200, 4), np.uint8); red[outside] = (255, 40, 40, 200)
        bg.alpha_composite(Image.fromarray(red, "RGBA"))
        bg.alpha_composite(g)
        op = out_dir / f"{v}_structure_overlay.png"
        bg.convert("RGB").save(op, compress_level=9)
        overlays[v] = {"path": rel(op, repo_root), "sha256": sha256_file(op), "width": 1200, "height": 1600, "mode": "RGB"}

    statuses = sorted({p["status"] for p in P.values()})
    spec = {"schema": "cas/master-body/0.8", "status": "UNAPPROVED_CANDIDATE", "characterId": character_id, "ageCategory": "minor",
            "bodyGuidePolicy": "minor_neutral_structure", "canvas": CANVAS, "anchor": {"px": [CX, GROUND], "n": to_norm([CX, GROUND], CANVAS)},
            "finalAdoption": "NOT_RUN",
            "statusLegend": {"VERIFIED": "automated canon measurement", "ESTIMATED": "AI visual observation (not human-confirmed)",
                             "DESIGNED_CANDIDATE": "new design value from a stated rule; NOT a canon measurement", "UNKNOWN": "not measurable and not designed"},
            "parameters": P, "joints3d": {k: [R(x), R(y), R(z)] for k, (x, y, z) in J.items()},
            "projection": {"front": "screen x = 600 + x", "back": "screen x = 600 - x", "left": "screen x = 600 - z", "right": "screen x = 600 + z", "y": "unchanged"},
            "views": {v: {"joints": PJ[v], "structureGuide": guides[v], "overlay": overlays[v]} for v in VIEWS},
            "baseBodySpecV2": {"schemaVersion": "2.0", "status": "candidate_not_canonical", "characterId": character_id, "presetId": "MORWEN_REAL_1200x1600",
                               "canvas": CANVAS, "groundNormalized": to_norm([CX, GROUND], CANVAS), "worldScale": {"pixelsPerUnit": None},
                               "coordinateSpace": "normalized canvas (0..1, origin top-left, y down); px = n * canvas size", "views": list(VIEWS),
                               "landmarks": v2_landmarks(PJ, P), "referenceBody": [{"id": f"{character_id.upper()}_MASTER_BODY_V0.8", "status": "UNAPPROVED_DESIGNED_CANDIDATE"}],
                               "assets": [], "notes": "Projection of the v0.8 designed master skeleton. manual_edit/provisional = DESIGNED_CANDIDATE, not measured."},
            "inputs": {"observations": {"path": rel(observations, repo_root), "sha256": sha256_file(observations)},
                       "layer0Evidence": {"path": rel(layer0_evidence_path, repo_root), "sha256": sha256_file(layer0_evidence_path)},
                       "viewTransforms": {"path": rel(transforms_path, repo_root), "sha256": sha256_file(transforms_path)}},
            "unapprovedObservationsKept": {"kneeYByView": lev["designedCandidates"]["commonKneeHeight"]["derivedFrom"]},
            "parameterStatuses": statuses}

    # ---------- QA ----------
    ck = Checks()
    vs = validate(spec["baseBodySpecV2"])
    ck.add("v2_compatible_landmarks", "baseBodySpecV2", vs["result"], detail=vs["errors"] or None)
    for v in VIEWS:
        gi = measure(out_dir / f"{v}_structure_guide.png")
        ck.add("canvas_1200x1600_rgba", v, "PASS" if (gi["width"], gi["height"], gi["mode"]) == (1200, 1600, "RGBA") else "FAIL")
        ck.add("transparent_area", v, "PASS" if gi["transparentPixels"] > 0 and gi["borderNonZero"] <= 2400 else "FAIL",
               detail={"alpha0": gi["transparentPixels"], "borderNonZero": gi["borderNonZero"], "note": "border pixels come only from the dashed reference lines"})
        bm = measure_shape(render(v, P, PJ, font, with_labels=False))
        ck.add("body_contact_on_anchor", v, "PASS" if bm["bottom"] == GROUND and abs(bm["contactX"] - CX) <= 1 else "FAIL", detail=bm)
        ck.add("body_top_on_headTop", v, "PASS" if bm["top"] == P["headTopY"]["value"] else "FAIL", detail={"top": bm["top"], "headTopY": P["headTopY"]["value"]})
        ck.add("ground_joint", v, "PASS" if PJ[v]["ground"] == [CX, GROUND] else "FAIL")
    # front/back and left/right parameter equality, reference lines
    def dims(view):
        j = PJ[view]
        return {"headsTall": round((GROUND - j["headTop"][1]) / P["headHeight"]["value"], 3),
                "shoulderWidth": abs(j["shoulderL"][0] - j["shoulderR"][0]), "pelvisWidth": abs(j["hipL"][0] - j["hipR"][0]),
                "legLength": j["foot" + "L"][1] - j["hipL"][1], "lines": [j["headTop"][1], j["pelvis"][1], j["kneeL"][1], j["ground"][1]]}
    fd, bd = dims("front"), dims("back")
    ck.add("front_back_dimensions_equal", "front/back", "PASS" if fd == bd else "FAIL", detail={"front": fd, "back": bd})
    sym = all(PJ["front"][f"{a}L"][0] - CX == CX - PJ["front"][f"{a}R"][0] and PJ["front"][f"{a}L"][1] == PJ["front"][f"{a}R"][1]
              for a in ("shoulder", "elbow", "wrist", "hip", "knee", "ankle", "foot"))
    ck.add("front_back_symmetric_skeleton", "front/back", "PASS" if sym else "FAIL")
    ly = {k: p[1] for k, p in PJ["left"].items()}; ry = {k: p[1] for k, p in PJ["right"].items()}
    lx = {k: p[0] - CX for k, p in PJ["left"].items()}; rx = {k: CX - p[0] for k, p in PJ["right"].items()}
    ck.add("left_right_joints_mirror", "left/right", "PASS" if ly == ry and lx == rx else "FAIL")
    seg = lambda a, b: round(math.dist(J[a], J[b]), 2)  # noqa: E731
    lens = {s: seg(*s.split("-")) for s in ("shoulderL-elbowL", "elbowL-wristL", "hipL-kneeL", "kneeL-ankleL", "shoulderR-elbowR", "hipR-kneeR")}
    ck.add("limb_lengths_symmetric_3d", "skeleton", "PASS" if lens["shoulderL-elbowL"] == lens["shoulderR-elbowR"] and lens["hipL-kneeL"] == lens["hipR-kneeR"] else "FAIL", detail=lens)
    lines = {v: [PJ[v]["headTop"][1], PJ[v]["pelvis"][1], PJ[v]["kneeL"][1], PJ[v]["ground"][1]] for v in VIEWS}
    ck.add("reference_lines_4views", "all", "PASS" if len({tuple(x) for x in lines.values()}) == 1 else "FAIL", detail={"headTop/pelvis/knee/ground": lines})
    # agreement with canon-derived points (VERIFIED must hold; ESTIMATED reported)
    for v in VIEWS:
        lm = lev["views"][v]["landmarks"]
        ck.add("verified_ground_match", v, "PASS" if lm["ground"]["px"] == PJ[v]["ground"] else "FAIL")
        for k, jn in (("footLeft", "footR" if v != "back" else "footL"), ("footRight", "footL" if v != "back" else "footR")):
            if lm[k]["measurementStatus"] == "VERIFIED" and v in ("front", "back"):
                dlt = PJ[v][jn][0] - lm[k]["px"][0]
                ck.add("verified_foot_contact_within_sole", f"{v}/{k}", "PASS" if abs(dlt) <= 10 else "FAIL",
                       detail={"designedX": PJ[v][jn][0], "measuredX": lm[k]["px"][0], "deltaPx": dlt, "tolPx": 10,
                               "note": "measured point = centre of the sole/heel span at the probe row; tolerance = quarter of a boot width"})
    obsd = {k: PJ["left"]["wristL"][1] - obs["observations"]["left.wrist"]["value"][1] for k in ["left.wrist"]}
    ck.add("side_wrist_vs_observation", "left", "NOT_RUN", "human", detail={"designedMinusObservedY": obsd},
           reason="same 3D arm pose projected sideways; the side-view observation differs slightly (ESTIMATED)")
    for v in VIEWS:
        c = contain[v]
        ck.add("body_inside_canon_figure", v, "PASS" if c["ratio"] >= 0.98 else "NOT_RUN", "automated" if c["ratio"] >= 0.98 else "human", detail=c,
               reason=None if c["ratio"] >= 0.98 else "some structure pixels fall outside the costumed figure (red in the overlay); check by eye")
    for e, before in canon_before.items():
        ck.add("protected_sha256", e, "PASS" if sha256_file(Path(repo_root) / e) == before else "FAIL")
    ck.add("designed_values_labelled", "parameters", "PASS" if all(p["status"] in ("VERIFIED", "ESTIMATED", "DESIGNED_CANDIDATE", "UNKNOWN") for p in P.values())
           and P["headTopY"]["status"] == "DESIGNED_CANDIDATE" and P["shoulderY"]["status"] == "DESIGNED_CANDIDATE" and P["pelvisY"]["status"] == "DESIGNED_CANDIDATE" else "FAIL")
    for cid, label in design_protection_checks(character_id):
        ck.add(cid, "design", "NOT_RUN", "human", reason="mandatory visual QA: " + label)
    ck.add("final_design_adoption", "all", "NOT_RUN", "human", reason="director decision")
    ck.add("final_skeleton_adoption", "all", "NOT_RUN", "human", reason="director decision after image generation and skeleton comparison")
    ck.add("independent_visual_qa", "all", "NOT_RUN", "human", reason="independent (non-author) visual QA of the guides and overlays")
    rep = make_report({"kind": "master-body-candidate", "characterId": character_id, "path": rel(out_dir, repo_root)}, ck.rows)

    brief = {"schema": "cas/production-brief/0.5", "status": "UNAPPROVED_INSTRUCTION",
             "task": {"id": f"{character_id.upper()}-LAYER0-MASTER-V0.8", "kind": "base_body", "characterId": character_id, "frameCount": 1,
                      "description": "Draw a neutral, non-explicit mannequin-type structure figure (simple head, ribcage, pelvis and limb volumes; smooth uniform "
                                     "grey; no anatomical or sexual detail; no clothing, hair or accessories) in four views on the guides. The character is 17: keep "
                                     "age-appropriate, unchanged proportions. Match the joints of the structure guide; exact pixel accuracy is NOT expected from "
                                     "image generation — results are measured and corrected deterministically afterwards (cas.py master-body-fit)."},
             "presetId": "MORWEN_REAL_1200x1600", "canvas": CANVAS, "anchor": spec["anchor"],
             "views": {v: {"guide": guides[v], "guidePreview": overlays[v],
                           "landmarks": {k: {"n": to_norm(p, CANVAS), "px": p, "confidence": "high" if k == "ground" else "provisional",
                                             "source": "VERIFIED" if k == "ground" else "DESIGNED_CANDIDATE"} for k, p in PJ[v].items() if k != "headCenter"},
                           "visualReference": None} for v in VIEWS},
             "landmarkSource": {"kind": "v0.8 designed master skeleton (shared 3D joints, projected)", "status": "DESIGNED_CANDIDATE except ground (VERIFIED)"},
             "outputRequirements": {"format": "PNG", "mode": "RGBA", "width": 1200, "height": 1600, "background": "real alpha=0 (transparent)",
                                    "fileNamePattern": f"{character_id}_layer0_master_{{view}}.png", "deliverTo": f"assets/candidates/{character_id}/layer0-master-v0.8",
                                    "forbidden": ["anatomical or sexual detail", "clothing, underwear, hair, hat or accessories", "changing age, height or build",
                                                  "editing protected files", "text or watermarks"]},
             "constraints": [{"id": "neutral_structure", "text": "minor_neutral_structure: mannequin-like volumes only", "check": "human"},
                             {"id": "shared_skeleton", "text": "all four views use the same parameters (MASTER_BODY_SPEC.candidate.json)", "check": "automated"},
                             {"id": "post_generation_fit", "text": "measure top/ground/contact; correct by uniform scale + integer translation; never redraw", "check": "automated"}],
             "protectedReferences": [{"path": e["path"], "sha256": e["sha256"], "use": "visual reference only; never modify"} for e in protected_list()["files"] if f"/{character_id}/" in e["path"]],
             "acceptanceChecks": [{"id": c, "kind": "automated"} for c in ("canvas_1200x1600_rgba", "transparent_area", "body_contact_on_anchor", "body_top_on_headTop", "reference_lines_4views")]
                                 + [{"id": "final_skeleton_adoption", "kind": "human", "text": "director"}],
             "adoption": {"autoAdopt": False, "requires": "image generation, numeric fit, skeleton comparison, independent visual QA and director approval"},
             "handoff": {"parameterStatus": {k: p["status"] for k, p in P.items()},
                         "statusLegend": spec["statusLegend"],
                         "returnFormat": "cas/modular-part/0.7 per view (layerId L0_BASE_BODY, measurementStatus DESIGNED_CANDIDATE, bodyGuidePolicy minor_neutral_structure)",
                         "fitCommand": "python3 tools/character-asset-studio/pipeline/cas.py master-body-fit --spec <MASTER_BODY_SPEC.candidate.json> --view <v> --image <png> --out <new png>"}}
    vb = validate(brief)
    rep_rows = rep["checks"]
    rep_rows.insert(0, {"id": "brief_schema", "scope": "production_brief.json", "result": vb["result"], "kind": "automated"})
    rep = make_report(rep["subject"], rep_rows)
    (out_dir / "MASTER_BODY_SPEC.candidate.json").write_text(stable_dumps(spec), encoding="utf-8")
    (out_dir / "BODY_CONSISTENCY_QA.json").write_text(stable_dumps(rep), encoding="utf-8")
    (out_dir / "production_brief.json").write_text(stable_dumps(brief), encoding="utf-8")
    return spec, rep


def measure_shape(img):
    import numpy as np
    a = np.asarray(img)[..., 3] > 0
    rows = np.where(a.any(axis=1))[0]
    bottom = int(rows[-1])
    xs = np.where(a[bottom])[0]
    return {"top": int(rows[0]), "bottom": bottom, "contactX": (int(xs[0]) + int(xs[-1])) / 2}
