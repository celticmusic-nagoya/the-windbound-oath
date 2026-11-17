"""GUI-session blockout from individually authored control nets.
No angles, radial repeats, templates, or PR399 hair geometry are used.
Each net is a separate intentional mass; it still requires sculpt and art review.
"""
import bpy,bmesh,json,pathlib
NETS={
 'Occipital_continuous_mass':[
 [(-.038,-.078,1.612),(-.044,-.040,1.625),(-.033,-.005,1.631),(-.018,.014,1.634),(.004,.020,1.635),(.025,.014,1.632),(.042,-.006,1.625),(.047,-.043,1.615),(.040,-.080,1.606)],
 [(-.081,-.105,1.582),(-.094,-.056,1.596),(-.083,.020,1.599),(-.045,.062,1.603),(.005,.074,1.606),(.055,.061,1.600),(.092,.019,1.592),(.104,-.053,1.582),(.087,-.105,1.570)],
 [(-.088,-.113,1.518),(-.103,-.055,1.530),(-.096,.028,1.540),(-.049,.078,1.548),(.008,.083,1.553),(.061,.073,1.548),(.104,.017,1.534),(.110,-.053,1.516),(.091,-.108,1.502)],
 [(-.086,-.108,1.452),(-.105,-.048,1.457),(-.098,.026,1.466),(-.048,.071,1.470),(.012,.078,1.480),(.069,.059,1.473),(.109,.009,1.452),(.107,-.054,1.441),(.086,-.107,1.432)],
 [(-.065,-.094,1.405),(-.089,-.046,1.409),(-.084,.021,1.423),(-.037,.056,1.416),(.018,.061,1.427),(.069,.045,1.415),(.092,-.002,1.403),(.088,-.058,1.402),(.068,-.097,1.414)]],
 'Left_face_framing_sweep':[
 [(-.035,-.082,1.618),(-.047,-.075,1.623),(-.059,-.062,1.615)],
 [(-.063,-.133,1.570),(-.083,-.121,1.572),(-.094,-.100,1.566)],
 [(-.076,-.143,1.505),(-.098,-.123,1.508),(-.108,-.099,1.496)],
 [(-.071,-.126,1.447),(-.097,-.110,1.440),(-.105,-.087,1.449)],
 [(-.055,-.105,1.410),(-.079,-.102,1.398),(-.087,-.084,1.415)]],
 'Right_temple_tucked_mass':[
 [(.033,-.086,1.615),(.047,-.074,1.620),(.057,-.063,1.610)],
 [(.064,-.133,1.569),(.087,-.119,1.565),(.099,-.096,1.556)],
 [(.072,-.138,1.506),(.100,-.116,1.505),(.112,-.088,1.490)],
 [(.069,-.117,1.446),(.097,-.095,1.437),(.103,-.071,1.444)],
 [(.057,-.101,1.423),(.079,-.084,1.408),(.084,-.062,1.427)]],
 'Fringe_long_diagonal_left':[
 [(.004,-.067,1.631),(.016,-.072,1.635),(.029,-.065,1.630)],
 [(-.032,-.110,1.606),(-.009,-.123,1.612),(.017,-.113,1.605)],
 [(-.064,-.147,1.569),(-.042,-.159,1.564),(-.013,-.151,1.567)],
 [(-.071,-.151,1.545),(-.052,-.161,1.535),(-.027,-.153,1.547)]],
 'Fringe_right_broad_turn':[
 [(.019,-.065,1.633),(.030,-.068,1.631),(.041,-.059,1.624)],
 [(.027,-.113,1.609),(.052,-.117,1.604),(.073,-.103,1.592)],
 [(.041,-.149,1.569),(.068,-.151,1.560),(.084,-.132,1.547)],
 [(.037,-.153,1.548),(.059,-.156,1.539),(.080,-.137,1.516)]],
 'Fringe_parting_secondary':[
 [(.017,-.074,1.631),(.022,-.077,1.633),(.028,-.074,1.630)],
 [(.003,-.129,1.592),(.019,-.136,1.591),(.034,-.127,1.588)],
 [(-.011,-.156,1.555),(.008,-.162,1.550),(.023,-.153,1.558)],
 [(-.016,-.159,1.544),(-.002,-.163,1.532),(.012,-.157,1.545)]],
 'Left_secondary_inward_lock':[
 [(-.075,-.086,1.554),(-.091,-.075,1.553),(-.099,-.061,1.545)],
 [(-.085,-.105,1.500),(-.109,-.080,1.492),(-.111,-.059,1.485)],
 [(-.080,-.090,1.448),(-.104,-.067,1.432),(-.100,-.048,1.439)],
 [(-.062,-.069,1.415),(-.082,-.055,1.404),(-.082,-.043,1.419)]]
}

def main():
 if bpy.context.object and bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 coll=bpy.data.collections.new('SCULPT02_AUTHORED_HAIR_MASSES');bpy.context.scene.collection.children.link(coll)
 mat=bpy.data.materials.new('SCULPT02_canonical_deep_violet');mat.diffuse_color=(.065,.018,.112,1);mat.use_nodes=True
 node=mat.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=(.065,.018,.112,1);node.inputs['Roughness'].default_value=.42
 for name,rows in NETS.items():
  n=len(rows);m=len(rows[0]);assert all(len(r)==m for r in rows)
  verts=[p for row in rows for p in row];faces=[(i*m+j,(i+1)*m+j,(i+1)*m+j+1,i*m+j+1) for i in range(n-1) for j in range(m-1)]
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
  ob=bpy.data.objects.new('SCULPT02_HAIR_'+name,me);coll.objects.link(ob);me.materials.append(mat);bpy.context.view_layer.objects.active=ob
  sub=ob.modifiers.new('authored_net_refinement','SUBSURF');sub.levels=2;bpy.ops.object.modifier_apply(modifier=sub.name)
  sol=ob.modifiers.new('real_sculpt_volume','SOLIDIFY');sol.thickness=.007 if name.startswith('Occipital') else .005;sol.offset=0;bpy.ops.object.modifier_apply(modifier=sol.name)
  for p in ob.data.polygons:p.use_smooth=True
  ob.shape_key_add(name='Authored_control_net_volume');key=ob.shape_key_add(name='GUI_sculpt_pass');key.value=1;ob.active_shape_key_index=1
  sub=ob.modifiers.new('sculpt_surface_preview','SUBSURF');sub.levels=1;sub.render_levels=2
  ob['method']='individually_authored_nonuniform_control_net_then_GUI_sculpt';ob['final_art_approved']=False
 pathlib.Path('/workspace/morwen-sculpt02/authored_hair_control_nets.json').write_text(json.dumps(NETS,indent=2)+'\n')
 body=bpy.data.objects['SCULPT02_FACE_BODY'];bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 bpy.ops.object.mode_set(mode='SCULPT')
 area=bpy.context.area;area.type='VIEW_3D'
 from mathutils import Quaternion
 import math
 area.spaces.active.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
 bpy.context.scene.tool_settings.unified_paint_settings.size=42
 b=bpy.data.brushes['ART02_Grab'];b.strength=.5;b.curve_preset='SMOOTH'
 bpy.ops.wm.save_as_mainfile(filepath='/workspace/morwen-sculpt02/sculpt02_face_profile_and_hair_blockout.blend',compress=True)
main()
