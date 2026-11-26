"""LIND-BUILD-01 — deterministic kit-based Rilde village buildings (inn, shop, dwellings, storage).

Status: CANDIDATE — NOT ART-APPROVED (G2 NOT_RUN, independent review pending).
Run (bpy module):   python3 tools/map_blender/lind/buildings/build_village_buildings.py --out OUT [--render]
Run (Blender CLI):  blender -b --python tools/map_blender/lind/buildings/build_village_buildings.py -- --out OUT --render
Heavy runs must be wrapped:  flock /tmp/blender.lock timeout 900 python3 ...

Options: --buildings inn,shop,house_a,house_b,house_c,storage  --states peaceful,burning
         --lineup  --samples N  --res 1280  --save-blend
Dimensions/materials come from kit_config.load_config() (HOME arch-kit contract v1).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (bpy must be imported before bmesh in module mode)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import kit_config  # noqa: E402
import kit_geometry as KG  # noqa: E402
import kit_materials as KM  # noqa: E402
import kit_roof as KR  # noqa: E402

Z = Vector((0, 0, 1))

PARTS = {  # key -> (contract collection, part name, uv tile m)
    "walls": ("WALL_SHELL", "WALLS", None),
    "plinth": ("FOUNDATION", "PLINTH", None),
    "dressing": ("MASONRY", "DRESSINGS", None),
    "timber": ("TIMBER", "TIMBER", 1.0),
    "roof_timber": ("ROOF_STRUCT", "ROOFFRAME", 1.0),
    "slates": ("ROOF_SLATE", "SLATES", 1.0),
    "ridge": ("ROOF_SLATE", "RIDGE", 0.5),
    "openings": ("OPENINGS", "OPENINGS", 1.0),
    "chimney": ("CHIMNEY", "CHIMNEY", None),
    "porch": ("PORCH", "PORCH", 1.0),
    "signage": ("PROPS_EXT", "SIGN", 0.6),
    "props": ("PROPS_EXT", "PROPS", 0.6),
    "interior": ("INTERIOR", "FLOORS", 1.0),
}


def beam(mb, p0, p1, w, h, mat, rand=0.0, up=None):
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0)
    ln = ax.length
    ax.normalize()
    ref = Vector(up) if up is not None else (Z if abs(ax.dot(Z)) < 0.95 else Vector((1, 0, 0)))
    yv = ref.cross(ax).normalized()
    zv = ax.cross(yv).normalized()
    KG.box(mb, (p0 + p1) / 2, (ln, w, h), mat, axes=(ax, yv, zv), rand=rand)


class Building:
    def __init__(self, key, cfg, state="peaceful", offset=(0, 0, 0), coll_root=None):
        self.key = key
        self.spec = kit_config.BUILDINGS[key]
        self.cfg = cfg
        self.state = state
        self.burning = state in ("burning", "ruin")
        self.bid = self.spec["bldg_id"]
        self.rng = random.Random(kit_config.SEED_BASE + 100 * self.spec["index"])
        self.t = cfg["walls"]["thickness"]
        self.gable_front = self.spec["front"] == "gable"
        w, d = self.spec["w"], self.spec["d"]
        self.Wc, self.Dc = (d, w) if self.gable_front else (w, d)
        rot = Matrix.Rotation(math.radians(90), 4, "Z") if self.gable_front else Matrix.Identity(4)
        self.M = Matrix.Translation(Vector(offset)) @ rot
        lv = cfg["levels"]
        self.ffl = lv["ffl"]
        if self.spec["storeys"] == 2:
            self.he = lv["ffl"] + 2 * lv["storey"] + lv["knee"]
        else:
            self.he = lv["plate_1_5"]
        self.pitch = cfg["roof"]["pitch_deg"]
        self.tp = math.tan(math.radians(self.pitch))
        self.s = self.Dc / 2
        self.ridge_z = self.he + self.s * self.tp
        self.excl = []
        self.skip_fns = []
        self.stats = {}
        self.anchors = []
        self.collisions = []
        self.fx = []
        self.lights = []
        self.mats = KM.build_materials(cfg, state)
        self.parts = {}
        for k, (_, pname, tile) in PARTS.items():
            tile = tile or (cfg["walls"]["texture_tile_m"] if k in ("walls", "chimney") else cfg["walls"]["dressed_tile_m"])
            mb = KG.MeshBuilder(f"GEO_{self.bid}_{pname}" + ("" if state == "peaceful" else f"_{state.upper()}"), uv_scale=tile)
            mb.M = self.M
            self.parts[k] = mb
        self.coll_root = coll_root

    # ------------------------------------------------------------------ frames
    def frames(self):
        W, D, t = self.Wc, self.Dc, self.t
        apex = self.he + self.s * self.tp
        gable = [(0, 0), (D, 0), (D, self.he), (D / 2, apex), (0, self.he)]
        rect_e = lambda L: [(0, 0), (L, 0), (L, self.he), (0, self.he)]
        return {
            "S": (KG.WallFrame((-W / 2 + t, -D / 2, 0), (1, 0, 0), (0, -1, 0)), W - 2 * t, rect_e(W - 2 * t), "eaves"),
            "N": (KG.WallFrame((W / 2 - t, D / 2, 0), (-1, 0, 0), (0, 1, 0)), W - 2 * t, rect_e(W - 2 * t), "eaves"),
            "W": (KG.WallFrame((-W / 2, D / 2, 0), (0, -1, 0), (-1, 0, 0)), D, gable, "gable"),
            "E": (KG.WallFrame((W / 2, -D / 2, 0), (0, 1, 0), (1, 0, 0)), D, gable, "gable"),
        }

    def front_id(self):
        return "W" if self.gable_front else "S"

    # ------------------------------------------------------------------ openings
    def op(self, kind, uc, z0=None, w=None, h=None, **kw):
        o = self.cfg["openings"]
        if kind == "door":
            w, h, z0 = o["door"]["clear_w"], o["door"]["clear_h"], self.ffl if z0 is None else z0
        elif kind == "door2":
            w, h, z0 = o["door2"]["clear_w"], o["door2"]["clear_h"], self.ffl if z0 is None else z0
        elif kind in ("W1", "W2", "W3"):
            w = w or o[kind]["clear_w"]
            h = h or o[kind]["clear_h"]
            if z0 is None:
                z0 = self.ffl + o["W1"]["sill_above_ffl"]
        d = {"kind": kind, "uc": uc, "z0": z0, "w": w, "h": h}
        d.update(kw)
        return d

    def layout(self):
        """Openings per wall, in metres from the wall's centre (u) and absolute z."""
        k = self.key
        up1 = self.ffl + self.cfg["levels"]["storey"] + 0.95
        loft = self.he + 0.35
        L = {"S": [], "N": [], "W": [], "E": []}
        if k == "inn":
            L["S"] = [self.op("W1", -3.7), self.op("W1", 3.7), self.op("W1", -3.7, z0=up1, shutters=True),
                      self.op("W1", 3.7, z0=up1, shutters=True)]
            L["N"] = [self.op("W1", -3.2), self.op("door2", 1.0), self.op("W1", 3.4),
                      self.op("W1", -3.2, z0=up1), self.op("W1", 0.0, z0=up1), self.op("W1", 3.4, z0=up1)]
            L["W"] = [self.op("W1", -2.2), self.op("W1", 2.2), self.op("W1", -2.2, z0=up1), self.op("W1", 2.2, z0=up1)]
            L["E"] = [self.op("W1", -2.2), self.op("W1", 2.2), self.op("W1", -2.2, z0=up1), self.op("W1", 2.2, z0=up1)]
        elif k == "shop":
            L["W"] = [self.op("bay", -1.15, z0=self.ffl + 0.70, w=2.2, h=1.35), self.op("door", 1.6),
                      self.op("W2", 0.0, z0=loft + 0.1)]
            L["N"] = [self.op("W1", -1.8), self.op("W1", 1.8)]
            L["S"] = [self.op("W1", -2.0)]
            L["E"] = [self.op("door2", 1.2), self.op("W2", 0.0, z0=loft + 0.1)]
        elif k == "house_a":
            L["S"] = [self.op("door", -0.4), self.op("W1", -2.1, flowers=True), self.op("W1", 1.6, flowers=True)]
            L["N"] = [self.op("W1", 1.5), self.op("W3", -1.5, z0=self.ffl + 1.3)]
            L["W"] = [self.op("W1", 0.0), self.op("W2", 0.0, z0=loft + 0.15)]
            L["E"] = [self.op("W3", 1.6, z0=self.ffl + 1.3)]
        elif k == "house_b":
            L["W"] = [self.op("door", 0.0), self.op("W1", -1.75, flowers=True), self.op("W1", 1.75, flowers=True),
                      self.op("W2", 0.0, z0=loft + 0.15)]
            L["N"] = [self.op("W1", 1.8)]
            L["S"] = [self.op("W1", -1.5), self.op("W1", 1.5)]
            L["E"] = [self.op("door2", -1.0), self.op("W2", 0.0, z0=loft + 0.15)]
        elif k == "house_c":
            L["S"] = [self.op("door", 0.8), self.op("W1", -1.0, flowers=True), self.op("W1", -2.6)]
            L["N"] = [self.op("W1", 0.0)]
            L["W"] = [self.op("W3", 1.6, z0=self.ffl + 1.3)]
            L["E"] = [self.op("W2", 0.0, z0=loft + 0.45)]
        elif k == "storage":
            L["W"] = [self.op("ddoor", 0.0, z0=0.05, w=2.2, h=2.45)]
            L["N"] = [self.op("slit", u, z0=1.3, w=0.14, h=0.70) for u in (-2.0, 0.0, 2.0)]
            L["S"] = [self.op("slit", u, z0=1.3, w=0.14, h=0.70) for u in (-2.0, 0.0, 2.0)]
            L["E"] = [self.op("W3", 0.0, z0=1.4)]
        return L

    # ------------------------------------------------------------------ build
    def build(self):
        m = self.mats
        fr = self.frames()
        lay = self.layout()
        self.layout_cache = lay
        board = self.spec.get("board_gable")
        for wid, (F, L, prof, kind) in fr.items():
            if board and kind == "gable":
                prof = [(0, 0), (L, 0), (L, self.he), (0, self.he)]
            rects = [self._rect(L, o) for o in lay[wid]]
            KG.wall_with_openings(self.parts["walls"], F, L, prof, self.t, rects, m["stone_wall"])
            self._plinth(F, L, lay[wid], start=0.0 if kind == "gable" else -0.0)
            for o in lay[wid]:
                self._opening(F, L, o)
            if board and kind == "gable":
                self._board_gable(F, L, loft_door=(wid == self.front_id()))
        self._quoins_main()
        if self.spec.get("cross_gable"):
            self._cross_gable()
        for xd in self.spec.get("dormers", []):
            self._dormer(xd)
        for c in self.spec.get("chimneys", []):
            self._chimney(c)
        if self.spec.get("lean_to"):
            self._lean_to()
        if self.spec.get("porch"):
            self._porch(self.spec["porch"])
        if self.spec.get("awning"):
            self._awning()
        if self.spec.get("sign"):
            self._sign(self.spec["sign"])
        if self.spec.get("hoist"):
            self._hoist()
        self._main_roof()
        self._props()
        self._interior()
        self._anchors_collision()

    def _rect(self, L, o):
        u = L / 2 + o["uc"]
        return (u - o["w"] / 2, u + o["w"] / 2, o["z0"], o["z0"] + o["h"])

    # ------------------------------------------------------------------ masonry dressings
    def _plinth(self, F, L, ops, start=0.0):
        rng = self.rng
        ph = self.cfg["walls"]["plinth_height"]
        doors = [self._rect(L, o) for o in ops if o["kind"] in ("door", "door2", "ddoor") and o["z0"] < ph + 0.1]
        u = 0.0
        while u < L - 0.05:
            ln = rng.uniform(0.55, 1.05)
            u1 = min(u + ln, L)
            if not any(d[0] - 0.02 < (u + u1) / 2 < d[1] + 0.02 for d in doors):
                for d in doors:
                    if u < d[0] < u1:
                        u1 = d[0] - 0.01
                    if u < d[1] < u1:
                        u = d[1] + 0.01
                if u1 - u > 0.12:
                    KG.dressed_stone(self.parts["plinth"], F, u + 0.006, u1 - 0.006, 0.0, ph + rng.uniform(-0.03, 0.02),
                                     0.05, self.mats["stone_dressed"], rng, embed=0.08, chip=0.05)
            u = u1 + 0.004

    def _quoin_column(self, corner, a_dir, na, b_dir, nb, ztop, z0=None):
        rng = self.rng
        wc = self.cfg["walls"]
        q = wc["quoin_proud"]
        Fa = KG.WallFrame(corner, a_dir, na)
        Fb = KG.WallFrame(corner, b_dir, nb)
        z = wc["plinth_height"] + 0.01 if z0 is None else z0
        i = rng.randint(0, 1)
        while z < ztop - 0.12:
            hz = min(rng.uniform(*wc["quoin_course_h"]), ztop - z)
            la, lb = (rng.uniform(*wc["quoin_long"]), rng.uniform(*wc["quoin_short"]))
            if i % 2:
                la, lb = lb, la
            KG.dressed_stone(self.parts["dressing"], Fa, -q, la, z, z + hz - 0.012, q, self.mats["stone_dressed"], rng)
            KG.dressed_stone(self.parts["dressing"], Fb, -q, lb, z, z + hz - 0.012, q, self.mats["stone_dressed"], rng)
            z += hz
            i += 1
        self.stats["quoin_courses"] = self.stats.get("quoin_courses", 0) + i

    def _quoins_main(self):
        W, D = self.Wc / 2, self.Dc / 2
        X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
        self._quoin_column((-W, -D, 0), X, -Y, Y, -X, self.he)
        self._quoin_column((W, -D, 0), -X, -Y, Y, X, self.he)
        self._quoin_column((W, D, 0), -X, Y, -Y, X, self.he)
        self._quoin_column((-W, D, 0), X, Y, -Y, -X, self.he)

    # ------------------------------------------------------------------ openings
    def _opening(self, F, L, o):
        m, rng, cfg = self.mats, self.rng, self.cfg
        u0, u1, z0, z1 = self._rect(L, o)
        uc = (u0 + u1) / 2
        kind = o["kind"]
        sb = cfg["openings"]["setback"]
        fw = 0.08
        dm = self.parts["dressing"]
        om = self.parts["openings"]
        lint = cfg["openings"]["lintel"]
        # oak lintel (contract) over doors/windows; slits get a dressed stone head
        if kind != "slit":
            beam(self.parts["timber"], F.p(u0 - lint["bearing_each_side"], z1 + lint["height"] / 2, -0.11),
                 F.p(u1 + lint["bearing_each_side"], z1 + lint["height"] / 2, -0.11), 0.26, lint["height"],
                 m["timber"], rand=rng.random(), up=F.N)
        else:
            KG.dressed_stone(dm, F, u0 - 0.12, u1 + 0.12, z1, z1 + 0.16, 0.02, m["stone_dressed"], rng)
        # alternating jamb stones (skipped behind open shutters)
        if kind in ("door", "door2", "W1", "bay", "ddoor") and not o.get("shutters"):
            for side in (-1, 1):
                z = z0 if kind not in ("W1", "bay") else z0 - 0.02
                i = rng.randint(0, 1)
                while z < z1 - 0.1:
                    hz = min(rng.uniform(0.26, 0.36), z1 - z)
                    ww = 0.34 if i % 2 else 0.22
                    if side < 0:
                        KG.dressed_stone(dm, F, u0 - ww, u0 + 0.01, z, z + hz - 0.012, 0.022, m["stone_dressed"], rng)
                    else:
                        KG.dressed_stone(dm, F, u1 - 0.01, u1 + ww, z, z + hz - 0.012, 0.022, m["stone_dressed"], rng)
                    z += hz
                    i += 1
        # sills / threshold
        if kind in ("W1", "W2", "W3", "bay"):
            KG.dressed_stone(dm, F, u0 - 0.08, u1 + 0.08, z0 - 0.09, z0, 0.065, m["stone_dressed"], rng, chip=0.02)
        if kind in ("door", "door2"):
            KG.box(dm, F.p(uc, self.ffl / 2 - 0.01, 0.22), (o["w"] + 0.45, 0.48, self.ffl), m["stone_dressed"],
                   axes=(F.U, -F.N, Z), rand=rng.random())
        # frame in the reveal
        if kind != "slit":
            d = -sb - fw / 2
            om_t = m["timber"]
            beam(om, F.p(u0 + fw / 2, z0, d), F.p(u0 + fw / 2, z1, d), fw, fw, om_t, up=F.N)
            beam(om, F.p(u1 - fw / 2, z0, d), F.p(u1 - fw / 2, z1, d), fw, fw, om_t, up=F.N)
            beam(om, F.p(u0, z1 - fw / 2, d), F.p(u1, z1 - fw / 2, d), fw, fw, om_t, up=F.N)
            if kind in ("W1", "W2", "W3", "bay"):
                beam(om, F.p(u0, z0 + fw / 2, d), F.p(u1, z0 + fw / 2, d), fw, fw, om_t, up=F.N)
        iu0, iu1, iz0, iz1 = u0 + fw, u1 - fw, z0 + fw, z1 - fw
        if kind in ("W1", "W2", "W3", "bay"):
            cols, rows = {"W1": (2, 3), "W2": (2, 2), "W3": (1, 2), "bay": (4, 2)}[kind]
            dg = -sb - 0.05
            if not self.burning:
                om.poly([F.p(iu0, iz0, dg), F.p(iu1, iz0, dg), F.p(iu1, iz1, dg), F.p(iu0, iz1, dg)], m["glass"],
                        rand=rng.random())
            else:
                self._glow_plane(F, iu0, iu1, iz0, iz1)
            bar_mat = m["timber"] if not self.burning else m["charred"]
            for c in range(1, cols):
                uu = iu0 + (iu1 - iu0) * c / cols
                beam(om, F.p(uu, iz0, dg + 0.02), F.p(uu, iz1, dg + 0.02), 0.045 if c == cols // 2 else 0.025,
                     0.03, bar_mat, up=F.N)
            if not (self.burning and rng.random() < 0.5):
                for r in range(1, rows):
                    zz = iz0 + (iz1 - iz0) * r / rows
                    beam(om, F.p(iu0, zz, dg + 0.02), F.p(iu1, zz, dg + 0.02), 0.02, 0.025, m["iron"], up=F.N)
            if o.get("shutters"):
                self._shutters(F, u0, u1, z0, z1)
            if o.get("flowers"):
                self._flower_box(F, u0, u1, z0)
        elif kind in ("door", "door2"):
            self._door_leaf(F, iu0, iu1, z0, iz1, -sb - 0.06)
        elif kind == "ddoor":
            mid = (iu0 + iu1) / 2
            self._door_leaf(F, iu0, mid - 0.005, z0, iz1, -sb - 0.06, braced=True)
            self._door_leaf(F, mid + 0.005, iu1, z0, iz1, -sb - 0.06, braced=True)
        elif kind == "slit":
            KG.dressed_stone(dm, F, u0 - 0.1, u1 + 0.1, z0 - 0.12, z0, 0.03, m["stone_dressed"], rng, chip=0.02)
            if self.burning:
                self._glow_plane(F, u0, u1, z0, z1)
        if self.burning and kind in ("W1", "W2", "bay", "door", "door2"):
            self.fx.append(("FIRE", F.p(uc, (z0 + z1) / 2, -self.t - 0.6)))

    def _glow_plane(self, F, u0, u1, z0, z1):
        d = -self.t - 0.35
        self.parts["openings"].poly([F.p(u0 - 0.3, z0 - 0.3, d), F.p(u1 + 0.3, z0 - 0.3, d),
                                     F.p(u1 + 0.3, z1 + 0.3, d), F.p(u0 - 0.3, z1 + 0.3, d)],
                                    self.mats["glow"], rand=self.rng.random())

    def _door_leaf(self, F, u0, u1, z0, z1, d, braced=False):
        rng, m = self.rng, self.mats
        om = self.parts["openings"]
        n = max(3, int(round((u1 - u0) / 0.19)))
        widths = [rng.uniform(0.8, 1.2) for _ in range(n)]
        sc = (u1 - u0) / sum(widths)
        u = u0
        for i, wv in enumerate(widths):
            wv *= sc
            if self.burning and rng.random() < 0.45:
                u += wv
                continue
            top = z1 - (rng.uniform(0.0, 0.5) if self.burning else 0.0)
            KG.box(om, F.p(u + wv / 2, (z0 + top) / 2, d + rng.uniform(-0.004, 0.004)), (wv - 0.006, 0.05, top - z0),
                   m["planks"], axes=(F.U, -F.N, Z), rand=rng.random())
            u += wv
        if self.burning:
            return
        # ledges (front, braced doors) or strap hinges (iron)
        if braced:
            for zz in (z0 + 0.25, z1 - 0.25):
                KG.box(om, F.p((u0 + u1) / 2, zz, d + 0.045), (u1 - u0 - 0.04, 0.04, 0.16), m["planks"],
                       axes=(F.U, -F.N, Z), rand=rng.random())
            beam(om, F.p(u0 + 0.08, z0 + 0.32, d + 0.045), F.p(u1 - 0.08, z1 - 0.32, d + 0.045), 0.14, 0.04,
                 m["planks"], rand=rng.random(), up=F.N)
        for zz in (z0 + 0.35, z1 - 0.35):
            KG.box(om, F.p(u0 + (u1 - u0) * 0.33, zz, d + 0.03), ((u1 - u0) * 0.62, 0.012, 0.045), m["iron"],
                   axes=(F.U, -F.N, Z))
        KG.box(om, F.p(u1 - 0.14, z0 + 1.0, d + 0.04), (0.04, 0.03, 0.12), m["iron"], axes=(F.U, -F.N, Z))

    def _shutters(self, F, u0, u1, z0, z1):
        rng, m = self.rng, self.mats
        w = (u1 - u0) / 2
        for side in (-1, 1):
            a, b = (u0 - w - 0.02, u0 - 0.02) if side < 0 else (u1 + 0.02, u1 + w + 0.02)
            if self.burning and rng.random() < 0.6:
                continue
            n = 3
            for i in range(n):
                ua = a + (b - a) * i / n
                ub = a + (b - a) * (i + 1) / n
                KG.box(self.parts["openings"], F.p((ua + ub) / 2, (z0 + z1) / 2, 0.03), (ub - ua - 0.006, 0.035, z1 - z0),
                       m["planks"], axes=(F.U, -F.N, Z), rand=rng.random())
            for zz in (z0 + 0.2, z1 - 0.2):
                KG.box(self.parts["openings"], F.p((a + b) / 2, zz, 0.055), (b - a - 0.02, 0.02, 0.09), m["planks"],
                       axes=(F.U, -F.N, Z), rand=rng.random())

    def _flower_box(self, F, u0, u1, z0):
        rng, m = self.rng, self.mats
        pm = self.parts["props"]
        d0 = 0.12
        KG.box(pm, F.p((u0 + u1) / 2, z0 + 0.10, d0 + 0.08), (u1 - u0 + 0.1, 0.2, 0.2), m["planks"],
               axes=(F.U, -F.N, Z), rand=rng.random())
        if self.burning:
            return
        KG.box(pm, F.p((u0 + u1) / 2, z0 + 0.205, d0 + 0.08), (u1 - u0 + 0.06, 0.16, 0.01), m["prop"],
               axes=(F.U, -F.N, Z), rand=KM.palette_value("soil"))
        n = int((u1 - u0) / 0.07)
        for i in range(n):
            uu = u0 + 0.02 + (u1 - u0 - 0.04) * (i + rng.random() * 0.6) / n
            dd = d0 + 0.08 + rng.uniform(-0.06, 0.06)
            hh = rng.uniform(0.08, 0.22)
            KG.lathe(pm, [(0.0, 0), (0.035, 0.03), (0.045, hh * 0.6), (0.0, hh)], F.p(uu, z0 + 0.2, dd), m["prop"],
                     segments=5, rand=KM.palette_value(rng.choice(["leaf", "leaf_dark"])))
            if rng.random() < 0.75:
                col = rng.choice(["flower_red", "flower_red", "flower_white", "flower_violet"])
                KG.lathe(pm, [(0.0, 0), (0.03, 0.01), (0.025, 0.035), (0.0, 0.04)],
                         F.p(uu + rng.uniform(-0.02, 0.02), z0 + 0.2 + hh * 0.85, dd), m["prop"], segments=6,
                         rand=KM.palette_value(col))

    # ------------------------------------------------------------------ boarded gable (storage)
    def _board_gable(self, F, L, loft_door=False):
        rng, m = self.rng, self.mats
        apex = self.he + self.s * self.tp
        tm = self.parts["timber"]
        tri = [(0, self.he), (L, self.he), (L / 2, apex)]
        KG.flat_prism(tm, tri, F.fn(), -0.10, -0.04, m["planks"], rand=0.5)
        bh = 0.24
        z = self.he - 0.02
        door = (L / 2 - 0.55, L / 2 + 0.55, self.he + 0.25, self.he + 1.5) if loft_door else None
        while z < apex - 0.1:
            za, zb = z, min(z + bh, apex - 0.02)
            ua = lambda zz: L / 2 - (apex - zz) / self.tp
            ub = lambda zz: L / 2 + (apex - zz) / self.tp
            segs = [(ua(za), ub(za), ua(zb), ub(zb))]
            if door and za < door[3] and zb > door[2]:
                segs = [(ua(za), door[0], ua(zb), door[0]), (door[1], ub(za), door[1], ub(zb))]
            for (a0, b0, a1, b1) in segs:
                if b0 - a0 < 0.05:
                    continue
                if self.burning and rng.random() < 0.4:
                    continue
                outline = [(a0, za), (b0, za), (b1, zb), (a1, zb)]
                tilt = rng.uniform(-0.004, 0.004)
                KG.flat_prism(tm, outline, lambda u, v, d, za=za: F.p(u, v, d + (0.03 if v <= za + 1e-6 else 0.0) + tilt),
                              -0.04, -0.005, m["planks"], rand=rng.random())
            z += bh - 0.035
        if door:
            u0, u1, z0, z1 = door
            KG.flat_prism(tm, [(u0, z0), (u1, z0), (u1, z1), (u0, z1)], F.fn(), -0.12, -0.10, m["planks"], rand=0.3)
            for i in range(5):
                if self.burning and rng.random() < 0.5:
                    continue
                ua = u0 + 0.05 + (u1 - u0 - 0.1) * i / 5
                KG.box(tm, F.p(ua + (u1 - u0 - 0.1) / 10, (z0 + z1) / 2, -0.07), ((u1 - u0 - 0.1) / 5 - 0.008, 0.04, z1 - z0 - 0.06),
                       m["planks"], axes=(F.U, -F.N, Z), rand=rng.random())
            for uu in (u0 - 0.04, u1 + 0.04):
                beam(tm, F.p(uu, z0 - 0.05, 0.0), F.p(uu, z1 + 0.05, 0.0), 0.08, 0.08, m["timber"], up=F.N)
            beam(tm, F.p(u0 - 0.1, z1 + 0.05, 0.0), F.p(u1 + 0.1, z1 + 0.05, 0.0), 0.1, 0.1, m["timber"], up=F.N)

    def _hoist(self):
        fr = self.frames()
        F, L, _, _ = fr[self.front_id()]
        m = self.mats
        apex = self.he + self.s * self.tp
        zb = apex - 0.55
        tm = self.parts["timber"]
        beam(tm, F.p(L / 2, zb, -0.4), F.p(L / 2, zb, 1.15), 0.2, 0.22, m["charred"] if self.burning else m["timber"],
             up=F.U)
        if not self.burning:
            KG.lathe(tm, [(0.0, -0.03), (0.11, -0.03), (0.11, 0.03), (0.0, 0.03)], F.p(L / 2, zb - 0.18, 1.0), m["timber"],
                     segments=12, axis_M=_basis(F.N, Z, F.U))
            beam(tm, F.p(L / 2, zb - 0.1, 1.0), F.p(L / 2, zb - 0.26, 1.0), 0.03, 0.03, m["iron"], up=F.U)
            beam(self.parts["props"], F.p(L / 2, zb - 0.2, 1.08), F.p(L / 2, self.he - 0.6, 1.08), 0.025, 0.025,
                 m["linen"], up=F.U)
            KG.box(self.parts["props"], F.p(L / 2, self.he - 0.66, 1.08), (0.04, 0.12, 0.1), m["iron"],
                   axes=(F.U, -F.N, Z))

    # ------------------------------------------------------------------ cross gable (inn)
    def _cross_gable(self):
        cg = self.spec["cross_gable"]
        m, rng = self.mats, self.rng
        cw, proj = cg["w"], cg["proj"]
        D = self.Dc / 2
        t = self.t
        s2 = cw / 2
        apex = self.he + s2 * self.tp
        yF = -D - proj
        Ff = KG.WallFrame((-cw / 2, yF, 0), (1, 0, 0), (0, -1, 0))
        prof = [(0, 0), (cw, 0), (cw, self.he), (cw / 2, apex), (0, self.he)]
        up1 = self.ffl + self.cfg["levels"]["storey"] + 0.95
        ops = [self.op("door", 0.0), self.op("W1", 0.0, z0=up1), self.op("W3", 0.0, z0=self.he + 0.4)]
        KG.wall_with_openings(self.parts["walls"], Ff, cw, prof, t, [self._rect(cw, o) for o in ops], m["stone_wall"])
        self._plinth(Ff, cw, ops)
        for o in ops:
            self._opening(Ff, cw, o)
        Fl = KG.WallFrame((-cw / 2, -D, 0), (0, -1, 0), (-1, 0, 0))
        Fr = KG.WallFrame((cw / 2, yF + t, 0), (0, 1, 0), (1, 0, 0))
        for Fs in (Fl, Fr):
            KG.wall_with_openings(self.parts["walls"], Fs, proj - t, [(0, 0), (proj - t, 0), (proj - t, self.he), (0, self.he)],
                                  t, [], m["stone_wall"])
        X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
        self._quoin_column((-cw / 2, yF, 0), X, -Y, Y, -X, self.he)
        self._quoin_column((cw / 2, yF, 0), -X, -Y, Y, X, self.he)
        self.front_frame_override = (Ff, cw)
        # wing roof (ridge along Y), pieces under the main roof are removed
        main_top = lambda yabs: KR.roof_top_z(yabs, self.s, self.he, self.pitch, self.cfg)
        wing_top = lambda xabs: KR.roof_top_z(xabs, s2, self.he, self.pitch, self.cfg)
        y_end = -D + s2 + 0.25
        ML = KR.ML_from((0, 0, 0), (0, 1, 0), (-1, 0, 0))

        def wing_skip(p):
            return p.y > -D - 0.1 and abs(p.x) < self.Wc / 2 and p.z < main_top(abs(p.y)) + 0.01

        KR.gable_roof(self.parts, ML, yF, y_end, s2, self.he, self.pitch, self.cfg["roof"]["eave_overhang"],
                      self.cfg["roof"]["verge_overhang"], self.cfg, rng, m, skip=wing_skip, state=self.state,
                      stats=self.stats)
        self.skip_fns.append(lambda p: p.y < 0 and abs(p.x) < s2 + 0.45 and p.y < -D + s2 + 0.3
                             and p.z < wing_top(abs(p.x)) - 0.005)

    # ------------------------------------------------------------------ dormer
    def _dormer(self, xd):
        dc = self.cfg["dormer"]
        m, rng = self.mats, self.rng
        w, fh = dc["w"], dc["front_h"]
        dp = dc["pitch_deg"]
        D = self.Dc / 2
        yf = -D + 0.55
        zb = KR.roof_top_z(D - 0.55, self.s, self.he, self.pitch, self.cfg)
        apex = zb + fh + (w / 2) * math.tan(math.radians(dp))
        F = KG.WallFrame((xd - w / 2, yf, 0), (1, 0, 0), (0, -1, 0))
        prof = [(0, zb - 0.35), (w, zb - 0.35), (w, zb + fh), (w / 2, apex), (0, zb + fh)]
        o = self.op("W2", 0.0, z0=zb + 0.22)
        KG.wall_with_openings(self.parts["walls"], F, w, prof, 0.2, [self._rect(w, o)], m["stone_wall"])
        self._opening(F, w, o)
        yb = yf + fh / self.tp
        for side in (-1, 1):
            xc = xd + side * (w / 2 - 0.04)
            KG.flat_prism(self.parts["timber"], [(yf + 0.02, zb - 0.05), (yb + 0.05, zb + fh), (yf + 0.02, zb + fh)],
                          lambda u, v, d, xc=xc: Vector((xc + d, u, v)), -0.03, 0.03, m["planks"], rand=rng.random())
        ML = KR.ML_from((xd, 0, 0), (0, 1, 0), (-1, 0, 0))
        main_top = lambda yabs: KR.roof_top_z(yabs, self.s, self.he, self.pitch, self.cfg)
        KR.gable_roof(self.parts, ML, yf - 0.02, yb + 0.35, w / 2, zb + fh, dp, 0.16, 0.22, self.cfg, rng, m,
                      skip=lambda p: p.y > yf + 0.05 and p.z < main_top(abs(p.y)) + 0.01, state=self.state,
                      stats=self.stats)
        self.excl.append(((xd - w / 2 - 0.03, yf + 0.04, zb - 0.6), (xd + w / 2 + 0.03, yb + 0.4, apex + 0.5)))

    # ------------------------------------------------------------------ chimneys
    def _chimney(self, where):
        cc = self.cfg["chimney"]
        m, rng = self.mats, self.rng
        pw, pd = cc["plan"]
        top_off = (self.cfg["roof"]["rafter_section"][1] + self.cfg["roof"]["batten_section"][1]) / math.cos(math.radians(self.pitch))
        ztop = self.ridge_z + top_off + max(cc["above_ridge_min"], 0.65)
        cm = self.parts["chimney"]
        W, D = self.Wc / 2, self.Dc / 2
        if where in ("left", "right"):
            sx = -1 if where == "left" else 1
            cx = sx * (W - pd / 2 + 0.02)
            c0 = Vector((cx, 0.0, self.he - 0.3))
            size = (pd, pw)
            zbot = self.he - 0.3
            KG.box(cm, (cx, 0, (zbot + ztop) / 2), (pd, pw, ztop - zbot), m["stone_wall"], rand=rng.random(), uv_scale=2.4)
            flash_z = self.ridge_z + top_off - 0.05
        else:
            sy = -1 if where == "side_right" else 1
            cx = self.Wc * 0.08
            cy = sy * (D + pd / 2 - 0.02)
            # lower stack wider up to the eave, shoulder, then flue stack
            KG.box(cm, (cx, cy + sy * 0.04, self.he / 2), (pw + 0.3, pd + 0.08, self.he), m["stone_wall"],
                   rand=rng.random(), uv_scale=2.4)
            KG.box(cm, (cx, cy + sy * 0.04, self.he + 0.06), (pw + 0.36, pd + 0.16, 0.12), m["stone_dressed"],
                   rand=rng.random())
            KG.box(cm, (cx, cy, (self.he + ztop) / 2), (pw, pd, ztop - self.he), m["stone_wall"], rand=rng.random(),
                   uv_scale=2.4)
            c0 = Vector((cx, cy, 0))
            size = (pw, pd)
            flash_z = None
        # cap slab with drip, pots
        sx_, sy_ = (size[0], size[1])
        KG.box(cm, (c0.x, c0.y, ztop + 0.06), (sx_ + 2 * cc["cap_slab_overhang"], sy_ + 2 * cc["cap_slab_overhang"], 0.12),
               m["stone_dressed"], rand=rng.random())
        npots = cc["pots"][1] if self.spec["size_class"] == "L" else cc["pots"][0]
        for k in range(npots):
            off = 0.0 if npots == 1 else (-0.2 if k == 0 else 0.2)
            pos = Vector((c0.x, c0.y, ztop + 0.12))
            if where in ("left", "right"):
                pos.y += off
            else:
                pos.x += off
            hgt = rng.uniform(0.34, 0.44)
            KG.lathe(cm, [(0.115, 0), (0.125, 0.04), (0.105, hgt * 0.75), (0.125, hgt * 0.9), (0.125, hgt),
                          (0.09, hgt), (0.09, hgt * 0.5)], pos, m["clay"], segments=14, rand=rng.random(), cap_top=False)
        if flash_z is not None:
            KG.box(cm, (c0.x, 0, flash_z), (pd + 0.04, pw + 0.04, 0.07), m["lead"])
        lo = Vector((c0.x - size[0] / 2 - 0.05, c0.y - size[1] / 2 - 0.05, -1))
        hi = Vector((c0.x + size[0] / 2 + 0.05, c0.y + size[1] / 2 + 0.05, ztop + 1))
        if where not in ("left", "right"):
            lo.x -= 0.2
            hi.x += 0.2
        self.excl.append((tuple(lo), tuple(hi)))
        self.fx.append(("SMOKE", Vector((c0.x, c0.y, ztop + 0.6))))
        self.stats["chimney_top_z"] = round(ztop, 3)

    # ------------------------------------------------------------------ lean-to (house_c)
    def _lean_to(self):
        lt = self.spec["lean_to"]
        m, rng = self.mats, self.rng
        lw = lt["w"]
        tl = 0.45
        W = self.Wc / 2
        yl = self.Dc / 2 - 0.5
        pl = 30.0
        tpl = math.tan(math.radians(pl))
        hl = 2.1
        zu = lambda dx: hl + (lw - dx) * tpl  # rafter underside height at distance dx from main gable face
        Fo = KG.WallFrame((W + lw, -yl, 0), (0, 1, 0), (1, 0, 0))
        KG.wall_with_openings(self.parts["walls"], Fo, 2 * yl, [(0, 0), (2 * yl, 0), (2 * yl, hl), (0, hl)], tl,
                              [self._rect(2 * yl, self.op("W3", 0.0, z0=1.2))], m["stone_wall"])
        self._opening(Fo, 2 * yl, self.op("W3", 0.0, z0=1.2))
        Ls = lw - tl
        Fs = KG.WallFrame((W, -yl, 0), (1, 0, 0), (0, -1, 0))
        dop = self.op("door2", 0.0)
        KG.wall_with_openings(self.parts["walls"], Fs, Ls, [(0, 0), (Ls, 0), (Ls, zu(Ls)), (0, zu(0))], tl,
                              [self._rect(Ls, dop)], m["stone_wall"])
        self._opening(Fs, Ls, dop)
        self._plinth(Fs, Ls, [dop])
        Fn = KG.WallFrame((W + Ls, yl, 0), (-1, 0, 0), (0, 1, 0))
        KG.wall_with_openings(self.parts["walls"], Fn, Ls, [(0, 0), (Ls, 0), (Ls, zu(0)), (0, zu(Ls))], tl, [],
                              m["stone_wall"])
        X, Y = Vector((1, 0, 0)), Vector((0, 1, 0))
        self._quoin_column((W + lw, -yl, 0), -X, -Y, Y, X, hl)
        self._quoin_column((W + lw, yl, 0), -X, Y, -Y, X, hl)
        ML = KR.ML_from((W, 0, 0), (0, 1, 0), (1, 0, 0))
        KR.gable_roof(self.parts, ML, -yl, yl, lw, hl, pl, 0.35, 0.25, self.cfg, rng, m, sides=(1,), state=self.state,
                      ridge=False, stats=self.stats)
        top = KR.roof_top_z(0.0, lw, hl, pl, self.cfg) + 0.02
        if not self.burning:
            KG.box(self.parts["roof_timber"], (W + 0.08, 0, top + 0.03), (0.2, 2 * yl + 0.5, 0.025), m["lead"])

    # ------------------------------------------------------------------ porches
    def _porch(self, kind):
        fr = self.frames()
        fid = self.front_id()
        F, L, _, _ = fr[fid]
        door = [o for o in self.layout_cache[fid] if o["kind"] == "door"][0]
        uc = L / 2 + door["uc"]
        m, rng = self.mats, self.rng
        pc = self.cfg["porch"]
        pm = self.parts["porch"]
        tmat = m["charred"] if self.burning else m["timber"]
        if kind == "gabled":
            dep, half = pc["depth"], 0.95
            ez = pc["eave_z"]
            for su in (-1, 1):
                KG.box(pm, F.p(uc + su * half, 0.08, dep - 0.1), (0.3, 0.3, 0.16), m["stone_dressed"], axes=(F.U, -F.N, Z))
                beam(pm, F.p(uc + su * half, 0.16, dep - 0.1), F.p(uc + su * half, ez, dep - 0.1), pc["post"], pc["post"],
                     tmat, up=F.N)
                beam(pm, F.p(uc + su * half, ez + 0.06, -0.1), F.p(uc + su * half, ez + 0.06, dep + 0.05), 0.12, 0.14,
                     tmat, up=F.U)
                beam(pm, F.p(uc + su * half, ez - 0.5, dep - 0.1), F.p(uc + su * half, ez, dep - 0.55), 0.09, 0.09, tmat,
                     up=F.U)
            beam(pm, F.p(uc - half - 0.1, ez + 0.06, dep - 0.1), F.p(uc + half + 0.1, ez + 0.06, dep - 0.1), 0.14, 0.14,
                 tmat, up=F.N)
            ptp = math.tan(math.radians(pc["pitch_deg"]))
            beam(pm, F.p(uc, ez + 0.12, dep - 0.1), F.p(uc, ez + half * ptp, dep - 0.1), 0.1, 0.1, tmat, up=F.N)
            if self.burning:
                return
            ML = KR.ML_from(F.p(uc, 0, 0), F.N, F.U)
            front_skip = lambda p: (p - F.O).dot(F.N) < 0.03
            KR.gable_roof(self.parts, ML, -0.05, dep, half + 0.08, ez + 0.13, pc["pitch_deg"], 0.2, 0.25, self.cfg, rng, m,
                          skip=front_skip, state=self.state, stats=self.stats)
        elif kind == "pent":
            half = 1.05
            out = 0.95
            pp = 26.0
            zlow = door["z0"] + door["h"] + 0.62
            for su in (-1, 1):
                beam(pm, F.p(uc + su * (half - 0.15), zlow - 0.75, 0.0), F.p(uc + su * (half - 0.15), zlow + 0.02, out - 0.05),
                     0.09, 0.09, tmat, up=F.U)
            if self.burning:
                return
            ML = KR.ML_from(F.p(uc, 0, 0), F.U, F.N)
            KR.gable_roof(self.parts, ML, -half, half, out, zlow, pp, 0.12, 0.12, self.cfg, rng, m, sides=(1,),
                          ridge=False, state=self.state, stats=self.stats)
            topz = KR.roof_top_z(0.0, out, zlow, pp, self.cfg)
            KG.box(pm, F.p(uc, topz + 0.04, 0.08), (2 * half + 0.3, 0.16, 0.025), m["lead"], axes=(F.U, -F.N, Z))
        # bench beside the door
        bu = uc + (1.5 if uc + 1.5 < L - 0.4 else -1.5)
        self._bench(F, bu, 0.45)

    def _bench(self, F, u, d):
        m, rng = self.mats, self.rng
        pm = self.parts["props"]
        if self.burning:
            beam(pm, F.p(u - 0.5, 0.05, d), F.p(u + 0.4, 0.2, d + 0.1), 0.3, 0.05, m["charred"], up=Z)
            return
        KG.box(pm, F.p(u, 0.44, d), (1.3, 0.34, 0.06), m["planks"], axes=(F.U, -F.N, Z), rand=rng.random())
        for su in (-0.5, 0.5):
            KG.box(pm, F.p(u + su, 0.21, d), (0.07, 0.3, 0.42), m["planks"], axes=(F.U, -F.N, Z), rand=rng.random())

    # ------------------------------------------------------------------ shop awning + counter
    def _awning(self):
        fr = self.frames()
        F, L, _, _ = fr[self.front_id()]
        bay = [o for o in self.layout_cache[self.front_id()] if o["kind"] == "bay"][0]
        u0, u1, z0, z1 = self._rect(L, bay)
        m, rng = self.mats, self.rng
        am = self.parts["props"]
        a0, a1 = u0 - 0.35, u1 + 0.35
        zt, zf, dep = z1 + 0.5, z1 - 0.02, 1.35
        beam(self.parts["timber"], F.p(a0 - 0.05, zt + 0.04, 0.05), F.p(a1 + 0.05, zt + 0.04, 0.05), 0.08, 0.1,
             m["timber"], up=F.N)
        # counter shelf (drop-down stall board) on iron brackets
        cz = z0 - 0.06
        KG.box(am, F.p((u0 + u1) / 2, cz, 0.3), (u1 - u0 + 0.1, 0.55, 0.05), m["planks"] if not self.burning else m["charred"],
               axes=(F.U, -F.N, Z), rand=rng.random())
        for uu in (u0 + 0.15, u1 - 0.15):
            beam(am, F.p(uu, cz - 0.45, 0.02), F.p(uu, cz - 0.03, 0.5), 0.03, 0.03, m["iron"], up=F.U)
        if not self.burning:
            for k, uu in enumerate((u0 + 0.45, (u0 + u1) / 2, u1 - 0.45)):
                self._crate(F, uu, cz + 0.025, 0.3, (0.45, 0.32, 0.22), produce=["apple", "cabbage", "carrot"][k])
        if self.burning:
            for i in range(3):
                uu = rng.uniform(a0, a1)
                beam(am, F.p(uu, zt, 0.05), F.p(uu + rng.uniform(-0.1, 0.1), zt - rng.uniform(0.4, 0.9), 0.15),
                     0.18, 0.01, m["charred"], up=F.N)
            return
        nu, nd = 14, 5
        grid = {}
        for i in range(nu + 1):
            for j in range(nd + 1):
                uu = a0 + (a1 - a0) * i / nu
                dd = dep * j / nd
                sag = 0.05 * math.sin(math.pi * j / nd) * (0.6 + 0.4 * abs(math.sin(math.pi * i / 2)))
                zz = zt + (zf - zt) * j / nd - sag
                grid[i, j] = F.p(uu, zz, dd + 0.05)
        for i in range(nu):
            for j in range(nd):
                am.poly([grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]],
                        m["linen"] if i % 2 == 0 else m["wool_green"],
                        uvs=[(i / nu, j / nd), ((i + 1) / nu, j / nd), ((i + 1) / nu, (j + 1) / nd), (i / nu, (j + 1) / nd)])
        # scalloped valance
        nsc = 9
        for i in range(nsc):
            ua = a0 + (a1 - a0) * i / nsc
            ub = a0 + (a1 - a0) * (i + 1) / nsc
            dz = dep + 0.05
            am.poly([F.p(ua, zf, dz), F.p(ub, zf, dz), F.p(ub, zf - 0.13, dz), F.p((ua + ub) / 2, zf - 0.22, dz),
                     F.p(ua, zf - 0.13, dz)], m["linen"] if (i * 14 // nsc) % 2 == 0 else m["wool_green"],
                    uvs=[(i / nsc, 0), ((i + 1) / nsc, 0), ((i + 1) / nsc, 0.1), ((i + 0.5) / nsc, 0.15), (i / nsc, 0.1)])
        beam(am, F.p(a0, zf - 0.02, dep + 0.06), F.p(a1, zf - 0.02, dep + 0.06), 0.035, 0.035, m["timber"], up=F.N)
        for uu in (a0 + 0.02, a1 - 0.02):
            beam(am, F.p(uu, zt - 0.55, 0.02), F.p(uu, zf - 0.02, dep + 0.05), 0.025, 0.025, m["iron"], up=F.U)

    # ------------------------------------------------------------------ signboard (no text)
    def _sign(self, emblem):
        fr = self.frames()
        if self.key == "inn":
            F, L, _, _ = fr["S"]
            u = L / 2 - 2.75
            zs = 3.45
        else:
            F, L, _, _ = fr[self.front_id()]
            u = L / 2 + 2.75
            zs = 3.0
        m, rng = self.mats, self.rng
        sm = self.parts["signage"]
        reach = 1.1
        beam(sm, F.p(u, zs, -0.05), F.p(u, zs, reach), 0.045, 0.06, m["iron"], up=F.U)
        beam(sm, F.p(u, zs - 0.55, 0.0), F.p(u, zs - 0.02, reach * 0.65), 0.03, 0.03, m["iron"], up=F.U)
        KG.box(sm, F.p(u, zs - 0.25, 0.01), (0.12, 0.03, 0.7), m["iron"], axes=(F.U, -F.N, Z))
        bw, bh, bt = 0.82, 0.64, 0.05
        dc = 0.2 + bw / 2
        if self.burning:
            # fallen, charred board at the wall foot; chains still hanging
            for dd in (dc - bw / 2 + 0.06, dc + bw / 2 - 0.06):
                beam(sm, F.p(u, zs, dd), F.p(u, zs - 0.35, dd), 0.012, 0.012, m["iron"], up=F.U)
            KG.box(sm, F.p(u + 0.3, 0.06, 0.9), (bt, bw, bh), m["charred"], axes=(Z, F.N, F.U), rand=0.2)
            return
        ztop = zs - 0.16
        for dd in (dc - bw / 2 + 0.06, dc + bw / 2 - 0.06):
            beam(sm, F.p(u, zs, dd), F.p(u, ztop, dd), 0.012, 0.012, m["iron"], up=F.U)
        zc = ztop - bh / 2
        # board: painted panel + oak frame, emblem raised on both faces
        KG.box(sm, F.p(u, zc, dc), (bt, bw - 0.08, bh - 0.08), m["sign_paint"], axes=(F.U, F.N, Z), rand=0.4)
        for (a, b2, horiz) in ((-1, 0, True), (1, 0, True), (0, -1, False), (0, 1, False)):
            if horiz:
                KG.box(sm, F.p(u, zc + a * (bh / 2 - 0.03), dc), (bt + 0.012, bw, 0.06), m["timber"], axes=(F.U, F.N, Z),
                       rand=rng.random())
            else:
                KG.box(sm, F.p(u, zc, dc + b2 * (bw / 2 - 0.03)), (bt + 0.012, 0.06, bh - 0.12), m["timber"],
                       axes=(F.U, F.N, Z), rand=rng.random())
        outlines = EMBLEMS.get(emblem, [])
        sc = min(bw, bh) * 0.78
        for side in (-1, 1):
            for ol in outlines:
                pts = [((x - 0.5) * sc * (-side), (y - 0.5) * sc) for (x, y) in ol]
                fn = lambda a, b, d, side=side: F.p(u + side * d, zc + b, dc + a)
                KG.flat_prism(sm, pts, fn, bt / 2 - 0.002, bt / 2 + 0.014, m["gold"], rand=0.6)
        self.stats["sign_emblem"] = emblem

    # ------------------------------------------------------------------ props
    def _barrel(self, pos, scale=1.0):
        m, rng = self.mats, self.rng
        pm = self.parts["props"]
        h = 0.86 * scale
        r0, r1 = 0.27 * scale, 0.31 * scale
        prof = [(r0, 0), ((r0 + r1) / 2, h * 0.2), (r1, h * 0.5), ((r0 + r1) / 2, h * 0.8), (r0, h)]
        KG.lathe(pm, prof, pos, m["charred"] if self.burning else m["planks"], segments=18, rand=rng.random())
        for zz in (0.08, 0.28, 0.72, 0.92):
            rr = r0 + (r1 - r0) * math.sin(math.pi * zz) + 0.006
            KG.lathe(pm, [(rr, h * zz - 0.025), (rr, h * zz + 0.025)], pos, m["iron"], segments=18, cap_bottom=False,
                     cap_top=False)

    def _crate(self, F, u, z, d, size, produce=None):
        m, rng = self.mats, self.rng
        pm = self.parts["props"]
        sx, sy, sz = size
        c = F.p(u, z + sz / 2, d)
        ax = (F.U, -F.N, Z)
        for side in (-1, 1):
            for k in range(3):
                zz = -sz / 2 + sz * (k + 0.5) / 3
                KG.box(pm, c + F.N * (side * (sy / 2 - 0.01)) + Z * zz, (sx, 0.02, sz / 3 - 0.012), m["planks"], axes=ax,
                       rand=rng.random())
                KG.box(pm, c + F.U * (side * (sx / 2 - 0.01)) + Z * zz, (0.02, sy - 0.04, sz / 3 - 0.012), m["planks"],
                       axes=ax, rand=rng.random())
        KG.box(pm, c - Z * (sz / 2 - 0.01), (sx - 0.04, sy - 0.04, 0.02), m["planks"], axes=ax, rand=rng.random())
        if produce:
            n = 7 if produce != "cabbage" else 4
            for i in range(n):
                rr = 0.045 if produce == "apple" else (0.075 if produce == "cabbage" else 0.03)
                pu = rng.uniform(-sx / 2 + rr + 0.03, sx / 2 - rr - 0.03)
                pd = rng.uniform(-sy / 2 + rr + 0.03, sy / 2 - rr - 0.03)
                pc = c + F.U * pu - F.N * pd + Z * (sz / 2 - rr * 0.4)
                if produce == "carrot":
                    beam(pm, pc, pc + F.U * 0.14 + Z * 0.02, 0.035, 0.035, m["prop"], rand=KM.palette_value("carrot"))
                else:
                    KG.lathe(pm, [(0.0, -rr), (rr * 0.8, -rr * 0.6), (rr, 0), (rr * 0.8, rr * 0.6), (0.0, rr)], pc,
                             m["prop"], segments=8, rand=KM.palette_value(produce))

    def _sack(self, pos):
        rng = self.rng
        h = rng.uniform(0.5, 0.65)
        KG.lathe(self.parts["props"], [(0.0, 0), (0.2, 0.02), (0.24, h * 0.35), (0.2, h * 0.75), (0.07, h * 0.88),
                                       (0.09, h), (0.0, h)], pos, self.mats["linen"], segments=10, rand=rng.random())

    def _woodpile(self, F, u0, u1, d):
        m, rng = self.mats, self.rng
        if self.burning:
            return
        rows = 4
        R = 0.075
        for r in range(rows):
            n = int((u1 - u0) / (2 * R)) - r
            for i in range(n):
                uu = u0 + R + r * R + i * 2 * R + rng.uniform(-0.01, 0.01)
                zz = R + r * 1.75 * R
                c = F.p(uu, zz, d)
                KG.lathe(self.parts["props"], [(R * rng.uniform(0.85, 1.05), -0.25), (R * rng.uniform(0.85, 1.05), 0.25)],
                         c, m["timber"], segments=7, rand=rng.random(),
                         axis_M=_basis(F.U, Z, F.N))

    def _props(self):
        k = self.key
        fr = self.frames()
        if hasattr(self, "front_frame_override") and k == "inn":
            Fw, Lw = self.front_frame_override
        F, L, _, _ = fr[self.front_id()]
        if k == "inn":
            Fs, Ls, _, _ = fr["S"]
            self._bench(Fs, Ls / 2 + 4.3, 0.45)
            self._barrel(Fs.p(Ls / 2 + 2.75, 0, 0.45))
            self._barrel(Fs.p(Ls / 2 + 2.6, 0, 1.05), 0.92)
            self._woodpile(fr["E"][0], 0.5, 1.8, 0.35)
            self._lantern(Fw, Lw / 2 - 0.95, 2.55)
            self._flower_box(Fs, Ls / 2 - 3.7 - 0.4, Ls / 2 - 3.7 + 0.4, self.ffl + 0.95)
            self._flower_box(Fs, Ls / 2 + 3.7 - 0.4, Ls / 2 + 3.7 + 0.4, self.ffl + 0.95)
        elif k == "shop":
            self._barrel(F.p(L / 2 + 0.6, 0, 0.5))
            self._sack(F.p(L / 2 + 2.6, 0, 0.45))
            self._sack(F.p(L / 2 + 2.85, 0, 0.8))
            self._crate(F, L / 2 - 2.9, 0, 0.55, (0.5, 0.4, 0.35), produce="apple")
            self._lantern(F, L / 2 + 1.0, 2.6)
        elif k == "house_a":
            self._woodpile(F, 0.6, 1.6, 0.35)
            self._barrel(F.p(L / 2 + 2.6, 0, 0.45), 0.8)
        elif k == "house_b":
            self._woodpile(fr["S"][0], 1.0, 2.6, 0.35)
        elif k == "house_c":
            self._barrel(F.p(L / 2 - 1.8, 0, 0.45), 0.85)
            self._sack(F.p(L / 2 + 0.0, 0, 0.5))
        elif k == "storage":
            self._crate(F, 0.55, 0, 0.55, (0.6, 0.5, 0.45))
            self._crate(F, 0.62, 0.45, 0.55, (0.5, 0.42, 0.35))
            self._sack(F.p(L - 0.8, 0, 0.5))
            self._sack(F.p(L - 0.45, 0, 0.75))
            self._barrel(F.p(L - 1.3, 0, 0.5))

    def _lantern(self, F, u, z):
        m = self.mats
        sm = self.parts["signage"]
        beam(sm, F.p(u, z, 0.0), F.p(u, z, 0.35), 0.025, 0.025, m["iron"], up=F.U)
        c = F.p(u, z - 0.22, 0.35)
        KG.box(sm, c, (0.16, 0.16, 0.24), m["lamp"], axes=(F.U, -F.N, Z))
        KG.box(sm, c + Z * 0.14, (0.2, 0.2, 0.04), m["iron"], axes=(F.U, -F.N, Z))
        KG.box(sm, c - Z * 0.13, (0.18, 0.18, 0.025), m["iron"], axes=(F.U, -F.N, Z))
        if not self.burning:
            self.lights.append(("LANTERN", self.M @ c, (1.0, 0.7, 0.35), 25.0))

    # ------------------------------------------------------------------ interior / roof / anchors
    def _interior(self):
        m = self.mats
        W, D, t = self.Wc / 2, self.Dc / 2, self.t
        KG.box(self.parts["interior"], (0, 0, self.ffl - 0.05), (2 * (W - t), 2 * (D - t), 0.1),
               m["charred"] if self.burning else m["planks"], rand=0.5)
        if self.spec["storeys"] == 2 and not self.burning:
            KG.box(self.parts["interior"], (0, 0, self.ffl + self.cfg["levels"]["storey"] - 0.1),
                   (2 * (W - t), 2 * (D - t), 0.2), m["planks"], rand=0.6)
        if self.burning:
            rng = self.rng
            for i in range(5):
                a = Vector((rng.uniform(-W + 1, W - 1), rng.uniform(-D + 1, D - 1), self.ffl + 0.1))
                b = a + Vector((rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(0.2, 1.4)))
                beam(self.parts["interior"], a, b, 0.09, 0.15, m["charred"], rand=rng.random())
            KG.box(self.parts["interior"], (0, 0, self.ffl + 0.02), (2 * (W - t) - 0.4, 2 * (D - t) - 0.4, 0.02),
                   m["glow"], rand=0.5)
            if self.state == "burning":
                self.lights.append(("FIRE", self.M @ Vector((0, 0, self.he * 0.6)), (1.0, 0.38, 0.08),
                                    900.0 * (self.Wc * self.Dc) / 50.0))

    def _main_roof(self):
        rc = self.cfg["roof"]

        def skip(p):
            for lo, hi in self.excl:
                if lo[0] <= p.x <= hi[0] and lo[1] <= p.y <= hi[1] and lo[2] <= p.z <= hi[2]:
                    return True
            return any(f(p) for f in self.skip_fns)

        res = KR.gable_roof(self.parts, Matrix.Identity(4), -self.Wc / 2, self.Wc / 2, self.s, self.he, self.pitch,
                            rc["eave_overhang"], rc["verge_overhang"], self.cfg, self.rng, self.mats, skip=skip,
                            state=self.state, stats=self.stats)
        self.stats["ridge_z"] = round(res["ridge_z"], 3)
        self.stats["eave_z"] = round(self.he, 3)
        if self.burning:
            self.fx.append(("SMOKE", Vector((0, 0, self.ridge_z + 1.0))))

    def _anchors_collision(self):
        fr = self.frames()
        fid = self.front_id()
        if self.key == "inn":
            F, L = self.front_frame_override
            door = {"uc": 0.0}
        else:
            F, L, _, _ = fr[fid]
            door = [o for o in self.layout_cache[fid] if o["kind"] in ("door", "ddoor")][0]
        uc = L / 2 + door["uc"]
        ext = self.M @ F.p(uc, 0.0, 0.6)
        intp = self.M @ F.p(uc, self.ffl, -self.t - 0.6)
        facing_in = (self.M.to_3x3() @ (-F.N)).normalized()
        rmap = self.spec["runtime_maps"][0]
        blocked = self.burning
        self.anchor_offsets = {"ext_from_facade_m": round((F.p(uc, 0.0, 0.6) - F.p(uc, 0.0, 0.0)).dot(F.N), 4),
                               "int_from_inner_face_m": round((F.p(uc, 0, -self.t) - F.p(uc, 0, -self.t - 0.6)).dot(F.N), 4),
                               "ext_z": round(ext.z, 4), "int_z": round(intp.z, 4), "ffl": self.ffl}
        self.anchors.append((f"ANC_{self.bid}_DOOR_MAIN_EXT", ext, facing_in,
                             {"anchor_kind": "door", "links_to": f"ANC_{self.bid}_DOOR_MAIN_INT", "runtime_map": rmap,
                              "runtime_id": "CANDIDATE_UNMAPPED", "door_state": "blocked" if blocked else "open"}))
        self.anchors.append((f"ANC_{self.bid}_DOOR_MAIN_INT", intp, -facing_in,
                             {"anchor_kind": "door", "links_to": f"ANC_{self.bid}_DOOR_MAIN_EXT", "runtime_map": rmap,
                              "runtime_id": "CANDIDATE_UNMAPPED", "door_state": "blocked" if blocked else "open"}))
        W, D = self.Wc / 2, self.Dc / 2
        self.collisions.append((f"COL_{self.bid}_shell", Vector((0, 0, 1.25)), (2 * W, 2 * D, 2.5)))
        if self.spec.get("cross_gable"):
            cg = self.spec["cross_gable"]
            self.collisions.append((f"COL_{self.bid}_wing", Vector((0, -D - cg["proj"] / 2, 1.25)),
                                    (cg["w"], cg["proj"], 2.5)))
        if self.spec.get("lean_to"):
            lw = self.spec["lean_to"]["w"]
            self.collisions.append((f"COL_{self.bid}_leanto", Vector((W + lw / 2, 0, 1.25)), (lw, 2 * D - 1.0, 2.5)))

    # ------------------------------------------------------------------ emit
    def emit(self):
        root = bpy.data.collections.new(f"BLD_{self.bid}_{self.state.upper()}")
        (self.coll_root or bpy.context.scene.collection).children.link(root)
        colls = {}
        objs = []
        for k, mb in self.parts.items():
            cname = PARTS[k][0]
            if cname not in colls:
                c = bpy.data.collections.new(f"{cname}_{self.bid}_{self.state}")
                root.children.link(c)
                colls[cname] = c
            ob = mb.to_object(colls[cname], merge=(k == "walls"))
            if ob:
                ob["lind_task"] = "LIND-BUILD-01"
                ob["status"] = "CANDIDATE_NOT_ART_APPROVED"
                ob["state_variant"] = self.state
                objs.append(ob)
        for cname in ("ANCHORS", "COLLISION"):
            c = bpy.data.collections.new(f"{cname}_{self.bid}_{self.state}")
            root.children.link(c)
            colls[cname] = c
        for name, pos, facing, props in self.anchors:
            e = bpy.data.objects.new(name, None)
            e.empty_display_type = "PLAIN_AXES"
            e.location = pos
            e.rotation_euler = (0, 0, math.atan2(-facing.x, facing.y))
            for kk, vv in props.items():
                e[kk] = vv
            colls["ANCHORS"].objects.link(e)
        for n_fx, (kind, p) in enumerate(self.fx):
            e = bpy.data.objects.new(f"ANC_{self.bid}_EVENT_FX{kind}{n_fx + 1:02d}", None)
            e.location = self.M @ p
            e["anchor_kind"] = "event"
            e["runtime_id"] = f"fx_{kind.lower()}_candidate"
            colls["ANCHORS"].objects.link(e)
        for name, c, size in self.collisions:
            me = bpy.data.meshes.new(name)
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
            bmesh.ops.translate(bm, vec=c, verts=bm.verts)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(name, me)
            ob.matrix_world = self.M
            ob.display_type = "WIRE"
            ob.hide_render = True
            colls["COLLISION"].objects.link(ob)
        for kind, pos, col, power in self.lights:
            ld = bpy.data.lights.new(f"LGT_{self.bid}_{kind}", "POINT")
            ld.color = col
            ld.energy = power
            ld.shadow_soft_size = 0.3 if kind == "LANTERN" else 1.5
            lo = bpy.data.objects.new(ld.name, ld)
            lo.location = pos
            root.objects.link(lo)
        self.objects = objs
        return objs


def _basis(xv, yv, zv):
    M = Matrix.Identity(3)
    for r in range(3):
        M[r][0], M[r][1], M[r][2] = xv[r], yv[r], zv[r]
    return M


# Emblem outlines in a unit square (no text): weathercock, pouch+leaf, harp
EMBLEMS = {
    "weathercock": [
        [(0.20, 0.52), (0.24, 0.60), (0.22, 0.68), (0.28, 0.66), (0.30, 0.74), (0.34, 0.67), (0.38, 0.72), (0.39, 0.63),
         (0.43, 0.56), (0.52, 0.52), (0.60, 0.56), (0.64, 0.70), (0.72, 0.84), (0.76, 0.70), (0.82, 0.74), (0.80, 0.58),
         (0.74, 0.46), (0.64, 0.38), (0.56, 0.36), (0.55, 0.30), (0.50, 0.30), (0.49, 0.36), (0.42, 0.37), (0.36, 0.44),
         (0.30, 0.47), (0.25, 0.47), (0.18, 0.48)],
        [(0.12, 0.24), (0.84, 0.24), (0.84, 0.28), (0.12, 0.28)],
        [(0.84, 0.18), (0.94, 0.26), (0.84, 0.34)],
        [(0.10, 0.18), (0.18, 0.26), (0.10, 0.34), (0.16, 0.26)],
    ],
    "pouch_leaf": [
        [(0.30, 0.18), (0.62, 0.18), (0.72, 0.30), (0.72, 0.46), (0.62, 0.58), (0.56, 0.62), (0.60, 0.68), (0.54, 0.70),
         (0.46, 0.70), (0.40, 0.68), (0.44, 0.62), (0.38, 0.58), (0.26, 0.46), (0.24, 0.30)],
        [(0.52, 0.70), (0.60, 0.80), (0.72, 0.86), (0.84, 0.86), (0.80, 0.76), (0.70, 0.70), (0.60, 0.68)],
    ],
    "harp": [
        [(0.30, 0.15), (0.40, 0.15), (0.40, 0.70), (0.52, 0.80), (0.70, 0.80), (0.74, 0.86), (0.50, 0.88), (0.30, 0.72)],
        [(0.40, 0.15), (0.74, 0.80), (0.70, 0.82), (0.36, 0.20)],
        [(0.46, 0.30), (0.48, 0.30), (0.48, 0.73), (0.46, 0.72)],
        [(0.54, 0.44), (0.56, 0.44), (0.56, 0.79), (0.54, 0.79)],
        [(0.62, 0.58), (0.64, 0.58), (0.64, 0.80), (0.62, 0.80)],
    ],
}


# ====================================================================== scene / render
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    KM.REPORT["loaded"].clear()
    KM.REPORT["missing"].clear()


def setup_render(cfg, res_x, res_y, samples):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.seed = 0
    sc.cycles.use_animated_seed = False
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 2
    try:
        sc.cycles.use_denoising = True
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 6
    sc.render.resolution_x, sc.render.resolution_y = res_x, res_y
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    world = bpy.data.worlds.new("W_lind_day")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (0.50, 0.62, 0.85, 1)
    bg.inputs[1].default_value = 0.85
    sc.world = world


def add_lighting(state):
    sun = bpy.data.lights.new("LGT_SUN", "SUN")
    if state == "peaceful":
        sun.energy = 4.6
        sun.color = (1.0, 0.88, 0.72)
    else:
        sun.energy = 0.9
        sun.color = (0.85, 0.55, 0.45)
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.12, 0.14, 1)
        bpy.context.scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.5
    sun.angle = math.radians(2.0)
    so = bpy.data.objects.new("LGT_SUN", sun)
    so.rotation_euler = (math.radians(48), 0, math.radians(35))  # sun from front-right, ~42 deg high
    bpy.context.scene.collection.objects.link(so)
    me = bpy.data.meshes.new("STG_ground")
    me.from_pydata([(-80, -80, 0), (80, -80, 0), (80, 80, 0), (-80, 80, 0)], [], [(0, 1, 2, 3)])
    g = bpy.data.objects.new("STG_ground_shadowcatcher", me)
    g.is_shadow_catcher = True
    bpy.context.scene.collection.objects.link(g)


