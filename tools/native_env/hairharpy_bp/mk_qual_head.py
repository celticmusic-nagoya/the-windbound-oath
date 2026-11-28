"""Neutral qualification head (not a TWO character): UV sphere r=0.1 scaled 0.82/0.95/1.18, exported Y-up OBJ."""
import sys
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.1)
h = bpy.context.active_object
h.name = "QUAL_head_neutral"
h.scale = (0.82, 0.95, 1.18)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.wm.obj_export(filepath=sys.argv[-1], export_selected_objects=True, forward_axis="NEGATIVE_Z", up_axis="Y",
                      export_materials=False)
