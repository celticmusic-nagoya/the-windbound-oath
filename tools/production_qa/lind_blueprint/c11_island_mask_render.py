"""Tint the faces that are NOT present in the SHA-pinned Method C carrier (i.e. the
Method D repair islands) over neutral clay, from the fixed close-up cameras.
Diagnostic only; never saves the blend.

  blender -b --factory-startup --python c11_island_mask_render.py -- CAND.blend METHOD_C.blend OUT_DIR TAG
"""
import bpy, sys
from pathlib import Path
from mathutils import Vector

cand, mc, out, tag = sys.argv[sys.argv.index("--") + 1:]
out = Path(out)
out.mkdir(parents=True, exist_ok=True)
T = "Cliff C8 B | joinable coastal segment"
rk = lambda c: (round(c[0], 6), round(c[1], 6), round(c[2], 6))
bpy.ops.wm.open_mainfile(filepath=mc)
m = bpy.data.objects[T].data
cf = {tuple(sorted(rk(m.vertices[i].co) for i in p.vertices)) for p in m.polygons}
bpy.ops.wm.open_mainfile(filepath=cand)
obj = bpy.data.objects[T]
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 16
scene.render.resolution_x, scene.render.resolution_y = 1000, 720
scene.world.color = (0.18, 0.18, 0.18)


def mat(name, rgb):
    mt = bpy.data.materials.new(name)
    mt.use_nodes = True
    b = mt.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = 0.8
    return mt
clay, tint = mat("clay", (0.2, 0.2, 0.2)), mat("tint", (0.35, 0.08, 0.05))
for o in scene.objects:
    if o.type == "MESH":
        o.data.materials.clear()
        o.data.materials.append(clay)
obj.data.materials.append(tint)
me = obj.data
for p in me.polygons:
    p.material_index = 1 if tuple(sorted(rk(me.vertices[i].co) for i in p.vertices)) not in cf else 0
cd = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cd)
scene.collection.objects.link(cam)
scene.camera = cam
cd.type = "ORTHO"
center = Vector((-5.95, 0.0, 2.35))
ld = bpy.data.lights.new("key", "AREA")
light = bpy.data.objects.new("key", ld)
scene.collection.objects.link(light)
light.location = center + Vector((-4, -5, 9))
ld.energy, ld.shape, ld.size = 2200, "DISK", 8
for name, tgt, off, sc in (("front", center, (0, -12, 5), 9.5),
                           ("close_west", Vector((-7.8, 0, 3.9)), (0, -12, 2.5), 4.2),
                           ("close_central", Vector((-5.75, 0, 4.6)), (0, -12, 2.5), 4.2)):
    cd.ortho_scale = sc
    cam.location = tgt + Vector(off)
    cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(out / f"{tag}_mask_{name}.png")
    bpy.ops.render.render(write_still=True)
