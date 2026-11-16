"""LIND-ECO-01 shared library: mesh accumulator, materials, global wind / water channels.

Runs under the pip `bpy` module (python3) and under `blender -b --python`.
Candidate tooling only (not production, not adopted art).

Wind channel contract (see docs/production/lind/ecology/ECO_PRODUCTION_SPEC_V1.md):
  scene["lind_wind_strength"]  float 0..1  -- the ONLY wind input. 0 == wind-stop event.
  scene["lind_water_flow"]     float 0..1  -- separate water channel, never driven by wind.
  Each is mirrored by a non-python driver onto an empty (LIND_WIND_CTRL / LIND_WATER_CTRL)
  location.x, which the geometry-node groups read through an Object Info node.
  Per-vertex float attribute `wind_weight` (0 = rigid root, 1 = free tip) scales sway.
"""
import hashlib
import math
import random

import bpy
from mathutils import Matrix, Vector

WIND_PROP = "lind_wind_strength"
WATER_PROP = "lind_water_flow"
WIND_CTRL = "LIND_WIND_CTRL"
WATER_CTRL = "LIND_WATER_CTRL"
WIND_GROUP = "LIND_WindSway"
WATER_GROUP = "LIND_WaterFlow"


def ensure_cycles():
    try:
        import addon_utils
        addon_utils.enable("cycles", default_set=True)
    except Exception:  # blender binary: already enabled
        pass


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ensure_cycles()
    return bpy.context.scene


