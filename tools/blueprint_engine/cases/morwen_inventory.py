"""Morwen design-value inventory (face / hair / body): evidence class for every value.

Read-only classification of the values that exist today. Nothing is promoted:
manual points stay ESTIMATED, authoring guides stay PROVISIONAL_DESIGN, occluded
or depth/thickness values stay UNDETERMINED, pixel-exact silhouette data is
OFFICIAL_SOURCE_MEASURED, VRoid/M00 values are NATIVE_MEASURED only on the
comparator (not the current #427 candidate). Definition-ambiguous eye corners are
HOLD and are not turned into official targets here.
Wardrobe/equipment are listed as out of scope for this inventory.
"""
import argparse
from collections import Counter
import json
from pathlib import Path

from ..evidence import (ESTIMATED, NATIVE_MEASURED, OFFICIAL_SOURCE_MEASURED, PROVISIONAL_DESIGN,
                        UNDETERMINED)
from ..export import write_json
from ..sources import file_sha256

FACE = ("eye", "nose", "mouth", "chin", "ear", "jaw", "brow", "far_eye", "far_ear")
HAIR = ("crown", "fringe", "hair", "nape", "hairline")


def module_of(name):
    n = name.lower()
    if any(n.startswith(h) or h in n for h in HAIR):
        return "hair"
    if any(n.startswith(f) or f in n for f in FACE):
        return "face"
    if "strap" in n or "buckle" in n or "clasp" in n:
        return "wardrobe"
    return "body"


def build(precision_json, landmarks_json, silhouette_json, owner_targets_json, face_out):
    pb = json.loads(Path(precision_json).read_text())
    l0 = json.loads(Path(landmarks_json).read_text())
    sil = json.loads(Path(silhouette_json).read_text())
    own = json.loads(Path(owner_targets_json).read_text())
    research = json.loads((Path(face_out) / "official_remeasure_research.json").read_text())
    face_case = json.loads((Path(face_out) / "case_summary.json").read_text())
    items = []

    def add(item_id, module, evidence, source, value=None, uncertainty=None, state=None, note=None):
        items.append(dict(id=item_id, module=module, evidence=evidence, source=source,
                          value=value, uncertainty=uncertainty, state=state, note=note))

    for view, rec in l0["views"].items():
        for name, p in rec["landmarks"].items():
            vis = p.get("visibility")
            cls = UNDETERMINED if vis == "occluded" else ESTIMATED
            add(f"l0.{view}.{name}", module_of(name), cls, "layer0_landmarks_v1",
                p.get("xy_px"), p.get("uncertainty_px"),
                note=f"visibility {vis}" + ("; 2D estimate of a hidden/soft landmark"
                                            if vis in ("estimated", "partial") else ""))
    for view, pts in pb["face"].items():
        for name, xy in pts.items():
            if name != "uncertainty_px":
                add(f"pb2.face.{view}.{name}", "face", ESTIMATED, "precision_blueprint_v2.face",
                    xy, pts.get("uncertainty_px"))
    for name, xy in pb["face_front_review"]["points"].items():
        add(f"pb2.face_front_review.{name}", "face", ESTIMATED, "face_front_review", xy, 3)
    for key, value in pb["metrics"].items():
        add(f"pb2.metrics.{key}", "hair" if "hair" in key else "body" if "shoulder" in key
            else "face", ESTIMATED, "precision_blueprint_v2.metrics", value,
            note="2D projected ratio; not calibrated 3D")
    for side in ("front_groups", "right_groups"):
        for group in pb["hair"].get(side, []):
            add(f"pb2.hair.{side}.{group['id']}", "hair", PROVISIONAL_DESIGN, "hair guides",
                group.get("guide_px"), pb["hair"]["uncertainty_px"],
                note="authoring hypothesis, not strand count / 3D curve / exact boundary")
    add("pb2.profile_hair.depth_and_thickness", "hair", UNDETERMINED, "profile_hair_review",
        note=pb["profile_hair_review"]["depth_and_thickness"])
    add("hair.strand_3d_curves", "hair", UNDETERMINED, "policy", note="not derivable from 2D")
    for view, rec in sil["source_views"].items():
        add(f"sil.{view}.alpha_bbox", "body", OFFICIAL_SOURCE_MEASURED,
            "reference_silhouette_landmarks", rec["alpha_bbox_xyxy"], 0,
            state="PASS (re-measured, #485)")
        for row in rec["silhouette_scanlines"]:
            add(f"sil.{view}.scan.{row['y']}", "body", OFFICIAL_SOURCE_MEASURED,
                "reference_silhouette_landmarks", [row["left_x"], row["right_x"]], 0,
                state="PASS (re-measured, #485)", note="alpha section, not anatomy")
    add("body.joints_and_hidden_depth", "body", UNDETERMINED, "precision_blueprint_v2.body",
        note=pb["body"]["status"])
    head = research["head"]
    add("research.head_height", "face", OFFICIAL_SOURCE_MEASURED, "official_face (research)",
        head["algorithmic_px"], head["algorithmic_u_px"], note="crown/chin algorithmic")
    for key, row in research["metrics"].items():
        state = row["m00_state_if_adopted"]
        cls = OFFICIAL_SOURCE_MEASURED
        hold = None
        if state == "DEFINITION_AMBIGUOUS":
            hold = "HOLD (eye corner definition ambiguous; owner decision)"
        add(f"research.{key}", "face", cls, "official_face (research)", row["algorithmic_px"],
            row["algorithmic_u_px"], state=hold or "RESEARCH_ONLY", note=row["definition"])
    for key, row in face_case["comparability"].items():
        add(f"m00.{key}", "face", NATIVE_MEASURED if row["native_ratio"] is not None else UNDETERMINED,
            "M00 comparator (not current candidate)", row["native_ratio"], None,
            state=row["state"] if row["status"] == "COMPARABLE" else "DEFINITION_MISMATCH")
    for t in own["targets"]:
        module = t["module"]
        if module in ("wardrobe", "equipment"):
            add(t["id"], module, ESTIMATED, "#427 blueprint-targets", t["target"], t["tolerance"],
                state="OUT_OF_SCOPE (wardrobe/equipment)")
            continue
        cls = {"face_front_review": ESTIMATED, "body.scanlines": OFFICIAL_SOURCE_MEASURED}.get(
            t["source"], PROVISIONAL_DESIGN)
        state = f"{t['status']} / operation {t['operation_status']}"
        if t["id"] in ("face.front.eye_width_right", "face.front.inner_eye_gap"):
            state = "HOLD (eye corner definition ambiguous) / " + state
        if module == "body":
            state += " / tolerance basis UNDETERMINED (#427 gap 'body tolerance')"
        add(t["id"], module, cls, "#427 blueprint-targets", t["target"], t["tolerance"], state=state)
    return items


