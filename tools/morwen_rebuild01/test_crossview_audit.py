#!/usr/bin/env python3
"""Regression checks for mirrored profile anatomy; no image or 3D claims."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "tools/morwen_rebuild01/audit_landmark_crossviews.py"

def main():
    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp) / "crossview.json"
        subprocess.run([sys.executable, str(SCRIPT), "--output", str(output)], check=True)
        data = json.loads(output.read_text(encoding="utf-8"))
        rows = data["observations"]
        assert len(rows) == 18, len(rows)
        profiles = [r for r in rows if r["pair"] == ["right", "left"]]
        assert len(profiles) == 9
        for feature in ("knee_R", "ankle_R", "sole_R"):
            row = next(r for r in profiles if r["feature"] == feature)
            assert row["counterpart"] == feature[:-2] + "_L", row
            assert row["status"] != "MISSING", row
        for feature in ("knee_L", "ankle_L", "sole_L"):
            row = next(r for r in profiles if r["feature"] == feature)
            assert row["status"] == "NOT_APPLICABLE_PROFILE_SIDE", row
        assert not any(r["status"] == "MISSING" for r in rows), [r for r in rows if r["status"] == "MISSING"]
        assert data["projection_calibrated"] is False
        assert data["physical_dimensions"] == "NOT_ESTABLISHED"
        print("MORWEN_CROSSVIEW_REGRESSION_PASS", len(rows))

if __name__ == "__main__":
    main()
