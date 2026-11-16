"""In-game-scale previews for LIND-HOME-01 (offline downsample; NOT an in-engine/Android check).

    python3 tools/map_blender/lind/home/game_scale.py <game_27deg.png> <out_dir>

Crops the transparent 27-degree ortho render to its alpha bbox, scales the house to 96 px and 48 px
wide (Lanczos), composites each on a flat grass tone, and writes nearest-neighbour enlargements for review.
"""
import hashlib
import json
import os
import sys

from PIL import Image


def main(src, out):
    os.makedirs(out, exist_ok=True)
    im = Image.open(src).convert("RGBA")
    bbox = im.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox()
    crop = im.crop(bbox)
    rep = {"source": os.path.basename(src), "alpha_bbox": bbox, "outputs": {}}
    for w, up in ((96, 4), (48, 8)):
        h = round(crop.height * w / crop.width)
        sm = crop.resize((w, h), Image.LANCZOS)
        bg = Image.new("RGBA", (w + 16, h + 12), (92, 118, 60, 255))
        bg.alpha_composite(sm, (8, 8))
        files = {
            "game_%dpx.png" % w: sm,
            "game_%dpx_on_ground.png" % w: bg,
            "game_%dpx_on_ground_x%d_nearest.png" % (w, up): bg.resize((bg.width * up, bg.height * up), Image.NEAREST),
        }
        for name, img in files.items():
            p = os.path.join(out, name)
            img.save(p)
            rep["outputs"][name] = {"size": img.size, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}
    json.dump(rep, open(os.path.join(out, "game_scale_report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
