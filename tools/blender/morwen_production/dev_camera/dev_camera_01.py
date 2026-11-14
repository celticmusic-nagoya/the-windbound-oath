"""Non-destructive Blender developer inspection camera.

Usage (Blender Python): exec(open(__file__).read()); install()
The developer camera lives in a separate collection. It never edits mesh,
materials, armatures, shape keys, or the scene's production camera.
Blender 4.x/5.x. Save a copy of the project for interactive inspection.
"""
import bpy
from mathutils import Vector

COLLECTION = "DEV_CAMERA_01"
PRESETS = {
    "front": (0, -1, 0),
    "back": (0, 1, 0),
    "left": (-1, 0, 0),
    "right": (1, 0, 0),
    "quarter_left": (-0.70710678, -0.70710678, 0),
    "quarter_right": (0.70710678, -0.70710678, 0),
    "high": (0, -0.8, 0.6),
}


def _target_point(focus):
    if focus == "eyes":
        face = bpy.data.objects.get("Face")
        if face is None:
            raise RuntimeError("Face object is required for eyes focus")
        # Approximate view target only; never a canonical landmark.
        return face.matrix_world @ Vector((0, 0, 1.44589))
    if focus == "face":
        obj = bpy.data.objects.get("Face")
    else:
        obj = bpy.data.objects.get("Body") or bpy.data.objects.get("Face")
    if obj is None:
        raise RuntimeError("No Face/Body object to inspect")
    return obj.matrix_world @ (sum((Vector(p) for p in obj.bound_box), Vector()) / 8)


def install(preset="front", focus="face", distance=0.65):
    if preset not in PRESETS:
        raise ValueError(f"Unknown preset {preset}")
    if not 0.08 <= distance <= 10:
        raise ValueError("Distance outside safe camera bounds")
    scene = bpy.context.scene
    original_camera = scene.camera
    coll = bpy.data.collections.get(COLLECTION)
    if coll is None:
        coll = bpy.data.collections.new(COLLECTION)
        scene.collection.children.link(coll)
    cam = bpy.data.objects.get("DEV_INSPECTION_CAMERA")
    if cam is None:
        data = bpy.data.cameras.new("DEV_INSPECTION_CAMERA_DATA")
        cam = bpy.data.objects.new("DEV_INSPECTION_CAMERA", data)
        coll.objects.link(cam)
    elif cam.type != "CAMERA" or cam.name not in coll.objects:
        raise RuntimeError("Developer camera name collision")
    target = _target_point(focus)
    offset = Vector(PRESETS[preset]).normalized() * distance
    cam.location = target + offset
    direction = target - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(0.12, distance * 0.9)
    cam["dev_only"] = True
    cam["preset"] = preset
    cam["focus"] = focus
    # Viewport camera is set only for the currently open 3D views.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                if space.region_3d:
                    space.region_3d.view_perspective = "CAMERA"
                    space.region_3d.view_camera_zoom = 0
                    space.camera = cam
    # Production scene camera is never reassigned.
    assert scene.camera == original_camera
    return cam


def verify():
    scene = bpy.context.scene
    cam = bpy.data.objects.get("DEV_INSPECTION_CAMERA")
    if cam is None or cam.type != "CAMERA":
        raise RuntimeError("Missing developer camera")
    if not cam.get("dev_only"):
        raise RuntimeError("Camera lacks developer-only marker")
    return {"camera": cam.name, "dev_only": True, "scene_camera": scene.camera.name if scene.camera else None,
            "mesh_unchanged_by_design": True, "G2": "NOT_RUN", "G3": "NOT_RUN", "G4": "NOT_RUN"}


if __name__ == "__main__":
    install()
    print(verify())