def frame_camera(cfg, objs, res_x, res_y, margin=1.07):
    cam_cfg = cfg["camera"]
    el = math.radians(cam_cfg["elevation_deg"])
    az = math.radians(cam_cfg["azimuth_deg"])
    dirv = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    pts = []
    for ob in objs:
        if ob.type != "MESH" or ob.hide_render:
            continue
        pts.extend(ob.matrix_world @ Vector(c) for c in ob.bound_box)
    cen = sum(pts, Vector()) / len(pts)
    fwd = -dirv.normalized()
    right = fwd.cross(Z).normalized()
    upv = right.cross(fwd).normalized()
    xs = [(p - cen).dot(right) for p in pts]
    ys = [(p - cen).dot(upv) for p in pts]
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    mid = cen + right * ((max(xs) + min(xs)) / 2) + upv * ((max(ys) + min(ys)) / 2)
    cd = bpy.data.cameras.new("CAM_game27")
    cd.type = "ORTHO"
    cd.ortho_scale = max(w, h * res_x / res_y) * margin
    cd.clip_end = 500
    co = bpy.data.objects.new("CAM_game27", cd)
    co.location = mid + dirv * 120
    co.rotation_euler = fwd.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(co)
    bpy.context.scene.camera = co
    return {"elevation_deg": cam_cfg["elevation_deg"], "azimuth_deg": cam_cfg["azimuth_deg"],
            "ortho_scale": round(cd.ortho_scale, 4), "type": "ORTHO"}


