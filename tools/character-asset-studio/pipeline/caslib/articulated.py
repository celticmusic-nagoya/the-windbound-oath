"""Layer 0 articulated master-body candidate (v0.9, MORWEN-LAYER0-02) + Layer 1 opaque base-layer candidate.

* Starts from the v0.8 skeleton file WITHOUT changing any v0.8 joint (verified); only joints needed for the
  articulation are ADDED (neckTop, jawL/R, waist, heelL/R, ballL/R, toeL/R, handL/R), each with a reason, in
  JOINT_CHANGES_v0.9.json.
* One 3D structure -> four projections (front/back symmetric, sides = same joints seen sideways).
* Neutral mannequin volumes only (cranium, jaw, neck, ribcage, waist, pelvis, ball joints, tapered limb
  segments, segmented feet). No anatomical or sexual detail is drawn.
* Layer 1 candidate here is an OPAQUE, NON-REVEALING base layer (high-neck short-sleeve top, knee-length
  shorts, over-knee socks) generated from the Layer 0 volumes — no lingerie elements.
"""
import math
from pathlib import Path

from .core import REPO_ROOT, VIEWS, guard_write, js_round, load_json, protected_list, rel, sha256_file, stable_dumps, to_norm
from .imageqa import design_protection_checks
from .report import Checks, make_report

CANVAS = {"width": 1200, "height": 1600}
CX, GROUND = 600, 1540
R = lambda v: int(js_round(v))  # noqa: E731
SEG = (184, 188, 196, 255)
JOINT = (150, 155, 166, 255)
EDGE = (92, 96, 108, 255)
FAR = 0.82

# kinematic tree (child -> parent) rooted at the pelvis
TREE = {"waist": "pelvis", "neckBase": "waist", "neckTop": "neckBase", "chin": "neckTop", "headCenter": "neckTop", "headTop": "headCenter",
        "jawL": "headCenter", "jawR": "headCenter",
        "shoulderL": "neckBase", "elbowL": "shoulderL", "wristL": "elbowL", "handL": "wristL",
        "shoulderR": "neckBase", "elbowR": "shoulderR", "wristR": "elbowR", "handR": "wristR",
        "hipL": "pelvis", "kneeL": "hipL", "ankleL": "kneeL", "heelL": "ankleL", "ballL": "ankleL", "toeL": "ballL", "footL": "ankleL",
        "hipR": "pelvis", "kneeR": "hipR", "ankleR": "kneeR", "heelR": "ankleR", "ballR": "ankleR", "toeR": "ballR", "footR": "ankleR",
        "ground": "pelvis"}
LAT = [1, 0, 0]
AXES = {  # walk rotation axes (designed ranges, degrees)
    "hip": {"joints": ["hipL", "hipR"], "axis": LAT, "rangeDeg": [-25, 30], "use": "thigh swing (flexion/extension)"},
    "knee": {"joints": ["kneeL", "kneeR"], "axis": LAT, "rangeDeg": [0, 65], "use": "knee flexion"},
    "ankle": {"joints": ["ankleL", "ankleR"], "axis": LAT, "rangeDeg": [-20, 20], "use": "dorsi/plantar flexion"},
    "ball": {"joints": ["ballL", "ballR"], "axis": LAT, "rangeDeg": [0, 40], "use": "toe-off pivot"},
    "heel": {"joints": ["heelL", "heelR"], "axis": LAT, "rangeDeg": [-15, 0], "use": "heel-strike pivot"},
    "shoulder": {"joints": ["shoulderL", "shoulderR"], "axis": LAT, "rangeDeg": [-30, 30], "use": "arm swing"},
    "elbow": {"joints": ["elbowL", "elbowR"], "axis": LAT, "rangeDeg": [0, 45], "use": "forearm swing"},
    "waist": {"joints": ["waist"], "axis": [0, 1, 0], "rangeDeg": [-8, 8], "use": "torso counter-rotation (vertical axis)"},
    "neck": {"joints": ["neckTop"], "axis": LAT, "rangeDeg": [-10, 10], "use": "head nod"},
}


