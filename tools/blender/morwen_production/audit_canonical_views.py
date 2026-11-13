"""Read-only image audit. Never infer facial landmarks from whole-body silhouettes."""
import bpy, json, hashlib
from pathlib import Path
root=Path("tools/blender/production_mesh_08/references")
names={"front":"7809.png","right":"7807.png","back":"7810.png","left":"7808.png"}
expected={"front":"b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed","right":"9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737","back":"b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f","left":"69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa"}
out=Path("render_output/morwen_vroid_review");out.mkdir(parents=True,exist_ok=True)
result={"schema":"MORWEN-CANONICAL-IMAGE-AUDIT-01","status":"PIXEL_METADATA_ONLY","landmarks_approved":False,"views":{},"landmark_requirements":["crown","chin","eye_centers","nose_tip","mouth_center","jaw_width","profile_nose","ear_anchor"],"note":"Alpha bounding boxes include hair/clothes and must not be interpreted as face proportions."}
for direction,name in names.items():
 path=root/name
 assert path.is_file(),f"Missing canonical reference {path}"
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 assert sha==expected[direction],f"Canonical SHA mismatch: {name}"
 im=bpy.data.images.load(str(path.resolve()),check_existing=False)
 w,h=im.size
 pixels=list(im.pixels[:])
 alpha=[pixels[i+3] for i in range(0,len(pixels),4)]
 opaque=sum(a>=0.99 for a in alpha)
 visible=[i for i,a in enumerate(alpha) if a>0.01]
 bbox=None
 if visible:
  xs=[i%w for i in visible];ys=[i//w for i in visible]
  bbox=[min(xs),min(ys),max(xs),max(ys)]
 result["views"][direction]={"filename":name,"sha256":sha,"width":w,"height":h,"alpha_min":round(min(alpha),4),"alpha_max":round(max(alpha),4),"opaque_fraction":round(opaque/len(alpha),5),"visible_bbox_blender_bottom_origin":bbox,"facial_landmarks":"NOT_ANNOTATED"}
 bpy.data.images.remove(im)
(out/"CANONICAL_IMAGE_AUDIT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
print("Canonical reference audit complete:",len(result["views"]),"views")
