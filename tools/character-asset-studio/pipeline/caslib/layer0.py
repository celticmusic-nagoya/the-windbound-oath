"""Layer 0 (BASE_BODY) master-body CANDIDATE guides from the normalised canon (TASK D, v0.7).

Inputs: v0.6 measurement evidence (unchanged) + v0.7 view transforms (normalised working copies).
Outputs (new files in out_dir):
  landmark_evidence.json         per view/landmark: normalised px/n + measurementStatus (VERIFIED/ESTIMATED/UNKNOWN),
                                 plus a separate designedCandidates block (DESIGNED_CANDIDATE, never canon measurements)
  BASE_BODY_SPEC.candidate.json  BASE_BODY_SPEC v2.0 (unchanged format), status candidate_not_canonical
  <view>_body_guide.png          RGBA guide (+ _preview with the normalised canon faint underneath)
  production_brief.json          cas/production-brief/0.5 for the separate image-generation step (ChatGPT)
  BODY_QA_REPORT.json            cas/qa-report/0.5 (adoptionReady false)

The 23 points hidden by the costume stay UNKNOWN: they are not registered as measured, and their v2.0 slots
carry template placeholders labelled template_default/provisional. Template values are never adopted.
"""
from pathlib import Path

from .core import (LANDMARK_KEYS, REPO_ROOT, STUDIO_DIR, VIEWS, guard_write, js_round, load_json, protected_list, rel,
                   sha256_file, stable_dumps, to_norm, to_pixel)
from .brief import TEMPLATE, AUTOMATED_CHECKS
from .canonmeasure import CANVAS
from .imageqa import design_protection_checks
from .modular import status_from_v06
from .report import Checks, make_report
from .schemas import validate

REFERENCE = [600, 1540]
POLICY = {"minor": "minor_neutral_structure", "adult": "adult_nonexplicit_anatomy"}
GUIDE_TEXT = {
    "minor_neutral_structure": "neutral structure guide: smooth mannequin-like form, uniform grey, no anatomical detail, "
                               "no sexual characteristics, age and body unchanged (character is a minor)",
    "adult_nonexplicit_anatomy": "non-explicit adult anatomy guide: proportions and joints only, no explicit detail",
}


