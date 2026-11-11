"""Shared constants, deterministic JSON, coordinate normalisation and protection guards.

Coordinate functions mirror studio-core.js exactly (JS Math.round semantics) so data produced by the
browser studio and by this pipeline is interchangeable. Parity is tested against Node in tests/.
"""
import hashlib
import json
import math
from pathlib import Path

VERSION = "0.5"
VIEWS = ["front", "back", "left", "right"]
LANDMARK_KEYS = ["headTop", "neck", "shoulderLeft", "shoulderRight", "pelvis", "kneeLeft", "kneeRight", "footLeft", "footRight", "ground"]
RESULTS = ["PASS", "FAIL", "BLOCKED", "NOT_RUN"]
WRITABLE_STATUSES = {"UNAPPROVED_CANDIDATE", "UNAPPROVED_REFERENCE", "UNAPPROVED_INSTRUCTION", "BLOCKED"}
HUMAN_ONLY_STATUSES = {"CANONICAL_PROTECTED", "DIRECTOR_APPROVED"}

PIPELINE_DIR = Path(__file__).resolve().parent.parent
STUDIO_DIR = PIPELINE_DIR.parent
REPO_ROOT = STUDIO_DIR.parent.parent


class PolicyError(Exception):
    """Raised when an operation would adopt unapproved data or touch protected assets."""


# ---------- deterministic JSON (same output as studio-core stableStringify) ----------
def _norm(v):
    if isinstance(v, dict):
        return {k: _norm(v[k]) for k in sorted(v)}
    if isinstance(v, (list, tuple)):
        return [_norm(x) for x in v]
    if isinstance(v, float) and v.is_integer() and abs(v) < 1e15:
        return int(v)
    return v


