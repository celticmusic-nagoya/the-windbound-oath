#!/usr/bin/env python3
"""Build Morwen real-canon v3 candidates from the checked-in v2 files.

No edits to official originals or v2. Requires Pillow. Trigger v3 CI once.
"""
from pathlib import Path
from PIL import Image
import hashlib, json
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets/candidates/morwen/real-canon-v2"
DST = ROOT / "assets/candidates/morwen/real-canon-v3"
MOVES = {
    "front": (22, -18, "16c71079231b1a0f7b960a35d1e5cb1e3abfcd092ad22729924ac74c0bb0bca4"),
    "right": (-96, -18, "55c5ce7ffaf5380eae56a79bae6fc3ddc50c5f7907a236c59bd4850c443823e1"),
    "back": (36, -18, "eb39bcbe0155f0b329e42cec1dc159f24d4758e362ad7a5130c14134020cb02c"),
    "left": (79, -18, "a4339f30cc7425521672b720aa226c510ec153c4f669b81deb48466a2dacb7e4"),
}
if DST.exists() and any(DST.iterdir()):
    raise SystemExit("Refusing to overwrite existing v3 candidate files")
DST.mkdir(parents=True, exist_ok=True)
manifest = {"version":"v3", "status":"CANDIDATE_NOT_PRODUCTION",
            "anchor_target":[600,1540], "files":[],
            "limitations":["Boot-center coordinates inherited from prior self-QA; independent anatomical contact QA NOT_RUN",
                           "Android/in-game scale QA NOT_RUN"]}
for direction, (dx,dy,sha) in MOVES.items():
    src = SRC / f"morwen_real_{direction}_normalized_v2.png"
    raw = src.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == sha, direction
    with Image.open(src) as opened:
        assert opened.size == (1200,1600) and opened.mode == "RGBA"
        image = opened.copy()
    bbox = image.getchannel("A").getbbox()
    assert bbox is not None
    assert 0 <= bbox[0]+dx and bbox[2]+dx <= 1200
    assert 0 <= bbox[1]+dy and bbox[3]+dy <= 1600
    result = Image.new("RGBA",image.size,(0,0,0,0))
    result.paste(image,(dx,dy))
    assert result.crop((bbox[0]+dx,bbox[1]+dy,bbox[2]+dx,bbox[3]+dy)).tobytes() == image.crop(bbox).tobytes()
    alpha = result.getchannel("A")
    assert alpha.getbbox() is not None
    # Alpha >=128 bottom contact line must match y=1540.
    assert alpha.point(lambda v: 255 if v >= 128 else 0).getbbox()[3] - 1 == 1540
    dst = DST / f"morwen_real_{direction}_anchor_v3.png"
    result.save(dst,optimize=True)
    manifest["files"].append({"direction":direction,"filename":dst.name,
      "sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"source_v2_sha256":sha,
      "dx":dx,"dy":dy,"canvas":[1200,1600],"mode":"RGBA","clipping":False})
(DST/"MANIFEST_V3.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(manifest,ensure_ascii=False,indent=2))