def build_joints(v08):
    """v0.8 joints unchanged + added articulation joints (with reasons)."""
    P = {k: p["value"] for k, p in v08["parameters"].items()}
    J = {k: list(v) for k, v in v08["joints3d"].items()}
    hh, hw, hd = P["headHeight"], P["headWidth"], P["headDepth"]
    added = {
        "neckTop": ([0, R(P["chinY"] - 0.12 * hh), -R(0.18 * hd)], "neck attaches under/behind the skull, not at the chin: needed for a clear skull-jaw-neck connection"),
        "jawL": ([R(0.33 * hw), R(P["chinY"] - 0.3 * hh), -R(0.12 * hd)], "jaw angle (left) so the jaw reads as a separate volume from the cranium"),
        "jawR": ([-R(0.33 * hw), R(P["chinY"] - 0.3 * hh), -R(0.12 * hd)], "jaw angle (right)"),
        "waist": ([0, R(P["ribcageBottomY"] + 0.35 * (P["pelvisY"] - P["ribcageBottomY"])), 0], "separates ribcage / waist / pelvis and gives the torso twist axis"),
    }
    for s, sg in (("L", 1), ("R", -1)):
        a = J[f"ankle{s}"]
        added[f"heel{s}"] = ([a[0], GROUND, -50], "heel-strike pivot at the back of the v0.8 sole contact span (-50..+50)")
        added[f"ball{s}"] = ([a[0], GROUND, 28], "ball-of-foot pivot for toe-off, inside the sole contact span")
        added[f"toe{s}"] = ([a[0], GROUND, 50], "front end of the v0.8 sole contact span")
        w, e = J[f"wrist{s}"], J[f"elbow{s}"]
        d = [w[i] - e[i] for i in range(3)]
        n = math.sqrt(sum(x * x for x in d))
        hl = 0.45 * hh
        added[f"hand{s}"] = ([R(w[0] + d[0] / n * hl), R(w[1] + d[1] / n * hl), R(w[2] + d[2] / n * hl)], "hand end along the forearm (0.45 head)")
    for k, (pos, _) in added.items():
        assert k not in J
        J[k] = pos
    return J, {k: {"joint3d": pos, "reason": why} for k, (pos, why) in added.items()}, P


def project(J, view):
    out = {}
    for k, (x, y, z) in J.items():
        sx = {"front": CX + x, "back": CX - x, "left": CX - z, "right": CX + z}[view]
        out[k] = [R(sx), R(y)]
    return out


def _taper(d, a, b, r0, r1, fill, outline=EDGE):
    ang = math.atan2(b[1] - a[1], b[0] - a[0]) + math.pi / 2
    c, s = math.cos(ang), math.sin(ang)
    poly = [(a[0] + c * r0, a[1] + s * r0), (b[0] + c * r1, b[1] + s * r1), (b[0] - c * r1, b[1] - s * r1), (a[0] - c * r0, a[1] - s * r0)]
    d.polygon(poly, fill=fill, outline=outline)


def _ball(d, p, r, fill=JOINT, outline=EDGE):
    d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=fill, outline=outline, width=2)


def _shade(c, k):
    return tuple(int(v * k) for v in c[:3]) + (255,)


