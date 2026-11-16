#!/usr/bin/env python3
"""Evidence-only shortlist of CC0 female basemesh objects; never auto-approve."""
import argparse, json, pathlib, re, sys

def shortlist(inventory):
    if inventory.get("status") != "PASS_GEOMETRY_INVENTORY_ONLY" or not inventory.get("source_unchanged"):
        raise ValueError("BLOCKED: geometry inventory not verified")
    rows = inventory.get("geometry", [])
    if not rows:
        raise ValueError("BLOCKED: no mesh objects")
    results = []
    for row in rows:
        name = (row.get("name", "") + " " + row.get("mesh", "")).lower()
        words = set(re.findall(r"[a-z]+", name))
        # Only source names are evidence; scores are discovery hints, not suitability judgments.
        female = bool(words & {"female", "woman", "fem"})
        body = bool(words & {"body", "base", "basemesh", "human", "stylized", "realistic"})
        exclude = bool(words & {"male", "man", "head", "eye", "teeth", "tongue", "hair", "hand", "foot"})
        if not female or not body or exclude:
            continue
        verts, faces = row.get("vertices", 0), row.get("faces", 0)
        if not isinstance(verts, int) or not isinstance(faces, int) or verts < 1 or faces < 1:
            continue
        results.append({
            "object_name": row["name"], "mesh_name": row["mesh"],
            "vertices": verts, "faces": faces,
            "quads": row.get("quads"), "triangles": row.get("triangles"),
            "uv_layers": row.get("uv_layers"), "materials": row.get("materials"),
            "bounds_xyz": row.get("bounds_xyz"),
            "modifiers": row.get("modifiers", []),
            "source_name_match": "female+body keyword",
            "art_qa": "NOT_RUN", "rig_qa": "NOT_RUN", "approved": False,
        })
    return {
        "status": "CANDIDATES_FOUND_REVIEW_REQUIRED" if results else "BLOCKED_NO_NAMED_FEMALE_BODY",
        "source_sha256": inventory["source_sha256"],
        "inventory_mesh_count": len(rows),
        "candidate_count": len(results),
        "candidates": sorted(results, key=lambda r: (r["object_name"].lower(), r["mesh_name"].lower())),
        "selection_basis": "object/mesh names only; no inferred body proportions or topology quality",
        "canonical_alignment": "BLOCKED",
        "art_qa": "NOT_RUN", "rig_qa": "NOT_RUN", "game_qa": "NOT_RUN",
        "production_approval": False,
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("inventory")
    p.add_argument("--output",required=True)
    args=p.parse_args()
    src=pathlib.Path(args.inventory)
    out=pathlib.Path(args.output)
    try:
        report=shortlist(json.loads(src.read_text()))
    except Exception as exc:
        report={"status":"BLOCKED", "reason":str(exc), "production_approval":False}
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"status":report["status"],"candidate_count":report.get("candidate_count",0)}))
    return 0 if report["status"]=="CANDIDATES_FOUND_REVIEW_REQUIRED" else 2

if __name__=="__main__":
    sys.exit(main())
