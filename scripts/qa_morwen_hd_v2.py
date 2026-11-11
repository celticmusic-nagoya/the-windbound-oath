#!/usr/bin/env python3
"""MORWEN-HD-CANONICAL-V2 technical QA. Read-only: never modifies images.

Checks: delivery SHA-256, registry SHA-256, RGBA/size, derivative reproducibility,
display canvas/baseline, superseded exclusion, production non-connection.
Exit 1 on any FAIL. Prints a JSON report.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "data" / "morwen-hd-canonical-v2.json"
BASE = ROOT / "assets" / "official" / "characters" / "morwen" / "hd-v2"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    from PIL import Image
    import numpy as np

    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    reg = json.loads(REG.read_text(encoding="utf-8"))
    delivery = json.loads((BASE / "DELIVERY_MANIFEST_V2.json").read_text(encoding="utf-8"))
    check("registry schema", reg.get("schema") == "windbound.morwen-hd-canonical/2")
    check("delivery manifest sha", sha(BASE / "DELIVERY_MANIFEST_V2.json") == reg["delivery_manifest"]["sha256"])

    # 1. delivery manifest SHA-256 (9 originals + 4 derivatives)
    by_sha = {a["sha256"]: a for a in reg["assets"].values()}
    for rel, a in delivery["assets"].items():
        r = by_sha.get(a["sha256"])
        ok = r is not None and (ROOT / r["path"]).is_file() and sha(ROOT / r["path"]) == a["sha256"]
        check(f"delivery {rel}", ok, r["path"] if r else "not in registry")

    # 2. registry entries
    superseded = {s.get("sha256") for s in reg.get("superseded", []) if s.get("sha256")}
    for key, a in reg["assets"].items():
        p = ROOT / a["path"]
        if not p.is_file():
            check(f"exists {key}", False, a["path"])
            continue
        check(f"sha {key}", sha(p) == a["sha256"])
        check(f"not superseded {key}", a["sha256"] not in superseded)
        with Image.open(p) as im:
            check(f"rgba+size {key}", im.mode == "RGBA" and list(im.size) == a["size"], f"{im.mode} {im.size}")

    # 3. derivatives reproducible from byte-preserved originals; canvas + baseline
    W, H = reg["display"]["canvas"]
    gx, gy = reg["display"]["ground_anchor"]
    for d in ("front", "left", "right", "back"):
        a = reg["assets"][f"display.pixel.{d}"]
        src = Image.open(ROOT / reg["assets"][a["source"]]["path"]).convert("RGBA")
        x0, y0, x1, y1 = a["source_bbox"]
        c = src.crop((x0, y0, x1, y1))
        if a["scale"] != 1.0:
            c = c.resize((round(c.width * a["scale"]), round(c.height * a["scale"])), Image.NEAREST)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(c, tuple(a["paste_xy"]))
        got = np.asarray(Image.open(ROOT / a["path"]).convert("RGBA"))
        check(f"reproducible {d}", np.array_equal(got, np.asarray(canvas)))
        alpha = got[..., 3]
        rows = np.nonzero(alpha.max(1) > 0)[0]
        check(f"baseline {d}", int(rows.max()) == gy - 1, f"lowest alpha row {int(rows.max())}")
        m = a["measured"]
        boot = alpha[gy - 80:gy, :] > 127
        cols = np.nonzero(boot[:, m["boot_x"][0]:m["boot_x"][1] + 1].any(0))[0]
        check(f"boot measure {d}", len(cols) > 0 and abs((m["boot_x"][0] + m["boot_x"][1]) / 2 - m["foot_center_x"]) < 0.01)
        check(f"anchor dx {d}", abs(gx - m["foot_center_x"] - m["anchor_dx"]) < 0.01, f"dx {m['anchor_dx']}")

    # 4. production not connected; superseded not referenced by new runtime files
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    check("index.html not connected", "hd-v2" not in index and "morwen-hd-canonical" not in index)
    for f in ("js/field/morwen-hd-canonical.js", "dev/morwen-hd-v2-preview/preview.js", "dev/morwen-hd-v2-preview/index.html"):
        t = (ROOT / f).read_text(encoding="utf-8")
        check(f"no superseded ref {f}", "35a0820989" not in t and "d858c428" not in t)

    fails = [c for c in checks if c["result"] == "FAIL"]
    report = {"task": reg["task"], "result": "PASS" if not fails else "FAIL", "checks": len(checks),
              "fails": fails, "warnings": reg.get("qa_warnings", []),
              "visual_director_review": "NOT_RUN", "android_physical_device": "NOT_RUN"}
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
