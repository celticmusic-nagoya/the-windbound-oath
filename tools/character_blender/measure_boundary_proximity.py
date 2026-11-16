"""Read-only candidate Body/Face boundary proximity audit.
Distance is diagnostic, not proof of weld or an anatomical neck seam.
"""
import argparse,collections,hashlib,json,math
from pathlib import Path
import bpy
from mathutils import kdtree

def boundary_vertices(obj):
    mesh=obj.data
    edges=collections.Counter()
    for face in mesh.polygons:
        for key in face.edge_keys:edges[tuple(sorted(key))]+=1
    ids=sorted({i for e,count in edges.items() if count==1 for i in e})
    return [(i,obj.matrix_world@mesh.vertices[i].co) for i in ids]

def stats(values):
    if not values:return None
    vals=sorted(values)
    return {"count":len(vals),"min_m":round(vals[0],8),"p50_m":round(vals[len(vals)//2],8),
        "p95_m":round(vals[min(len(vals)-1,int(len(vals)*.95))],8),
        "max_m":round(vals[-1],8),
        "within_1mm":sum(v<=.001 for v in vals),
        "within_5mm":sum(v<=.005 for v in vals),
        "within_10mm":sum(v<=.01 for v in vals)}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--expected-sha256",required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    sha=hashlib.sha256(a.input.read_bytes()).hexdigest()
    if sha!=a.expected_sha256:raise ValueError("SHA mismatch")
    bpy.ops.wm.open_mainfile(filepath=str(a.input.resolve()))
    body=boundary_vertices(bpy.data.objects["Body"])
    face=boundary_vertices(bpy.data.objects["Face"])
    def nearest(source,target):
        tree=kdtree.KDTree(len(target))
        for i,(_,co) in enumerate(target):tree.insert(co,i)
        tree.balance()
        return [(idx,co,tree.find(co)[2]) for idx,co in source]
    b2f=nearest(body,face)
    f2b=nearest(face,body)
    # Z bands only for exploration, not named neck without approved anatomical markers.
    bands=[(1.25,1.35),(1.35,1.40),(1.40,1.45),(1.45,1.50),(1.50,1.60)]
    def summarize(entries):
        return {"overall":stats([d for _,_,d in entries]),
          "z_bands":[{"z_min_m":lo,"z_max_m":hi,
           "nearest_opposite_boundary":stats([d for _,co,d in entries if lo<=co.z<hi])} for lo,hi in bands]}
    report={"schema":"TWO_CHARACTER_BOUNDARY_PROXIMITY_V1",
      "status":"CANDIDATE_DIAGNOSTIC_ONLY","source_sha256":sha,
      "blender_version":bpy.app.version_string,
      "body_to_face":summarize(b2f),"face_to_body":summarize(f2b),
      "caveats":["Nearest boundary vertex is not nearest mesh surface.",
         "Z bands are not approved neck anatomy; close distances do not prove mesh weld.",
         "No canonical reference or camera-handedness verification was performed.",
         "This read-only diagnostic does not modify the blend."],
      "neck_seam":"BLOCKED_UNTIL_APPROVED_REGION_ANNOTATION",
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_MEASUREMENT_ONLY","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("BOUNDARY_PROXIMITY="+json.dumps({"body_to_face":report["body_to_face"]["overall"],
      "face_to_body":report["face_to_body"]["overall"]}),flush=True)
if __name__=="__main__":main()
