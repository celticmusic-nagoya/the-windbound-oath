"""Fail closed when a purported new Morwen face/hair candidate repeats sculpt02's failed method.
Uses the existing production geometry-difference manifest; no Blender or source mutation.
Exit 0: measurable topology and hair-method changes evidenced. Exit 1: insufficient evidence.
"""
import json
import sys
from pathlib import Path

def evaluate(record):
    errors = []
    if record.get("face_topology_changed") is not True:
        errors.append("Face topology unchanged: sculpt-only tweaks cannot be counted as a retopology method switch")
    hair = [h for h in record.get("hair", []) if h.get("rendered") is True]
    changed = [h for h in hair if h.get("GUI_changed_vertices", 0) > 0]
    if not hair:
        errors.append("No visible hair meshes documented")
    elif len(changed) < len(hair):
        errors.append(f"Only {len(changed)}/{len(hair)} visible hair meshes show GUI edits; rooted strand redesign unproven")
    if not record.get("hair_root_structure_changed", False):
        errors.append("No explicit evidence of hair-root structural redesign")
    return errors

def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs/qa/morwen-sculpt02/geometry_difference.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    errors = evaluate(data)
    print(json.dumps({"source": str(source), "method_switch_gate": "FAIL" if errors else "PASS", "reasons": errors}, ensure_ascii=False, indent=2))
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())