def render_to(path):
    bpy.context.scene.render.filepath = path
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    return round(time.time() - t0, 1)


def mesh_stats(objs):
    tris = 0
    no_uv = []
    nonmanifold_walls = None
    for ob in objs:
        me = ob.data
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        if not me.uv_layers or me.uv_layers[0].name != "UVMap":
            no_uv.append(ob.name)
        if "_WALLS" in ob.name:
            bm = bmesh.new()
            bm.from_mesh(me)
            nonmanifold_walls = sum(1 for e in bm.edges if not e.is_manifold)
            bm.free()
    mats = sorted({ms.material.name for ob in objs for ms in ob.material_slots if ms.material})
    return {"tris": tris, "objects": len(objs), "meshes_without_UVMap": no_uv,
            "walls_nonmanifold_edges": nonmanifold_walls, "materials": mats, "material_count": len(mats)}


def slate_stats(objs):
    for ob in objs:
        if ob.name.split("_")[2:3] == ["SLATES"] or "_SLATES" in ob.name:
            n = len(ob.data.polygons)
            return {"slate_faces": n}
    return {}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--buildings", default="inn,shop,house_a,house_b,house_c,storage")
    ap.add_argument("--states", default="peaceful")
    ap.add_argument("--render", action="store_true")
    ap.add_argument("--lineup", action="store_true")
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--res", type=int, default=1280)
    ap.add_argument("--save-blend", action="store_true")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    cfg, info = kit_config.load_config(REPO)
    samples = a.samples or cfg["render"]["samples"]
    manifest = {"task_id": "LIND-BUILD-01", "status": "CANDIDATE_NOT_ART_APPROVED", "blender": bpy.app.version_string,
                "seed_base": kit_config.SEED_BASE, "contract": info, "samples": samples, "entries": []}
    jobs = [(b, s) for b in a.buildings.split(",") for s in a.states.split(",")]
    for (bk, st) in jobs:
        reset_scene()
        t0 = time.time()
        B = Building(bk, cfg, st)
        B.build()
        objs = B.emit()
        entry = {"building": bk, "bldg_id": B.bid, "state": st, "build_s": round(time.time() - t0, 1),
                 "dims": {"footprint_w": B.spec["w"], "footprint_d": B.spec["d"], "eave_z": round(B.he, 3),
                          "ridge_z": round(B.ridge_z, 3), "pitch_deg": B.pitch, "front": B.spec["front"]},
                 "stats": {k: v for k, v in B.stats.items() if not k.startswith("_")},
                 "slate_unique_dims": len(B.stats.get("_slate_dims", ())),
                 "mesh": mesh_stats(objs),
                 "anchors": [o.name for o in bpy.data.objects if o.name.startswith("ANC_")],
                 "anchor_offsets": B.anchor_offsets,
                 "walls": {w: {"L": round(v[1], 4), "corner_offset": (B.t if v[3] == "eaves" else 0.0),
                               "outer_len": round(v[1] + (2 * B.t if v[3] == "eaves" else 0.0), 4)}
                           for w, v in B.frames().items()},
                 "textures": {"loaded": list(KM.REPORT["loaded"]), "missing": list(KM.REPORT["missing"])},
                 "layout": {w: [{k: (round(v, 3) if isinstance(v, float) else v) for k, v in o.items()} for o in ol]
                            for w, ol in B.layout_cache.items()}}
        if a.render:
            rx, ry = a.res, int(a.res * 0.75)
            setup_render(cfg, rx, ry, samples)
            add_lighting(st)
            entry["camera"] = frame_camera(cfg, objs, rx, ry)
            png = os.path.join(a.out, f"{bk}_{st}_game27.png")
            entry["render_s"] = render_to(png)
            entry["render_png"] = os.path.basename(png)
            entry["render_sha256"] = sha256(png)
        if a.save_blend:
            bp = os.path.join(a.out, f"{bk}_{st}.blend")
            bpy.ops.wm.save_as_mainfile(filepath=bp, compress=True)
            entry["blend_sha256"] = sha256(bp)
        manifest["entries"].append(entry)
        print(f"[LIND-BUILD] {bk}/{st}: tris={entry['mesh']['tris']} slates={B.stats.get('slates')} "
              f"build={entry['build_s']}s render={entry.get('render_s')}", flush=True)
    if a.lineup:
        reset_scene()
        objs = []
        keys = a.buildings.split(",")
        diag = Vector((math.cos(math.radians(-45)), math.sin(math.radians(-45)), 0))
        pos = 0.0
        prev = 0.0
        for bk in keys:
            sp = kit_config.BUILDINGS[bk]
            r = 0.5 * math.hypot(sp["w"], sp["d"]) * 0.82
            pos += prev + r + 1.0
            B = Building(bk, cfg, "peaceful", offset=tuple(diag * pos))
            B.build()
            objs += B.emit()
            prev = r
        rx, ry = a.res, int(a.res * 0.5)
        setup_render(cfg, rx, ry, samples)
        add_lighting("peaceful")
        cam = frame_camera(cfg, objs, rx, ry, margin=1.04)
        png = os.path.join(a.out, "lineup_peaceful_game27.png")
        manifest["lineup"] = {"buildings": keys, "camera": cam, "render_s": render_to(png),
                              "render_png": os.path.basename(png), "render_sha256": sha256(png),
                              "tris_total": mesh_stats(objs)["tris"]}
    with open(os.path.join(a.out, "build_manifest.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1, ensure_ascii=False)
    print("[LIND-BUILD] manifest written", flush=True)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
