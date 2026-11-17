"""Prepare an editable GUI sculpt session; does NOT sculpt or auto-fit the face.
Blender CLI: -- source.blend canonical_dir output.blend
"""
import bpy
import hashlib,json,pathlib,sys,math
from mathutils import Vector,Quaternion
src,canon,dest=map(pathlib.Path,sys.argv[sys.argv.index('--')+1:])
assert hashlib.sha256(src.read_bytes()).hexdigest()=='4e818c24d9d05258bd0c4f5a1cc6116826807a234aa7819f65fc49cc01f307d7'
for f in json.loads((canon/'MANIFEST.json').read_text())['files']:
 assert hashlib.sha256((canon/f['filename']).read_bytes()).hexdigest()==f['sha256']
bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False,use_scripts=False)
sc=bpy.context.scene
baseline=bpy.data.collections.new('PR399_REJECTED_BASELINE_DO_NOT_EDIT');sc.collection.children.link(baseline)
working=bpy.data.collections.new('SCULPT02_WORKING_NONAPPROVED');sc.collection.children.link(working)
meshobs=[o for o in bpy.data.objects if o.type=='MESH']
for ob in meshobs:
 for coll in list(ob.users_collection):coll.objects.unlink(ob)
 baseline.objects.link(ob)
baseline.hide_viewport=True;baseline.hide_render=True
source=bpy.data.objects['Morwen_anatomical_body_head_UNAPPROVED']
body=source.copy();body.data=source.data.copy();body.name='SCULPT02_FACE_BODY';working.objects.link(body)
# Freeze the already delivered PR399 mixed coordinates, without fitting anything.
coords=[v.co.copy() for v in source.data.shape_keys.key_blocks['Morwen_proportion_and_face_study'].data]
body.shape_key_clear()
for v,p in zip(body.data.vertices,coords):v.co=p
body.shape_key_add(name='PR399_frozen_start')
key=body.shape_key_add(name='SCULPT02_GUI_brush_layer');key.value=1;body.active_shape_key_index=1
# Mask only the protected crown/body; no displacement is computed here.
mask=body.data.attributes.get('.sculpt_mask') or body.data.attributes.new('.sculpt_mask','FLOAT','POINT')
for i,p in enumerate(coords):mask.data[i].value=1 if p.z<1.420 or p.z>1.600 else 0
for ob in meshobs:
 if ob==source or ob.name.startswith(('Bob_','Fringe_','Brow_')):continue
 new=ob.copy();new.data=ob.data.copy();new.name='SCULPT02_'+ob.name;working.objects.link(new)
# Copy the six fixed review views; source camera remains retained.
evidence=json.loads((src.parent/'build_evidence.json').read_text())
for view in evidence['views'][:6]:
 cd=bpy.data.cameras.new('SCULPT02_'+view['name']);cam=bpy.data.objects.new(cd.name,cd);sc.collection.objects.link(cam)
 cd.type='ORTHO';cd.ortho_scale=view['ortho_scale'];cam.location=view['camera'];cam.rotation_euler=(Vector(view['target'])-cam.location).to_track_quat('-Z','Y').to_euler()
