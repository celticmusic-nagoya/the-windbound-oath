"""Analyze render framing feasibility from QA JSON, without rerendering or edits."""
import argparse,json,pathlib,sys
p=argparse.ArgumentParser()
p.add_argument("report")
p.add_argument("--output",required=True)
a=p.parse_args()
src=json.loads(pathlib.Path(a.report).read_text())
out={"schema":"MORWEN_FRAMING_DIAGNOSIS_V1","input_status":src.get("status"),"render_attempts":len(src.get("attempts",[])),"source_unchanged":src.get("source_unchanged"),"art_qa":"NOT_RUN","game_qa":"NOT_RUN"}
if not src.get("attempts"):
 out.update(status="BLOCKED_NO_RENDER_EVIDENCE")
else:
 last=src["attempts"][-1]
 bbox=last.get("alpha_bbox_sampled")
 if not bbox or len(bbox)!=4:
  out.update(status="BLOCKED_MISSING_BOUNDS")
 else:
  # Renderer is fixed at 512x768 in the inspected production script.
  width=(bbox[2]-bbox[0]+4)/512
  height=(bbox[3]-bbox[1]+4)/768
  # For uniform zoom, hitting the 72% height threshold increases width by same factor.
  required_zoom=0.72/height if height>0 else None
  projected_width=width*required_zoom if required_zoom else None
  out.update(occupancy_x=round(width,4),occupancy_y=round(height,4),required_zoom_for_minimum_height=round(required_zoom,4) if required_zoom else None,projected_width_at_minimum_height=round(projected_width,4) if projected_width else None)
  if not required_zoom:
   out.update(status="BLOCKED_EMPTY_SILHOUETTE")
  elif projected_width>=0.98:
   out.update(status="BLOCKED_ASPECT_CONFLICT",reason="Uniform zoom to minimum height would clip width; change canvas aspect or review occupancy acceptance policy before another render")
  else:
   out.update(status="DIAGNOSTIC_ONLY",reason="Framing might be feasible but prior bounded correction method is exhausted; inspect camera coordinates before rerender")
pathlib.Path(a.output).parent.mkdir(parents=True,exist_ok=True)
pathlib.Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
