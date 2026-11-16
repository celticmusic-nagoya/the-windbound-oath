"""LIND-BUILD-01 PBR materials. CC0 Poly Haven maps (ledgered in PR #309) loaded from a cache
outside the repository; if a map is missing the material falls back to procedural noise and the
fallback is reported (never silently).

Per-piece variation: face attribute `piece_rand` (0..1) drives hue/value shifts so no two
slates/stones/planks share an identical colour (stopped family H-A: identical slates)."""
from __future__ import annotations

import os

import bpy

TEX_DIR = os.environ.get("LIND_BUILD_TEX", os.path.expanduser("~/.cache/lind_buildings_tex"))
REPORT = {"tex_dir": TEX_DIR, "loaded": [], "missing": []}


def _img(name, non_color=False):
    path = os.path.join(TEX_DIR, name)
    if not os.path.isfile(path):
        REPORT["missing"].append(name)
        return None
    img = bpy.data.images.get(name) or bpy.data.images.load(path)
    if non_color:
        img.colorspace_settings.name = "Non-Color"
    if name not in REPORT["loaded"]:
        REPORT["loaded"].append(name)
    return img


class NB:
    def __init__(self, name):
        self.m = bpy.data.materials.new(name)
        self.m.use_nodes = True
        self.nt = self.m.node_tree
        self.nt.nodes.clear()
        self.out = self.n("ShaderNodeOutputMaterial", 900, 0)
        self.bsdf = self.n("ShaderNodeBsdfPrincipled", 600, 0)
        self.l(self.bsdf.outputs[0], self.out.inputs[0])

    def n(self, t, x=0, y=0, **kw):
        node = self.nt.nodes.new(t)
        node.location = (x, y)
        for k, v in kw.items():
            setattr(node, k, v)
        return node

    def l(self, a, b):
        self.nt.links.new(a, b)

    def value(self, v):
        nd = self.n("ShaderNodeValue")
        nd.outputs[0].default_value = v
        return nd.outputs[0]

    def math(self, op, a, b, x=0, y=0):
        nd = self.n("ShaderNodeMath", x, y, operation=op)
        for i, s in enumerate((a, b)):
            if hasattr(s, "is_linked") or hasattr(s, "links"):
                self.l(s, nd.inputs[i])
            else:
                nd.inputs[i].default_value = s
        return nd.outputs[0]

    def mix(self, fac, a, b, blend="MIX", x=0, y=0):
        nd = self.n("ShaderNodeMix", x, y, data_type="RGBA", blend_type=blend)
        for sock, val in ((nd.inputs[0], fac), (nd.inputs[6], a), (nd.inputs[7], b)):
            if isinstance(val, (int, float)):
                sock.default_value = val
            elif isinstance(val, tuple):
                sock.default_value = val
            else:
                self.l(val, sock)
        return nd.outputs[2]


