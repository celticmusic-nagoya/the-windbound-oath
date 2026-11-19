"""Orthographic projections and section from exported Blender geometry."""
from html import escape
from math import sqrt

VIEWS = {
    "front": ((1,0,0), (0,0,1), (0,-1,0)),
    "back": ((-1,0,0), (0,0,1), (0,1,0)),
    "left": ((0,-1,0), (0,0,1), (-1,0,0)),
    "right": ((0,1,0), (0,0,1), (1,0,0)),
    "top": ((1,0,0), (0,1,0), (0,0,1)),
    "bottom": ((1,0,0), (0,-1,0), (0,0,-1)),
    "oblique45": ((1,1,0), (-1,1,sqrt(2)), (1,-1,sqrt(2))),
}


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def unit(vector):
    norm = sqrt(dot(vector, vector))
    return tuple(x / norm for x in vector)


def write_views(path, objects, scene):
    path.mkdir(exist_ok=True)
    records = {name: data["evaluated"] for name, data in objects.items()
               if not scene["objects"][name]["render_hidden"] and data["evaluated"]["xyz_world"]
               and name != "Provisional sea at Z=0"}
    carriers = [n for n in records if scene["objects"][n]["cliff_variant"] == "B"]
    rocks = [n for n in records if "C10 large rock" in n]
    targets = rocks or carriers or list(records)
    if not targets:
        raise ValueError("No visible mesh geometry")
    center = targets[(len(targets)-1)//2]
    bounds = records[center]["bounds_world"]
    cut = (bounds[0][0] + bounds[0][1]) / 2
    landmarks = {}

    for name in targets:
        data = records[name]
        points = data["xyz_world"]
        landmarks[name] = {
            key: {"vertex_id": index, "xyz": points[index], "source": "evaluated_mesh"}
            for key, index in {
                "crest": max(range(len(points)), key=lambda i: points[i][2]),
                "seaward_extreme": min(range(len(points)), key=lambda i: points[i][1]),
            }.items()
        }
    section = []
    palette = ("#6293ae", "#908575", "#69885c", "#a99271", "#8899a1")
    for view, axes in {**VIEWS, "rock_detail": VIEWS["oblique45"],
                       "section": VIEWS["left"]}.items():
        u, v, w = map(unit, axes)
        selected = {name: records[name] for name in targets} if view == "rock_detail" else records
        shapes = []
        for name, data in selected.items():
            points = data["xyz_world"]
            if view == "section":
                for face_id, *ids in data["triangles"]:
                    xyz = [points[i] for i in ids]
                    crossings = []
                    for a,b in zip(xyz, xyz[1:]+xyz[:1]):
                        if (a[0] < cut <= b[0]) or (b[0] < cut <= a[0]):
                            t = (cut-a[0])/(b[0]-a[0])
                            crossings.append(tuple(x+t*(y-x) for x,y in zip(a,b)))
                    if len(crossings) == 2 and crossings[0] != crossings[1]:
                        slot = data["faces"][face_id]["material_slot"]
                        section.append({"object": name, "face_id": face_id, "endpoints": crossings,
                                        "material_slot": slot})
                        shapes.append((0, name, face_id, crossings, slot))
            else:
                for i, face in enumerate(data["faces"]):
                    xyz = [points[j] for j in face["vertices"]]
                    depth = sum(dot(p,w) for p in xyz) / len(xyz)
                    shapes.append((depth, name, i, xyz, face["material_slot"]))
        if not shapes:
            raise ValueError(f"No drawable geometry for {view}")
        projected = [(dot(p,u), dot(p,v)) for _,_,_,xyz,_ in shapes for p in xyz]
        lo_u, hi_u = min(p[0] for p in projected), max(p[0] for p in projected)
        lo_v, hi_v = min(p[1] for p in projected), max(p[1] for p in projected)
        scale = min(1000/max(hi_u-lo_u,1e-6), 580/max(hi_v-lo_v,1e-6))

        def to_screen(p):
            return 55 + (dot(p,u)-lo_u)*scale, 105 + (hi_v-dot(p,v))*scale

        svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1110" height="750" viewBox="0 0 1110 750">',
               '<rect width="1110" height="750" fill="#f2f5f5"/>',
               f'<text x="55" y="39" font-size="25">{view.upper()} | UNAPPROVED</text>',
               f'<text x="55" y="67" font-size="15">Span {hi_u-lo_u:.3f} × {hi_v-lo_v:.3f} BU (provisional) | {scale:.3f} px/BU | +X coast, -Y sea, +Z up</text>',
               f'<text x="55" y="89" font-size="13">U {tuple(round(x,3) for x in u)} | V {tuple(round(x,3) for x in v)}'
               + (f" | plane X={cut:.4f} BU" if view == "section" else "") + '</text>']
        for _, name, i, xyz, slot in sorted(shapes):
            coords = " ".join(f"{x:.2f},{y:.2f}" for x,y in map(to_screen, xyz))
            kind = "polyline" if view == "section" else "polygon"
            color = palette[slot % len(palette)]
            fill, stroke, width = ("none", color, "1.5") if kind == "polyline" else (color, "#344a57", ".45")
            svg.append(f'<{kind} points="{coords}" fill="{fill}" stroke="{stroke}" stroke-width="{width}">'
                       f'<title>{escape(name)} | face {i} | slot {slot}</title></{kind}>')
        if view != "section":
            for i, name in enumerate(n for n in targets if n in selected):
                for suffix, item in landmarks[name].items():
                    x,y = to_screen(item["xyz"])
                    label = f"L{i+1}-{suffix[0].upper()} / v{item['vertex_id']}"
                    item["id"] = f"{name}/{suffix}"
                    svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="3" fill="#ad2418"/>'
                               f'<text x="{x+4:.2f}" y="{y-4:.2f}" font-size="11">{label}'
                               f'<title>{escape(item["id"])}</title></text>')
        svg.append("</svg>")
        (path / f"{view}.svg").write_text("\n".join(svg)+"\n", encoding="utf-8")
    return {"measured": landmarks, "section": {"x": cut, "segments": section},
            "display_omissions": ["Provisional sea at Z=0"],
            "grass_rock_contact": {"status": "NOT_RUN"},
            "canonical_targets": {"status": "BLOCKED"}, "scale": "provisional"}


def comparison_sheet(reference, renders, output):
    """Package source images and a fixed layout for independent review."""
    import shutil
    output.mkdir(parents=True, exist_ok=True)
    panels = [("Approved CG", reference), *renders]
    rows = ['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="420">',
            '<rect width="1500" height="420" fill="#17232b"/>']
    for index, (label, source) in enumerate(panels):
        dest = f"source-{index}.png"
        shutil.copyfile(source, output / dest)
        x = 10 + index * 500
        rows.append(f'<text x="{x}" y="30" fill="white" font-size="18">{escape(label)}</text>')
        rows.append(f'<image x="{x}" y="45" width="480" height="315" href="{dest}" '
                    'preserveAspectRatio="xMidYMid meet"/>')
    rows.append('<text x="10" y="395" font-size="16" fill="white">Visual review | '
                'CG camera registration and world scale pending | candidates unapproved</text></svg>')
    (output / "official-cg-comparison.svg").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    import argparse
    import hashlib
    from pathlib import Path

    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("c9", type=Path)
    parser.add_argument("c10", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    expected = "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07"
    if hashlib.sha256(args.reference.read_bytes()).hexdigest() != expected:
        raise ValueError("Official CG SHA-256 mismatch")
    comparison_sheet(args.reference, [("C9-B C · low view", args.c9),
                                        ("C10 · low view", args.c10)], args.output)
