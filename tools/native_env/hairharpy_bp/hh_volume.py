"""Volumetric lock authoring in HairHarpy's native .hairmesh (v2): 4 strands around a lens cross-section, closed by
4 walls, sharing one tip anchor -> HairHarpy cocoon/convert yields a closed tube (verified: 4 strands -> 258 v / 256 f).

Spine: a scalp-following arc (elevation/azimuth on the head ellipsoid, offset by clearance + half thickness), then
optionally a gravity hang straight down to `hang_to_y`, bowed outward by `bend`. Cross-section frame at each station:
n = outward head normal, b = spine tangent x n. Controls per lock (what the correction stage may change):
  len  -> tip elevation (scalp locks) or hang end height (hanging locks)
  w    -> scale of the width profile, t -> scale of the thickness profile, bend -> bow amplitude
"""
import math

STATIONS = 9  # spine stations per strand (root .. before tip); the tip is shared


def surf(ax, elev, az):
    e, z = math.radians(elev), math.radians(az)
    return [ax[0] * math.cos(e) * math.sin(z), ax[1] * math.sin(e), ax[2] * math.cos(e) * math.cos(z)]


def normal(ax, p):
    g = [p[0] / ax[0] ** 2, p[1] / ax[1] ** 2, p[2] / ax[2] ** 2]
    L = math.sqrt(sum(v * v for v in g)) or 1e-9
    return [v / L for v in g]


def add(a, b, k=1.0):
    return [a[i] + k * b[i] for i in range(3)]


def norm(v):
    L = math.sqrt(sum(x * x for x in v)) or 1e-9
    return [x / L for x in v]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def profile(vals, u):
    """root -> mid (u=.5) -> tip, smooth (quadratic Bezier through the mid value)."""
    r, m, t = vals
    if u <= 0.5:
        s = u / 0.5
        return r + (m - r) * math.sin(s * math.pi / 2)
    s = (u - 0.5) / 0.5
    return m + (t - m) * (1 - math.cos(s * math.pi / 2))


def spine(ax, lk, ctl):
    """Stations (u in [0,1]) along the designed path; returns [(point_on_scalp_or_hang, outward_normal)]."""
    e0, a0 = lk["root"]["elev"], lk["root"]["az"]
    e1, a1 = lk["tip"]["elev"], lk["tip"]["az"]
    hang = lk.get("hang_to_y")
    if hang is None:
        # scalp lock (bangs): a quadratic Bezier root -> tip over the scalp, its middle lifted by the scalp's own
        # sagitta + `bend`; straighter than a surface-following arc (HairHarpy's ring projection breaks on tight arcs)
        e1 = e1 + ctl["len"]  # control = tip elevation offset (deg)
        r = surf(ax, e0, a0)
        t = surf(ax, e1, a1)
        m = surf(ax, (e0 + e1) / 2, (a0 + a1) / 2)
        chord_mid = [(r[k] + t[k]) / 2 for k in range(3)]
        nm = normal(ax, m)
        sag = max(0.0, sum((m[k] - chord_mid[k]) * nm[k] for k in range(3)))
        ctrl = add(m, nm, sag + ctl["bend"])
        pts = []
        for i in range(STATIONS + 1):
            u = i / STATIONS
            q = [(1 - u) ** 2 * r[k] + 2 * (1 - u) * u * ctrl[k] + u * u * t[k] for k in range(3)]
            pts.append((q, normal(ax, q), u))
        return pts
    hang = hang + ctl["len"]  # hanging lock: control = hang end height (m)
    s_end = surf(ax, e1, a1)
    arc = [(surf(ax, e0 + (e1 - e0) * k / 4, a0 + (a1 - a0) * k / 4)) for k in range(5)]
    arc_len = sum(math.dist(p, q) for p, q in zip(arc, arc[1:]))
    drop = max(0.0, s_end[1] - hang)
    total = arc_len + drop
    pts = []
    for i in range(STATIONS + 1):
        d = total * i / STATIONS
        if d <= arc_len:
            f = d / arc_len if arc_len else 0
            s = surf(ax, e0 + (e1 - e0) * f, a0 + (a1 - a0) * f)
            n = normal(ax, s)
        else:
            f = (d - arc_len) / drop if drop else 1
            n0 = normal(ax, s_end)
            n = norm([n0[0], 0.0, n0[2]])
            bow = ctl["bend"] * math.sin(math.pi * f)  # outward bow in the hanging part
            s = [s_end[0] + n[0] * bow, s_end[1] - drop * f, s_end[2] + n[2] * bow]
        pts.append((s, n, i / STATIONS))
    return pts


LENS = [[-1, 0], [-0.7, -0.6], [0, -0.85], [0.7, -0.6], [1, 0], [0.7, 0.75], [0, 1.0], [-0.7, 0.75]]
SPINE_ANCHORS = 12


def lens(aspect):
    """Lens cross-section in HairHarpy profile space: x across [-1,1], y outward; y scaled by thickness/width."""
    return [[x, round(y * aspect, 5)] for x, y in LENS]


def loop_step(lk, ctl):
    return max(0.006, min(0.012, 0.45 * lk["width"][1] * ctl["w"]))


