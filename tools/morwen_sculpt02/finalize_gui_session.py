import bpy,pathlib,json,hashlib,math
from mathutils import Quaternion
out=pathlib.Path('/workspace/morwen-sculpt02');body=bpy.data.objects['SCULPT02_FACE_BODY']
start=json.loads((out/'session_start.json').read_text())['working_start_coordinates'];key=body.data.shape_keys.key_blocks['SCULPT02_GUI_brush_layer'];delta=[(v.co-p.co).length for v,p in zip(key.data,body.data.shape_keys.key_blocks['PR399_frozen_start'].data)]
report={'status':'GUI_SCULPT_EXECUTED_UNAPPROVED','human_artist_present':False,'input_method':'Agent-directed XTest pointer drags in live Blender 4.3.2 GUI, not an analytic face-fit function','face_changed_vertices':sum(d>1e-7 for d in delta),'face_max_displacement':max(delta),'face_rms_displacement':(sum(d*d for d in delta)/len(delta))**.5,'face_topology_changed':False,'hair':[]}
for ob in bpy.data.collections['SCULPT02_AUTHORED_HAIR_MASSES'].objects:
 a=ob.data.shape_keys.key_blocks[0].data;b=ob.data.shape_keys.key_blocks[1].data;ds=[(x.co-y.co).length for x,y in zip(a,b)]
 report['hair'].append({'name':ob.name,'vertices':len(ob.data.vertices),'faces':len(ob.data.polygons),'GUI_changed_vertices':sum(d>1e-7 for d in ds),'GUI_max_displacement':max(ds)})
crown=key.data[8063].co;chin=key.data[8064].co;sole=min(v.co.z for v in key.data);report['head_count']=(crown.z-sole)/(crown.z-chin.z);report['crown']=list(crown);report['chin']=list(chin);report['sole']=sole
assert report['face_changed_vertices']>0;assert any(r['GUI_changed_vertices']>0 for r in report['hair']);assert len(report['hair'])==8
# Old body and all baseline geometry remain separately retained, hidden in both viewport/render.
old=bpy.data.objects['Morwen_anatomical_body_head_UNAPPROVED'];old_key=old.data.shape_keys.key_blocks['Morwen_proportion_and_face_study'].data
report['PR399_baseline_active_shape_unchanged']=all((v.co-q.co).length<1e-7 for v,q in zip(old_key,body.data.shape_keys.key_blocks['PR399_frozen_start'].data))
assert report['PR399_baseline_active_shape_unchanged']
body['status']='GUI_SCULPT_EXECUTED_UNAPPROVED';bpy.context.scene['sculpt02_status']='GUI_SCULPT_EXECUTED_UNAPPROVED';bpy.context.scene['G1']='BLOCKED';bpy.context.scene['G2']='NOT_APPROVED';bpy.context.scene['G4']='NOT_RUN'
if bpy.context.object.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
area=bpy.context.area;area.type='VIEW_3D';area.spaces.active.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
area.spaces.active.region_3d.view_location=(0,-.04,1.52);area.spaces.active.region_3d.view_distance=.32;area.spaces.active.shading.color_type='MATERIAL'
bpy.context.scene.camera=bpy.data.objects['SCULPT02_three_quarter']
text=bpy.data.texts.new('SCULPT02_ACTUAL_GEOMETRY_REPORT');text.write(json.dumps(report,indent=2))
path=out/'morwen_sculpt02_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
report['blend_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();(out/'geometry_difference.json').write_text(json.dumps(report,indent=2)+'\n')
