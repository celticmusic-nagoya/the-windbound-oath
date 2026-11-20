"""Acquire candidate PBR maps from Poly Haven API; never overwrite inputs."""
import hashlib
import json
import pathlib
import urllib.request
import argparse

ASSETS = {"sparse_grass": "Amal Kumar", "stony_dirt_path": "eye-candy.xyz"}
CHANNELS = {"diff": "basecolor", "nor_gl": "normal", "rough": "roughness"}

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "TWO-material-intake/1.0"}), timeout=45) as response:
        return response.read(32 * 1024 * 1024 + 1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=pathlib.Path)
    args = parser.parse_args()
    for asset, author in ASSETS.items():
        dst = args.output / asset
        dst.mkdir(parents=True, exist_ok=True)
        files = json.loads(get("https://api.polyhaven.com/files/" + asset))
        manifest = {"asset_status": "candidate", "source_url": "https://polyhaven.com/a/" + asset,
                    "author": author, "license": "CC0", "license_evidence_url": "https://polyhaven.com/a/" + asset,
                    "capture_location_claim": "unknown", "textures": {}}
        for source, role in CHANNELS.items():
            entry = files[source]["1k"]["jpg"]
            data = get(entry["url"])
            if len(data) != entry["size"] or hashlib.md5(data).hexdigest() != entry["md5"]:
                raise ValueError("Provider checksum mismatch: " + asset + "/" + source)
            path = dst / (role + ".jpg")
            if path.exists() and path.read_bytes() != data:
                raise FileExistsError(path)
            path.write_bytes(data)
            manifest["textures"][role] = {"path": path.name, "sha256": hashlib.sha256(data).hexdigest(),
                "color_space": "sRGB" if role == "basecolor" else "Non-Color", "download_url": entry["url"]}
        output = dst / "manifest.json"
        encoded = json.dumps(manifest, indent=2) + "\n"
        if output.exists() and output.read_text() != encoded:
            raise FileExistsError(output)
        output.write_text(encoded)
if __name__ == "__main__":
    main()
