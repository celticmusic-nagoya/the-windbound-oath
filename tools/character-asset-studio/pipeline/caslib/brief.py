"""Guide PNGs and machine-readable production briefs for AI image generation.

Guides are drawing aids (canvas, anchor, ground, landmark lines) on a transparent canvas. Briefs carry the
same numbers as JSON so a receiving AI never has to read coordinates off an image. Both are
UNAPPROVED_INSTRUCTION; a brief cannot adopt anything (adoption.autoAdopt is always false).
"""
from pathlib import Path

from .core import (VIEWS, LANDMARK_KEYS, REPO_ROOT, STUDIO_DIR, PolicyError, guard_write, is_protected, load_json,
                   preset, preset_canvas, protected_list, rel, sha256_file, to_norm, to_pixel, placement, anchor_record)
from .imageqa import HUMAN_CHECKS

# Same template as studio-core.js TEMPLATE (normalised). Parity is unit-tested.
TEMPLATE = {
    "headTop": [0.5, 0.075], "neck": [0.5, 0.19375], "shoulderLeft": [0.4, 0.21875], "shoulderRight": [0.6, 0.21875],
    "pelvis": [0.5, 0.5125], "kneeLeft": [0.44583, 0.725], "kneeRight": [0.55417, 0.725],
    "footLeft": [0.43333, 0.9625], "footRight": [0.56667, 0.9625], "ground": [0.5, 0.9625],
}
AUTOMATED_CHECKS = ["schema_valid", "status_unapproved", "frame_set_complete", "file_sha256", "dimensions", "alpha_channel",
                    "real_transparency", "transparent_border", "content_present", "ground_contact", "anchor_x_at_contact",
                    "frame_size_consistency", "ground_consistency", "bbox_height_consistency", "no_identical_consecutive_frames"]
POLICY_CONSTRAINTS = [
    ("canon_protected", "Do not edit, overwrite, re-encode or move protected canonical files; use them as visual references only."),
    ("no_auto_adoption", "Every delivered image is UNAPPROVED_CANDIDATE until a director approval record exists."),
    ("age_and_body_unchanged", "Keep the character's age, body and proportions; no sexualised emphasis (Morwen is 17)."),
    ("no_guessed_structure", "Do not invent unconfirmed equipment or costume structure; mark unknown regions in the delivery note."),
    ("real_alpha", "Transparent background must be real alpha=0, not a painted checkerboard or solid colour."),
    ("shared_anchor", "All views and frames share the same canvas and anchor; feet contact the ground line at the anchor."),
]


def landmarks_for(spec, canvas):
    """Landmarks per view from a BASE_BODY_SPEC v2.0 (normalised, re-projected to this canvas) or the template."""
    out = {}
    for v in VIEWS:
        out[v] = {}
        for k in LANDMARK_KEYS:
            if spec:
                rec = spec["landmarks"][v][k]
                n, conf, src = rec["n"], rec["confidence"], rec["source"]
            else:
                n, conf, src = TEMPLATE[k], "provisional", "template_default"
            out[v][k] = {"n": list(n), "px": to_pixel(n, canvas), "confidence": conf, "source": src}
    return out


def visual_reference(character_id, view, repo_root=REPO_ROOT):
    for e in protected_list()["files"]:
        if f"/{character_id}/" in e["path"] and e.get("role") == "director_approved_visual_canon_4view" and Path(e["path"]).stem == view:
            return {"path": e["path"], "sha256": e["sha256"]}
    return None


