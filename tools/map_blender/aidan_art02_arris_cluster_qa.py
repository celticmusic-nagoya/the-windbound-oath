#!/usr/bin/env python3
"""Independent arris-ray clustering report for AIDAN-MASONRY-ART-02.
Read-only diagnostic of producer manifest. Does NOT inspect Blender geometry.
"""
import argparse,csv,json,pathlib
def main():
    p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--out",required=True)
    args=p.parse_args()
    m=json.loads(pathlib.Path(args.manifest).read_text())
    q=m["qa"]["see_through_rays"];courses=m["courses"]
    out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for axis,offset,z in q["miss_points"]:
        distances=[(min(abs(z-a),abs(z-b)),i) for i,(a,b) in enumerate(courses)]
        distance,course=min(distances)
        rows.append({"axis":axis,"arris_offset_m":offset,"z_m":z,
                     "nearest_course_index":course,"nearest_bed_distance_m":round(distance,6),
                     "within_20mm_of_bed":distance<.02})
    with (out/"arris_miss_points.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ["axis","arris_offset_m","z_m","nearest_course_index","nearest_bed_distance_m","within_20mm_of_bed"])
        w.writeheader();w.writerows(rows)
    result={"rays":q["rays"],"misses":len(rows),
            "miss_rate_pct":round(100*len(rows)/q["rays"],5),
            "near_bed_20mm":sum(r["within_20mm_of_bed"] for r in rows),
            "x_face":sum(r["axis"]=="x" for r in rows),
            "y_face":sum(r["axis"]=="y" for r in rows),
            "max_arris_offset_m":max((r["arris_offset_m"] for r in rows),default=None),
            "producer_arris_band_m":q["arris_band_m"],
            "limits":"Correlation is descriptive only; neither missing geometry nor dark wedge cause is proven. Camera-ray material-ID diagnostic still required."}
    (out/"arris_cluster_report.json").write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
