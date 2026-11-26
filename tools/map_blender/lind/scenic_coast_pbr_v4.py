"""Native offshore material comparison on exact V3; no topology or placement edits."""
import bpy,sys,json,hashlib
from pathlib import Path
from array import array
from mathutils import Vector
src,photos,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='ff4f9c64a31da6d961b2d3473293e38b084be12634bd76d318d80c6c01c1b7e1'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()),load_ui=False)
scene=bpy.context.scene;target=bpy.data.objects['Offshore coastal strata | provisional']
def dg(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(dg(o.data.vertices,'co',len(o.data.vertices)*3,'f'),dg(o.data.loops,'vertex_index',len(o.data.loops),'i'),dg(o.data.polygons,'material_index',len(o.data.polygons),'i'),tuple(tuple(row) for row in o.matrix_world),tuple(m.name if m else None for m in o.data.materials) if o.name!=target.name else ()) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.context.view_layer.update();old=snap()
assert len(target.data.materials)==2
records={}
for i,asset in enumerate(('rock_boulder_dry','sparse_grass')):
    folder=photos/asset;rec=json.loads((folder/'manifest.json').read_text());assert rec['license']=='CC0';records[asset]={}
    oldmat=target.data.materials[i];m=oldmat.copy();m.name='F01_V4_'+asset;nt=m.node_tree;n=nt.nodes;l=nt.links
    bs=next(x for x in n if x.type=='BSDF_PRINCIPLED')
    # Native object-space box projection; preserve existing UV and exact mesh geometry.
    texcoord=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='SCALE'
    mapping.inputs['Scale'].default_value=.24 if i==0 else .5;l.new(texcoord.outputs['Object'],mapping.inputs[0])
    for role,key in (('basecolor','Base Color'),('roughness','Roughness'),('normal','Normal')):
        v=rec['textures'][role];p=folder/v['path'];assert sha(p)==v['sha256'];records[asset][role]=v['sha256']
        image=bpy.data.images.load(str(p.resolve()),check_existing=True);image.colorspace_settings.name=v['color_space'];image.pack()
        q=n.new('ShaderNodeTexImage');q.image=image;q.projection='BOX';q.projection_blend=.22;l.new(mapping.outputs['Vector'],q.inputs['Vector'])
        if role=='basecolor':
            # Mild atmosphere-inspired colour grade while preserving photographic detail.
            mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.45;mix.inputs[2].default_value=(.53,.64,.80,1) if i==0 else (.65,.76,.65,1)
            l.new(q.outputs['Color'],mix.inputs[1]);l.new(mix.outputs[0],bs.inputs[key])
        elif role=='normal':
            # Box-projected normal is not a tangent-UV normal. Retain source map packed,
            # use roughness-derived microrelief as a scalar bump rather than invalid tangent transform.
            pass
        else:
            l.new(q.outputs['Color'],bs.inputs[key]);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.25;bump.inputs['Distance'].default_value=.11
            l.new(q.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    target.data.materials[i]=m
bpy.context.view_layer.update();assert snap()==old and sha(src)==lock
scene.camera=bpy.data.objects['F01_diagnostic'];scene.render.image_settings.file_format='PNG'
dest=out/'cliff_coast_pbr_v4_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()),load_ui=False);scene=bpy.context.scene;target=bpy.data.objects['Offshore coastal strata | provisional']
assert snap()==old and sha(src)==lock
q=dict(status='ISOLATED_NATIVE_MATERIAL_COMPARISON',source_sha256=lock,protected_meshes=len(old),geometry_material_indices_transforms_exact=True,material_sources=records,native_reopen='PASS',limits=['No scan geometry added, no silhouette correction, no GLB bake or runtime. Photo normal packed but intentionally not connected to box projection; scalar bump approximation from roughness. No G1/D4/G2/G4 acceptance.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.render.filepath=str((out/'candidate.png').resolve());bpy.ops.render.render(write_still=True);finish()
d=bpy.data.cameras.new('V4 oblique');o=bpy.data.objects.new('V4 oblique',d);scene.collection.objects.link(o)
o.location=(-105,-1,37);o.rotation_euler=(Vector((-25,-100,5))-o.location).to_track_quat('-Z','Y').to_euler();d.lens=34;d.clip_end=500
scene.camera=o;scene.render.filepath=str((out/'oblique.png').resolve());bpy.ops.render.render(write_still=True);finish()
