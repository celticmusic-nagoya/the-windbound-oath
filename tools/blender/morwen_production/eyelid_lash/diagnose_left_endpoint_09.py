"""Read-only endpoint diagnosis; no mesh changes or guessed corrections."""
import argparse,json,hashlib
from pathlib import Path
from math import sqrt

def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def norm(a):return sqrt(dot(a,a))
def unit(a):
    n=norm(a)
    if n<1e-12:raise ValueError("degenerate vector")
    return [v/n for v in a]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--anchors",required=True,type=Path)
    p.add_argument("--comparison",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    raw=a.anchors.read_bytes()
    roots=json.loads(raw)["sides"]["L"]
    comparison=json.loads(a.comparison.read_text())
    if comparison["sides"]["L"]["new_intersecting_strips"]!=["M09_L_LASH_CANDIDATE_00"]:
        raise ValueError("Unexpected residual pattern; do not infer endpoint cause")
    details=[]
    for i in range(3):
        r=roots[i]
        pt=r["root_world_m"]
        n=unit(r["normal_world"])
        fwd=unit(sub(roots[min(i+1,8)]["root_world_m"],pt))
        tangent=sub(fwd,[dot(fwd,n)*v for v in n])
        tangent=unit(tangent)
        details.append({"index":i,"root":pt,"normal":n,
                        "forward_tangent":tangent,"normal_forward_dot":dot(n,fwd),
                        "next_root_distance_m":norm(sub(roots[min(i+1,8)]["root_world_m"],pt))})
    result={"status":"DIAGNOSIS_ONLY","issue":"LASH_CANDIDATE_00_ONLY",
            "anchors_sha256":hashlib.sha256(raw).hexdigest(),
            "endpoint_neighbors":details,
            "hypotheses_not_proven":["endpoint one-sided tangent","cage normal orientation","surface offset inadequate"],
            "G3":"FAIL","geometry_changed":False}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+"\n")
    print("M09_LEFT_ENDPOINT_DIAGNOSIS="+json.dumps(result,sort_keys=True),flush=True)
if __name__=="__main__":main()
