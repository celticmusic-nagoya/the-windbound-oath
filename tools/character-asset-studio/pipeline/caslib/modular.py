"""4-layer modular character model (v0.7): validation, measurement-status mapping, part selection, compositing.

Logical layers (L0 BASE_BODY, L1 UNDERWEAR, L2 BASE_OUTFIT, L3 OUTER_ACCESSORIES) classify parts; the draw order
is zOrder (ties broken by partId) so e.g. a rear robe can sit behind the body. measurementStatus and approvalStatus
are independent fields. Nothing here changes approval status or writes to protected paths.
"""
from pathlib import Path

from .core import REPO_ROOT, STUDIO_DIR, guard_write, load_json, rel, sha256_file, to_norm
from .report import Checks
from .schemas import validate

LAYERS = ["L0_BASE_BODY", "L1_UNDERWEAR", "L2_BASE_OUTFIT", "L3_OUTER_ACCESSORIES"]
MEASUREMENT_STATUSES = ["VERIFIED", "ESTIMATED", "UNKNOWN", "TEMPLATE", "DESIGNED_CANDIDATE"]


def catalog():
    return load_json(STUDIO_DIR / "profiles" / "layer_catalog.json")


def status_from_v06(rec):
    """Map a v0.6 measurement-evidence landmark to the v0.7 measurementStatus.
    automated visible -> VERIFIED; AI-visual 'visible' and 'estimated' -> ESTIMATED (not human-confirmed);
    unmeasurable -> UNKNOWN. (TEMPLATE / DESIGNED_CANDIDATE never come from a measurement.)"""
    if rec["status"] == "unmeasurable":
        return "UNKNOWN"
    if rec["status"] == "visible" and rec.get("origin") == "automated_alpha":
        return "VERIFIED"
    return "ESTIMATED"


def check_character(doc, repo_root=REPO_ROOT, check_files=True):
    """Schema + semantic checks for a cas/modular-character/0.7 document. Returns Checks rows."""
    ck = Checks()
    v = validate(doc)
    ck.add("schema_valid", "modular-character", v["result"], detail=v["errors"] or None)
    if v["result"] != "PASS":
        return ck.rows
    canvas, anchor = doc["canvas"], doc["anchor"]
    ck.add("anchor_px_norm_consistent", "modular-character", "PASS" if to_norm(anchor["px"], canvas) == anchor["n"] else "FAIL")
    seen = set()
    for p in doc["parts"]:
        scope = f"{p['view']}/f{p['frameIndex']:02d}/{p['layerId']}/{p['partId']}"
        key = (p["view"], p["frameIndex"], p["partId"])
        ck.add("part_unique", scope, "FAIL" if key in seen else "PASS")
        seen.add(key)
        ck.add("part_matches_character", scope, "PASS" if (p["characterId"], p["canvas"]) == (doc["characterId"], canvas) and p["view"] in doc["views"] and p["frameIndex"] < doc["frameCount"] else "FAIL")
        ck.add("anchor_shared", scope, "PASS" if p["anchorSet"]["anchor"]["px"] == anchor["px"] else "FAIL",
               detail={"part": p["anchorSet"]["anchor"]["px"], "character": anchor["px"]})
        ck.add("sha256_field_matches_source", scope, "PASS" if p["sha256"] == p["sourceAsset"]["sha256"] else "FAIL")
        if p["layerId"] == "L0_BASE_BODY":
            ck.add("body_guide_policy", scope, "PASS" if p.get("bodyGuidePolicy") == doc["bodyGuidePolicy"] else "FAIL",
                   detail={"part": p.get("bodyGuidePolicy"), "character": doc["bodyGuidePolicy"], "ageCategory": doc["ageCategory"]})
        if p["approvalStatus"] == "DIRECTOR_APPROVED" and not any(a.get("decision") == "approved" for a in p.get("approvals", [])):
            ck.add("approval_record", scope, "FAIL", reason="DIRECTOR_APPROVED without an approval record")
        if check_files:
            f = Path(repo_root) / p["sourceAsset"]["path"]
            if not f.exists():
                ck.add("file_present", scope, "FAIL", reason=p["sourceAsset"]["path"])
            else:
                ck.add("file_sha256", scope, "PASS" if sha256_file(f) == p["sourceAsset"]["sha256"] else "FAIL")
    if doc.get("baseBodySpec"):
        f = Path(repo_root) / doc["baseBodySpec"]["path"]
        ok = f.exists() and sha256_file(f) == doc["baseBodySpec"]["sha256"]
        ck.add("base_body_spec_link", "modular-character", "PASS" if ok else "FAIL", detail=doc["baseBodySpec"]["path"])
        if ok:
            sv = validate(load_json(f))
            ck.add("base_body_spec_v2_compatible", "modular-character", sv["result"], detail=sv["schema"])
    return ck.rows


def select_parts(doc, view, frame, layers=None):
    """Parts for one view/frame in draw order (zOrder, partId). layers=None -> all layers ON."""
    on = set(layers) if layers is not None else set(LAYERS)
    unknown = on - set(LAYERS)
    if unknown:
        raise ValueError(f"unknown layer ids: {sorted(unknown)}")
    ps = [p for p in doc["parts"] if p["view"] == view and p["frameIndex"] == frame and p["layerId"] in on]
    return sorted(ps, key=lambda p: (p["zOrder"], p["partId"]))


def compose(doc, view, frame, layers=None, out=None, repo_root=REPO_ROOT, overwrite=False):
    """Alpha-composite the selected parts onto a transparent canvas. Returns (PIL image, parts used).
    If out is given, writes a NEW preview file (never a source asset or protected path)."""
    from PIL import Image
    W, H = doc["canvas"]["width"], doc["canvas"]["height"]
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    used = select_parts(doc, view, frame, layers)
    sources = {p["sourceAsset"]["path"] for p in doc["parts"]}
    for p in used:
        with Image.open(Path(repo_root) / p["sourceAsset"]["path"]) as im:
            canvas.alpha_composite(im.convert("RGBA"))
    if out is not None:
        if rel(out, repo_root) in sources:
            raise ValueError("refusing to write a composite over a source part")
        o = guard_write(out, repo_root, overwrite)
        o.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(o, compress_level=9)
    return canvas, [p["partId"] for p in used]