def author(d, bp, controls):
    """Per lock: an evenly resampled spine curve + a HairHarpy profile modifier (item 'tube': lens profiles at
    root/mid/end, radii r0/r1/r2 = half widths, tip collapse). HairHarpy's own modconv turns it into a closed
    volume lock (curves + walls); cocoon + convert build the mesh. Weld is off (thin locks)."""
    import hh_native as H
    items, anchors = H.index(d)
    cont = next(i for i in d["items"] if i["type"] == "group" and "continuation" in i["name"])
    gen = {i["id"] for i in d["items"] if i["type"] in ("cocoon", "mesh", "tube")}
    drop = set(cont["children"]) | gen
    for gid in [i["id"] for i in d["items"] if i.get("parent") == cont["id"] and i["type"] == "group"]:
        drop |= set(items[gid].get("children", [])) | {gid}
    keep_anchor = {a for i in d["items"] if i["id"] not in drop for a in i.get("anchors", [])}
    gone = {a for i in d["items"] if i["id"] in drop for a in i.get("anchors", [])} - keep_anchor
    for i in d["items"]:
        if "children" in i:
            i["children"] = [c for c in i["children"] if c not in drop]
    d["roots"] = [r for r in d.get("roots", []) if r not in drop]
    d["items"] = [i for i in d["items"] if i["id"] not in drop]
    d["anchors"] = [a for a in d["anchors"] if a["id"] not in gone]
    d["weld"] = {"on": False, "dist": None}
    d["lockWeld"] = False
    items, anchors = H.index(d)
    nid = [max(max(items), max(anchors)) + 1]

    def new_id():
        nid[0] += 1
        return nid[0] - 1

    ax = bp["head"]["semi_axes_xyz"]
    made, children = {}, []
    for lk in bp["locks"]:
        c = controls[lk["id"]]
        global STATIONS
        STATIONS = 40
        sp = resample(spine(ax, lk, c), SPINE_ANCHORS)
        ids = []
        for s, n, u in sp:
            k = new_id()
            off = lk["clear"] + profile(lk["thickness"], u) * c["t"] / 2
            d["anchors"].append({"id": k, "p": [float(v) for v in add(s, n, off)], "s": 1})
            ids.append(k)
        gid, cid, tid = new_id(), new_id(), new_id()
        d["items"].append({"anchors": ids, "fair": 0.5, "id": cid, "name": f"{lk['id']}_spine", "ovr": [], "parent": gid,
                           "round": 0.6, "seg": True, "type": "curve", "visible": True})
        w = [v * c["w"] for v in lk["width"]]
        t = [v * c["t"] for v in lk["thickness"]]
        profs = [lens(t[i] / w[i]) for i in range(3)]
        d["items"].append({"id": tid, "name": f"Modifier ({lk['id']}_spine)", "parent": gid, "profile": profs[1], "profs": profs,
                           "p": {"collapse": True, "r0": w[0] / 2, "r1": w[1] / 2, "r2": w[2] / 2, "rRef": w[1] / 2,
                                 "rot0": 0, "rot1": 0, "rot2": 0, "tipLen": 0.25},
                           "src": cid, "type": "tube", "visible": True})
        g = {k: v for k, v in cont.items() if k not in ("children", "id", "name", "parent", "gpivot", "cont")}
        g.update({"children": [cid, tid], "id": gid, "name": lk["id"], "parent": cont["id"], "cont": False,
                  "expanded": False, "conv": {"step": loop_step(lk, c), "dev": 0.0}})
        d["items"].append(g)
        children.append(gid)
        made[lk["id"]] = {"group": gid, "spine": cid, "tube": tid}
    cont["children"] = children
    return made


def events(d, bp, extra):
    ids = {lk["id"] for lk in bp["locks"]}
    ev = ["room hair", "wait 300"]
    groups = sorted((i for i in d["items"] if i["type"] == "group" and i["name"] in ids), key=lambda i: i["name"])
    tubes = {i["parent"]: i["id"] for i in d["items"] if i["type"] == "tube"}
    for g in groups:
        ev += [f"modconv {tubes[g['id']]}", "wait 300", f"select {g['id']}", "cocoon", "wait 200"]
    return ";".join(ev + ["selcocoons", "convert", "wait 3000", "convsum", "meshdump"] + extra)


def default_controls(bp):
    return {lk["id"]: {"len": 0.0, "w": 1.0, "t": 1.0, "bend": lk["bend"]} for lk in bp["locks"]}


def resample(pts, n):
    """Even arc-length resampling of [(p, normal, u)] (normals interpolated)."""
    import bisect
    acc = [0.0]
    for a, b in zip(pts, pts[1:]):
        acc.append(acc[-1] + math.dist(a[0], b[0]))
    out = []
    for i in range(n + 1):
        d = acc[-1] * i / n
        j = max(1, min(len(acc) - 1, bisect.bisect_left(acc, d)))
        f = (d - acc[j - 1]) / ((acc[j] - acc[j - 1]) or 1e-9)
        p = [pts[j - 1][0][k] + (pts[j][0][k] - pts[j - 1][0][k]) * f for k in range(3)]
        nn = norm([pts[j - 1][1][k] + (pts[j][1][k] - pts[j - 1][1][k]) * f for k in range(3)])
        out.append((p, nn, i / n))
    return out


def events_modconv(d, extra):
    """v2 mesh path: HairHarpy converts every profile modifier into its closed lock curves (modconv); the crown cap is
    converted by HairHarpy itself (select crown; convert). Lock meshes are lofted in Blender from those curves."""
    tubes = sorted(i["id"] for i in d["items"] if i["type"] == "tube")
    crown = next(i["id"] for i in d["items"] if i["type"] == "crown")
    ev = ["room hair", "wait 300"] + [x for t in tubes for x in (f"modconv {t}", "wait 150")]
    return ";".join(ev + [f"select {crown}", "convert", "wait 800", "meshdump"] + extra)
