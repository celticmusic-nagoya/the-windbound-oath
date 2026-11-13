"""MORWEN-REBUILD-04: review manual annotations; no inferred geometry."""
import argparse,json,math
from pathlib import Path

def analyze(data):
 assert data.get("schema")=="MORWEN-LANDMARK-REVIEW-UNAPPROVED"
 assert data.get("coordinate_system")=="image top-left; 384x1024"
 views=data.get("views")
 assert isinstance(views,dict) and set(views)=={"front","right","back","left"}
 required={"front":{"head_top","chin","left_eye_center","right_eye_center","nose_tip","mouth_center","left_jaw_edge","right_jaw_edge","left_ear_anchor","right_ear_anchor"},
 "right":{"head_top","chin","eye_center","nose_tip","mouth_center","jaw_edge","ear_anchor"},
 "left":{"head_top","chin","eye_center","nose_tip","mouth_center","jaw_edge","ear_anchor"},
 "back":{"head_top","neck_center","left_ear_anchor","right_ear_anchor"}}
 normalized={}
 for direction,points in views.items():
  assert isinstance(points,dict)
  assert set(points)<=required[direction],(direction,set(points)-required[direction])
  normalized[direction]={}
  for name,p in points.items():
   assert isinstance(p,dict) and p.get("confidence")=="MANUAL_UNREVIEWED"
   x,y=p["x"],p["y"]
   assert type(x) in (int,float) and type(y) in (int,float)
   assert math.isfinite(x) and math.isfinite(y) and 0<=x<384 and 0<=y<1024
   normalized[direction][name]={"x":x/384,"y":y/1024}
 metrics={}
 front=views["front"]
 if all(k in front for k in ("head_top","chin","left_eye_center","right_eye_center")):
  head=front["chin"]["y"]-front["head_top"]["y"]
  eye_sep=abs(front["left_eye_center"]["x"]-front["right_eye_center"]["x"])
  if head>0:
   metrics["front_eye_separation_to_head_height"]=round(eye_sep/head,5)
 if all(k in front for k in ("left_jaw_edge","right_jaw_edge","head_top","chin")):
  head=front["chin"]["y"]-front["head_top"]["y"]
  if head>0:
   metrics["front_jaw_width_to_head_height"]=round(abs(front["left_jaw_edge"]["x"]-front["right_jaw_edge"]["x"])/head,5)
 return {"schema":"MORWEN-REBUILD-04-MANUAL-LANDMARK-METRICS",
 "status":"UNAPPROVED_MANUAL_COORDINATES","canonical_fit":"NOT_EVALUATED",
 "measured_points":sum(map(len,views.values())),
 "normalized_landmarks":normalized,"metrics":metrics,
 "warning":"Manual landmarks are not independently reviewed; no 3D deformation is authorized."}

def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("input",type=Path)
 ap.add_argument("--output",type=Path)
 args=ap.parse_args()
 result=analyze(json.loads(args.input.read_text(encoding="utf-8")))
 text=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
 if args.output:
  args.output.parent.mkdir(parents=True,exist_ok=True)
  args.output.write_text(text,encoding="utf-8")
 else: print(text)
if __name__=="__main__":main()
