"""Fail-fast preflight for Blender render/export runtime. No geometry changes."""
import json,sys,importlib.util
from pathlib import Path
import bpy
root=Path(__file__).resolve().parents[3]
out=root/"assets/candidates/morwen-blender-27"
out.mkdir(parents=True,exist_ok=True)
checks={
 "blender_version":list(bpy.app.version),
 "numpy_available":importlib.util.find_spec("numpy") is not None,
 "gltf_exporter_available":hasattr(bpy.ops.export_scene,"gltf"),
 "render_engine_available":("BLENDER_EEVEE" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys() or
     "BLENDER_EEVEE_NEXT" in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items.keys()),
}
checks["ready"]=bool(checks["numpy_available"] and checks["gltf_exporter_available"] and checks["render_engine_available"])
(out/"preflight.json").write_text(json.dumps(checks,indent=2)+"\n")
print("MORWEN_27_PREFLIGHT",json.dumps(checks))
if not checks["ready"]:sys.exit(2)
