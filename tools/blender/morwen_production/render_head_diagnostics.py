"""MORWEN-HEAD-STRUCTURE-01: non-destructive head diagnostic renders (Cycles, CPU, headless).

All overrides (diagnostic materials, per-face ids) are applied to in-memory
copies of mesh data. Nothing is saved or exported; the source VRM SHA-256 is
asserted unchanged at the end.

Passes x views (front=+Y, right=+X/character right, back=-Y, left=-X):
  parts            welded connected-component id colours (all meshes)
  material         one flat colour per source material
  normals          blue = front face seen, red = back face seen (Backfacing)
  clay             neutral clay, world fill + camera-relative key light
  wire             clay + wireframe overlay
  original         imported materials untouched (VRM unlit/emission textures)
  legacy588_oldlight  previous method reproduced: 588-vert seam fragment, flat, light behind subject
  legacy588_relit     same fragment and shading, only the light changed (A/B for the black anomaly)

Camera: orthographic, ortho_scale fixed, centre fixed from J_Bip_C_Head bone.
"""
import colorsys
import hashlib
import json
import os
from pathlib import Path

import bpy
from mathutils import Vector

SRC = Path(os.environ.get("MORWEN_VRM", "render_output/morwen_vroid_review/Base_Female.vrm"))
OUT = Path(os.environ.get("MORWEN_OUT", "render_output/morwen_head_structure"))
RES = int(os.environ.get("MORWEN_RES", "512"))
VIEWS = {"front": (0, 1, 0), "right": (1, 0, 0), "back": (0, -1, 0), "left": (-1, 0, 0)}
ORTHO_SCALE = 0.40          # metres, identical for every pass and view
CENTER_OFFSET_Z = 0.10      # metres above J_Bip_C_Head head joint
CAM_DIST = 2.0


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def emission_mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*rgb, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def normals_mat():
    m = bpy.data.materials.new("DIAG_NORMALS")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    mix = nt.nodes.new("ShaderNodeMixRGB")
    mix.inputs["Color1"].default_value = (0.15, 0.35, 1.0, 1)   # front
    mix.inputs["Color2"].default_value = (1.0, 0.08, 0.05, 1)   # back
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
    shade = nt.nodes.new("ShaderNodeMath")
    shade.operation = "MULTIPLY_ADD"
    nt.links.new(lw.outputs["Facing"], shade.inputs[0])
    shade.inputs[1].default_value = -0.55
    shade.inputs[2].default_value = 1.0
    tint = nt.nodes.new("ShaderNodeMixRGB")
    tint.blend_type = "MULTIPLY"
    tint.inputs["Fac"].default_value = 1.0
    nt.links.new(mix.outputs[0], tint.inputs["Color1"])
    nt.links.new(shade.outputs[0], tint.inputs["Color2"])
    e = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(tint.outputs[0], e.inputs["Color"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


def clay_mat(wire=False):
    m = bpy.data.materials.new("DIAG_CLAY_WIRE" if wire else "DIAG_CLAY")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    b = nt.nodes.new("ShaderNodeBsdfDiffuse")
    b.inputs["Color"].default_value = (0.62, 0.55, 0.50, 1)
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    if not wire:
        nt.links.new(b.outputs[0], o.inputs["Surface"])
        return m
    w = nt.nodes.new("ShaderNodeWireframe")
    w.use_pixel_size = True
    w.inputs["Size"].default_value = 0.6
    line = nt.nodes.new("ShaderNodeEmission")
    line.inputs["Color"].default_value = (0.05, 0.05, 0.08, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(w.outputs[0], mix.inputs["Fac"])
    nt.links.new(b.outputs[0], mix.inputs[1])
    nt.links.new(line.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], o.inputs["Surface"])
    return m


def palette(n):
    return [colorsys.hsv_to_rgb((i * 0.618034) % 1.0, 0.75, 0.95) for i in range(n)]


def component_ids(obj):
    """Seam-welded edge components (union-find over edges + identical positions).

    Returns (component id per polygon, {component id: welded vertex count}).
    Mesh data is only read.
    """
    me = obj.data
    parent = list(range(len(me.vertices)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    first_at = {}
    for v in me.vertices:
        key = tuple(round(c * 1e6) for c in v.co)  # seam duplicates are exact copies
        if key in first_at:
            union(first_at[key], v.index)
        else:
            first_at[key] = v.index
    for e in me.edges:
        union(*e.vertices)
    roots = {}
    ids = [roots.setdefault(find(p.vertices[0]), len(roots)) for p in me.polygons]
    sizes = {}
    for key, vi in first_at.items():
        c = roots.get(find(vi))
        if c is not None:
            sizes[c] = sizes.get(c, 0) + 1
    return ids, sizes


class Scene:
    def __init__(self):
        assert SRC.is_file(), f"Pinned source missing: {SRC}"
        self.src_sha = sha(SRC)
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(SRC.resolve()))
        sc = bpy.context.scene
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.render.resolution_x = sc.render.resolution_y = RES
        sc.render.resolution_percentage = 100
        sc.render.film_transparent = True
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGBA"
        sc.view_settings.view_transform = "Standard"
        if hasattr(sc.cycles, "use_denoising"):
            sc.cycles.use_denoising = False
        self.sc = sc
        for o in list(sc.objects):
            if o.users_collection and o.users_collection[0].name == "glTF_not_exported":
                o.hide_render = True  # importer bone-shape helper (Icosphere), not model geometry
        self.meshes = [o for o in sc.objects if o.type == "MESH" and not o.hide_render]
        for o in self.meshes:
            o.data = o.data.copy()  # in-memory override target; source datablock untouched
        self.orig_mats = {o.name: [s.material for s in o.material_slots] for o in self.meshes}
        self.orig_index = {o.name: [p.material_index for p in o.data.polygons] for o in self.meshes}
        arm = next(o for o in sc.objects if o.type == "ARMATURE")
        head = arm.matrix_world @ arm.data.bones["J_Bip_C_Head"].head_local
        self.center = Vector((head.x, head.y, head.z + CENTER_OFFSET_Z))
        world = bpy.data.worlds.new("DIAG_WORLD")
        world.use_nodes = True
        self.world_bg = world.node_tree.nodes["Background"]
        sc.world = world
        cam_data = bpy.data.cameras.new("DIAG_CAM")
        cam_data.type = "ORTHO"
        cam_data.ortho_scale = ORTHO_SCALE
        cam_data.clip_end = 10
        self.cam = bpy.data.objects.new("DIAG_CAM", cam_data)
        sc.collection.objects.link(self.cam)
        sc.camera = self.cam
        sun = bpy.data.lights.new("DIAG_KEY", "SUN")
        sun.energy = 3.0
        self.sun = bpy.data.objects.new("DIAG_KEY", sun)
        sc.collection.objects.link(self.sun)
        self.records = []

    # ---- state helpers -------------------------------------------------
    def lighting(self, mode, view_dir=None):
        if mode == "emission":
            self.world_bg.inputs["Strength"].default_value = 0.0
            self.sun.hide_render = True
            self.sc.cycles.samples = 4
        elif mode == "clay":
            self.world_bg.inputs["Color"].default_value = (0.8, 0.8, 0.8, 1)
            self.world_bg.inputs["Strength"].default_value = 0.6
            self.sun.hide_render = False
            d = Vector(view_dir)
            side = Vector((-d.y, d.x, 0))            # camera-left in world
            key = (d + side * 0.6 + Vector((0, 0, 0.8))).normalized()
            self.sun.rotation_euler = (-key).to_track_quat("-Z", "Y").to_euler()
            self.sc.cycles.samples = 32

    def assign(self, per_object_material_lists, per_object_indices=None):
        for o in self.meshes:
            o.data.materials.clear()
            for m in per_object_material_lists[o.name]:
                o.data.materials.append(m)
            idx = (per_object_indices or self.orig_index)[o.name]
            o.data.polygons.foreach_set("material_index", idx)
            o.data.update()

    def restore(self):
        self.assign(self.orig_mats)

    def shot(self, pass_name, view, hide=()):
        d = Vector(VIEWS[view])
        self.cam.location = self.center + d * CAM_DIST
        self.cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
        for o in self.meshes:
            o.hide_render = o.name in hide
        path = OUT / pass_name / f"{view}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        self.sc.render.filepath = str(path.resolve())
        bpy.ops.render.render(write_still=True)
        self.records.append({"pass": pass_name, "view": view, "file": str(path.relative_to(OUT))})

    # ---- passes ----------------------------------------------------------
    def run_parts(self):
        mats, idx, legend = {}, {}, {}
        for o in self.meshes:
            ids, sizes = component_ids(o)
            order = sorted(sizes, key=lambda c: -sizes[c])
            rank = {c: i for i, c in enumerate(order)}
            pal = palette(len(order))
            mats[o.name] = [emission_mat(f"DIAG_PART_{o.name}_{i:02d}", pal[i]) for i in range(len(order))]
            idx[o.name] = [rank[c] for c in ids]
            legend[o.name] = [{"rank": i, "vertices_welded": sizes[c], "rgb": [round(x, 3) for x in pal[i]]}
                              for i, c in enumerate(order)]
        self.assign(mats, idx)
        self.lighting("emission")
        for v in VIEWS:
            self.shot("parts", v)
        return legend

    def run_material(self):
        names = sorted({m.name for ms in self.orig_mats.values() for m in ms if m})
        pal = dict(zip(names, palette(len(names))))
        cache = {n: emission_mat(f"DIAG_MAT_{n}", pal[n]) for n in names}
        self.assign({o: [cache[m.name] for m in ms] for o, ms in self.orig_mats.items()})
        self.lighting("emission")
        for v in VIEWS:
            self.shot("material", v)
        return {n: [round(x, 3) for x in pal[n]] for n in names}

    def run_uniform(self, pass_name, mat, light):
        self.assign({o: [mat] * max(1, len(ms)) for o, ms in self.orig_mats.items()})
        for v, d in VIEWS.items():
            self.lighting(light, d)
            self.shot(pass_name, v)

    def run_original(self):
        self.restore()
        self.lighting("emission")
        for v in VIEWS:
            self.shot("original", v)

    def run_legacy588(self):
        """Rebuild the previous 588-vertex fragment exactly as render_neutral_skin_head.py did."""
        face = next(o for o in self.meshes if o.name == "Face")
        me = face.data
        adj = [set() for _ in me.vertices]
        for e in me.edges:
            a, b = e.vertices
            adj[a].add(b)
            adj[b].add(a)
        seen, comps = set(), []
        for v in range(len(adj)):
            if v in seen:
                continue
            todo, ids = [v], set()
            seen.add(v)
            while todo:
                q = todo.pop()
                ids.add(q)
                for n in adj[q]:
                    if n not in seen:
                        seen.add(n)
                        todo.append(n)
            comps.append(ids)
        ids = next(c for c in comps if len(c) == 588)
        order = sorted(ids)
        ix = {v: i for i, v in enumerate(order)}
        verts = [tuple(face.matrix_world @ me.vertices[i].co) for i in order]
        polys = [tuple(ix[v] for v in p.vertices) for p in me.polygons if all(v in ids for v in p.vertices)]
        lm = bpy.data.meshes.new("LEGACY588")
        lm.from_pydata(verts, [], polys)
        lm.update()
        mat = bpy.data.materials.new("LEGACY_SKIN")
        mat.diffuse_color = (.67, .52, .46, 1)
        lm.materials.append(mat)
        lo = bpy.data.objects.new("LEGACY588", lm)
        self.sc.collection.objects.link(lo)
        hidden = {o.name for o in self.meshes}
        lo_pts = [Vector(v) for v in verts]
        lo_min = Vector([min(p[i] for p in lo_pts) for i in range(3)])
        lo_max = Vector([max(p[i] for p in lo_pts) for i in range(3)])
        c, ext = (lo_min + lo_max) * 0.5, max(lo_max - lo_min)
        # (a) previous lighting: single AREA light at +X -Y +Z (behind a +Y-facing face), no fill
        area = bpy.data.lights.new("LEGACY_AREA", "AREA")
        area.energy = 450
        area.size = ext * 2
        ao = bpy.data.objects.new("LEGACY_AREA", area)
        ao.location = c + Vector((ext, -ext, ext))
        ao.rotation_euler = (0, 0, 0)  # bpy.ops.object.light_add default orientation (points -Z)
        self.sc.collection.objects.link(ao)
        self.world_bg.inputs["Color"].default_value = (0.051, 0.051, 0.051, 1)  # factory world grey
        self.world_bg.inputs["Strength"].default_value = 1.0
        self.sun.hide_render = True
        self.sc.cycles.samples = 16
        for v in VIEWS:
            self.shot("legacy588_oldlight", v, hide=hidden)
        # (b) only lighting changed
        ao.hide_render = True
        for v, d in VIEWS.items():
            self.lighting("clay", d)
            self.shot("legacy588_relit", v, hide=hidden)
        faces_in_fragment = len(polys)
        skin_idx = [i for i, m in enumerate(self.orig_mats["Face"]) if m and "SKIN" in m.name.upper()][0]
        skin_total = sum(1 for i in self.orig_index["Face"] if i == skin_idx)
        skin_in_fragment = sum(1 for p in me.polygons
                               if all(v in ids for v in p.vertices) and self.orig_index["Face"][p.index] == skin_idx)
        bpy.data.objects.remove(lo)
        bpy.data.objects.remove(ao)
        return {"fragment_vertices": 588, "fragment_faces": faces_in_fragment,
                "skin_faces_total": skin_total, "skin_faces_in_fragment": skin_in_fragment,
                "skin_coverage_ratio": round(skin_in_fragment / skin_total, 4),
                "old_light_location_relative": "(+ext, -ext, +ext): behind a +Y-facing face",
                "old_shading": "flat (from_pydata, custom split normals dropped)"}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    s = Scene()
    legend_parts = s.run_parts()
    legend_mat = s.run_material()
    s.run_uniform("normals", normals_mat(), "emission")
    s.run_uniform("clay", clay_mat(False), "clay")
    s.run_uniform("wire", clay_mat(True), "clay")
    s.run_original()
    legacy = s.run_legacy588()
    assert sha(SRC) == s.src_sha, "source changed"
    qa = {
        "task_id": "MORWEN-HEAD-STRUCTURE-01",
        "source_vrm_sha256": s.src_sha, "source_modified": False,
        "blender_version": bpy.app.version_string, "engine": "CYCLES", "device": "CPU",
        "resolution": RES,
        "camera": {"type": "ORTHO", "ortho_scale_m": ORTHO_SCALE, "distance_m": CAM_DIST,
                   "anchor": "J_Bip_C_Head head joint + (0,0,%.2f) m" % CENTER_OFFSET_Z,
                   "center_world": [round(x, 5) for x in s.center],
                   "views": {k: list(v) for k, v in VIEWS.items()},
                   "identical_for_all_passes": True},
        "hidden_helpers": ["Icosphere (glTF_not_exported collection, importer bone-shape helper)"],
        "renders": s.records,
        "legend_parts_welded_components": legend_parts,
        "legend_materials": legend_mat,
        "normals_colour_key": {"front_face_seen": "blue", "back_face_seen": "red"},
        "legacy_588_ab": legacy,
        "G2": "NOT_ASSESSED", "G3": "DIAGNOSTIC_RENDERS_ONLY",
    }
    (OUT / "HEAD_DIAGNOSTIC_RENDER_QA.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n")
    print("HEAD diagnostics:", len(s.records), "renders")


if __name__ == "__main__":
    main()