def stable_dumps(obj):
    return json.dumps(_norm(obj), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


# ---------- JS-compatible rounding and coordinates ----------
def js_round(x, d=0):
    f = 10 ** d
    return math.floor(x * f + 0.5) / f if d else math.floor(x + 0.5)


def to_pixel(n, canvas):
    return [js_round(n[0] * canvas["width"]), js_round(n[1] * canvas["height"])]


def to_norm(px, canvas):
    return [js_round(min(1, max(0, px[0] / canvas["width"])), 5), js_round(min(1, max(0, px[1] / canvas["height"])), 5)]


def placement(img_w, img_h, canvas):
    """Uniform scale-to-fit, bottom-centred (studio-core placement)."""
    if img_w == canvas["width"] and img_h == canvas["height"]:
        return {"scale": 1, "x": 0, "y": 0, "w": img_w, "h": img_h, "exact": True}
    s = min(canvas["width"] / img_w, canvas["height"] / img_h)
    w, h = img_w * s, img_h * s
    return {"scale": js_round(s, 6), "x": js_round((canvas["width"] - w) / 2, 3), "y": js_round(canvas["height"] - h, 3),
            "w": js_round(w, 3), "h": js_round(h, 3), "exact": False}


def map_point(px, src_canvas, dst_canvas):
    """Map a pixel coordinate from one canvas preset to another through normalised space."""
    return to_pixel(to_norm(px, src_canvas), dst_canvas)


def anchor_record(px, canvas, definition=None):
    rec = {"px": [px[0], px[1]], "n": to_norm(px, canvas)}
    if definition:
        rec["definition"] = definition
    return rec


def alignment_offset(contact, anchor_px):
    """Integer translation (dx, dy) that moves a measured contact point onto the anchor.
    Internal alignment logic only: callers write the result to a NEW candidate file, never in place."""
    return [int(js_round(anchor_px[0] - contact[0])), int(js_round(anchor_px[1] - contact[1]))]


# ---------- presets / profiles ----------
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def preset(preset_id):
    for p in load_json(STUDIO_DIR / "profiles" / "presets.json")["presets"]:
        if p["id"] == preset_id:
            return p
    raise KeyError(f"unknown preset: {preset_id}")


def preset_canvas(p):
    return {"width": p["canvas"][0], "height": p["canvas"][1]}


# ---------- protection ----------
def protected_list():
    return load_json(PIPELINE_DIR / "protected_assets.json")


def is_protected(rel_path):
    rel = str(rel_path).replace("\\", "/")
    data = protected_list()
    if any(rel == e["path"] for e in data["files"]):
        return True
    return any(rel.startswith(d.rstrip("/") + "/") for d in data.get("protectedDirs", []))


GENERATED_SCHEMAS = {"cas/qa-report/0.5", "cas/manifest/0.5", "cas/production-brief/0.5", "cas/canon-measurement/0.5",
                     "cas/view-transforms/0.7", "cas/body-landmark-evidence/0.7", "cas/layer-outputs/0.7",
                     "cas/master-body/0.8", "cas/joint-changes/0.9", "cas/layer1-base/0.9"}
GENERATED_MD_MARK = "<!-- cas:generated -->"
OUTPUT_KEYS = {"guide", "guidePreview", "guides", "output", "outputs", "bodyGuides", "structureGuide", "overlay", "layer0Part", "articulatedGuide"}


def _output_paths(doc, under_output=False):
    """Every 'path' that appears below an output-type key (guide/guidePreview/guides/output/outputs/bodyGuides)."""
    found = set()
    if isinstance(doc, dict):
        for k, v in doc.items():
            inside = under_output or k in OUTPUT_KEYS
            if k == "path" and inside and isinstance(v, str):
                found.add(v)
            else:
                found |= _output_paths(v, inside)
    elif isinstance(doc, list):
        for x in doc:
            found |= _output_paths(x, under_output)
    return found


def pipeline_owned(path, repo_root=REPO_ROOT):
    """(owned, reason): is an existing file something this pipeline generated and may regenerate?
    Owned = a qa-report / manifest / production-brief JSON, a Markdown file carrying the generated marker,
    or a guide PNG listed by the production_brief.json next to it. Everything else is not owned."""
    p = Path(path)
    suf = p.suffix.lower()
    try:
        if suf == ".json":
            doc = load_json(p)
            sid = doc.get("schema")
            refs = doc.get("referenceBody") if isinstance(doc.get("referenceBody"), list) else []
            if sid is None and any(isinstance(r, dict) and r.get("status") == "UNAPPROVED_PARTIAL_MEASUREMENT" for r in refs):
                return (True, "canon-measurement candidate spec")
            if sid == "cas/modular-character/0.7" and str(doc.get("note", "")).startswith("GENERATED by cas.py"):
                return (True, "generated modular character")
            return (sid in GENERATED_SCHEMAS, f"schema {sid!r}")
        if suf == ".md":
            return (GENERATED_MD_MARK in p.read_text(encoding="utf-8"), "generated marker")
        if suf == ".png":
            # owned only if a pipeline-generated JSON in the same folder lists it as one of its OUTPUTS
            r = rel(p, repo_root)
            for j in sorted(p.parent.glob("*.json")):
                try:
                    doc = load_json(j)
                except (ValueError, OSError):
                    continue
                if isinstance(doc, dict) and doc.get("schema") in GENERATED_SCHEMAS and r in _output_paths(doc):
                    return (True, f"listed as output by {j.name}")
            return (False, "not listed as an output by a pipeline-generated JSON in the same folder")
    except (ValueError, OSError, AttributeError) as e:
        return (False, f"unreadable: {e}")
    return (False, f"{suf or 'no extension'} files are never treated as pipeline output")


def guard_write(path, repo_root=REPO_ROOT, overwrite=False):
    """Write gate, strictest first:
    1. protected (canonical) path -> always refused, with or without --overwrite;
    2. new file -> allowed;
    3. existing file -> refused unless overwrite=True AND it is not under assets/ (candidate deliveries are
       never replaced) AND the pipeline generated it (pipeline_owned)."""
    p = Path(path).resolve()
    try:
        r = p.relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        r = None
    if r is not None and is_protected(r):
        raise PolicyError(f"refusing to write protected path: {r}")
    if not p.exists():
        return p
    if not overwrite:
        raise PolicyError(f"refusing to overwrite existing file (use --overwrite; only pipeline-generated files can be replaced): {r or p}")
    if r is not None and r.startswith("assets/"):
        raise PolicyError(f"refusing to overwrite a file under assets/ (candidate deliveries are never replaced): {r}")
    owned, why = pipeline_owned(p, repo_root)
    if not owned:
        raise PolicyError(f"refusing to overwrite a file the pipeline did not generate ({why}): {r or p}")
    return p


def assert_writable_status(status):
    if status in HUMAN_ONLY_STATUSES:
        raise PolicyError(f"status {status} can only be set by a director record, not by pipeline tools")
    if status not in WRITABLE_STATUSES:
        raise PolicyError(f"unknown status {status}")


def rel(path, root=REPO_ROOT):
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()
