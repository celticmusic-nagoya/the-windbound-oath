"""Render an SVG design-review sheet: Layer 0 neutral upper/lower curves vs closed-eye proposal.

This is a 2D technical overlay, NOT a Blender render or an artistic approval.
"""
import argparse
import json
import math
from pathlib import Path


def bezier(coef, u):
    return sum(math.comb(4, i) * (1-u)**(4-i) * u**i * coef[i] for i in range(5))


def path(points):
    return "M " + " L ".join(f"{x:.3f},{y:.3f}" for x, y in points)


def render(source, target):
    chunks = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="460" viewBox="0 0 960 460">',
              '<rect width="960" height="460" fill="#f4f1e9"/>',
              '<text x="36" y="38" font-family="sans-serif" font-size="19" fill="#172b35">EYELID-06 | UNREVIEWED 2D CURVE PROPOSAL</text>',
              '<text x="36" y="62" font-family="sans-serif" font-size="12" fill="#38434a">Neutral opening (blue/gray), proposed closure (orange). Not Blender or G2 approval.</text>']
    for index, side in enumerate(("R", "L")):
        xoff = 80 + index * 470
        yoff = 105
        scale = 13
        up = source["design_coef"][side]["upper_coef"]
        lo = source["design_coef"][side]["lower_coef"]
        upts = [(xoff + 22*scale*u, yoff + (bezier(up,u)-114)*scale) for u in (i/64 for i in range(65))]
        lpts = [(xoff + 22*scale*u, yoff + (bezier(lo,u)-114)*scale) for u in (i/64 for i in range(65))]
        cpts = [(xoff + 22*scale*p["u"], yoff + (p["y_px"]-114)*scale) for p in target["sides"][side]["points"]]
        chunks += [f'<text x="{xoff}" y="94" font-family="sans-serif" font-size="16" fill="#172b35">Eye {side} | inner to outer canthus</text>',
                   f'<path d="{path(upts)}" fill="none" stroke="#29638d" stroke-width="2.5"/>',
                   f'<path d="{path(lpts)}" fill="none" stroke="#6a879a" stroke-width="2.5"/>',
                   f'<path d="{path(cpts)}" fill="none" stroke="#d2682d" stroke-width="3.5"/>']
        for x,y in (cpts[0],cpts[-1]):
            chunks.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="4" fill="#d2682d"/>')
    chunks += ['<text x="36" y="437" font-family="sans-serif" font-size="12" fill="#38434a">Art review needed: closure arc, canthal tangent, 45-degree appearance, eyelash fit, and expression combinations.</text>', '</svg>']
    return "\n".join(chunks) + "\n"


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--target", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args=ap.parse_args()
    source=json.loads(args.source.read_text(encoding="utf-8"))
    target=json.loads(args.target.read_text(encoding="utf-8"))
    if target["source_sha256"] != source["source"]["sha256"]:
        raise ValueError("target provenance mismatch")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(source,target),encoding="utf-8")


if __name__=="__main__":
    main()
