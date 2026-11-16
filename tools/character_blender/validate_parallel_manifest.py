"""Validate character parallel candidate manifest metadata (not art or Blender QA)."""
import argparse,json,sys
from pathlib import Path

REQUIRED=("task_id","asset_id","candidate_id","producer","branch","reference_canon_ref","reference_canon_sha256","reference_candidate_ref","reference_candidate_sha256","blender_version","seed","generation_script","manifest_version","output_dimensions","camera","materials","licenses","dependencies","review_images","G1","G2","G3","G4")
STATES={"PASS","FAIL","BLOCKED","NOT_RUN"}
def validate(data):
    errors=[]
    for k in REQUIRED:
        if k not in data:errors.append("missing:"+k)
    for k in ("G1","G2","G3","G4"):
        if k in data and data[k] not in STATES:errors.append("invalid gate:"+k)
    for k in ("reference_canon_sha256","reference_candidate_sha256"):
        v=data.get(k)
        if v is not None and (not isinstance(v,str) or len(v)!=64 or any(x not in "0123456789abcdef" for x in v.lower())):
            errors.append("invalid sha256:"+k)
    if data.get("G1")=="PASS" and data.get("reference_canon_sha256") is None:
        errors.append("G1 PASS without verified canon hash")
    return errors

def main():
    p=argparse.ArgumentParser()
    p.add_argument("manifest",nargs="+",type=Path)
    a=p.parse_args()
    failed=False
    for f in a.manifest:
        try: errors=validate(json.loads(f.read_text(encoding="utf-8")))
        except (ValueError,OSError) as e: errors=[str(e)]
        print(json.dumps({"manifest":str(f),"status":"FAIL" if errors else "PASS_METADATA_ONLY","errors":errors}))
        failed|=bool(errors)
    sys.exit(1 if failed else 0)
if __name__=="__main__":main()