def _pbr_textured(name, prefix, tint, uv_mult=1.0, rough_mult=1.0, vary=0.18, hue_vary=0.03,
                  normal_strength=1.0, soot=0.0, desat=0.0, ext="jpg"):
    b = NB(name)
    uv = b.n("ShaderNodeUVMap", -1400, 0)
    uv.uv_map = "UVMap"
    attr = b.n("ShaderNodeAttribute", -1400, -300, attribute_type="GEOMETRY", attribute_name="piece_rand")
    # per-piece UV offset so repeated pieces sample different texture regions
    off = b.n("ShaderNodeCombineXYZ", -1200, -300)
    b.l(attr.outputs["Fac"], off.inputs[0])
    sc = b.math("MULTIPLY", attr.outputs["Fac"], 7.31, -1200, -450)
    b.l(sc, off.inputs[1])
    vm = b.n("ShaderNodeVectorMath", -1000, 0, operation="MULTIPLY_ADD")
    b.l(uv.outputs[0], vm.inputs[0])
    vm.inputs[1].default_value = (uv_mult, uv_mult, uv_mult)
    b.l(off.outputs[0], vm.inputs[2])
    diff = _img(f"{prefix}_diff_1k.{ext}")
    rough = _img(f"{prefix}_rough_1k.{ext}", True)
    nor = _img(f"{prefix}_nor_gl_1k.{ext}", True)
    if diff:
        t = b.n("ShaderNodeTexImage", -800, 200, image=diff)
        b.l(vm.outputs[0], t.inputs[0])
        col = t.outputs[0]
    else:
        t = b.n("ShaderNodeTexNoise", -800, 200)
        b.l(vm.outputs[0], t.inputs[0])
        t.inputs["Scale"].default_value = 6.0
        col = t.outputs[1]
    if desat > 0:
        hs = b.n("ShaderNodeHueSaturation", -600, 300)
        hs.inputs["Saturation"].default_value = 1.0 - desat
        b.l(col, hs.inputs["Color"])
        col = hs.outputs[0]
    # tint and per-piece value / hue variation
    tinted = b.mix(1.0, col, tint + (1.0,), blend="MULTIPLY", x=-400, y=200)
    hsv = b.n("ShaderNodeHueSaturation", -200, 200)
    b.l(tinted, hsv.inputs["Color"])
    vv = b.n("ShaderNodeMapRange", -400, -150)
    b.l(attr.outputs["Fac"], vv.inputs[0])
    vv.inputs[3].default_value = 1.0 - vary
    vv.inputs[4].default_value = 1.0 + vary
    b.l(vv.outputs[0], hsv.inputs["Value"])
    hv = b.n("ShaderNodeMapRange", -400, -350)
    b.l(attr.outputs["Fac"], hv.inputs[0])
    hv.inputs[3].default_value = 0.5 - hue_vary
    hv.inputs[4].default_value = 0.5 + hue_vary
    b.l(hv.outputs[0], hsv.inputs["Hue"])
    final = hsv.outputs[0]
    if soot > 0:
        geo = b.n("ShaderNodeNewGeometry", -800, -600)
        sep = b.n("ShaderNodeSeparateXYZ", -600, -600)
        b.l(geo.outputs["Position"], sep.inputs[0])
        nz = b.n("ShaderNodeTexNoise", -600, -800)
        b.l(geo.outputs["Position"], nz.inputs[0])
        nz.inputs["Scale"].default_value = 1.4
        zz = b.math("ADD", sep.outputs[2], nz.outputs[0], -400, -650)
        mr = b.n("ShaderNodeMapRange", -200, -650)
        b.l(zz, mr.inputs[0])
        mr.inputs[1].default_value = 2.0
        mr.inputs[2].default_value = 6.5
        mr.inputs[3].default_value = soot * 0.35
        mr.inputs[4].default_value = soot
        final = b.mix(mr.outputs[0], final, (0.025, 0.022, 0.02, 1.0), x=100, y=200)
    b.l(final, b.bsdf.inputs["Base Color"])
    if rough:
        tr = b.n("ShaderNodeTexImage", -800, -100, image=rough)
        b.l(vm.outputs[0], tr.inputs[0])
        rr = b.math("MULTIPLY", tr.outputs[0], rough_mult, -400, -100)
        b.l(rr, b.bsdf.inputs["Roughness"])
    else:
        b.bsdf.inputs["Roughness"].default_value = 0.8 * rough_mult
    if nor:
        tn = b.n("ShaderNodeTexImage", -800, -400, image=nor)
        b.l(vm.outputs[0], tn.inputs[0])
        nm = b.n("ShaderNodeNormalMap", -400, -500)
        nm.inputs["Strength"].default_value = normal_strength
        b.l(tn.outputs[0], nm.inputs["Color"])
        b.l(nm.outputs[0], b.bsdf.inputs["Normal"])
    return b.m


def _slate(name, base, jitter, burnt=False):
    """Individual slate shader: per-slate colour from piece_rand, cleavage streaks, lichen."""
    b = NB(name)
    uv = b.n("ShaderNodeUVMap", -1400, 0)
    attr = b.n("ShaderNodeAttribute", -1400, -300, attribute_type="GEOMETRY", attribute_name="piece_rand")
    ramp = b.n("ShaderNodeValToRGB", -1000, -300)
    b.l(attr.outputs["Fac"], ramp.inputs[0])
    els = ramp.color_ramp.elements
    r, g, bb = base
    j = jitter
    els[0].color = (r - j * 0.9, g - j * 0.8, bb - j * 0.6, 1)
    els[1].color = (r + j * 0.7, g + j * 0.8, bb + j * 0.9, 1)
    mid = els.new(0.55)
    mid.color = (r * 0.92, g * 0.97, bb * 1.05, 1)
    warm = els.new(0.9)
    warm.color = (r + j * 0.5, g + j * 0.35, bb + j * 0.1, 1)  # a few weathered warmer slates
    wave = b.n("ShaderNodeTexWave", -1000, 100, wave_type="BANDS")
    b.l(uv.outputs[0], wave.inputs[0])
    wave.inputs["Scale"].default_value = 9.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 4.0
    noise = b.n("ShaderNodeTexNoise", -1000, 350)
    b.l(uv.outputs[0], noise.inputs[0])
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 8.0
    grain = b.math("MULTIPLY", wave.outputs[1], noise.outputs[0], -800, 200)
    gr = b.n("ShaderNodeMapRange", -600, 200)
    b.l(grain, gr.inputs[0])
    gr.inputs[3].default_value = 0.82
    gr.inputs[4].default_value = 1.12
    mulc = b.n("ShaderNodeMix", -400, 0, data_type="RGBA", blend_type="MULTIPLY")
    mulc.inputs[0].default_value = 1.0
    b.l(ramp.outputs[0], mulc.inputs[6])
    cg = b.n("ShaderNodeCombineColor", -550, 100)
    for k in range(3):
        b.l(gr.outputs[0], cg.inputs[k])
    b.l(cg.outputs[0], mulc.inputs[7])
    col = mulc.outputs[2]
    # sparse pale lichen spots
    lich = b.n("ShaderNodeTexNoise", -1000, 600)
    b.l(uv.outputs[0], lich.inputs[0])
    lich.inputs["Scale"].default_value = 5.0
    lr = b.n("ShaderNodeMapRange", -700, 600)
    b.l(lich.outputs[0], lr.inputs[0])
    lr.inputs[1].default_value = 0.66
    lr.inputs[2].default_value = 0.74
    lr.inputs[3].default_value = 0.0
    lr.inputs[4].default_value = 0.55
    col = b.mix(lr.outputs[0], col, (0.42, 0.44, 0.33, 1), x=-200, y=0)
    if burnt:
        col = b.mix(0.75, col, (0.02, 0.018, 0.017, 1), x=0, y=0)
    b.l(col, b.bsdf.inputs["Base Color"])
    rough = b.n("ShaderNodeMapRange", -400, -200)
    b.l(noise.outputs[0], rough.inputs[0])
    rough.inputs[3].default_value = 0.42
    rough.inputs[4].default_value = 0.78
    b.l(rough.outputs[0], b.bsdf.inputs["Roughness"])
    bump = b.n("ShaderNodeBump", -200, -400)
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.004
    b.l(grain, bump.inputs["Height"])
    b.l(bump.outputs[0], b.bsdf.inputs["Normal"])
    return b.m


