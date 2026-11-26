"""V75 isolated fixed-vista backdrop feasibility; original V73 unchanged, no game placement."""
import bpy,sys,math,hashlib,json,random,collections
from pathlib import Path
from array import array
from mathutils import Vector,Matrix
from mathutils.geometry import convex_hull_2d
from mathutils.bvhtree import BVHTree
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='9ae2baa35f9d9d11a17a720f1e8fa1dc7cda90e40275a581b788d118b66bfbf2'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
ext_name='V58_SCENIC_ONLY_terrain_extension'
src_name='A3 provisional reconstructed terrain'
attr='V19_ground_color'
def digest(data,prop,count,code):
    a=array(code,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    result={};cache={}
    for o in bpy.context.scene.objects:
        if o.type!='MESH':continue
        m=o.data
        if m.name not in cache:
            colors={a.name:(a.domain,a.data_type,digest(a.data,'color',len(a.data)*4,'f')) for a in m.color_attributes}
            uv={a.name:digest(a.data,'uv',len(a.data)*2,'f') for a in m.uv_layers}
            cache[m.name]=(digest(m.vertices,'co',len(m.vertices)*3,'f'),digest(m.loops,'vertex_index',len(m.loops),'i'),digest(m.polygons,'loop_start',len(m.polygons),'i'),digest(m.polygons,'loop_total',len(m.polygons),'i'),digest(m.polygons,'material_index',len(m.polygons),'i'),uv,colors,tuple(a.name if a else None for a in m.materials))
        result[o.name]=(cache[m.name],tuple(tuple(r) for r in o.matrix_world),o.hide_render,tuple(s.material.name if s.material else None for s in o.material_slots))
    return result

scene=bpy.context.scene
old=snap();assert len(old)==692,len(old)
qa=src.parent/'v73_qa.json';assert sha(qa)=='f133fec17bf731b35769b37eafb160373c496a5e43fde7a7cb1a51db4a768e65'
eye=Vector((78.17052459716797,-80.77701568603516,29.82533073425293))
aim=Vector((93.94316101074219,-93.07432556152344,30.988130569458008))
direction=Vector((.788631932636555,-.6148655745981655,0));direction.normalize();side=Vector((-direction.y,direction.x,0))
# Native source captures from two distinct existing mesh templates and one existing scan group.
# Isolate render scenes without modifying the original data or render visibility.
names=sorted(old)
t=next(n for n in names if n.startswith('V18_T_'))
d=next(n for n in names if n.startswith('V18_D_'))
hero=[n for n in names if n.startswith('V57_hero_A')]
assert hero
groups=[('oak_variant_a',[t]),('oak_variant_b',[d]),('scan_variant',hero)]
materials=[];captures=[]
def capture(label,names):
    sc=bpy.data.scenes.new('V75_CAPTURE_'+label);sc.world=scene.world
    sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.cycles.use_denoising=True
    sc.render.resolution_x=512;sc.render.resolution_y=512;sc.render.resolution_percentage=100;sc.render.film_transparent=True
    sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='16'
    originals=[bpy.data.objects[n] for n in names]
    corners=[o.matrix_world@Vector(p) for o in originals for p in o.bound_box]
    mn=Vector(tuple(min(p[i] for p in corners) for i in range(3)));mx=Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    pivot=Vector(((mn.x+mx.x)/2,(mn.y+mx.y)/2,mn.z))
    height=mx.z-mn.z;assert height>0
    focus=Vector((0,0,height/2))
    # square capture volume covers projection on the camera horizontal axis
    width=2*max(abs((p-pivot).dot(side)) for p in corners)
    extent=max(height,width)*1.15
    made=[]
    for obj in originals:
        o=bpy.data.objects.new('V75_capture_'+obj.name,obj.data);sc.collection.objects.link(o);o.matrix_world=Matrix.Translation(-pivot)@obj.matrix_world;made.append(o)
    camdata=bpy.data.cameras.new('V75_capture_cam');camdata.type='ORTHO';camdata.ortho_scale=extent;camdata.clip_end=200
    cam=bpy.data.objects.new('V75_capture_cam',camdata);sc.collection.objects.link(cam);cam.location=focus-direction*40;cam.rotation_euler=(focus-cam.location).to_track_quat('-Z','Y').to_euler();sc.camera=cam;made.append(cam)
    # Capture lighting is illustrative and fixed (not a PBR base-color bake).
    for i,(pos,power,col,size) in enumerate([((-12,-8,20),2200,(1,.92,.78),14),((10,7,15),1250,(.79,.91,1),14)]):
        ld=bpy.data.lights.new('V75_capture_light','AREA');ld.energy=power;ld.color=col;ld.shape='DISK';ld.size=size
        light=bpy.data.objects.new('V75_capture_light',ld);sc.collection.objects.link(light);light.location=Vector(pos);light.rotation_euler=(focus-light.location).to_track_quat('-Z','Y').to_euler();made.append(light)
    f=out/(label+'.exr');sc.render.filepath=str(f.resolve());bpy.ops.render.render(scene=sc.name,write_still=True)
    assert f.is_file()
    im=bpy.data.images.load(str(f.resolve()),check_existing=False);im.pack();assert tuple(im.size)==(512,512)
    # Verify transparent background and substantial nonzero alpha; EXR is scene-linear fixed lighting.
    arr=array('f',[0])*(512*512*4);im.pixels.foreach_get(arr);alpha=arr[3::4]
    assert min(alpha)<.01 and max(alpha)>.9 and sum(a>.5 for a in alpha)>5000
    assert max(alpha[:512]+alpha[-512:]+alpha[::512]+alpha[511::512])<.05,'capture clipped'
    mat=bpy.data.materials.new('V75_FAR_FIXED_'+label);mat.use_nodes=True;nt=mat.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
    tex=n.new('ShaderNodeTexImage');tex.image=im;tex.extension='CLIP'
    emission=n.new('ShaderNodeEmission');l.new(tex.outputs['Color'],emission.inputs['Color'])
    tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(tex.outputs['Alpha'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(emission.outputs[0],mix.inputs[2]);output=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],output.inputs['Surface'])
    # Only newly created capture objects/scenes are removed.
    if bpy.context.window: bpy.context.window.scene=scene
    for obj in made:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.scenes.remove(sc)
    captures.append({'label':label,'source_objects':names,'source_polygon_count':sum(len(o.data.polygons) for o in originals),'ortho_extent_m':extent,'source_height_m':height,'alpha_pixels':sum(a>.5 for a in alpha),'sha256':sha(f)})
    return mat,extent,height
for label,group in groups:materials.append(capture(label,group))
if bpy.context.window:bpy.context.window.scene=scene
assert snap()==old
# All cards must be outside the conservative original native bounds. No inferred canonical terrain or collision.
corners=[bpy.data.objects[n].matrix_world@Vector(p) for n in old for p in bpy.data.objects[n].bound_box]
xmin,ymin=min(p.x for p in corners),min(p.y for p in corners);xmax,ymax=max(p.x for p in corners),max(p.y for p in corners)
coll=bpy.data.collections.new('V75_SCENIC_ONLY_FIXED_VISTA');scene.collection.children.link(coll)
placed=[];rejected=[]
for j,dep in enumerate((75,100,125)):
    for i,offset in enumerate((-36,-24,-12,0,12,24,36)):
        mat,extent,height=materials[(i*3+j+i//2)%len(materials)]
        scale=.88+.09*((i*3+j*2)%5);size=extent*scale
        xy=eye+direction*dep+side*(offset+((j%2)*6-3));left=xy-side*size/2;right=xy+side*size/2
        lo=min(left.x,right.x);hi=max(left.x,right.x);bot=min(left.y,right.y);top=max(left.y,right.y)
        gap=math.hypot(max(0,xmin-hi,lo-xmax),max(0,ymin-top,bot-ymax))
        if gap<=.5:rejected.append({'depth':dep,'offset':offset,'reason':'conservative native bounds overlap'});continue
        # Deliberately illustrative far horizon base: local altar-height reference, not surveyed terrain.
        z=27.988129971478276-1.2*j-.4
        zc=z+height*scale/2;vv=[(left.x,left.y,zc-size/2),(right.x,right.y,zc-size/2),(right.x,right.y,zc+size/2),(left.x,left.y,zc+size/2)]
        name=f'V75_FAR_{j+1}_{i+1}';me=bpy.data.meshes.new(name);me.from_pydata(vv,[],[(0,1,2),(0,2,3)]);me.update()
        uv=me.uv_layers.new(name='UVMap');uvs=((0,0),(1,0),(1,1),(0,1))
        for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
        me.materials.append(mat);o=bpy.data.objects.new(name,me);coll.objects.link(o)
        o['scope']='fixed-vista scenic candidate, no runtime collision';o['not_canonical']=True
        placed.append({'id':name,'vertices':vv,'triangles':2,'depth_m':dep,'illustrative_base_z':z,'source_material':mat.name,'conservative_native_bbox_gap_m':gap})
assert len(placed)>=4,('no usable scenic backdrop',rejected)
bpy.context.view_layer.update()
s=snap();assert all(s[k]==v for k,v in old.items())
assert sha(src)==lock
dest=out/'v75_fixed_vista_feasibility.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()))
scene=bpy.context.scene
ss=snap();assert s==ss and sha(src)==lock
assert all(bpy.data.objects[x['id']].data.materials[0].node_tree.nodes for x in placed)
assert all(im.packed_file for im in bpy.data.images if im.name in [n.image.name for o in scene.objects if o.name.startswith('V75_FAR_') for n in o.data.materials[0].node_tree.nodes if n.type=='TEX_IMAGE'])
q={'status':'FIXED_VISTA_FEASIBILITY_NOT_RUNTIME','source_sha256':lock,'native_sha256':sha(dest),'blender':bpy.app.version_string,'protected_meshes_exact':len(old),'captures':captures,'placed':placed,'rejected':rejected,'added_triangles':2*len(placed),'native_bounds_xy':[xmin,ymin,xmax,ymax],'limits':['No surveyed terrain or canonical placement outside old scene; illustrative Z is not actual ground.','Fixed-light emission image, not PBR or dynamic relighting. No player reachability, depth impostor, 360 degree or Android acceptance.','Preserve all original terrain, materials, trees, events and collision. D4 and independent G2 not run.']}
(out/'v75_qa.json').write_text(json.dumps(q,indent=2)+'\n')
cam=scene.camera
assert scene.render.engine=='CYCLES' and scene.render.resolution_x==960 and scene.render.resolution_y==540
# Main baseline view exactly matches V73; second camera is explicitly a diagnostic, not a matched baseline.
for name,aa,bb in [('v75_matched',eye,aim),('v75_lateral_diagnostic',eye+side*8,aim)]:
    cam.location=aa;cam.rotation_euler=(bb-aa).to_track_quat('-Z','Y').to_euler();cam.data.lens=22
    scene.render.filepath=str((out/(name+'.png')).resolve());bpy.ops.render.render(write_still=True)
q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png','.exr')};(out/'v75_qa.json').write_text(json.dumps(q,indent=2)+'\n');print(q)
