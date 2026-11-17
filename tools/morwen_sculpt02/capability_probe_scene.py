import bpy,json,pathlib
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16)
ob=bpy.context.object;ob.name='CAPABILITY_PROBE_NOT_MORWEN'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':
  area.spaces.active.region_3d.view_distance=5
pathlib.Path('/workspace/morwen-input/gui_probe_state_02.json').write_text(json.dumps({'background':bpy.app.background,'window_count':len(bpy.context.window_manager.windows),'areas':[a.type for a in bpy.context.screen.areas],'version':bpy.app.version_string}))