# ----------------------------------------------------------------------------- mesh accumulator
class MeshAcc:
    """Accumulates verts / faces / per-vertex colour / wind_weight / per-face material index."""

    def __init__(self):
        self.v = []
        self.f = []
        self.col = []
        self.ww = []
        self.mi = []
        self.fuv = []  # per-face corner UVs or None
        self.extra = {}  # name -> per-vertex float list (e.g. flow_u / flow_v for water)
        self.vn = {}  # vertex index -> custom shading normal (normal transfer for foliage cards)

    def vert(self, co, col, ww):
        self.v.append((co[0], co[1], co[2]))
        self.col.append((col[0], col[1], col[2], 1.0))
        self.ww.append(max(0.0, min(1.0, ww)))
        return len(self.v) - 1

    def face(self, idx, mat=0, uv=None):
        self.f.append(tuple(idx))
        self.mi.append(mat)
        self.fuv.append(uv)

    # -- tubes (branches, stems, legs, rails) ------------------------------------
    def tube(self, pts, radii, sides, cols, wws, mat=0, cap_tip=True, cap_base=False, rjit=None):
        """Parallel-transport swept tube. pts/radii/cols/wws are per-ring lists."""
        n = len(pts)
        if n < 2:
            return
        tans = []
        for i in range(n):
            a = pts[max(0, i - 1)]
            b = pts[min(n - 1, i + 1)]
            t = (b - a)
            if t.length < 1e-9:
                t = Vector((0, 0, 1))
            tans.append(t.normalized())
        ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
        nrm = tans[0].cross(ref).normalized()
        rings = []
        for i in range(n):
            if i > 0:
                axis = tans[i - 1].cross(tans[i])
                if axis.length > 1e-8:
                    ang = tans[i - 1].angle(tans[i])
                    nrm = (Matrix.Rotation(ang, 3, axis.normalized()) @ nrm)
                nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
            bin_ = tans[i].cross(nrm)
            ring = []
            for s in range(sides):
                a = math.tau * s / sides
                r = radii[i] * (rjit[i][s] if rjit else 1.0)
                p = pts[i] + (nrm * math.cos(a) + bin_ * math.sin(a)) * r
                ring.append(self.vert(p, cols[i], wws[i]))
            rings.append(ring)
        for i in range(n - 1):
            r0, r1 = rings[i], rings[i + 1]
            for s in range(sides):
                s2 = (s + 1) % sides
                self.face((r0[s], r0[s2], r1[s2], r1[s]), mat)
        if cap_tip:
            tip = self.vert(pts[-1] + tans[-1] * radii[-1] * 0.8, cols[-1], wws[-1])
            r = rings[-1]
            for s in range(sides):
                self.face((r[s], r[(s + 1) % sides], tip), mat)
        if cap_base:
            r = rings[0]
            self.face(tuple(reversed(r)), mat)

    # -- generic transformed mesh copy (metaball conversions, primitives) --------
    def add_mesh(self, me, mat4, col_fn, ww_fn, mat=0):
        base = len(self.v)
        for vx in me.vertices:
            co = mat4 @ vx.co
            self.vert(co, col_fn(co), ww_fn(co))
        for p in me.polygons:
            self.face([base + i for i in p.vertices], mat)

    def ribbon(self, pts, widths, sides_dir, cols, wws, mat=0, fold=0.0, fold_dir=None):
        """V-folded strip (grass blade / leaf blade). sides_dir: per-ring lateral unit vectors.
        fold: midrib offset (m, fraction of width) along fold_dir (per-ring vectors)."""
        n = len(pts)
        rows = []
        for i in range(n):
            side = sides_dir[i]
            w = widths[i]
            mid = pts[i] + (fold_dir[i] * fold * w if fold_dir else Vector())
            if w < 1e-5:
                rows.append([self.vert(pts[i], cols[i], wws[i])])
                continue
            rows.append([self.vert(pts[i] - side * w, cols[i], wws[i]),
                         self.vert(mid, cols[i], wws[i]),
                         self.vert(pts[i] + side * w, cols[i], wws[i])])
        for i in range(n - 1):
            a, b = rows[i], rows[i + 1]
            if len(a) == 3 and len(b) == 3:
                self.face((a[0], a[1], b[1], b[0]), mat)
                self.face((a[1], a[2], b[2], b[1]), mat)
            elif len(a) == 3 and len(b) == 1:
                self.face((a[0], a[1], b[0]), mat)
                self.face((a[1], a[2], b[0]), mat)

    def tri_count(self):
        return sum(len(f) - 2 for f in self.f)

    def build(self, name, materials, smooth=True, collection=None):
        me = bpy.data.meshes.new(name + "_mesh")
        me.from_pydata(self.v, [], self.f)
        me.update()
        if len(me.polygons) != len(self.f):
            raise RuntimeError("face count changed during build of %s" % name)
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        flat = [c for rgba in self.col for c in rgba]
        ca.data.foreach_set("color", flat)
        at = me.attributes.new("wind_weight", "FLOAT", "POINT")
        at.data.foreach_set("value", self.ww)
        me.polygons.foreach_set("material_index", self.mi)
        for nm, vals in self.extra.items():
            ea = me.attributes.new(nm, "FLOAT", "POINT")
            ea.data.foreach_set("value", vals)
        if any(u is not None for u in self.fuv):
            uvl = me.uv_layers.new(name="UVMap")
            flat_uv = []
            for f, u in zip(self.f, self.fuv):
                flat_uv.extend(c for corner in (u or [(0.0, 0.0)] * len(f)) for c in corner)
            uvl.data.foreach_set("uv", flat_uv)
        me.polygons.foreach_set("use_smooth", [smooth] * len(self.f))
        for m in materials:
            me.materials.append(m)
        if self.vn:
            try:
                me.use_auto_smooth = True  # Blender < 4.1 only
            except AttributeError:
                pass
            normals = [tuple(vx.normal) for vx in me.vertices]
            for vi, nv in self.vn.items():
                normals[vi] = (nv[0], nv[1], nv[2])
            me.normals_split_custom_set_from_vertices(normals)
        ob = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob


def geometry_hash(ob):
    """Deterministic hash of mesh topology + rounded positions + attributes (pre-modifier)."""
    me = ob.data
    h = hashlib.sha256()
    for vx in me.vertices:
        h.update(("%.5f,%.5f,%.5f;" % tuple(vx.co)).encode())
    for p in me.polygons:
        h.update((",".join(str(i) for i in p.vertices) + "|%d;" % p.material_index).encode())
    if "Col" in me.color_attributes:
        h.update(",".join("%.3f" % c for d in me.color_attributes["Col"].data for c in d.color[:3]).encode())
    if "wind_weight" in me.attributes:
        h.update(",".join("%.4f" % d.value for d in me.attributes["wind_weight"].data).encode())
    return h.hexdigest()


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# ----------------------------------------------------------------------------- materials
def _principled(nt):
    return next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")


