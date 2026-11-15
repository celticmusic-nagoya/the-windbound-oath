"""Read-only EYELID-09 input audit: no mesh edits, no old failed-method rebuild."""
import argparse,hashlib,json
from pathlib import Path
import bpy

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",required=True,type=Path)
    p.add_argument("--candidate",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite of QA evidence")
    source_sha=hashlib.sha256(a.source.read_bytes()).hexdigest()
    if source_sha!="a30b05af5369864578aea85b72f6c8e5100630d2ceb638c8a9a52add6e5defd7":
        raise ValueError("Unexpected EYELID-07 source SHA256")
    candidate_sha=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(a.candidate.resolve()))
    face=bpy.data.objects.get("Face")
    if face is None or face.type!="MESH":raise ValueError("Protected Face missing")
    keys=face.data.shape_keys.key_blocks
    expected=["Basis"]+[f"target_{i}" for i in range(56)]+["MORWEN_DESIGN_NoseDepth"]
    if len(face.data.vertices)!=1972 or [k.name for k in keys]!=expected:
        raise ValueError("Protected Face topology/shape keys mismatch")
    report={"source_sha256":source_sha,"candidate_sha256":candidate_sha,
        "protected_face_vertices":len(face.data.vertices),"protected_face_keys":len(keys),
        "objects":{},"G1_full_canonical":"BLOCKED","G2":"NOT_RUN",
        "G3_real_lash_collision":"NOT_RUN","G4":"NOT_RUN"}
    for name in ("M08_R_CONTACT_CAGE_050","M08_L_CONTACT_CAGE_050","M08_ATTACHMENT_PREVIEW_ONLY","MORWEN_Eyes"):
        ob=bpy.data.objects.get(name)
        if ob is None or ob.type!="MESH":raise ValueError("Required source object missing: "+name)
        coords=[ob.matrix_world@v.co for v in ob.data.vertices]
        mins=[min(p[i] for p in coords) for i in range(3)]
        maxs=[max(p[i] for p in coords) for i in range(3)]
        report["objects"][name]={"vertices":len(coords),"polygons":len(ob.data.polygons),
            "world_bounds_m":{"min":mins,"max":maxs},
            "visible_render":not ob.hide_render}
    report["status"]="PASS_INPUT_INSPECTION_ONLY"
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("EYELID09_INPUT_AUDIT="+json.dumps(report,sort_keys=True))
if __name__=="__main__":main()
