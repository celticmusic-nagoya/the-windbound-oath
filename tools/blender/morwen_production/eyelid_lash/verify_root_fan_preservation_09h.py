"""09H independent, read-only geometry-preservation audit for 09G candidate.

Checks unchanged 17 strips byte-for-byte at mesh coordinate/topology level,
and verifies L00 distal sections (original vertices 4..11) are unchanged.
"""
import argparse,hashlib,json,struct
from pathlib import Path
import bpy

CHANGED="M09_L_LASH_CANDIDATE_00"
def signature(obj):
    m=obj.data
    h=hashlib.sha256()
    h.update(struct.pack("<16d",*(v for row in obj.matrix_world for v in row)))
    h.update(struct.pack("<II",len(m.vertices),len(m.polygons)))
    for v in m.vertices:h.update(struct.pack("<3d",*map(float,v.co)))
    for p in m.polygons:
        ids=tuple(p.vertices)
        h.update(struct.pack("<I",len(ids)))
        h.update(struct.pack("<"+"I"*len(ids),*ids))
    return h.hexdigest()

def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(path.resolve()))
    return {o.name:o for o in bpy.data.objects if o.name.startswith("M09_") and "_LASH_CANDIDATE_" in o.name}

def main():
    p=argparse.ArgumentParser()
    for k in ("before","after","out"):p.add_argument("--"+k,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    before=load(a.before)
    if len(before)!=18:raise ValueError("Expected 18 baseline strips")
    hashes={n:signature(o) for n,o in before.items()}
    old=before[CHANGED]
    distal=[tuple(float(x) for x in old.matrix_world@v.co) for v in list(old.data.vertices)[4:]]
    after=load(a.after)
    if set(before)!=set(after):raise ValueError("Changed strip name set")
    preserved=[n for n in after if n!=CHANGED and hashes[n]==signature(after[n])]
    new=after[CHANGED]
    new_distal=[tuple(float(x) for x in new.matrix_world@v.co) for v in list(new.data.vertices)[1:]]
    # Allow floating point roundoff from world/local coordinate conversion.
    max_diff=max(abs(x-y) for a,b in zip(distal,new_distal) for x,y in zip(a,b))
    faces=[tuple(poly.vertices) for poly in new.data.polygons]
    topology_ok=len(new.data.vertices)==9 and len(faces)==4 and len(faces[0])==3 and all(len(f)==4 for f in faces[1:])
    passed=len(preserved)==17 and max_diff<=1e-8 and topology_ok
    report={"status":"PASS_GEOMETRY_PRESERVATION_ONLY" if passed else "FAIL_GEOMETRY_PRESERVATION",
        "unchanged_strips_verified":len(preserved),"expected_unchanged_strips":17,
        "unchanged_strip_names":sorted(preserved),"distal_max_world_coordinate_difference_m":max_diff,
        "root_fan_topology_ok":topology_ok,
        "before_sha256":hashlib.sha256(a.before.read_bytes()).hexdigest(),
        "after_sha256":hashlib.sha256(a.after.read_bytes()).hexdigest(),
        "G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_ONLY","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_PRESERVATION_09H="+json.dumps({k:report[k] for k in ("status","unchanged_strips_verified","distal_max_world_coordinate_difference_m","root_fan_topology_ok")},sort_keys=True),flush=True)
    if not passed:raise SystemExit(1)
if __name__=="__main__":main()
