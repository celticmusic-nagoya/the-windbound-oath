"""MORWEN-RIG-07: render QA overlay only after all joint anchors are measured.

Produces one SVG per facing without modifying or embedding original image bytes.
"""
import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape
from qa_morwen_anchors import validate

EDGES = [
    ("head","shoulder.L"), ("head","shoulder.R"),
    ("shoulder.L","shoulder.R"), ("shoulder.L","elbow.L"),
    ("elbow.L","wrist.L"), ("shoulder.R","elbow.R"),
    ("elbow.R","wrist.R"), ("shoulder.L","pelvis"),
    ("shoulder.R","pelvis"), ("pelvis","knee.L"),
    ("pelvis","knee.R"), ("knee.L","ankle.L"),
    ("knee.R","ankle.R"),
]

def svg_for(facing, anchors, width=480, height=640):
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#151923"/>',
        f'<text x="12" y="22" fill="white" font-size="16">{escape(facing)} - JOINTS ONLY (NOT CANON ART)</text>',
        f'<line x1="0" y1="{height-1}" x2="{width}" y2="{height-1}" stroke="#e4bf62" stroke-dasharray="5 4"/>'
    ]
    for a,b in EDGES:
        x1,y1 = anchors[a]["x"]*width, anchors[a]["y"]*height
        x2,y2 = anchors[b]["x"]*width, anchors[b]["y"]*height
        lines.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#5bd4e9" stroke-width="2"/>')
    for name,xy in anchors.items():
        x,y=xy["x"]*width,xy["y"]*height
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#f9a66b"/>')
        lines.append(f'<text x="{x+6:.2f}" y="{y-5:.2f}" font-size="11" fill="white">{escape(name)}</text>')
    lines.append("</svg>")
    return "\n".join(lines) + "\n"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--anchors",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    doc=json.loads(args.anchors.read_text(encoding="utf-8"))
    errors=validate(doc,require_measured=True)
    if errors:
        raise SystemExit("BLOCKED: " + "; ".join(errors))
    args.output_dir.mkdir(parents=True,exist_ok=True)
    for facing,entry in doc["facings"].items():
        (args.output_dir / (facing+"_joint_overlay.svg")).write_text(svg_for(facing,entry["anchors"]),encoding="utf-8")
    print("MORWEN_RIG_07_OVERLAY_PASS_NOT_CANON_APPROVAL")

if __name__=="__main__":
    main()