def render_parts(view, J, P):
    """Return {partName: RGBA image} drawn in draw order; union = body."""
    from PIL import Image, ImageDraw
    W, H = CANVAS["width"], CANVAS["height"]
    j = project(J, view)
    side = view in ("left", "right")
    near = {"left": "L", "right": "R"}.get(view)
    hh, hw, hd = P["headHeight"], P["headWidth"], P["headDepth"]
    parts = {}

    def layer(name):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        parts[name] = im
        return ImageDraw.Draw(im)

    def limbs(s, k=1.0):
        seg, jt = _shade(SEG, k), _shade(JOINT, k)
        d = layer(f"arm{s}")
        _taper(d, j[f"shoulder{s}"], j[f"elbow{s}"], 19, 15, seg); _taper(d, j[f"elbow{s}"], j[f"wrist{s}"], 14, 11, seg)
        _ball(d, j[f"elbow{s}"], 15, jt); _ball(d, j[f"wrist{s}"], 11, jt)
        _taper(d, j[f"wrist{s}"], j[f"hand{s}"], 13, 10, seg); _ball(d, j[f"shoulder{s}"], 22, jt)
        d = layer(f"leg{s}")
        _taper(d, j[f"hip{s}"], j[f"knee{s}"], 30, 22, seg); _taper(d, j[f"knee{s}"], j[f"ankle{s}"], 21, 15, seg)
        if side:
            fw = -1 if view == "left" else 1
            a, he, ba, to = j[f"ankle{s}"], j[f"heel{s}"], j[f"ball{s}"], j[f"toe{s}"]
            d.polygon([(a[0] - 14, a[1]), (a[0] + 14, a[1]), (ba[0], GROUND - 26), (to[0], GROUND - 10), (to[0], GROUND), (he[0], GROUND), (he[0], GROUND - 30)],
                      fill=seg, outline=EDGE)
            d.line([(ba[0], GROUND - 26), (ba[0], GROUND)], fill=EDGE, width=2)
            _ball(d, (ba[0], GROUND - 7), 6, jt)   # pivot marker kept above the ground line
        else:
            f = j[f"foot{s}"]
            d.rounded_rectangle([f[0] - 22, j[f"ankle{s}"][1], f[0] + 22, GROUND], radius=10, fill=seg, outline=EDGE)
            d.line([(f[0] - 22, j[f"ball{s}"][1] - 26), (f[0] + 22, j[f"ball{s}"][1] - 26)], fill=EDGE, width=2)
        _ball(d, j[f"knee{s}"], 22, jt); _ball(d, j[f"ankle{s}"], 15, jt); _ball(d, j[f"hip{s}"], 26, jt)

    if side:
        far = "R" if near == "L" else "L"
        limbs(far, FAR)
    # torso: pelvis, waist, ribcage (distinct blocks with outlines)
    d = layer("pelvis")
    pw = hd * 0.9 / 2 if side else P["pelvisHalfWidth"]
    d.rounded_rectangle([CX - pw, j["waist"][1] - 6, CX + pw, P["pelvisY"] + 48], radius=34, fill=SEG, outline=EDGE, width=2)
    d = layer("waist")
    ww = hd * 0.8 / 2 if side else 0.72 * P["pelvisHalfWidth"]
    d.rounded_rectangle([CX - ww, P["ribcageBottomY"] - 14, CX + ww, j["waist"][1] + 10], radius=16, fill=_shade(SEG, 0.93), outline=EDGE, width=2)
    if not side:   # shoulder girdle: connects the neck base to both shoulder balls
        d = layer("girdle")
        for s in ("L", "R"):
            _taper(d, j["neckBase"], j[f"shoulder{s}"], 15, 17, SEG)
    d = layer("ribcage")
    rw = hd * 0.95 / 2 if side else 0.8 * P["shoulderHalfWidth"]
    d.ellipse([CX - rw, P["neckBaseY"] - 6, CX + rw, P["ribcageBottomY"] + 4], fill=SEG, outline=EDGE, width=2)
    # neck + head
    d = layer("neck")
    nt, nb = j["neckTop"], j["neckBase"]
    _taper(d, nt, nb, 0.17 * hw if not side else 0.2 * hd, 0.2 * hw if not side else 0.22 * hd, _shade(SEG, 0.95))
    d = layer("jaw")
    if side:
        fw = -1 if view == "left" else 1
        ja, ch = j["jaw" + ("L" if near == "L" else "R")], j["chin"]
        d.polygon([(ja[0], ja[1]), (CX + fw * 0.42 * hd, ja[1] - 10), (ch[0] + fw * 0.30 * hd, ch[1] - 6), (ch[0] + fw * 0.16 * hd, ch[1]), (ja[0] + fw * -6, ch[1] - 30)],
                  fill=SEG, outline=EDGE)
    else:
        jl, jr, ch = j["jawL"], j["jawR"], j["chin"]
        d.polygon([(jl[0], jl[1]), (jr[0], jr[1]), (CX - 18, ch[1]), (CX + 18, ch[1])], fill=SEG, outline=EDGE)
    d = layer("cranium")
    cw = hd if side else hw
    top = P["headTopY"]
    d.ellipse([CX - cw / 2, top, CX + cw / 2, top + 0.82 * hh], fill=SEG, outline=EDGE, width=2)
    _ball(d, j["neckTop"], 9)
    if side:
        limbs(near, 1.0)
    else:
        for s in ("L", "R"):
            limbs(s, 1.0)
    return parts, j


