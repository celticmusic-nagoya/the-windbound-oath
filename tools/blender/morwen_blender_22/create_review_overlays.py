"""BLENDER-22: create four view visual overlay SVGs for human silhouette review.

The SVG references the canonical PNG by relative path and adds diagnostic spans.
Do not interpret alpha connected spans as nude anatomy or change the mesh.
"""
import hashlib, json
from pathlib import Path
from importlib.util import spec_from_file_location,module_from_spec
ROOT=Path(__file__).resolve().parents[3]
SCRIPT=ROOT/"tools/blender/morwen_blender_21/segment_torso_candidates.py"
spec=spec_from_file_location("segments21",SCRIPT)
mod=module_from_spec(spec);spec.loader.exec_module(mod)
OUT=ROOT/"assets/candidates/morwen-blender-22"
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    a=json.loads(mod.ANCHORS.read_text()) if hasattr(mod,"ANCHORS") else json.loads((ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json").read_text())
    report={"task":"MORWEN-BLENDER-22","human_review_required":True,
            "anatomical_fit_authorized":False,"views":{}}
    for name,sha in mod.mod.EXPECTED.items():
        src=mod.mod.REF/("REFERENCE_"+name+".png")
        assert hashlib.sha256(src.read_bytes()).hexdigest()==sha
        rows=mod.mod.rgba_png_alpha(src.read_bytes())
        facing={"front":"front","back":"back","profile_facing_left":"left","profile_facing_right":"right"}[name]
        pts=a["facings"][facing]["rig_points_pixels"]
        cx=pts["chest"][0]
        chest=pts["chest"][1];waist=pts["waist"][1];pelvis=pts["pelvis"][1]
        marks=[]
        for y in range(chest,pelvis+1,12):
            ss=mod.segments(rows[y])
            chosen=next((s for s in ss if s[0]<=cx<=s[1]),None)
            if chosen:
                l,r=chosen
                marks.append(f'<line x1="{l}" y1="{y}" x2="{r}" y2="{y}" stroke="#00e5ff" stroke-width="1.5" opacity=".85"/>')
            marks.append(f'<circle cx="{cx}" cy="{y}" r="2" fill="#ff6a00"/>')
        for key,color in (("chest","#ffca28"),("waist","#7cfc00"),("pelvis","#ff65c0")):
            y=pts[key][1]
            marks.append(f'<line x1="0" y1="{y}" x2="384" y2="{y}" stroke="{color}" stroke-width="1" stroke-dasharray="5 4"/>')
        # Embed reference as a data URI so the review artifact is self-contained.
        import base64
        b64=base64.b64encode(src.read_bytes()).decode("ascii")
        svg='<svg xmlns="http://www.w3.org/2000/svg" width="384" height="1024" viewBox="0 0 384 1024"><rect width="384" height="1024" fill="#20252b"/><image width="384" height="1024" href="data:image/png;base64,'+b64+'"/>'+''.join(marks)+'</svg>'
        target=OUT/(name+"_review.svg")
        target.write_text(svg)
        report["views"][name]={"reference_sha256":sha,"overlay":target.name,
            "samples":len(range(chest,pelvis+1,12)),
            "status":"HUMAN_REVIEW_REQUIRED"}
    (OUT/"review_manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_22_REVIEW_OVERLAYS_PASS")
if __name__=="__main__":main()
