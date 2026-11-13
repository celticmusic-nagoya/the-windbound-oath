"""MORWEN-REBUILD-01: canonical landmarks review contract, no guessed measurements."""
import json, hashlib
from pathlib import Path

root=Path("tools/blender/production_mesh_08/references")
out=Path("render_output/morwen_rebuild_01")
out.mkdir(parents=True,exist_ok=True)
refs={
 "front":("7809.png","b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"),
 "right":("7807.png","9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737"),
 "back":("7810.png","b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"),
 "left":("7808.png","69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa")
}
# The review schema deliberately keeps unknown landmarks null.
landmarks={
 "front":["head_top","chin","left_eye_center","right_eye_center","nose_tip","mouth_center","left_jaw_edge","right_jaw_edge","left_ear_anchor","right_ear_anchor"],
 "right":["head_top","chin","eye_center","nose_tip","mouth_center","jaw_edge","ear_anchor"],
 "left":["head_top","chin","eye_center","nose_tip","mouth_center","jaw_edge","ear_anchor"],
 "back":["head_top","neck_center","left_ear_anchor","right_ear_anchor"]
}
views={}
for direction,(filename,expected_sha) in refs.items():
 data=(root/filename).read_bytes()
 actual=hashlib.sha256(data).hexdigest()
 assert actual==expected_sha,(filename,actual)
 views[direction]={
  "filename":filename,"sha256":actual,"image_dimensions_px":[384,1024],
  "coordinate_system":"image pixels; top-left origin; x right, y down",
  "landmarks":{key:None for key in landmarks[direction]},
  "annotation_status":"NOT_ANNOTATED",
  "confidence":"UNASSESSED"
 }
report={
 "schema":"MORWEN-REBUILD-01-LANDMARK-CONTRACT",
 "status":"REFERENCE_VERIFIED_ANNOTATION_PENDING",
 "canonical_sources_unchanged":True,
 "landmark_positions_invented":False,
 "views":views,
 "requirements":{
  "review_before_geometry":["verify each landmark against visible anatomy, not hair/hat","check four-view camera alignment and scale","identify occluded landmarks as null","obtain independent art review"],
  "model_decision":"Do not choose reuse vs rebuild until annotated front/profile proportions are reviewed",
  "prohibited":["unverified percentage deformation as official design","using hair silhouette as face contour","merging into main without approval"]
 }
}
assert len(views)==4
assert all(all(v is None for v in view["landmarks"].values()) for view in views.values())
(out/"LANDMARK_REVIEW_TEMPLATE.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("MORWEN-REBUILD-01: 4 canonical SHA PASS; annotation pending")
