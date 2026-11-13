"""Production mesh preflight: fail closed for BODY-04 primitive placeholders.
Usage: python3 tools/blender/production_mesh_05/preflight.py --manifest path.json
"""
import argparse,json,sys
from pathlib import Path
REQUIRED=("source_sha256","reference_available","view_alignment","silhouette_comparison","topology_deformation","asymmetry_check","art_qa","technical_qa","promotion_eligible","attempt_count","next_method")
def validate(d):
    errors=[]
    for key in REQUIRED:
        if key not in d: errors.append("missing:"+key)
    if d.get("reference_available") is not True: errors.append("reference_unavailable")
    if d.get("view_alignment")!="PASS": errors.append("view_alignment_not_passed")
    if d.get("silhouette_comparison")!="PASS": errors.append("silhouette_not_passed")
    if d.get("topology_deformation")!="PASS": errors.append("deformation_not_passed")
    if d.get("asymmetry_check")!="PASS": errors.append("asymmetry_not_passed")
    if d.get("art_qa")!="PASS": errors.append("art_qa_not_passed")
    if d.get("technical_qa")!="PASS": errors.append("technical_qa_not_passed")
    if d.get("mesh_method") in ("primitive_blockout","cones_and_spheres",None): errors.append("nonproduction_mesh_method")
    if d.get("attempt_count",0)>2: errors.append("retry_limit_exceeded")
    if d.get("promotion_eligible") is not True: errors.append("not_eligible")
    return errors
def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);a=p.parse_args()
    d=json.loads(Path(a.manifest).read_text())
    errors=validate(d)
    print(json.dumps({"status":"BLOCKED" if errors else "PASS","errors":errors},ensure_ascii=False))
    return 1 if errors else 0
if __name__=="__main__":sys.exit(main())