def mat_vcol(name, rough=0.7, translucent=0.0, sheen=0.0, noise_mod=0.0, noise_scale=40.0, spec=0.35,
             stretch=None):
    """Vertex-colour material (attribute 'Col'); optional translucency for leaves and
    low-amplitude noise modulation for bark/straw grain."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = _principled(nt)
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    attr.attribute_type = "GEOMETRY"
    col_out = attr.outputs["Color"]
    if noise_mod > 0:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = noise_scale
        tex.inputs["Detail"].default_value = 6.0
        if stretch:  # anisotropic grain: bark furrows / timber grain along object Z or X
            tc = nt.nodes.new("ShaderNodeTexCoord")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = stretch
            nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = noise_mod
        nt.links.new(col_out, mix.inputs["A"])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.3
        ramp.color_ramp.elements[0].color = (0.55, 0.55, 0.55, 1)
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = (1.25, 1.25, 1.25, 1)
        nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], mix.inputs["B"])
        col_out = mix.outputs["Result"]
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.35 * noise_mod
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    nt.links.new(col_out, bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = rough
    if "Specular IOR Level" in bs.inputs:
        bs.inputs["Specular IOR Level"].default_value = spec
    if sheen > 0 and "Sheen Weight" in bs.inputs:
        bs.inputs["Sheen Weight"].default_value = sheen
    if translucent > 0:
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
        nt.links.new(col_out, tr.inputs["Color"])
        mx = nt.nodes.new("ShaderNodeMixShader")
        mx.inputs["Fac"].default_value = translucent
        nt.links.new(bs.outputs["BSDF"], mx.inputs[1])
        nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
        nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    m.diffuse_color = (0.3, 0.4, 0.2, 1)
    return m


def mat_image_alpha(name, image_path):
    """Alpha-tested card material (LOD1 grass cards)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = _principled(nt)
    img = bpy.data.images.load(image_path, check_existing=True)
    img.alpha_mode = "STRAIGHT"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], bs.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bs.inputs["Alpha"])
    bs.inputs["Roughness"].default_value = 0.75
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    return m


def mat_leafcard(name, image_path):
    """Alpha-tested leaf-spray card: image colour x vertex tint (attribute 'Col'), translucent."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = _principled(nt)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    img = bpy.data.images.load(image_path, check_existing=True)
    img.alpha_mode = "STRAIGHT"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    attr.attribute_type = "GEOMETRY"
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    nt.links.new(tex.outputs["Color"], mix.inputs["A"])
    nt.links.new(attr.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.55
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    nt.links.new(mix.outputs["Result"], tr.inputs["Color"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs["Fac"].default_value = 0.4
    nt.links.new(bs.outputs["BSDF"], mx.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mx.inputs[2])
    tsp = nt.nodes.new("ShaderNodeBsdfTransparent")
    am = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Alpha"], am.inputs["Fac"])
    nt.links.new(tsp.outputs["BSDF"], am.inputs[1])
    nt.links.new(mx.outputs["Shader"], am.inputs[2])
    nt.links.new(am.outputs["Shader"], out.inputs["Surface"])
    try:
        m.surface_render_method = "DITHERED"
    except Exception:
        pass
    return m


def mat_soil(name="M_eco_soil"):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = mat_vcol(name, rough=0.95, noise_mod=0.6, noise_scale=18.0, spec=0.2)
    return m


def mat_ground(name="M_eco_preview_ground", base=(0.075, 0.17, 0.035), alt=(0.15, 0.24, 0.06)):
    """Preview ground only (not an ECO deliverable; WORLD owns terrain materials)."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = _principled(nt)
    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 0.12
    tex.inputs["Detail"].default_value = 8.0
    geo = nt.nodes.new("ShaderNodeNewGeometry")  # world-space coords: seamless across objects
    nt.links.new(geo.outputs["Position"], tex.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*base, 1)
    ramp.color_ramp.elements[1].color = (*alt, 1)
    nt.links.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.95
    return m


