#!/usr/bin/env python3
"""Validate public Studio blueprint inventory without requiring network access."""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "docs/production/region_master/PRODUCTION_STUDIO_BLUEPRINT_CANDIDATES_V01.json"
ALLOWED = {".svg", ".md", ".json"}
def main():
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert m["schema"] == "two.production-studio.blueprint-candidates.v1"
    assert m["status"] == "STAGING_ONLY_NOT_DEPLOYED"
    assert len(m["entries"]) == len({x["id"] for x in m["entries"]})
    results = []
    for entry in m["entries"]:
        rel = pathlib.PurePosixPath(entry["path"])
        assert not rel.is_absolute() and ".." not in rel.parts
        assert rel.parts[:3] == ("docs", "production", "region_master")
        assert rel.suffix in ALLOWED
        assert entry["privacy"] == "PUBLIC_SAFE"
        assert entry["adoption"] == "DESIGN_CANDIDATE"
        assert entry["qa"] == "G1_BLOCKED"
        p = ROOT.joinpath(*rel.parts)
        if not p.is_file():
            raise FileNotFoundError("Missing staged source: " + str(rel))
        payload = p.read_bytes()
        if rel.suffix == ".svg":
            text = payload.decode("utf-8")
            assert "<svg" in text and "</svg>" in text
            assert not re.search(r"<script\\b|onload\\s*=|<foreignObject\\b", text, re.I)
        results.append({"id":entry["id"], "path":str(rel), "bytes":len(payload),
                        "sha256":hashlib.sha256(payload).hexdigest(), "qa":"SOURCE_INTEGRITY_PASS"})
    print(json.dumps({"status":"PASS_SOURCE_INTEGRITY_ONLY","G1":"BLOCKED","G2":"NOT_RUN",
                      "G3":"NOT_RUN","G4":"NOT_RUN","entries":results},ensure_ascii=False,indent=2))
if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        print("FAIL:",type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(1)
