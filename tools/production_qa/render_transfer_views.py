"""Render body and head views from the saved editable VRM 1.0 import."""
from mathutils import Vector
from pathlib import Path
import sys

import _cycles
import bpy

out = Path(sys.argv[sys.argv.index("--") + 1])
out.mkdir(exist_ok=False)
scene = bpy.context.scene
rig, = [obj for obj in scene.objects if obj.type == "ARMATURE"]
human = rig.data.vrm_addon_extension.vrm1.humanoid.human_bones


def bone(name):
    return rig.data.bones[getattr(human, name).node.bone_name]


def joint(name):
    return rig.matrix_world @ bone(name).head_local


left = joint("left_upper_arm") - joint("right_upper_arm")
up = joint("head") - joint("hips")
forward = left.cross(up).normalized()
if forward.dot(Vector((0, -1, 0))) < 0.95:
    raise RuntimeError("imported humanoid orientation does not match the comparison cameras")

head = bone("head")
head_bones = {b.name for b in (head, *head.children_recursive)}
head_points = []
for obj in scene.objects:
    if obj.type != "MESH":
        continue
    groups = {group.index for group in obj.vertex_groups if group.name in head_bones}
    for vertex in obj.data.vertices:
        if any(weight.group in groups and weight.weight > 0.25 for weight in vertex.groups):
            head_points.append(obj.matrix_world @ vertex.co)


def framing(points):
    lo = Vector(tuple(min(v[axis] for v in points) for axis in range(3)))
    hi = Vector(tuple(max(v[axis] for v in points) for axis in range(3)))
    return (hi + lo) * 0.5, max(hi - lo)


corners = [obj.matrix_world @ Vector(point) for obj in scene.objects if obj.type == "MESH"
           for point in obj.bound_box]
if not corners or not head_points:
    raise RuntimeError("missing body or weighted head geometry for comparison")
center, size = framing(corners)
head_center, head_size = framing(head_points)
if not 0 < head_size < size:
    raise RuntimeError("degenerate body or head framing")
bpy.ops.object.camera_add()
camera = bpy.context.object
camera.data.type = "ORTHO"
scene.camera = camera
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.use_denoising = getattr(_cycles, "with_openimagedenoise", False)
scene.cycles.samples = 16
scene.render.resolution_x = scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
for where, strength in [((2, -3, 3), 500), ((-2, 2, 3), 350), ((0, 4, 1), 160)]:
    bpy.ops.object.light_add(type="AREA", location=center + Vector(where) * size)
    light = bpy.context.object
    light.data.energy = strength * size ** 2
    light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
for name, offset, target, scale in (
    ("minus-y", (0, -1, 0), center, size * 1.15),
    ("plus-x", (1, 0, 0), center, size * 1.15),
    ("plus-y", (0, 1, 0), center, size * 1.15),
    ("minus-x", (-1, 0, 0), center, size * 1.15),
    ("face-front", (0, -1, 0), head_center, head_size * 1.45),
    ("hair-three-quarter", (1, 1, 0), head_center, head_size * 1.45),
):
    camera.location = target + Vector(offset).normalized() * (size * 3)
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.ortho_scale = scale
    scene.render.filepath = str(out / f"{name}.png")
    bpy.ops.render.render(write_still=True)