def _flat(name, color, rough=0.6, metal=0.0, emit=None, emit_strength=0.0, alpha=1.0, transmission=0.0):
    b = NB(name)
    b.bsdf.inputs["Base Color"].default_value = color + (1.0,)
    b.bsdf.inputs["Roughness"].default_value = rough
    b.bsdf.inputs["Metallic"].default_value = metal
    if emit:
        b.bsdf.inputs["Emission Color"].default_value = emit + (1.0,)
        b.bsdf.inputs["Emission Strength"].default_value = emit_strength
    if transmission:
        b.bsdf.inputs["Transmission Weight"].default_value = transmission
    return b.m


def _canvas(name, c1, c2, stripes=10.0):
    b = NB(name)
    uv = b.n("ShaderNodeUVMap", -900, 0)
    sep = b.n("ShaderNodeSeparateXYZ", -700, 0)
    b.l(uv.outputs[0], sep.inputs[0])
    s = b.math("MULTIPLY", sep.outputs[0], stripes, -500, 0)
    f = b.math("FRACT", s, 0.0, -350, 0)
    st = b.math("GREATER_THAN", f, 0.5, -200, 0)
    col = b.mix(st, c1 + (1,), c2 + (1,), x=0, y=0)
    b.l(col, b.bsdf.inputs["Base Color"])
    b.bsdf.inputs["Roughness"].default_value = 0.85
    b.bsdf.inputs["Sheen Weight"].default_value = 0.3
    return b.m


def _srgb_to_lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def slate_base_linear(hsv):
    """Contract colour candidate (HSV, sRGB value) -> linear RGB centre + jitter."""
    import colorsys
    h = sum(hsv["h_deg"]) / 2 / 360.0
    s_ = sum(hsv["s"]) / 2
    v = sum(hsv["v_srgb"]) / 2
    r, g, b = colorsys.hsv_to_rgb(h, s_, v)
    lo = colorsys.hsv_to_rgb(h, s_, hsv["v_srgb"][0])
    jit = _srgb_to_lin(v) - _srgb_to_lin(lo[2])
    return tuple(_srgb_to_lin(x) for x in (r, g, b)), jit


def _palette(name, entries, rough=0.65):
    """One material for small painted/organic props: colour chosen by piece_rand from a stepped
    ramp (keeps the per-building material count within the contract's 16)."""
    b = NB(name)
    attr = b.n("ShaderNodeAttribute", -600, 0, attribute_type="GEOMETRY", attribute_name="piece_rand")
    ramp = b.n("ShaderNodeValToRGB", -300, 0)
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    n = len(entries)
    els[0].position = 0.0
    els[0].color = entries[0] + (1,)
    els[1].position = 1.0 / n
    els[1].color = entries[1] + (1,)
    for k in range(2, n):
        e = els.new(k / n)
        e.color = entries[k] + (1,)
    b.l(attr.outputs["Fac"], ramp.inputs[0])
    b.l(ramp.outputs[0], b.bsdf.inputs["Base Color"])
    b.bsdf.inputs["Roughness"].default_value = rough
    return b.m