def run(precision_json, landmarks_json, silhouette_json, owner_targets_json, face_out, out):
    items = build(precision_json, landmarks_json, silhouette_json, owner_targets_json, face_out)
    counts = Counter((i["module"], i["evidence"]) for i in items)
    holds = [i for i in items if i["state"] and i["state"].startswith("HOLD")]
    record = dict(
        case="morwen.design-value-inventory", scope="face/hair/body (wardrobe/equipment listed only)",
        sources={n: file_sha256(p) for n, p in (
            ("precision_blueprint_v2", precision_json), ("layer0_landmarks_v1", landmarks_json),
            ("reference_silhouette_landmarks", silhouette_json),
            ("owner_blueprint_targets_427", owner_targets_json))},
        counts={f"{m}/{e}": n for (m, e), n in sorted(counts.items())},
        hold=[dict(id=i["id"], reason=i["state"]) for i in holds],
        rules=["no value promoted to a stronger class", "2D values never become 3D",
               "eye-corner ambiguous items stay HOLD; no official target is set here",
               "native values exist only for the M00 comparator; current #427 candidate NOT_RUN"],
        items=items)
    write_json(Path(out) / "morwen_inventory.json", record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("precision", "landmarks", "silhouette", "owner-targets", "face-out", "out"):
        parser.add_argument("--" + name, required=True)
    a = parser.parse_args()
    r = run(a.precision, a.landmarks, a.silhouette, a.owner_targets, a.face_out, a.out)
    print(json.dumps(dict(counts=r["counts"], hold=r["hold"]), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
