"""TEST-ONLY fault injection for the engine acceptance loop (never a qualified operation).

Applies the #468 fixture correction (scale X to dimensions.x + delta) and additionally
disturbs one other quantity, so the Factory interference monitor must stop:
  width -> also scales Y by 1.01 (non-affected metric y_max/y_min moves)
  gap   -> also translates +Y by 0.2 (PASS lower-bound clearance 4.0 falls below L=3.9)
Usage: python fault_injection_blender.py -- correct FILE DELTA:KIND
"""
import sys

import bpy

mode, filename, value = sys.argv[sys.argv.index("--") + 1:]
if mode != "correct":
    raise SystemExit("fault injection supports only 'correct'")
delta, kind = value.split(":")
bpy.ops.wm.open_mainfile(filepath=filename)
obj = bpy.data.objects["target"]
obj.scale.x *= (obj.dimensions.x + float(delta)) / obj.dimensions.x
if kind == "width":
    obj.scale.y *= 1.01
elif kind == "gap":
    obj.location.y += 0.2
else:
    raise SystemExit("unknown fault kind")
bpy.context.view_layer.update()
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=filename)