def draw_guide(canvas, anchor_px, lms, view, label_lines, out_path, preview_ref=None, overwrite=False, repo_root=REPO_ROOT):
    from PIL import Image, ImageDraw, ImageFont
    W, H = canvas["width"], canvas["height"]
    s = max(1, round(W / 600))
    try:
        font = ImageFont.load_default(size=max(10, round(W / 60)))
    except TypeError:                     # Pillow < 10.1
        font = ImageFont.load_default()
    lh = font.getbbox("Ag")[3] + 4
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(150, 160, 175, 200), width=s)
    inset = round(W * 0.04)
    for x in range(inset, W - inset, 12 * s):       # dotted safe area
        d.line([x, inset, x + 5 * s, inset], fill=(120, 200, 255, 160), width=s)
        d.line([x, H - inset, x + 5 * s, H - inset], fill=(120, 200, 255, 160), width=s)
    for y in range(inset, H - inset, 12 * s):
        d.line([inset, y, inset, y + 5 * s], fill=(120, 200, 255, 160), width=s)
        d.line([W - inset, y, W - inset, y + 5 * s], fill=(120, 200, 255, 160), width=s)
    ax, ay = anchor_px
    d.line([ax, 0, ax, H], fill=(255, 255, 255, 110), width=s)
    d.line([0, ay, W, ay], fill=(240, 120, 60, 255), width=2 * s)
    d.line([ax - 14 * s, ay - 14 * s, ax + 14 * s, ay + 14 * s], fill=(240, 120, 60, 255), width=2 * s)
    d.line([ax - 14 * s, ay + 14 * s, ax + 14 * s, ay - 14 * s], fill=(240, 120, 60, 255), width=2 * s)
    for k, rec in lms.items():
        x, y = rec["px"]
        col = (255, 215, 90, 230) if rec["source"] != "template_default" else (200, 170, 255, 210)
        if k in ("headTop", "neck", "pelvis", "ground"):
            d.line([inset, y, W - inset, y], fill=col[:3] + (90,), width=s)
        r = 6 * s
        d.ellipse([x - r, y - r, x + r, y + r], outline=col, width=2 * s)
        d.text((x + 9 * s, y - lh // 2), k, fill=col, font=font)
    for i, t in enumerate(label_lines):
        d.text((inset + 4 * s, inset + 4 * s + i * lh), t, fill=(255, 255, 255, 230), font=font)
    out = guard_write(out_path, repo_root, allow_overwrite=overwrite)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, optimize=True)
    files = {"guide": {"path": rel(out, repo_root), "sha256": sha256_file(out), "width": W, "height": H, "mode": "RGBA"}}
    if preview_ref is not None:
        bg = Image.new("RGBA", (W, H), (58, 62, 70, 255))
        ref_path = Path(repo_root) / preview_ref["path"]
        if ref_path.exists() and sha256_file(ref_path) == preview_ref["sha256"]:
            with Image.open(ref_path) as ref:                       # read-only use of the protected reference
                pl = placement(ref.width, ref.height, canvas)
                r2 = ref.convert("RGBA").resize((round(pl["w"]), round(pl["h"])))
                r2.putalpha(r2.getchannel("A").point(lambda a: a * 90 // 255))
                bg.alpha_composite(r2, (round(pl["x"]), round(pl["y"])))
        bg.alpha_composite(im)
        pv = guard_write(Path(out_path).with_name(Path(out_path).stem + "_preview.png"), repo_root, allow_overwrite=overwrite)
        bg.convert("RGB").save(pv, optimize=True)
        files["guidePreview"] = {"path": rel(pv, repo_root), "sha256": sha256_file(pv), "width": W, "height": H, "mode": "RGB"}
    return files


def build_brief(task_id, kind, character_id, preset_id, out_dir, deliver_to, frame_count=None, layer_slot=None,
                description=None, body_spec_path=None, views=VIEWS, with_preview=True, overwrite=False, repo_root=REPO_ROOT):
    if not deliver_to.startswith("assets/candidates/") or is_protected(deliver_to + "/x.png"):
        raise PolicyError("deliverTo must be a new folder under assets/candidates/ and not a protected path")
    p = preset(preset_id)
    canvas = preset_canvas(p)
    anchor_px = to_pixel(p["ground"], canvas)
    spec = None
    if body_spec_path:
        blocked = {r["path"]: r for r in load_json(STUDIO_DIR / "profiles" / "reference_bodies.json")["references"]}
        if rel(body_spec_path, repo_root) in blocked and blocked[rel(body_spec_path, repo_root)]["status"].startswith("BLOCKED"):
            raise PolicyError(f"body spec {rel(body_spec_path, repo_root)} is BLOCKED: {blocked[rel(body_spec_path, repo_root)]['reason'][:160]}")
        spec = load_json(body_spec_path)
    lms = landmarks_for(spec, canvas)
    src = {"kind": "BASE_BODY_SPEC" if spec else "template_default",
           "status": spec["status"] if spec else "TEMPLATE_NOT_MEASURED",
           "note": rel(body_spec_path, repo_root) if spec else "Template landmarks only; not a measured body. Use for canvas/anchor/ground framing, not anatomy."}
    fc = frame_count or p["frames"]
    out_dir = Path(out_dir)
    vdocs = {}
    for v in views:
        ref = visual_reference(character_id, v, repo_root)
        labels = [f"{task_id} · {character_id} · {kind} · {v}", f"canvas {canvas['width']}x{canvas['height']} · anchor {anchor_px[0]},{anchor_px[1]}",
                  f"landmarks: {src['kind']} ({src['status']})", "UNAPPROVED_INSTRUCTION - guide only, not artwork"]
        files = draw_guide(canvas, anchor_px, lms[v], v, labels, out_dir / f"guide_{v}.png", ref if with_preview else None, overwrite, repo_root)
        vdocs[v] = {"guide": files["guide"], "landmarks": lms[v], "visualReference": ref}
        if "guidePreview" in files:
            vdocs[v]["guidePreview"] = files["guidePreview"]
    cons = [{"id": cid, "text": t, "check": "human" if cid in ("age_and_body_unchanged", "no_guessed_structure") else "automated"} for cid, t in POLICY_CONSTRAINTS]
    cpath = STUDIO_DIR / "profiles" / f"{character_id}_constraints.json"
    if cpath.exists():
        cons += [{"id": f"constraint:{c['id']}", "text": c["label"], "views": c.get("views", []), "check": "human"} for c in load_json(cpath)["constraints"]]
    task = {"id": task_id, "kind": kind, "characterId": character_id, "frameCount": fc}
    if layer_slot:
        task["layerSlot"] = layer_slot
    if description:
        task["description"] = description
    brief = {
        "schema": "cas/production-brief/0.5", "status": "UNAPPROVED_INSTRUCTION", "task": task, "presetId": preset_id,
        "canvas": canvas, "anchor": anchor_record(anchor_px, canvas, "ground contact: outer sole span at bottom-6 row, centre x; lowest alpha>=128 row = anchor y"),
        "views": vdocs, "landmarkSource": src,
        "outputRequirements": {"format": "PNG", "mode": "RGBA", "width": canvas["width"], "height": canvas["height"],
                               "background": "real alpha=0 (transparent), no checkerboard, no solid fill",
                               "fileNamePattern": f"{character_id}_{kind}_{{view}}_f{{frame:02d}}.png", "deliverTo": deliver_to,
                               "forbidden": ["text or watermarks", "more than one character", "cropping at the canvas edge", "editing protected files"]},
        "constraints": cons,
        "protectedReferences": [{"path": e["path"], "sha256": e["sha256"], "use": "visual reference only; never modify"} for e in protected_list()["files"] if f"/{character_id}/" in e["path"]],
        "acceptanceChecks": [{"id": c, "kind": "automated"} for c in AUTOMATED_CHECKS] + [{"id": c, "kind": "human", "text": t} for c, t in HUMAN_CHECKS],
        "adoption": {"autoAdopt": False, "requires": "director approval record after automated QA PASS and human review"},
        "handoff": {"returnFormat": "cas/asset-set/0.5 JSON listing every delivered PNG with sha256",
                    "qaCommand": "python3 tools/character-asset-studio/pipeline/cas.py qa <asset-set.json>",
                    "prAggregation": "python3 tools/character-asset-studio/pipeline/cas.py pr-summary <qa-report.json>..."},
    }
    return brief