def union(parts):
    from PIL import Image
    out = Image.new("RGBA", (CANVAS["width"], CANVAS["height"]), (0, 0, 0, 0))
    for im in parts.values():
        out.alpha_composite(im)
    return out


def masks(parts, names):
    import numpy as np
    m = np.zeros((CANVAS["height"], CANVAS["width"]), bool)
    for n in names:
        if n in parts:
            m |= np.asarray(parts[n])[..., 3] > 0
    return m


def base_layer(parts, J, P, view):
    """Layer 1 candidate: opaque, non-revealing base layer built from the Layer 0 volumes."""
    import numpy as np
    from PIL import Image
    from scipy import ndimage
    H, W = CANVAS["height"], CANVAS["width"]
    yy = np.arange(H)[:, None]
    torso = masks(parts, ["ribcage", "waist", "pelvis", "neck", "girdle"]) & (yy >= P["neckBaseY"] - 22)
    arms = masks(parts, ["armL", "armR"]) & (yy <= (P["shoulderY"] + J["elbowL"][1]) / 2 + 10)
    legs = masks(parts, ["legL", "legR"])
    shorts = legs & (yy <= P["kneeY"] - 150)
    socks = legs & (yy >= P["kneeY"] - 110)
    top = ndimage.binary_dilation(torso | arms | (legs & (yy <= P["pelvisY"] + 48)), iterations=3)
    bottom = ndimage.binary_dilation(shorts, iterations=3)
    sock = ndimage.binary_dilation(socks, iterations=2)
    img = np.zeros((H, W, 4), np.uint8)
    img[sock] = (52, 42, 60, 255)
    img[bottom] = (64, 48, 82, 255)
    img[top] = (78, 56, 102, 255)
    return Image.fromarray(img, "RGBA"), {"top": int(top.sum()), "shorts": int(bottom.sum()), "socks": int(sock.sum())}


def fk_rotate(J, joint, axis_deg, chain):
    """Rotate every joint in `chain` about the lateral axis through `joint` (y/z plane)."""
    a = math.radians(axis_deg)
    c, s = math.cos(a), math.sin(a)
    px, py, pz = J[joint]
    out = dict(J)
    for k in chain:
        x, y, z = J[k]
        dy, dz = y - py, z - pz
        out[k] = [x, py + c * dy - s * dz, pz + s * dy + c * dz]
    return out


def descendants(root):
    kids = [k for k, p in TREE.items() if p == root]
    out = list(kids)
    for k in kids:
        out += descendants(k)
    return out


