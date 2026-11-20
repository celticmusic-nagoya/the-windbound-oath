"""Reference-only Blender scene: embeds four verified Layer 0 PNGs. No sculpt."""
import bpy,sys,pathlib,hashlib,json,math
args=sys.argv[sys.argv.index('--')+1:]
src=pathlib.Path(args[0]);out=pathlib.Path(args[1]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene
refs=bpy.data.collections.new('REFERENCES__NON_MESH');scene.collection.children.link(refs)
sculpt=bpy.data.collections.new('SCULPT__EMPTY__AUTHOR_HERE');scene.collection.children.link(sculpt)
items=[]
for view,name,angle in [('front','7809.png',0),('right','7807.png',math.pi/2),('back','7810.png',math.pi),('left','7808.png',-math.pi/2)]:
 p=src/name
 im=bpy.data.images.load(str(p),check_existing=False)
 assert tuple(im.size)==(384,1024),(name,tuple(im.size))
 im.pack()
 ob=bpy.data.objects.new('REF_'+view.upper(),None);refs.objects.link(ob)
 ob.empty_display_type='IMAGE';ob.data=im;ob.empty_display_size=4.0
 ob.location=(0,0,2);ob.rotation_euler=(math.pi/2,0,angle)
 ob.show_in_front=True;ob.hide_render=True
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 ob['source_sha256']=sha;ob['reference_only']=True
 items.append({'view':view,'file':name,'sha256':sha,'dimensions':[384,1024]})
scene['production_status']='REFERENCE_ONLY_NO_SCULPT'
scene['axis_contract']='Z_UP_NEGATIVE_Y_FORWARD_PROVISIONAL_UNITS'
blend=out/'morwen_layer0_sculpt_reference_setup.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
(out/'source_manifest.json').write_text(json.dumps({'status':'REFERENCE_ONLY','sculpt_mesh_count':0,'blender':bpy.app.version_string,'references':items},indent=2)+'\n')