def run(character_id, age_category, evidence_path, transforms_path, out_dir, overwrite=False, repo_root=REPO_ROOT):
    from PIL import Image, ImageDraw, ImageFont
    ev, tf = load_json(evidence_path), load_json(transforms_path)
    policy = POLICY[age_category]
    out_dir = Path(out_dir)
    names = ["landmark_evidence.json", "BASE_BODY_SPEC.candidate.json", "production_brief.json", "BODY_QA_REPORT.json"]
    names += [f"{v}_body_guide{s}.png" for v in VIEWS for s in ("", "_preview")]
    for n in names:
        guard_write(out_dir / n, repo_root, overwrite)
    out_dir.mkdir(parents=True, exist_ok=True)
    ck = Checks()
    ck.add("transforms_derived_from_evidence", "view_transforms.json",
           "PASS" if tf["derivedFrom"]["sha256"] == sha256_file(evidence_path) else "FAIL", detail=tf["derivedFrom"])

    lev = {"schema": "cas/body-landmark-evidence/0.7", "status": "UNAPPROVED_REFERENCE", "characterId": character_id,
           "ageCategory": age_category, "bodyGuidePolicy": policy, "canvas": CANVAS, "referenceContact": REFERENCE,
           "inputs": {"measurementEvidence": {"path": rel(evidence_path, repo_root), "sha256": sha256_file(evidence_path)},
                      "viewTransforms": {"path": rel(transforms_path, repo_root), "sha256": sha256_file(transforms_path)}},
           "policy": "Normalised coordinates = v0.6 canon measurements + per-view translation. measurementStatus: VERIFIED (automated sole/ground), "
                     "ESTIMATED (AI visual or inferred, not human-confirmed), UNKNOWN (hidden by costume). DESIGNED_CANDIDATE values are listed "
                     "separately and are never canon measurements. Nothing here is adopted.",
           "views": {}}
    spec_lm = {}
    for v in VIEWS:
        dx, dy = tf["views"][v]["translate"]
        lev["views"][v] = {"translate": [dx, dy], "landmarks": {}}
        spec_lm[v] = {}
        for k in LANDMARK_KEYS:
            r = ev["views"][v]["landmarks"][k]
            st = status_from_v06(r)
            rec = {"measurementStatus": st, "v06Status": r["status"], "v06Origin": r.get("origin")}
            if st == "UNKNOWN":
                rec["reason"] = r.get("reason", "")
                n = list(TEMPLATE[k])
                spec_lm[v][k] = {"n": n, "px": to_pixel(n, CANVAS), "confidence": "provisional", "source": "template_default"}
            else:
                px = [r["px"][0] + dx, r["px"][1] + dy]
                n = to_norm(px, CANVAS)
                rec.update({"px": px, "n": n, "confidence": r["confidence"], "method": r.get("method", "")})
                spec_lm[v][k] = {"n": n, "px": to_pixel(n, CANVAS), "confidence": r["confidence"] if st == "VERIFIED" else ("medium" if r["status"] == "visible" else "low"),
                                 "source": "measured_reference"}
            lev["views"][v]["landmarks"][k] = rec

    # designed candidates (common body values across views) — derived, never canon measurements
    knees = {f"{v}/{k}": lev["views"][v]["landmarks"][k]["px"][1] for v in VIEWS for k in ("kneeLeft", "kneeRight")
             if lev["views"][v]["landmarks"][k]["measurementStatus"] != "UNKNOWN"}
    knee_y = int(js_round(sum(knees.values()) / len(knees))) if knees else None
    lev["designedCandidates"] = {
        "commonGround": {"px": REFERENCE, "n": to_norm(REFERENCE, CANVAS), "measurementStatus": "VERIFIED",
                         "note": "all four normalised views put the measured sole contact on this point"},
        "commonKneeHeight": {"y": knee_y, "measurementStatus": "DESIGNED_CANDIDATE",
                             "derivedFrom": knees, "spreadPx": (max(knees.values()) - min(knees.values())) if knees else None,
                             "note": "mean of the normalised knee heights (all ESTIMATED). A proposal for a common build, not a measurement."},
        "hiddenJoints": {"measurementStatus": "UNKNOWN", "keys": ["headTop", "neck (back/side)", "shoulderLeft", "shoulderRight", "pelvis", "far knee/foot (side views)"],
                         "note": "To be designed in the image-generation step and returned as DESIGNED_CANDIDATE; never back-filled from the template or the canon outline."},
    }

    # ---------- guides ----------
    try:
        font = ImageFont.load_default(size=20)
    except TypeError:
        font = ImageFont.load_default()
    W, H = CANVAS["width"], CANVAS["height"]
    guides = {}
    for v in VIEWS:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(g)
        d.line([0, REFERENCE[1], W, REFERENCE[1]], fill=(240, 120, 60, 255), width=3)
        d.line([REFERENCE[0], 0, REFERENCE[0], H], fill=(255, 255, 255, 90), width=1)
        d.line([REFERENCE[0] - 16, REFERENCE[1] - 16, REFERENCE[0] + 16, REFERENCE[1] + 16], fill=(240, 120, 60, 255), width=3)
        d.line([REFERENCE[0] - 16, REFERENCE[1] + 16, REFERENCE[0] + 16, REFERENCE[1] - 16], fill=(240, 120, 60, 255), width=3)
        if knee_y:
            for x in range(0, W, 24):
                d.line([x, knee_y, x + 12, knee_y], fill=(80, 210, 255, 200), width=2)
            d.text((W - 40 - font.getlength(f"common knee height {knee_y} (DESIGNED_CANDIDATE)"), knee_y - 26), f"common knee height {knee_y} (DESIGNED_CANDIDATE)", fill=(80, 210, 255, 255), font=font)
        offs = {"kneeLeft": (-12, -40), "kneeRight": (12, 14), "footLeft": (-12, -66), "footRight": (12, -40), "ground": (12, 14)}
        for k, r in lev["views"][v]["landmarks"].items():
            if r["measurementStatus"] == "UNKNOWN":
                continue
            x, y = r["px"]
            c = (80, 230, 120, 255) if r["measurementStatus"] == "VERIFIED" else (255, 210, 60, 255)
            if r["measurementStatus"] == "VERIFIED":
                d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=c, width=3)
            else:
                d.rectangle([x - 9, y - 9, x + 9, y + 9], outline=c, width=3)
            label = f"{k} {r['measurementStatus']}"
            ox, oy = offs.get(k, (12, -11))
            d.text((x + ox - (font.getlength(label) if ox < 0 else 0), y + oy), label, fill=c, font=font)
        unknown = [k for k, r in lev["views"][v]["landmarks"].items() if r["measurementStatus"] == "UNKNOWN"]
        lines = [f"{character_id} LAYER 0 BASE_BODY guide · {v} · CANDIDATE (UNAPPROVED)", f"policy: {policy}",
                 "circle = VERIFIED   square = ESTIMATED   dashed = DESIGNED_CANDIDATE", "UNKNOWN (design in generation step, not measured):"]
        lines += [", ".join(unknown[i:i + 4]) for i in range(0, len(unknown), 4)]
        for i, t in enumerate(lines):
            d.text((40, 40 + i * 26), t, fill=(255, 255, 255, 235), font=font)
        gp = out_dir / f"{v}_body_guide.png"
        g.save(gp, compress_level=9)
        src = Path(repo_root) / tf["views"][v]["output"]["path"]
        bg = Image.new("RGBA", (W, H), (58, 62, 70, 255))
        with Image.open(src) as im:
            faint = im.convert("RGBA")
        if faint.mode == "RGBA" and tf["views"][v]["source"]["mode"] != "RGBA":
            import numpy as np
            a = np.asarray(faint).copy()
            a[..., 3] = np.where(a[..., :3].max(axis=2) > 10, 255, 0)     # black background of RGB copies -> hidden in preview only
            faint = Image.fromarray(a, "RGBA")
        faint.putalpha(faint.getchannel("A").point(lambda x: x * 100 // 255))
        bg.alpha_composite(faint)
        bg.alpha_composite(g)
        pp = out_dir / f"{v}_body_guide_preview.png"
        bg.convert("RGB").save(pp, compress_level=9)
        guides[v] = {"guide": {"path": rel(gp, repo_root), "sha256": sha256_file(gp), "width": W, "height": H, "mode": "RGBA"},
                     "guidePreview": {"path": rel(pp, repo_root), "sha256": sha256_file(pp), "width": W, "height": H, "mode": "RGB"}}
    lev["bodyGuides"] = {v: guides[v] for v in VIEWS}

    spec = {"schemaVersion": "2.0", "status": "candidate_not_canonical", "characterId": character_id, "presetId": "MORWEN_REAL_1200x1600",
            "canvas": CANVAS, "groundNormalized": to_norm(REFERENCE, CANVAS), "worldScale": {"pixelsPerUnit": None},
            "coordinateSpace": "normalized canvas (0..1, origin top-left, y down); px = n * canvas size",
            "views": list(VIEWS), "landmarks": spec_lm,
            "referenceBody": [{"id": r["id"], "status": r["status"]} for r in load_json(STUDIO_DIR / "profiles" / "reference_bodies.json")["references"]]
                             + [{"id": f"{character_id.upper()}_LAYER0_V0.7", "status": "UNAPPROVED_PARTIAL_MEASUREMENT", "path": rel(out_dir / "landmark_evidence.json", repo_root)}],
            "assets": [{"name": Path(tf["views"][v]["output"]["path"]).name, "view": v, "layer": "reference", "frame": 0, "sha256": tf["views"][v]["output"]["sha256"],
                        "dimensions": [W, H], "canonical": False} for v in VIEWS],
            "notes": "UNAPPROVED Layer 0 candidate on the normalised working coordinates (contact (600,1540)). template_default/provisional entries are UNKNOWN "
                     "placeholders (hidden by costume), not measurements; DESIGNED_CANDIDATE values live only in landmark_evidence.json. Not for adoption without director approval."}

    known = {v: {k: {"n": spec_lm[v][k]["n"], "px": spec_lm[v][k]["px"], "confidence": spec_lm[v][k]["confidence"], "source": spec_lm[v][k]["source"]}
                 for k in LANDMARK_KEYS if lev["views"][v]["landmarks"][k]["measurementStatus"] != "UNKNOWN"} for v in VIEWS}
    brief = {"schema": "cas/production-brief/0.5", "status": "UNAPPROVED_INSTRUCTION",
             "task": {"id": f"{character_id.upper()}-LAYER0-BODY-V0.7", "kind": "base_body", "characterId": character_id, "frameCount": 1,
                      "description": f"Draw a Layer 0 master-body guide for {character_id} in four views on the normalised canvas. {GUIDE_TEXT[policy]}. "
                                     "Keep every VERIFIED point exactly; treat ESTIMATED points as soft targets; propose positions for UNKNOWN joints and "
                                     "return them as DESIGNED_CANDIDATE. Do not copy costume outlines as body contours."},
             "presetId": "MORWEN_REAL_1200x1600", "canvas": CANVAS,
             "anchor": {"px": REFERENCE, "n": to_norm(REFERENCE, CANVAS), "definition": "normalised sole contact shared by all four views"},
             "views": {v: {"guide": guides[v]["guide"], "guidePreview": guides[v]["guidePreview"], "landmarks": known[v],
                           "visualReference": {"path": tf["views"][v]["output"]["path"], "sha256": tf["views"][v]["output"]["sha256"]}} for v in VIEWS},
             "landmarkSource": {"kind": "normalised canon measurement (v0.6 + v0.7 transforms)", "status": "PARTIAL: UNKNOWN joints omitted, see landmark_evidence.json"},
             "outputRequirements": {"format": "PNG", "mode": "RGBA", "width": W, "height": H, "background": "real alpha=0 (transparent)",
                                    "fileNamePattern": f"{character_id}_layer0_body_{{view}}.png", "deliverTo": f"assets/candidates/{character_id}/layer0-body-v0.7",
                                    "forbidden": ["clothing or costume", "anatomical or sexual detail", "changing age, height or build", "editing protected files", "text or watermarks"]},
             "constraints": [{"id": "body_guide_policy", "text": GUIDE_TEXT[policy], "check": "human"},
                             {"id": "keep_verified_points", "text": "VERIFIED points (ground, sole contacts) must match within 2 px", "check": "automated"},
                             {"id": "designed_values_labelled", "text": "Return designed joints as DESIGNED_CANDIDATE with px/n; never as measured", "check": "automated"}]
                            + [{"id": cid, "text": label, "check": "human"} for cid, label in design_protection_checks(character_id)],
             "protectedReferences": [{"path": e["path"], "sha256": e["sha256"], "use": "visual reference only; never modify"} for e in protected_list()["files"] if f"/{character_id}/" in e["path"]],
             "acceptanceChecks": [{"id": c, "kind": "automated"} for c in AUTOMATED_CHECKS] + [{"id": "director_layer0_approval", "kind": "human", "text": "director approves the master body"}],
             "adoption": {"autoAdopt": False, "requires": "image generation, skeleton comparison and director approval (separate steps)"},
             "handoff": {"returnFormat": "cas/modular-part/0.7 (layerId L0_BASE_BODY, measurementStatus DESIGNED_CANDIDATE) per view",
                         "qaCommand": "python3 tools/character-asset-studio/pipeline/cas.py layer-qa <modular-character.json>"}}

    # ---------- QA ----------
    for v in VIEWS:
        src = Path(repo_root) / tf["views"][v]["output"]["path"]
        ck.add("normalised_source_sha256", v, "PASS" if sha256_file(src) == tf["views"][v]["output"]["sha256"] else "FAIL")
        for k in LANDMARK_KEYS:
            r, s = lev["views"][v]["landmarks"][k], spec_lm[v][k]
            scope = f"{v}/{k}"
            if r["measurementStatus"] == "UNKNOWN":
                ck.add("landmark_known", scope, "BLOCKED", reason="UNKNOWN (hidden by costume): " + r.get("reason", ""))
                ck.add("unknown_not_registered_as_measured", scope, "PASS" if (s["source"], s["confidence"]) == ("template_default", "provisional") else "FAIL")
            else:
                ck.add("px_norm_consistency", scope, "PASS" if s["px"] == r["px"] and to_norm(r["px"], CANVAS) == r["n"] else "FAIL", detail={"px": r["px"], "n": r["n"]})
                if r["measurementStatus"] == "ESTIMATED":
                    ck.add("landmark_visual_review", scope, "NOT_RUN", "human", reason="ESTIMATED; needs human confirmation")
    grounds = {v: tuple(lev["views"][v]["landmarks"]["ground"]["px"]) for v in VIEWS}
    ck.add("ground_identical_4views", "all", "PASS" if set(grounds.values()) == {tuple(REFERENCE)} else "FAIL", detail={v: list(g) for v, g in grounds.items()})
    ck.add("designed_values_separate_from_spec", "all", "PASS" if all(s["source"] in ("measured_reference", "template_default") for v in VIEWS for s in spec_lm[v].values()) else "FAIL")
    ck.add("common_knee_height_consistency", "all", "NOT_RUN", "human",
           detail=lev["designedCandidates"]["commonKneeHeight"], reason="normalised knee heights differ across views; all inputs are ESTIMATED, so this needs a human/skeleton comparison")
    ck.add("skeleton_consistency_4views", "all", "NOT_RUN", "human", reason="contact alignment is not skeleton alignment; compare after the Layer 0 image exists")
    vs = validate(spec)
    ck.add("spec_schema_v2", "BASE_BODY_SPEC.candidate.json", vs["result"], detail=vs["errors"] or None)
    ck.add("spec_status_unapproved", "BASE_BODY_SPEC.candidate.json", "PASS" if spec["status"] == "candidate_not_canonical" else "FAIL")
    vb = validate(brief)
    ck.add("brief_schema", "production_brief.json", vb["result"], detail=vb["errors"] or None)
    ck.add("brief_not_auto_adopt", "production_brief.json", "PASS" if brief["adoption"]["autoAdopt"] is False else "FAIL")
    r21 = [r for r in load_json(STUDIO_DIR / "profiles" / "reference_bodies.json")["references"] if r["id"] == "MORWEN_BASE_BODY_R2.1"]
    ck.add("r21_still_blocked", "profiles/reference_bodies.json", "PASS" if r21 and r21[0]["status"] == "BLOCKED_FOR_FINAL_CANON" else "FAIL")
    for e in protected_list()["files"]:
        ck.add("protected_sha256", e["path"], "PASS" if sha256_file(Path(repo_root) / e["path"]) == e["sha256"] else "FAIL")
    for cid, label in design_protection_checks(character_id):
        ck.add(cid, "design", "NOT_RUN", "human", reason="mandatory visual QA: " + label)
    ck.add("director_layer0_approval", "all", "NOT_RUN", "human", reason="Layer 0 master body is a candidate; adoption needs image generation, skeleton comparison and director approval")
    rep = make_report({"kind": "layer0-body-candidate", "characterId": character_id, "path": rel(out_dir, repo_root)}, ck.rows)
    counts = {}
    for v in VIEWS:
        for r in lev["views"][v]["landmarks"].values():
            counts[r["measurementStatus"]] = counts.get(r["measurementStatus"], 0) + 1
    lev["summary"] = {"measurementStatusCounts": counts, "commonKneeHeight": knee_y}
    (out_dir / "landmark_evidence.json").write_text(stable_dumps(lev), encoding="utf-8")
    (out_dir / "BASE_BODY_SPEC.candidate.json").write_text(stable_dumps(spec), encoding="utf-8")
    (out_dir / "production_brief.json").write_text(stable_dumps(brief), encoding="utf-8")
    (out_dir / "BODY_QA_REPORT.json").write_text(stable_dumps(rep), encoding="utf-8")
    return lev, rep
