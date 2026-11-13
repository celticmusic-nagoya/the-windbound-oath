"""Reproducible image-space silhouette measurement; NOT anatomical landmark inference."""
import hashlib,json
from pathlib import Path
from PIL import Image
repo=Path(__file__).resolve().parents[3]
manifest_path=repo/"tools/blender/production_mesh_08/layer0_reference_manifest.json"
manifest=json.loads(manifest_path.read_text())
root=repo/manifest["reference_root"]
result={"schema":"MORWEN-LAYER0-MEASURE-01","coordinate_convention":"image pixels: x right, y down; character right +X","views":{},"status":"MEASURED_NOT_ART_APPROVED"}
for item in manifest["images"]:
    path=root/item["filename"]
    data=path.read_bytes()
    assert hashlib.sha256(data).hexdigest()==item["sha256"],path
    with Image.open(path) as im:
        assert im.size==(item["width"],item["height"]),(path,im.size)
        rgba=im.convert("RGBA")
        alpha=rgba.getchannel("A")
        bbox=alpha.getbbox()
        assert bbox is not None,path
        # Alpha>0 includes semi-transparent antialiasing; also report robust 50% threshold.
        solid=alpha.point(lambda a:255 if a>=128 else 0).getbbox()
        assert solid is not None,path
        result["views"][item["view"]]={"source":item["filename"],"sha256":item["sha256"],
          "canvas_px":list(im.size),"alpha_nonzero_bbox_xyxy":list(bbox),
          "alpha_128_bbox_xyxy":list(solid),
          "alpha_128_height_px":solid[3]-solid[1],
          "alpha_128_width_px":solid[2]-solid[0]}
# The reference sheet's image silhouette includes costume and may not define body joints.
result["limitations"]=["Image alpha bounds are NOT head, joint, or body landmarks.",
"Do not derive anatomical measurements from costume silhouette automatically.",
"Head/chin/shoulder/hip/knee/ankle require separate reviewed annotations.",
"Do not build production geometry from these values without art review."]
out=Path("render_output/morwen_layer0_measure");out.mkdir(parents=True,exist_ok=True)
(out/"measurements.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print(json.dumps({k:v["alpha_128_bbox_xyxy"] for k,v in result["views"].items()}))
