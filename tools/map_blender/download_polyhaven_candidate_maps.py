"""Download only chosen 1K Poly Haven PBR maps into an ephemeral candidate folder.

Uses provider file manifest, verifies HTTPS host, hashes bytes, never writes into source assets.
"""
import hashlib
import json
import pathlib
import sys
import urllib.parse
import urllib.request

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
out = pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
allowed = {"Diffuse", "Normal", "Rough"}
records = []
for asset in manifest["assets"]:
    if asset["status"] != "FILES_FOUND":
        raise SystemExit("Unverified source: " + asset["asset_id"])
    for channel in sorted(allowed):
        options = [m for m in asset["maps"] if m["channel"] == channel
                   and m["resolution"] == "1k" and m["format"] in ("jpg", "png")
                   and (channel != "Normal" or m.get("provider_channel") != "nor_dx")]
        if not options:
            raise SystemExit("Missing required 1K map: " + asset["asset_id"] + "/" + channel)
        entry = sorted(options, key=lambda m: (m["format"] != "jpg", m["url"]))[0]
        url = entry["url"]
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "https" or parsed.hostname not in ("dl.polyhaven.org", "polyhaven.com"):
            raise SystemExit("Untrusted download host: " + parsed.hostname.__str__())
        if not asset["asset_id"].replace("_", "").replace("-", "").isalnum():
            raise SystemExit("Unsafe asset ID")
        filename = asset["asset_id"] + "_" + channel.lower() + "." + entry["format"]
        target = out / filename
        req = urllib.request.Request(url, headers={"User-Agent": "TWO-Candidate-PBR/1.0"})
        digest = hashlib.sha256()
        total = 0
        with urllib.request.urlopen(req, timeout=90) as response, target.open("wb") as dest:
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > 12 * 1024 * 1024:
                    target.unlink(missing_ok=True)
                    raise SystemExit("Texture exceeds 12MiB: " + filename)
                digest.update(block)
                dest.write(block)
        if total == 0:
            target.unlink(missing_ok=True)
            raise SystemExit("Empty texture: " + filename)
        records.append({"asset_id": asset["asset_id"], "role": asset["role"],
                        "channel": channel, "path": filename, "source_url": url,
                        "bytes": total, "sha256": digest.hexdigest()})
(out / "download-manifest.json").write_text(
    json.dumps({"status": "CANDIDATE_NOT_CANON", "license_review": "PENDING",
                "textures": records}, indent=2) + "\n", encoding="utf-8")
print("Downloaded candidate maps:", len(records))
