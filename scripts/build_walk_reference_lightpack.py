#!/usr/bin/env python3
"""Build a small, provenance-preserving WALK reference pack. No production assets modified."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import hashlib, io, json, zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dist" / "player-walk-official-reference-lightpack.zip"
OUT.parent.mkdir(exist_ok=True)
LIMIT = 360
KEYWORDS = ("aidan", "fiona")
VALID = {".png", ".webp"}
files = []
for root in (ROOT / "img" / "field", ROOT / "docs" / "art" / "reference"):
    if root.exists():
        for path in root.rglob("*"):
            if path.suffix.lower() not in VALID or not any(k in str(path).lower() for k in KEYWORDS):
                continue
            s = str(path.relative_to(ROOT)).lower()
            if any(x in s for x in ("walk", "idle", "front", "back", "side", "diagonal")):
                files.append(path)
files = sorted(set(files))
if not files:
    raise SystemExit("ERROR: no official reference sprites found; refusing empty artifact")
manifest = []
thumbs = []
with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=8) as z:
    for path in files:
        rel = str(path.relative_to(ROOT))
        try:
            with Image.open(path) as src:
                im = src.convert("RGBA")
                im.thumbnail((LIMIT, LIMIT), Image.Resampling.LANCZOS)
                canvas = Image.new("RGBA", (LIMIT, LIMIT), (0, 0, 0, 0))
                canvas.alpha_composite(im, ((LIMIT-im.width)//2, (LIMIT-im.height)//2))
                data = io.BytesIO()
                canvas.save(data, format="PNG", optimize=True)
                target = "previews/" + rel.rsplit(".", 1)[0] + ".png"
                z.writestr(target, data.getvalue())
                manifest.append(dict(source=rel, preview=target, sha256=hashlib.sha256(path.read_bytes()).hexdigest(), original_size=list(src.size), preview_canvas=[LIMIT,LIMIT], original_mode=src.mode))
                if len(thumbs) < 150:
                    small = canvas.copy()
                    small.thumbnail((160,160))
                    thumbs.append((rel, small))
        except Exception as e:
            manifest.append(dict(source=rel, error=str(e)))
    # Index page provides source mapping and avoids confusing previews with production frames.
    z.writestr("README.txt", "THE WINDBOUND OATH - OFFICIAL SPRITE REFERENCE PREVIEWS\nGenerated from this PR checkout. Previews are resized and must NOT replace production PNGs.\nSee manifest.json for original paths, sizes, SHA256. This archive contains no candidate redraws.\n")
    z.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    # Preserve a few key original PNGs for pixel-exact identity reference, size cap.
    chosen = [m for m in manifest if "error" not in m and any(x in m["source"].lower() for x in ("aidan_walk_down_01", "aidan_walk_up_01", "fiona_walk_down_01", "fiona_side_left_01", "fiona_side_right_01", "fiona_idle_down"))]
    for m in chosen:
        path = ROOT / m["source"]
        if path.stat().st_size <= 2_000_000:
            z.write(path, "selected-originals/" + m["source"])
print(f"Reference files: {len(files)}; selected originals: {len(chosen)}; ZIP: {OUT.stat().st_size / 1048576:.1f} MiB")