def mat_water(name="M_eco_water"):
    """River water: vertex colour (deep centre / shallow edge) + glossy surface + mild transmission."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bs = _principled(nt)
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Col"
    attr.attribute_type = "GEOMETRY"
    nt.links.new(attr.outputs["Color"], bs.inputs["Base Color"])
    bs.inputs["Roughness"].default_value = 0.05
    if "Transmission Weight" in bs.inputs:
        bs.inputs["Transmission Weight"].default_value = 0.25
    if "Coat Weight" in bs.inputs:
        bs.inputs["Coat Weight"].default_value = 0.3
    return m


# ----------------------------------------------------------------------------- channels
def _driver_mirror(scene, ctrl, prop):
    fc = ctrl.driver_add("location", 0)
    d = fc.driver
    d.type = "AVERAGE"
    var = d.variables.new()
    var.name = "v"
    var.type = "SINGLE_PROP"
    var.targets[0].id_type = "SCENE"
    var.targets[0].id = scene
    var.targets[0].data_path = '["%s"]' % prop


def ensure_channels(scene, wind=1.0, water=1.0):
    if WIND_PROP not in scene:
        scene[WIND_PROP] = float(wind)
    if WATER_PROP not in scene:
        scene[WATER_PROP] = float(water)
    ui = scene.id_properties_ui(WIND_PROP)
    ui.update(min=0.0, max=1.0, soft_min=0.0, soft_max=1.0,
              description="LIND global wind strength 0..1 (0 = wind-stop event)")
    ui = scene.id_properties_ui(WATER_PROP)
    ui.update(min=0.0, max=1.0, description="LIND water flow 0..1 (independent of wind)")
    for nm, prop in ((WIND_CTRL, WIND_PROP), (WATER_CTRL, WATER_PROP)):
        ob = bpy.data.objects.get(nm)
        if ob is None:
            ob = bpy.data.objects.new(nm, None)
            scene.collection.objects.link(ob)
            ob.empty_display_size = 0.3
            ob.hide_render = True
            _driver_mirror(scene, ob, prop)
    return bpy.data.objects[WIND_CTRL], bpy.data.objects[WATER_CTRL]


def set_channel(scene, wind=None, water=None):
    if wind is not None:
        scene[WIND_PROP] = float(wind)
    if water is not None:
        scene[WATER_PROP] = float(water)
    scene.update_tag()
    bpy.context.view_layer.update()


class _NB:
    """Tiny node-building helper for geometry node trees."""

    def __init__(self, ng):
        self.ng = ng
        self.n = ng.nodes
        self.l = ng.links

    def math(self, op, a, b=None, c=None):
        nd = self.n.new("ShaderNodeMath")
        nd.operation = op
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                nd.inputs[i].default_value = float(x)
            else:
                self.l.new(x, nd.inputs[i])
        return nd.outputs[0]

    def sep(self, vec):
        nd = self.n.new("ShaderNodeSeparateXYZ")
        self.l.new(vec, nd.inputs[0])
        return nd.outputs

    def comb(self, x, y, z):
        nd = self.n.new("ShaderNodeCombineXYZ")
        for i, s in enumerate((x, y, z)):
            if isinstance(s, (int, float)):
                nd.inputs[i].default_value = float(s)
            else:
                self.l.new(s, nd.inputs[i])
        return nd.outputs[0]


def _new_gn(name, inputs):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    for nm, default in inputs:
        s = ng.interface.new_socket(nm, in_out="INPUT", socket_type="NodeSocketFloat")
        s.default_value = default
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    return ng, gi, go


def ensure_wind_group():
    """offset = W*A*w^1.4*(0.62+0.38*sin(2*pi*f*t - k.pos)) along +X (world wind dir),
    flutter = W*A*Fl*w*sin(2*pi*2.7f*t + hash(pos)) along Y, droop z = -0.3*W*A*w^2*gust.
    W comes only from LIND_WIND_CTRL.location.x (mirror of scene['lind_wind_strength']).
    At W == 0 every term is exactly zero, so geometry equals the rest pose."""
    ng = bpy.data.node_groups.get(WIND_GROUP)
    if ng:
        return ng
    ng, gi, go = _new_gn(WIND_GROUP, [("Amplitude", 0.15), ("Frequency", 0.45), ("Flutter", 0.25)])
    b = _NB(ng)
    ctrl = bpy.data.objects[WIND_CTRL]
    oi = b.n.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = ctrl
    W = b.sep(oi.outputs["Location"])[0]
    # world-space phase: add own object location so copies do not sway in lockstep
    selfo = b.n.new("GeometryNodeSelfObject")
    oself = b.n.new("GeometryNodeObjectInfo")
    oself.transform_space = "ORIGINAL"
    b.l.new(selfo.outputs[0], oself.inputs["Object"])
    pos = b.n.new("GeometryNodeInputPosition").outputs[0]
    vadd = b.n.new("ShaderNodeVectorMath")
    vadd.operation = "ADD"
    b.l.new(pos, vadd.inputs[0])
    b.l.new(oself.outputs["Location"], vadd.inputs[1])
    px, py, pz = b.sep(vadd.outputs[0])
    na = b.n.new("GeometryNodeInputNamedAttribute")
    na.data_type = "FLOAT"
    na.inputs["Name"].default_value = "wind_weight"
    w = na.outputs["Attribute"]
    t = b.n.new("GeometryNodeInputSceneTime").outputs["Seconds"]
    A, F, FL = gi.outputs["Amplitude"], gi.outputs["Frequency"], gi.outputs["Flutter"]
    # gust wave travelling along +X
    omega = b.math("MULTIPLY", F, math.tau)
    ph = b.math("ADD", b.math("MULTIPLY", px, 0.9), b.math("MULTIPLY", py, 0.35))
    s1 = b.math("SINE", b.math("SUBTRACT", b.math("MULTIPLY", omega, t), ph))
    gust = b.math("MULTIPLY_ADD", s1, 0.38, 0.62)
    wp = b.math("POWER", w, 1.4)
    WA = b.math("MULTIPLY", W, A)
    ox = b.math("MULTIPLY", b.math("MULTIPLY", WA, wp), gust)
    # flutter (higher frequency, per-position phase)
    ph2 = b.math("ADD", b.math("MULTIPLY", px, 3.1), b.math("MULTIPLY", py, 2.3))
    ph2 = b.math("ADD", ph2, b.math("MULTIPLY", pz, 4.7))
    s2 = b.math("SINE", b.math("ADD", b.math("MULTIPLY", omega, b.math("MULTIPLY", t, 2.7)), ph2))
    oy = b.math("MULTIPLY", b.math("MULTIPLY", b.math("MULTIPLY", WA, FL), w), s2)
    oz = b.math("MULTIPLY", b.math("MULTIPLY", b.math("MULTIPLY", WA, b.math("MULTIPLY", w, w)), gust), -0.3)
    off = b.comb(ox, oy, oz)
    # offset is authored in world space (+X downwind); rotate into object space so that
    # rotated instances of one asset all bend the same world direction
    try:  # Blender >= 4.1 rotation sockets; on 4.0 fall back to object-local wind direction
        inv = b.n.new("FunctionNodeInvertRotation")
        rv = b.n.new("FunctionNodeRotateVector")
        b.l.new(oself.outputs["Rotation"], inv.inputs[0])
        b.l.new(off, rv.inputs["Vector"])
        b.l.new(inv.outputs[0], rv.inputs["Rotation"])
        off = rv.outputs[0]
        ng["lind_world_space_wind"] = True
    except Exception:
        ng["lind_world_space_wind"] = False
    sp = b.n.new("GeometryNodeSetPosition")
    b.l.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    b.l.new(off, sp.inputs["Offset"])
    b.l.new(sp.outputs[0], go.inputs[0])
    return ng


def ensure_water_group():
    """Water ripple travelling downstream, driven ONLY by LIND_WATER_CTRL (scene['lind_water_flow']).
    Uses per-vertex flow_u (metres along the channel) and flow_v (-1..1 across). No wind input."""
    ng = bpy.data.node_groups.get(WATER_GROUP)
    if ng:
        return ng
    ng, gi, go = _new_gn(WATER_GROUP, [("Height", 0.02), ("Speed", 1.0)])
    b = _NB(ng)
    oi = b.n.new("GeometryNodeObjectInfo")
    oi.inputs["Object"].default_value = bpy.data.objects[WATER_CTRL]
    F = b.sep(oi.outputs["Location"])[0]

    def attr(nm):
        na = b.n.new("GeometryNodeInputNamedAttribute")
        na.data_type = "FLOAT"
        na.inputs["Name"].default_value = nm
        return na.outputs["Attribute"]
    u, v = attr("flow_u"), attr("flow_v")
    t = b.n.new("GeometryNodeInputSceneTime").outputs["Seconds"]
    tt = b.math("MULTIPLY", b.math("MULTIPLY", t, gi.outputs["Speed"]), F)
    a1 = b.math("SINE", b.math("SUBTRACT", b.math("MULTIPLY", u, 3.1), b.math("MULTIPLY", tt, 7.0)))
    a2 = b.math("SINE", b.math("ADD", b.math("MULTIPLY", v, 5.3), b.math("SUBTRACT", b.math("MULTIPLY", u, 7.7), b.math("MULTIPLY", tt, 11.0))))
    a3 = b.math("SINE", b.math("SUBTRACT", b.math("MULTIPLY", u, 13.0), b.math("ADD", b.math("MULTIPLY", v, 2.0), b.math("MULTIPLY", tt, 17.0))))
    # flow is faster/rougher mid-channel: scale by (1 - v^2)
    mid = b.math("SUBTRACT", 1.0, b.math("MULTIPLY", v, v))
    zsum = b.math("ADD", b.math("ADD", a1, b.math("MULTIPLY", a2, 0.55)), b.math("MULTIPLY", a3, 0.3))
    z = b.math("MULTIPLY", b.math("MULTIPLY", zsum, gi.outputs["Height"]), b.math("MULTIPLY_ADD", mid, 0.7, 0.3))
    sp = b.n.new("GeometryNodeSetPosition")
    b.l.new(gi.outputs["Geometry"], sp.inputs["Geometry"])
    b.l.new(b.comb(0.0, 0.0, z), sp.inputs["Offset"])
    b.l.new(sp.outputs[0], go.inputs[0])
    return ng


def add_wind(ob, amplitude, frequency=0.45, flutter=0.25):
    ng = ensure_wind_group()
    mod = ob.modifiers.new("LIND_Wind", "NODES")
    mod.node_group = ng
    for item in ng.interface.items_tree:
        if getattr(item, "in_out", None) != "INPUT" or item.socket_type != "NodeSocketFloat":
            continue
        val = {"Amplitude": amplitude, "Frequency": frequency, "Flutter": flutter}[item.name]
        props = getattr(mod, "properties", None)
        if props is not None and hasattr(props, "inputs"):  # Blender 5.x
            getattr(props.inputs, item.identifier).value = float(val)
        else:  # Blender 4.x
            mod[item.identifier] = float(val)
    ob["lind_wind_responsive"] = True
    ob["lind_wind_amplitude_m"] = float(amplitude)
    return mod


def add_water(ob, height=0.02, speed=1.0):
    ng = ensure_water_group()
    mod = ob.modifiers.new("LIND_Water", "NODES")
    mod.node_group = ng
    for item in ng.interface.items_tree:
        if getattr(item, "in_out", None) != "INPUT" or item.socket_type != "NodeSocketFloat":
            continue
        val = {"Height": height, "Speed": speed}[item.name]
        props = getattr(mod, "properties", None)
        if props is not None and hasattr(props, "inputs"):
            getattr(props.inputs, item.identifier).value = float(val)
        else:
            mod[item.identifier] = float(val)
    ob["lind_water_channel"] = True
    return mod


# ----------------------------------------------------------------------------- misc helpers
def rot_to(v_from, v_to):
    return v_from.rotation_difference(v_to).to_matrix()


def jitter_col(rng, c, amt):
    return tuple(max(0.0, min(1.0, x * (1.0 + rng.uniform(-amt, amt)))) for x in c)


def lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def new_rng(seed, salt):
    return random.Random("%d:%s" % (seed, salt))
