#!/usr/bin/env python3
"""Build non-destructive editable bob-hair *guides*, not a finished hair model.

The real basemesh determines placement and size. Curve guides are separated from
the canonical references and body. This stage is explicitly NOT an art pass.
"""
import argparse,hashlib,json,math,pathlib
import bpy
from mathutils import Vector

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--stage",required=True);p.add_argument("--output",required=True)
 a=p.parse_args();src=pathlib.Path(a.stage).resolve();out=pathlib.Path(a.output).resolve()
 if not src.is_file() or src==out or out.is_relative_to(src):raise SystemExit("BLOCKED paths")
 sha=hashlib.sha256(src.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
 body=bpy.data.objects.get("MORWEN_PROPORTION_STAGE_UNAPPROVED")
 if body is None or body.type!="MESH":raise SystemExit("BLOCKED missing basemesh")
 vertices=[body.matrix_world@v.co for v in body.data.vertices]
 zmin=min(v.z for v in vertices);zmax=max(v.z for v in vertices);height=zmax-zmin
 # Restrict head reference band; all derived dimensions are *guides* and not
 # anatomical measurements. Keep them adjustable until a reviewer aligns them.
 head_band=[v for v in vertices if v.z>zmax-height*.115]
 if len(head_band)<20:raise SystemExit("BLOCKED no head-region geometry")
 cx=(min(v.x for v in head_band)+max(v.x for v in head_band))/2
 cy=(min(v.y for v in head_band)+max(v.y for v in head_band))/2
 rx=(max(v.x for v in head_band)-min(v.x for v in head_band))/2
 ry=(max(v.y for v in head_band)-min(v.y for v in head_band))/2
 if min(rx,ry)<.015:raise SystemExit("BLOCKED head bounds implausible")
 coll=bpy.data.collections.new("MORWEN_HAIR_GUIDES_UNAPPROVED")
 bpy.context.scene.collection.children.link(coll)
 mat=bpy.data.materials.new("GUIDE_purple_NOT_FINAL_PBR")
 mat.diffuse_color=(.19,.09,.31,1);mat.use_nodes=True
 mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.19,.09,.31,1)
 # Editable, smooth Bezier curves. Distinct layers: cap boundary, rear bob,
 # side locks and fringe. No generic primitives are marked as finished assets.
 guide_defs=[]
 for i in range(24):
  theta=2*math.pi*i/24
  x=cx+rx*1.06*math.cos(theta);y=cy+ry*1.07*math.sin(theta)
  # Crown follows an approximate ellipse; bob hem sits above shoulder.
  top=Vector((cx+rx*.45*math.cos(theta),cy+ry*.45*math.sin(theta),zmax+height*.005))
  mid=Vector((x,y,zmax-height*.065))
  hem=Vector((x*1.0,y*1.0,zmax-height*(.135 if math.sin(theta)>-.25 else .115)))
  guide_defs.append(("bob_guide_%02d"%i,[top,mid,hem]))
 for i in range(9):
  t=(i-4)/4
  # Front fringe only; note front is -Y in this source stage.
  guide_defs.append(("fringe_guide_%02d"%i,[
   Vector((cx+t*rx*.65,cy-ry*.7,zmax-height*.014)),
   Vector((cx+t*rx*.8,cy-ry*1.1,zmax-height*.055)),
   Vector((cx+t*rx*.82,cy-ry*1.12,zmax-height*.09))]))
 for name,pts in guide_defs:
  curve=bpy.data.curves.new(name,"CURVE");curve.dimensions="3D"
  curve.resolution_u=16;curve.bevel_depth=height*.0018;curve.bevel_resolution=2
  spline=curve.splines.new("BEZIER");spline.bezier_points.add(2)
  for bp,v in zip(spline.bezier_points,pts):
   bp.co=v;bp.handle_left_type="AUTO";bp.handle_right_type="AUTO"
  obj=bpy.data.objects.new(name,curve);coll.objects.link(obj)
  obj.data.materials.append(mat)
  obj["qa_status"]="UNAPPROVED_GUIDE_ONLY"
 body["hair_guides_created"]=True
 body["hair_model_completed"]=False
 out.parent.mkdir(parents=True,exist_ok=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(out),load_ui=False)
 actual=[o for o in bpy.data.objects if o.name.startswith(("bob_guide_","fringe_guide_"))]
 if len(actual)!=33:raise SystemExit("FAIL guide count")
 if hashlib.sha256(src.read_bytes()).hexdigest()!=sha:raise SystemExit("FAIL stage mutated")
 report={"status":"PASS_EDITABLE_GUIDE_GENERATION_ONLY","guides":33,
  "input_sha256":sha,"output_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
  "head_center_approx":[cx,cy,zmax],"head_radius_approx":[rx,ry],
  "canonical_art_qa":"NOT_RUN","hair_surface_model":"NOT_RUN",
  "head_ratio":"NOT_MEASURED","source_unchanged":True}
 (out.parent/"hair_guide_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
 print(json.dumps({"status":report["status"],"guides":33}))
if __name__=="__main__":main()
