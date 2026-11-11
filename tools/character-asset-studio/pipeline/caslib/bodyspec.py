"""BASE_BODY_SPEC v1.0 (pixel landmarks, legacy) -> v2.0 (normalised) conversion.

Mirrors studio-core.js parseSpec (v1.0 branch) + buildSpec exactly; parity is tested against Node.
The source file is never modified: the result is written to a new file. Converted landmarks are
confidence 'provisional', source 'imported_spec'; status is 'candidate_not_canonical' (never approved).
"""
from .core import LANDMARK_KEYS, VIEWS, preset, preset_canvas, to_norm, to_pixel

NOTES = "Landmarks are provisional unless confidence/source say otherwise. No anatomy is inferred automatically."
COORDINATE_SPACE = "normalized canvas (0..1, origin top-left, y down); px = n * canvas size"


def upgrade_v1(doc, preset_id=None):
    if doc.get("schemaVersion") != "1.0":
        raise ValueError("not a BASE_BODY_SPEC v1.0 document")
    cw, ch = (doc.get("canvas") or {}).get("width"), (doc.get("canvas") or {}).get("height")
    if not (isinstance(cw, (int, float)) and isinstance(ch, (int, float)) and cw > 0 and ch > 0):
        raise ValueError("v1.0: canvas.width/height invalid")
    src_canvas = {"width": cw, "height": ch}
    p = preset(preset_id or doc.get("presetId"))
    canvas = preset_canvas(p)
    lm = {}
    for v in VIEWS:
        lm[v] = {}
        for k in LANDMARK_KEYS:
            pt = (doc.get("landmarks", {}).get(v) or {}).get(k)
            if not (isinstance(pt, list) and len(pt) == 2 and all(isinstance(x, (int, float)) for x in pt)
                    and 0 <= pt[0] <= cw and 0 <= pt[1] <= ch):
                raise ValueError(f"{v}.{k}: invalid coordinate")
            n = to_norm(pt, src_canvas)
            lm[v][k] = {"n": n, "px": to_pixel(n, canvas), "confidence": "provisional", "source": "imported_spec"}
    return {
        "schemaVersion": "2.0", "status": "candidate_not_canonical", "characterId": doc.get("characterId") or "candidate",
        "presetId": p["id"], "canvas": canvas, "groundNormalized": list(p["ground"]),
        "worldScale": {"pixelsPerUnit": p.get("pixelsPerUnit")}, "coordinateSpace": COORDINATE_SPACE,
        "views": list(VIEWS), "landmarks": lm, "referenceBody": None, "assets": [], "notes": NOTES,
    }
