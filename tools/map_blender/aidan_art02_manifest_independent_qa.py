#!/usr/bin/env python3
"""Independent static QA for AIDAN-MASONRY-ART-02 candidate manifest.
Run against a checked-out candidate PR, not against the production main branch.
No Blender or third-party dependency. This is NOT an art-quality test.
"""
import argparse,json,math,pathlib,sys
def inspect(path):
    m=json.loads(pathlib.Path(path).read_text())
    q=m["qa"];s=q["summary"];r=q["see_through_rays"]
    pts=r["miss_points"];band=r["arris_band_m"]
    failures=[]
    def check(ok,message):
        if not ok:failures.append(message)
    check(len(pts)==r["misses"],"miss count differs from point records")
    check(r["misses"]==s["see_through_misses"],"summary ray count mismatch")
    check(r["through_wall_misses"]==s["through_wall_misses"],"summary through-wall mismatch")
    check(r["through_wall_misses"]+r["arris_grazing_misses"]==r["misses"],"unclassified rays")
    check(len(m["stones"])==s["stone_count"],"stone count mismatch")
    check(all(len(p)==3 and p[0] in ("x","y") and all(math.isfinite(float(v)) for v in p[1:]) for p in pts),"invalid ray record")
    check(all(0<=p[1]<=band for p in pts),"miss outside arris band")
    check(s["through_wall_misses"]==0,"through-wall miss detected")
    check(s["stone_stone_bvh_overlaps"]==0,"stone BVH overlap")
    check(s["stones_watertight_single_component"] and s["mortar_watertight"],"topology report FAIL")
    check(s["min_bed_support_ratio"]>=0.5,"minimum bearing below threshold")
    report={
      "task":"AIDAN-MASONRY-ART-02",
      "method":"independent_manifest_consistency_only",
      "source_manifest":str(path),
      "checks":"PASS" if not failures else "FAIL",
      "failures":failures,
      "rays_total":r["rays"],
      "misses":r["misses"],
      "miss_fraction":round(r["misses"]/r["rays"],8),
      "misses_x":sum(p[0]=="x" for p in pts),
      "misses_y":sum(p[0]=="y" for p in pts),
      "max_arris_offset_m":max((p[1] for p in pts),default=None),
      "arris_band_m":band,
      "through_wall_misses":r["through_wall_misses"],
      "caveats":["Manifest is producer-authored; this check cannot verify underlying mesh geometry.",
                 "Visible dark wedges cannot be diagnosed without camera-ray mesh intersections.",
                 "G2 art QA and G4 game/device QA are not covered."]
    }
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if not failures else 1
if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("manifest");a=parser.parse_args()
    sys.exit(inspect(a.manifest))
