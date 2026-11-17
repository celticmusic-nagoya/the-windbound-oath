import bpy,bmesh,json,pathlib
if bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
# Preserve the rejected root bridge, not delete it.
old=bpy.data.objects['SCULPT02_HAIR_Crown_parting_bridge'];old.hide_render=True;old.hide_set(True);old['status']='REJECTED_ROOT_BRIDGE_RETAINED_NOT_RENDERED'
rows=[
 [(-.064,-.142,1.565),(-.032,-.148,1.587),(0,-.151,1.594),(.032,-.147,1.588),(.064,-.139,1.560)],
 [(-.075,-.110,1.590),(-.040,-.112,1.620),(0,-.114,1.628),(.040,-.111,1.623),(.078,-.106,1.586)],
 [(-.080,-.060,1.610),(-.042,-.060,1.640),(0,-.061,1.648),(.042,-.059,1.640),(.081,-.055,1.604)],
 [(-.077,-.010,1.608),(-.040,-.010,1.631),(0,-.009,1.640),(.040,-.010,1.630),(.078,-.010,1.603)],
 [(-.062,.038,1.590),(-.032,.040,1.612),(0,.041,1.620),(.032,.040,1.609),(.064,.035,1.584)]]
me=bpy.data.meshes.new('Crown_continuity_mass');me.from_pydata([p for row in rows for p in row],[],[(i*5+j,(i+1)*5+j,(i+1)*5+j+1,i*5+j+1) for i in range(4) for j in range(4)]);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
ob=bpy.data.objects.new('SCULPT02_HAIR_Crown_continuity_mass',me);bpy.data.collections['SCULPT02_AUTHORED_HAIR_MASSES'].objects.link(ob);me.materials.append(bpy.data.materials['SCULPT02_canonical_deep_violet']);bpy.context.view_layer.objects.active=ob
sub=ob.modifiers.new('authored_net_refinement','SUBSURF');sub.levels=2;bpy.ops.object.modifier_apply(modifier=sub.name);sol=ob.modifiers.new('closed_volume','SOLIDIFY');sol.thickness=.006;sol.offset=0;bpy.ops.object.modifier_apply(modifier=sol.name)
for p in ob.data.polygons:p.use_smooth=True
ob.shape_key_add(name='Authored_control_net_volume');key=ob.shape_key_add(name='GUI_sculpt_pass');key.value=1;ob.active_shape_key_index=1
sub=ob.modifiers.new('sculpt_surface_preview','SUBSURF');sub.levels=1;sub.render_levels=2
p=pathlib.Path('/workspace/morwen-sculpt02/authored_hair_control_nets.json');r=json.loads(p.read_text());r['Crown_continuity_mass']=rows;p.write_text(json.dumps(r,indent=2)+'\n')
bpy.context.area.type='VIEW_3D'
# Export as a new version; prior sculpt file stays intact.
path='/workspace/morwen-sculpt02/morwen_sculpt02_v02_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=path,compress=True)