def run(v08_spec_path, canon_transforms_path, out_l0, out_l1, overwrite=False, repo_root=REPO_ROOT):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from scipy import ndimage
    from . import layers as layerlib, modular
    v08 = load_json(v08_spec_path)
    tf = load_json(canon_transforms_path)
    out_l0, out_l1 = Path(out_l0), Path(out_l1)
    t0 = ["MASTER_BODY_SPEC.v0.9.candidate.json", "JOINT_CHANGES_v0.9.json", "BODY_QA_v0.9.json", "compare_4views_structure.png"]
    t0 += [f"{v}_articulated_guide.png" for v in VIEWS] + [f"{v}_layer0_part.png" for v in VIEWS] + [f"{v}_stack_with_canon.png" for v in VIEWS]
    t1 = ["LAYER1_BASE_SPEC.candidate.json"] + [f"{v}_layer1_base_part.png" for v in VIEWS]
    for t in [out_l0 / n for n in t0] + [out_l1 / n for n in t1]:
        guard_write(t, repo_root, overwrite)
    out_l0.mkdir(parents=True, exist_ok=True); out_l1.mkdir(parents=True, exist_ok=True)
    canon_before = {e["path"]: sha256_file(Path(repo_root) / e["path"]) for e in protected_list()["files"]}
    v08_files = {p.name: sha256_file(p) for p in Path(v08_spec_path).parent.iterdir()}
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    J, added, P = build_joints(v08)
    ck = Checks()
    unchanged = all(J[k] == v for k, v in v08["joints3d"].items())
    ck.add("v08_joints_unchanged", "joints3d", "PASS" if unchanged else "FAIL", detail={"v08Joints": len(v08["joints3d"]), "added": sorted(added)})
    changes = {"schema": "cas/joint-changes/0.9", "status": "UNAPPROVED_CANDIDATE", "base": {"path": rel(v08_spec_path, repo_root), "sha256": sha256_file(v08_spec_path)},
               "changed": [], "added": added,
               "note": "No v0.8 joint coordinate was changed. Only articulation joints were added; each entry gives the reason. All added joints are DESIGNED_CANDIDATE."}
    PJ, l0imgs, l1imgs, partsets = {}, {}, {}, {}
    for v in VIEWS:
        parts, j = render_parts(v, J, P)
        PJ[v], partsets[v] = j, parts
        body = union(parts)
        p = out_l0 / f"{v}_layer0_part.png"; body.save(p, compress_level=9); l0imgs[v] = p
        g = body.copy(); d = ImageDraw.Draw(g)
        for y, name, col in ((GROUND, "ground (VERIFIED)", (240, 120, 60, 255)), (P["headTopY"], "headTop", (80, 210, 255, 230)),
                             (P["pelvisY"], "hip axis", (80, 210, 255, 230)), (P["kneeY"], "knee axis", (80, 210, 255, 230)), (P["ankleY"], "ankle axis", (80, 210, 255, 230))):
            for x in range(0, CANVAS["width"], 24):
                d.line([x, y, x + 12, y], fill=col, width=2)
            d.text((CANVAS["width"] - 40 - font.getlength(name), y - 24), name, fill=col, font=font)
        for k in ("hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR", "ballL", "ballR", "heelL", "heelR", "shoulderL", "shoulderR", "elbowL", "elbowR", "neckTop", "waist"):
            x, y = j[k]
            d.line([x - 8, y, x + 8, y], fill=(255, 210, 60, 255), width=2); d.line([x, y - 8, x, y + 8], fill=(255, 210, 60, 255), width=2)
        for i, t in enumerate([f"morwen LAYER 0 articulated master body · {v} · CANDIDATE (UNAPPROVED)", "neutral mannequin (minor_neutral_structure); + = rotation centres"]):
            d.text((40, 40 + i * 26), t, fill=(255, 255, 255, 235), font=font)
        g.save(out_l0 / f"{v}_articulated_guide.png", compress_level=9)
        l1, l1stats = base_layer(parts, J, P, v)
        p1 = out_l1 / f"{v}_layer1_base_part.png"; l1.save(p1, compress_level=9); l1imgs[v] = (p1, l1stats)

    # ---------- geometry QA ----------
    for v in VIEWS:
        a = np.asarray(Image.open(l0imgs[v]))[..., 3] > 0
        rows = np.where(a.any(axis=1))[0]; xs = np.where(a[rows[-1]])[0]
        ok = rows[-1] == GROUND and abs((xs[0] + xs[-1]) / 2 - CX) <= 1 and rows[0] == P["headTopY"]
        ck.add("canvas_contact_headtop", v, "PASS" if ok and a.shape == (1600, 1200) else "FAIL",
               detail={"top": int(rows[0]), "bottom": int(rows[-1]), "contactX": (int(xs[0]) + int(xs[-1])) / 2})
    def dims(v):
        j = PJ[v]
        return {"headsTall": round((GROUND - P["headTopY"]) / P["headHeight"], 3), "hipY": j["hipL"][1], "kneeY": j["kneeL"][1], "ankleY": j["ankleL"][1],
                "legLength": GROUND - j["hipL"][1], "shoulderY": j["shoulderL"][1], "elbowY": j["elbowL"][1], "wristY": j["wristL"][1]}
    ds = {v: dims(v) for v in VIEWS}
    ck.add("heads_joints_leglength_4views", "all", "PASS" if len({tuple(sorted(x.items())) for x in ds.values()}) == 1 else "FAIL", detail=ds)
    fb = all(PJ["front"][k][0] == 2 * CX - PJ["back"][k][0] and PJ["front"][k][1] == PJ["back"][k][1] for k in J)
    ck.add("front_back_mirror", "front/back", "PASS" if fb else "FAIL")
    lr = all(PJ["left"][k][0] == 2 * CX - PJ["right"][k][0] and PJ["left"][k][1] == PJ["right"][k][1] for k in J)
    ck.add("left_right_mirror", "left/right", "PASS" if lr else "FAIL")
    # connectivity: every joint reaches the root; every segment has both ends
    def root_of(k, seen=()):
        return k if k == "pelvis" else (None if k in seen or k not in TREE else root_of(TREE[k], seen + (k,)))
    orphans = [k for k in J if k != "pelvis" and root_of(k) != "pelvis"]
    ck.add("skeleton_connected", "joints", "PASS" if not orphans and all(p in J for p in TREE.values()) else "FAIL", detail={"orphans": orphans, "joints": len(J)})
    seglen = {f"{TREE[k]}->{k}": round(math.dist(J[k], J[TREE[k]]), 2) for k in TREE}
    pairs = [(k, k[:-1] + "R") for k in TREE if k.endswith("L") and k[:-1] + "R" in TREE]
    sym = all(math.isclose(math.dist(J[a], J[TREE[a]]), math.dist(J[b], J[TREE[b]])) for a, b in pairs)
    ck.add("segment_lengths_left_right", "joints", "PASS" if sym else "FAIL", detail=seglen)
    # rendered connection: each child joint lies inside the drawn body (no gaps between volumes)
    gaps = []
    for v in VIEWS:
        a = ndimage.binary_dilation(np.asarray(Image.open(l0imgs[v]))[..., 3] > 0, iterations=1)
        lab, n = ndimage.label(a)
        if n != 1:
            gaps.append(f"{v}: {n} separate pieces")
        for k in ("neckTop", "neckBase", "waist", "shoulderL", "shoulderR", "elbowL", "elbowR", "wristL", "wristR", "hipL", "hipR", "kneeL", "kneeR", "ankleL", "ankleR", "ballL", "ballR", "heelL", "heelR"):
            x, y = PJ[v][k]
            y = min(y, GROUND)
            if not a[y, x]:
                gaps.append(f"{v}/{k}")
    ck.add("joints_connected_in_render", "all", "PASS" if not gaps else "FAIL", detail=gaps or None)
    # walk rotation axes: forward kinematics keeps the parent fixed and segment lengths constant
    fk = {}
    for name, ax in AXES.items():
        jn = ax["joints"][0]
        if ax["axis"] != LAT:
            fk[name] = "vertical axis (twist): not tested by the sagittal FK check"
            continue
        ch = descendants(jn)
        if name == "heel":   # heel strike: the foot and shank rotate about the heel contact
            ch = [k for k in ["ankleL"] + descendants("ankleL") if k != jn]
        Jr = fk_rotate(J, jn, ax["rangeDeg"][1] if ax["rangeDeg"][1] else ax["rangeDeg"][0], ch)
        lens_ok = all(math.isclose(math.dist(Jr[k], Jr[TREE[k]]), math.dist(J[k], J[TREE[k]]), abs_tol=1e-6) for k in ch if TREE.get(k) in ch or TREE.get(k) == jn)
        lens_ok = lens_ok and all(math.isclose(math.dist(Jr[k], Jr[jn]), math.dist(J[k], J[jn]), abs_tol=1e-6) for k in ch)
        fk[name] = {"pivotFixed": Jr[jn] == J[jn], "lengthsPreserved": lens_ok, "moved": [k for k in ch if Jr[k] != J[k]][:6]}
    ok = all(isinstance(x, str) or (x["pivotFixed"] and x["lengthsPreserved"] and x["moved"]) for x in fk.values())
    ck.add("walk_rotation_axes", "joints", "PASS" if ok else "FAIL", detail=fk)
    gr = all(J[f"{p}{s}"][1] == GROUND for p in ("heel", "ball", "toe", "foot") for s in "LR")
    ck.add("foot_contact_pivots_on_ground", "joints", "PASS" if gr else "FAIL", detail={k: J[k] for k in ("heelL", "ballL", "toeL", "footL")})

    # ---------- interference with Layers 1-3 ----------
    contain = {}
    for v in VIEWS:
        src = Path(repo_root) / tf["views"][v]["output"]["path"]
        with Image.open(src) as cim:
            ca = np.asarray(cim.convert("RGBA"))
        fg = (ca[..., 3] >= 128) & (ca[..., :3].max(axis=2) > 10) if tf["views"][v]["source"]["mode"] != "RGBA" else ca[..., 3] >= 128
        fg = ndimage.binary_fill_holes(fg)
        b0 = np.asarray(Image.open(l0imgs[v]))[..., 3] > 0
        b1 = np.asarray(Image.open(l1imgs[v][0]))[..., 3] > 0
        near0 = ndimage.binary_dilation(b0, iterations=4)
        contain[v] = {"L0insideCanon": round(float((b0 & fg).sum() / b0.sum()), 4), "L1insideCanon": round(float((b1 & fg).sum() / b1.sum()), 4),
                      "L1onL0": round(float((b1 & near0).sum() / b1.sum()), 4)}
        ck.add("L1_hugs_L0", v, "PASS" if contain[v]["L1onL0"] >= 0.999 else "FAIL", detail=contain[v])
        core_m = masks(partsets[v], ["ribcage", "waist", "pelvis", "girdle"])
        cov = float((core_m & b1).sum() / core_m.sum())
        ck.add("L1_opaque_coverage_torso_hips", v, "PASS" if cov >= 0.999 else "FAIL", detail={"coveredRatio": round(cov, 4)},
               reason=None if cov >= 0.999 else "the base layer must fully cover the torso and hip volumes")
        for lay, key in (("L0", "L0insideCanon"), ("L1", "L1insideCanon")):
            r = contain[v][key]
            ck.add(f"{lay}_inside_L2L3_canon", v, "PASS" if r >= 0.98 else "NOT_RUN", "automated" if r >= 0.98 else "human", detail=r,
                   reason=None if r >= 0.98 else "some pixels fall outside the costumed canon figure; check by eye in *_stack_with_canon.png")
        # stack preview: L0 + L1 under the canon (L2/L3 reference, semi-transparent)
        st = Image.new("RGBA", (1200, 1600), (58, 62, 70, 255))
        st.alpha_composite(Image.open(l0imgs[v])); st.alpha_composite(Image.open(l1imgs[v][0]))
        faint = Image.fromarray(np.dstack([ca[..., :3], np.where(fg, 140, 0).astype(np.uint8)]), "RGBA")
        st.alpha_composite(faint)
        st.convert("RGB").save(out_l0 / f"{v}_stack_with_canon.png", compress_level=9)
    ck.add("L1_layer_design_is_non_revealing", "layer1", "NOT_RUN", "human", reason="independent visual review of the opaque base layer (no lingerie elements by construction)")
    for e, before in canon_before.items():
        ck.add("protected_sha256", e, "PASS" if sha256_file(Path(repo_root) / e) == before else "FAIL")
    after = {p.name: sha256_file(p) for p in Path(v08_spec_path).parent.iterdir()}
    ck.add("v08_outputs_unchanged", rel(Path(v08_spec_path).parent, repo_root), "PASS" if after == v08_files else "FAIL")
    for cid, label in design_protection_checks("morwen"):
        ck.add(cid, "design", "NOT_RUN", "human", reason="mandatory visual QA: " + label)
    for cid, why in (("independent_visual_review_layer0", "independent (non-author) review of the articulated guides"),
                     ("final_layer0_adoption", "director decision"), ("final_layer1_adoption", "director decision")):
        ck.add(cid, "all", "NOT_RUN", "human", reason=why)

    # ---------- documents ----------
    spec = {"schema": "cas/master-body/0.8", "status": "UNAPPROVED_CANDIDATE", "characterId": v08["characterId"], "ageCategory": v08["ageCategory"],
            "bodyGuidePolicy": v08["bodyGuidePolicy"], "canvas": CANVAS, "anchor": v08["anchor"], "finalAdoption": "NOT_RUN",
            "version": "0.9-articulated", "statusLegend": v08["statusLegend"], "parameters": v08["parameters"],
            "joints3d": {k: [R(c) for c in v] for k, v in J.items()}, "addedJoints": sorted(added), "kinematicTree": TREE, "rotationAxes": AXES,
            "projection": v08["projection"], "views": {v: {"joints": PJ[v], "layer0Part": {"path": rel(l0imgs[v], repo_root), "sha256": sha256_file(l0imgs[v])},
                                                         "articulatedGuide": {"path": rel(out_l0 / f"{v}_articulated_guide.png", repo_root)}} for v in VIEWS},
            "baseBodySpecV2": v08["baseBodySpecV2"], "base": changes["base"],
            "outputs": [{"path": rel(out_l0 / n, repo_root)} for n in ["compare_4views_structure.png"] + [f"{v}_stack_with_canon.png" for v in VIEWS]]}
    l1spec = {"schema": "cas/layer1-base/0.9", "status": "UNAPPROVED_CANDIDATE", "characterId": "morwen", "layerId": "L1_UNDERWEAR", "ageCategory": "minor",
              "design": {"kind": "opaque non-revealing base layer", "pieces": ["high-neck short-sleeve top (opaque)", "knee-length shorts (opaque)", "over-knee socks"],
                         "palette": {"top": "#4e3866", "shorts": "#403052", "socks": "#342a3c"}, "excluded": ["lingerie elements", "lace", "sheer fabric", "garter belt (canon structure to be taken from the approved outfit separately)"]},
              "builtFrom": "Layer 0 v0.9 volumes (dilated 2-3 px); no new body measurements",
              "outputs": {v: {"path": rel(l1imgs[v][0], repo_root), "sha256": sha256_file(l1imgs[v][0]), "pixels": l1imgs[v][1]} for v in VIEWS},
              "finalAdoption": "NOT_RUN"}
    sheet = layerlib.comparison_sheet([Image.open(out_l0 / f"{v}_articulated_guide.png") for v in VIEWS], [f"{v}" for v in VIEWS], GROUND)
    sheet.save(out_l0 / "compare_4views_structure.png", compress_level=9)
    rep = make_report({"kind": "layer0-articulated-candidate", "characterId": "morwen", "path": rel(out_l0, repo_root)}, ck.rows)
    (out_l0 / "MASTER_BODY_SPEC.v0.9.candidate.json").write_text(stable_dumps(spec), encoding="utf-8")
    (out_l0 / "JOINT_CHANGES_v0.9.json").write_text(stable_dumps(changes), encoding="utf-8")
    (out_l0 / "BODY_QA_v0.9.json").write_text(stable_dumps(rep), encoding="utf-8")
    (out_l1 / "LAYER1_BASE_SPEC.candidate.json").write_text(stable_dumps(l1spec), encoding="utf-8")
    # modular character with L0 + L1 parts (for layer-qa / ON-OFF compositing)
    anchor = v08["anchor"]
    mparts = []
    for v in VIEWS:
        for layer, pid, path, z, ms in (("L0_BASE_BODY", "master_body", l0imgs[v], 10, "DESIGNED_CANDIDATE"), ("L1_UNDERWEAR", "base_layer", l1imgs[v][0], 110, "DESIGNED_CANDIDATE")):
            sha = sha256_file(path)
            part = {"schema": "cas/modular-part/0.7", "characterId": "morwen", "view": v, "frameIndex": 0, "canvas": CANVAS, "layerId": layer, "partId": pid,
                    "zOrder": z, "anchorSet": {"anchor": anchor}, "sourceAsset": {"path": rel(path, repo_root), "sha256": sha, "width": 1200, "height": 1600, "mode": "RGBA"},
                    "sha256": sha, "approvalStatus": "UNAPPROVED_CANDIDATE", "measurementStatus": ms,
                    "sourceEvidence": [{"kind": "v0.9 articulated master body", "path": rel(out_l0 / "MASTER_BODY_SPEC.v0.9.candidate.json", repo_root)}]}
            if layer == "L0_BASE_BODY":
                part["bodyGuidePolicy"] = "minor_neutral_structure"
            mparts.append(part)
    mdoc = {"schema": "cas/modular-character/0.7", "characterId": "morwen", "ageCategory": "minor", "bodyGuidePolicy": "minor_neutral_structure",
            "canvas": CANVAS, "anchor": anchor, "views": list(VIEWS), "frameCount": 1, "layerCatalog": "tools/character-asset-studio/profiles/layer_catalog.json",
            "parts": mparts, "note": "GENERATED by cas.py articulated-body. Layer 0 (v0.9) + Layer 1 base-layer candidates only. Layers 2-3 exist only as the protected canon (reference)."}
    return spec, rep, mdoc, contain