# palette slots for MAT_PROP_PAINTED_A (use palette_value(slot))
PALETTE = ["leaf", "leaf_dark", "flower_red", "flower_white", "flower_violet", "apple", "cabbage", "soil",
           "carrot", "bread"]
PALETTE_RGB = [(0.10, 0.25, 0.06), (0.05, 0.14, 0.04), (0.75, 0.06, 0.05), (0.85, 0.85, 0.80),
               (0.35, 0.18, 0.65), (0.55, 0.06, 0.04), (0.35, 0.55, 0.22), (0.10, 0.07, 0.04),
               (0.80, 0.30, 0.05), (0.62, 0.40, 0.18)]


def palette_value(slot):
    k = PALETTE.index(slot)
    return (k + 0.5) / len(PALETTE)


def build_materials(cfg, state="peaceful"):
    burning = state in ("burning", "ruin")
    soot = 0.85 if burning else 0.0
    base, jit = slate_base_linear(cfg["roof"]["slate_hsv"])
    M = {}
    # wall field: wall-pattern map (yellow_stone_wall) desaturated into the contract albedo range
    M["stone_wall"] = _pbr_textured("MAT_STONE_RUBBLE_LIMESTONE_A", "yellow_stone_wall", (0.97, 0.96, 0.94),
                                    uv_mult=1.0, vary=0.05, hue_vary=0.01, soot=soot, desat=0.25, ext="png")
    # dressed quoins/jambs/sills/caps: same CC0 maps as HOME (rock_boulder_dry)
    M["stone_dressed"] = _pbr_textured("MAT_STONE_QUOIN_DRESSED_A", "rock_boulder_dry", (1.05, 1.02, 0.96),
                                       uv_mult=1.0, vary=0.14, hue_vary=0.02, desat=0.2,
                                       normal_strength=0.8, soot=soot * 0.8)
    M["timber"] = _pbr_textured("MAT_TIMBER_OAK_WEATHERED_A", "rough_wood",
                                (0.85, 0.72, 0.58) if not burning else (0.07, 0.06, 0.05),
                                uv_mult=1.0, vary=0.20, hue_vary=0.02)
    M["planks"] = _pbr_textured("MAT_DOOR_PLANK_A", "weathered_brown_planks",
                                (0.95, 0.90, 0.84) if not burning else (0.10, 0.08, 0.07),
                                uv_mult=1.0, vary=0.22, hue_vary=0.02)
    M["slate"] = _slate("MAT_SLATE_BLUEGRAY_A", base, jit, burnt=burning)
    M["ridge"] = _slate("MAT_SLATE_RIDGE_A", tuple(x * 0.85 for x in base), jit * 0.5, burnt=burning)
    M["charred"] = M["timber"] if burning else None
    M["iron"] = _flat("MAT_IRON_WROUGHT_A", (0.020, 0.020, 0.024), rough=0.55, metal=1.0)
    M["glass"] = _flat("MAT_GLASS_CROWN_A", (0.07, 0.10, 0.08), rough=0.06,
                       emit=(1.0, 0.62, 0.30), emit_strength=0.0 if burning else 0.5)
    M["clay"] = _flat("MAT_TERRACOTTA_A", (0.36, 0.13, 0.065), rough=0.8)
    M["lead"] = _flat("MAT_LEAD_FLASHING_A", (0.11, 0.115, 0.13), rough=0.6, metal=0.6)
    M["linen"] = _pbr_textured("MAT_LINEN_A", "rough_wood", (1.0, 0.92, 0.75), uv_mult=3.0, vary=0.15,
                               normal_strength=0.2, desat=0.85)
    M["canvas"] = _canvas("MAT_FABRIC_AWNING_STRIPE_A", (0.80, 0.72, 0.55), (0.06, 0.20, 0.12))
    M["sign_paint"] = _flat("MAT_PAINT_SIGN_GREEN_A", (0.035, 0.11, 0.065), rough=0.7)
    M["gold"] = _flat("MAT_PAINT_GILT_A", (0.62, 0.40, 0.12), rough=0.38, metal=0.7)
    M["prop"] = _palette("MAT_PROP_PAINTED_A", PALETTE_RGB)
    if burning:
        M["glow"] = _flat("MAT_FIRE_GLOW_FX_A", (0.1, 0.03, 0.0), rough=1.0, emit=(1.0, 0.33, 0.05),
                          emit_strength=14.0 if state == "burning" else 0.0)
        M["lamp"] = M["glass"]
        M["charred"] = M["timber"]
    else:
        M["lamp"] = _flat("MAT_LANTERN_GLOW_A", (0.9, 0.7, 0.4), rough=0.2, emit=(1.0, 0.68, 0.32), emit_strength=4.0)
        M["glow"] = M["glass"]
        M["charred"] = M["timber"]
    return M
