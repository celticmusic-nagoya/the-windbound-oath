#!/usr/bin/env python3
"""Overlay world-Z ruler on actual diagnostic PNGs; no anatomical inference."""
import argparse,html,json,pathlib
def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True);p.add_argument("--output",required=True)
    a=p.parse_args();data=json.loads(pathlib.Path(a.manifest).read_text())
    out=pathlib.Path(a.output);out.mkdir(parents=True,exist_ok=True)
    if data.get("status")!="PASS_DIAGNOSTIC_RENDER_ONLY" or len(data.get("views",[]))!=8:
        raise SystemExit("BLOCKED missing eight successful source renders")
    records=[]
    for v in data["views"]:
        source=pathlib.Path(a.manifest).parent/v["file"]
        if not source.is_file():raise SystemExit("BLOCKED missing PNG "+str(source))
        bounds=v["bounds_xyz"];lo,hi=bounds[2]
        scale=v.get("camera_ortho_scale")
        if scale is None or scale<=0:raise SystemExit("BLOCKED camera scale missing")
        # Ortho scale is the vertical image extent. Camera targets midpoint of bounds.
        mid=(lo+hi)/2
        def ypos(z):return 384-(z-mid)*768/scale
        ruler=[]
        for i in range(9):
            z=lo+(hi-lo)*i/8
            y=ypos(z)
            ruler.append(f'<line x1="0" y1="{y:.2f}" x2="512" y2="{y:.2f}" stroke="#25b4e8" stroke-width="1" stroke-dasharray="4 5" opacity=".65"/>')
            ruler.append(f'<text x="5" y="{y-4:.2f}" font-family="sans-serif" font-size="12" fill="#fff" stroke="#222" stroke-width="2" paint-order="stroke">Z {z:.3f}</text>')
        title=html.escape(v["object"]+" / "+v["view"])
        svg=f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="512" height="768" viewBox="0 0 512 768">
<image href="{html.escape(source.name)}" x="0" y="0" width="512" height="768"/>
<rect x="0" y="0" width="512" height="26" fill="#1c2530" opacity=".85"/>
<text x="8" y="18" fill="white" font-family="sans-serif" font-size="13">{title}</text>
{''.join(ruler)}
<rect x="0" y="742" width="512" height="26" fill="#1c2530" opacity=".85"/>
<text x="8" y="759" fill="white" font-family="sans-serif" font-size="12">WORLD Z GUIDE ONLY — NOT ANATOMICAL LANDMARKS</text>
</svg>'''
        dest=out/(source.stem+"_height_grid.svg")
        dest.write_text(svg)
        records.append({"source_png":source.name,"overlay_svg":dest.name,"z_bounds":[lo,hi],"camera_ortho_scale":scale,"anatomical_landmarks":"NOT_RUN"})
    (out/"height_overlay_manifest.json").write_text(json.dumps({"status":"PASS_GRID_ONLY","overlays":records,"reviewer_confirmed":False,"anatomical_qa":"BLOCKED"},indent=2)+"\n")
    print("PASS_GRID_ONLY",len(records))
if __name__=="__main__":main()
