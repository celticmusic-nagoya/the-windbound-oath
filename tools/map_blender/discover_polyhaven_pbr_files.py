"""Read-only Poly Haven file manifest discovery for approved-to-investigate candidates.

No texture downloads, no Blender changes, no canon approval.
"""
import json
import pathlib
import sys
import urllib.request
import urllib.error

source = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
target.parent.mkdir(parents=True, exist_ok=True)
items = json.loads(source.read_text(encoding="utf-8"))["shortlist"]
rows = []
for item in items:
    if item["provider"] != "polyhaven":
        continue
    asset_id = item["asset_id"]
    row = {"asset_id": asset_id, "role": item["role"], "status": "UNVERIFIED", "maps": []}
    try:
        url = "https://api.polyhaven.com/files/" + asset_id
        request = urllib.request.Request(url, headers={"User-Agent": "TWO-PBR-Intake/1.0"})
        with urllib.request.urlopen(request, timeout=30) as response:
            manifest = json.load(response)
        for channel in ("Diffuse", "Normal", "Rough", "Displacement", "AO", "Metalness"):
            options = manifest.get(channel, {})
            if not isinstance(options, dict):
                continue
            for resolution in ("1k", "2k"):
                variants = options.get(resolution, {})
                if not isinstance(variants, dict):
                    continue
                for fmt in ("jpg", "png", "exr"):
                    entry = variants.get(fmt)
                    if isinstance(entry, dict) and entry.get("url"):
                        row["maps"].append({
                            "channel": channel,
                            "resolution": resolution,
                            "format": fmt,
                            "url": entry["url"],
                            "size": entry.get("size"),
                            "md5": entry.get("md5")
                        })
        row["status"] = "FILES_FOUND" if row["maps"] else "NO_SUPPORTED_MAPS"
    except (urllib.error.URLError, ValueError, TimeoutError) as exc:
        row["error"] = str(exc)
    rows.append(row)
report = {"status": "CANDIDATE_METADATA_ONLY", "approval": "NONE",
          "downloads": "NOT_PERFORMED", "assets": rows}
target.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"assets": [(x["asset_id"], x["status"], len(x["maps"])) for x in rows]}, indent=2))
if any(x["status"] != "FILES_FOUND" for x in rows):
    sys.exit(1)
