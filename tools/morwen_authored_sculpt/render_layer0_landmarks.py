"""Register verified Layer 0 drawings and render manual landmark overlays."""

import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw


def render_view(source, view, annotation, expected_size, output):
    path = source / annotation["image"]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != annotation["sha256"]:
        raise ValueError(f"{view}: reference SHA-256 mismatch")
    with Image.open(path) as original:
        if original.size != expected_size or "A" not in original.getbands():
            raise ValueError(f"{view}: unexpected reference size or missing alpha")
        image = original.convert("RGBA")

    alpha = image.getchannel("A")
    bounds = alpha.point(lambda value: 255 if value >= 128 else 0).getbbox()
    if bounds is None or bounds[3] - bounds[1] < 2:
        raise ValueError(f"{view}: insufficient subject silhouette")
    ground = bounds[3] - 1
    height = ground - bounds[1]
    center = annotation["stance_center_x_px"]
    scale = 960 / height

    # Keep the stance anchor and ground fixed in one common image grid.
    origin_x, origin_y = 272, 1000
    overlay_size = (760, 1040)
    registered = image.transform(
        overlay_size,
        Image.Transform.AFFINE,
        (1 / scale, 0, center - origin_x / scale,
         0, 1 / scale, ground - origin_y / scale),
        resample=Image.Resampling.BICUBIC,
    )
    canvas = Image.new("RGBA", overlay_size, "#25242e")
    canvas.alpha_composite(registered)
    draw = ImageDraw.Draw(canvas)
    draw.text((12, 12), f"{view.upper()} / {path.name} / provisional 2D", fill="white")
    draw.line((origin_x, 40, origin_x, origin_y), fill="#88839a")
    draw.line((12, origin_y + 1, 505, origin_y + 1), fill="#88839a")
    result = {}

    for index, (name, point) in enumerate(annotation["landmarks"].items(), 1):
        xy = point["xy_px"]
        state = point["visibility"]
        color = {"visible": "#75f4db", "partial": "#ffda82", "estimated": "#ffaece",
                 "occluded": "#b4b0bf"}[state]
        row = dict(point, registered_normalized_xy=None)
        label = f"{index:02d}  {name}"
        if xy is None:
            if state != "occluded" or not point.get("reason"):
                raise ValueError(f"{view}/{name}: missing occlusion reason")
            label += " [hidden]"
        else:
            x, y = xy
            uncertainty = point["uncertainty_px"]
            if (state == "occluded" or not (0 <= x < image.width and 0 <= y < image.height)
                    or not math.isfinite(uncertainty) or uncertainty <= 0):
                raise ValueError(f"{view}/{name}: invalid point")
            if state == "visible" and alpha.getpixel((x, y)) < 128:
                raise ValueError(f"{view}/{name}: visible landmark outside silhouette")
            row["registered_normalized_xy"] = [round((x - center) / height, 7),
                                                round((ground - y) / height, 7)]
            u = origin_x + (x - center) * scale
            v = origin_y + (y - ground) * scale
            r = max(3, uncertainty * scale)
            draw.ellipse((u-r, v-r, u+r, v+r), outline=color, width=1)
            draw.point((u, v), fill=color)
            draw.text((u+4, v-13), f"{index:02d}", fill=color, stroke_width=1,
                      stroke_fill="#25242e")
            label += f"  ({x},{y}) ±{uncertainty}"
        draw.text((518, 65 + 20 * index), label, fill=color)
        result[name] = row
    canvas.convert("RGB").save(output / f"{view}_landmarks.png")
    return {"sha256": digest, "alpha_bounds_px_inclusive": [*bounds[:2], bounds[2]-1, ground],
            "stance_anchor_px": [center, ground], "height_span_px": height,
            "landmarks": result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    annotation_path = Path(__file__).with_name("layer0_landmarks_v1.json")
    manifest = json.loads(annotation_path.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    results = {}
    for view, annotation in manifest["views"].items():
        results[view] = render_view(args.source, view, annotation,
                                    tuple(manifest["source_size_px"]), args.output)
    report = {
        "annotation_sha256": hashlib.sha256(annotation_path.read_bytes()).hexdigest(),
        "coordinate_system": "x right, y up; stance anchor is (0,0); alpha span is 1",
        "projection": "UNCALIBRATED_2D_DRAWINGS",
        "views": results,
    }
    (args.output / "registered_landmarks.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