sc.camera=bpy.data.objects['SCULPT02_front']
# Two-point visual registration. Hair crown is a proxy, NOT anatomical proof.
chin=coords[8064];crown=coords[8063]
references=bpy.data.collections.new('SCULPT02_REFERENCE_REGISTRATION_PROVISIONAL');sc.collection.children.link(references)
register={
 'front':{'file':'LAYER0_FRONT.png','chin_px':[213,181],'hair_crown_px':[211,19], 'landmarks_px':{'brow_left':[188,112],'brow_right':[237,112],'eye_outer_left':[174,123],'eye_inner_left':[202,126],'eye_inner_right':[224,126],'eye_outer_right':[252,123],'nose_tip':[214,144],'lip_line':[213,160],'chin':[213,181],'ear_visible_left':[171,143],'hair_part':[216,39],'bangs_center':[213,108],'bob_left':[123,171],'bob_right':[300,171]},'hidden':['anatomical_crown','most_ear_contours']},
 'profile':{'file':'LAYER0_PROFILE_FACING_LEFT.png','chin_px':[125,176],'hair_crown_px':[176,18], 'landmarks_px':{'brow':[123,109],'eye_visible_corner':[128,123],'nose_tip':[99,139],'lip_line':[109,158],'chin':[125,176],'ear':[183,124],'hair_part':[174,31],'bangs':[115,111],'bob_back':[270,162]},'hidden':['anatomical_crown','far_eye_corners']}
}
for label,row in register.items():
 image=bpy.data.images.load(str(canon/row['file']),check_existing=False);image.pack()
 scale=(crown.z+.010-chin.z)/(row['chin_px'][1]-row['hair_crown_px'][1])
 # Full-resolution image, exact original aspect. Pixel positions use top-left origin.
 w,h=image.size;ax,ay=row['chin_px']
 locz=chin.z+(ay-h/2)*scale
 ob=bpy.data.objects.new('SCULPT02_REF_'+label,None);references.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=image;ob.empty_display_size=max(w,h)*scale;ob.color=(1,1,1,.22);ob.empty_image_depth='FRONT';ob.show_in_front=True;ob.hide_render=True
 if label=='front':
  ob.rotation_euler=(math.pi/2,0,0);ob.location=((w/2-ax)*scale,-.23,locz)
  mapping={'x_per_pixel':scale,'x_zero_pixel':ax,'z_per_pixel':-scale,'z_zero_pixel':ay,'z_at_zero':chin.z}
 else:
  # Local x -> world +Y, local y -> world +Z. Camera at +X sees a left-facing profile.
  from mathutils import Matrix
  ob.rotation_euler=Matrix(((0,0,1),(1,0,0),(0,1,0))).to_euler();ob.location=(.23,chin.y+(w/2-ax)*scale,locz)
  mapping={'y_per_pixel':scale,'y_zero_pixel':ax,'y_at_zero':chin.y,'z_per_pixel':-scale,'z_zero_pixel':ay,'z_at_zero':chin.z}
 ob['registration']='PROVISIONAL_CHIN_PLUS_HAIR_CROWN_PROXY; NOT VERIFIED ORTHOGRAPHIC ANATOMY';row['world_units_per_pixel']=scale;row['mapping']=mapping
 row['anchor_note']='Only chin and visible hair-crown registered; source art is stylized, not a measured orthographic scan. No image-driven face fitting.'
# Hide reference overlays initially: enable one view at a time for GUI checking.
references.hide_viewport=True
bpy.ops.object.select_all(action='DESELECT');body.hide_set(False);body.select_set(True);bpy.context.view_layer.objects.active=body
# Do not activate Sculpt Mode headlessly; GUI will activate and record actual strokes.
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':
   area.spaces.active.region_3d.view_location=(0,-.04,1.52);area.spaces.active.region_3d.view_distance=.32;area.spaces.active.region_3d.view_perspective='ORTHO';area.spaces.active.region_3d.view_rotation=Quaternion((1,0,0),math.pi/2)
   area.spaces.active.shading.type='SOLID';area.spaces.active.shading.color_type='MATERIAL';area.spaces.active.overlay.show_floor=False
body['status']='PREPARED_NOT_SCULPTED';sc['sculpt02_status']='PREPARED_NOT_SCULPTED'
text=bpy.data.texts.new('SCULPT02_SESSION_README');text.write('UNAPPROVED. PR399 baseline is hidden and immutable evidence. Working face starts with identical delivered coordinates. No face fitting or radial hair generator is run. Reference scale is provisional chin/hair-crown registration; skull crown is hidden in art. New brush strokes must be logged and QA reviewed.\n')
dest.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(dest),compress=True)
(dest.parent/'reference_registration.json').write_text(json.dumps({'status':'PROVISIONAL_VISUAL_REGISTRATION','G1':'BLOCKED','views':register},indent=2)+'\n')
(dest.parent/'session_start.json').write_text(json.dumps({'status':'PREPARED_NOT_SCULPTED','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'working_start_coordinates':[list(p) for p in coords],'baseline_vertices':len(coords),'source_vertex_crown':8063,'source_vertex_chin':8064},indent=2)+'\n')
