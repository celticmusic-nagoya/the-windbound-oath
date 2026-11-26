"""V4 bounded native material composition; preserve all V3 geometry and navigation envelope."""
import bpy, sys, json, hashlib
from pathlib import Path
from array import array
src,pkg,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
lock='72980be4c2dba240ecdf20e578eddac9ddc8657f8102438939ed9600dc1a4774'
assert bpy.app.version[:3]==(5,3,0) and sha(src)==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
scene=bpy.context.scene;ground=bpy.data.objects['V3_village_reconstructed_patch']
def dg(data,prop,count,typ):
    a=array(typ,[0])*count
    if count:data.foreach_get(prop,a)
    return hashlib.sha256(a.tobytes()).hexdigest()
def snap():
    return {o.name:(dg(o.data.vertices,'co',len(o.data.vertices)*3,'f'),dg(o.data.loops,'vertex_index',len(o.data.loops),'i'),dg(o.data.polygons,'loop_total',len(o.data.polygons),'i'),tuple((u.name,dg(u.data,'uv',len(u.data)*2,'f')) for u in o.data.uv_layers),tuple(tuple(row) for row in o.matrix_world),tuple(m.name if m else None for m in o.data.materials) if o!=bpy.data.objects[ground.name] else ()) for o in bpy.context.scene.objects if o.type=='MESH'}
old=snap();assert len(old)==77
grass,road=list(ground.data.materials);assert grass.name=='grass' and road.name=='road'
mat=bpy.data.materials.new('V4 continuous verge PBR');mat.use_nodes=True
nt=mat.node_tree;n=nt.nodes;l=nt.links;n.clear()
output=n.new('ShaderNodeOutputMaterial')
geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0])
def mathnode(op,a,b=None):
    q=n.new('ShaderNodeMath');q.operation=op
    for i,x in enumerate((a,b)):
        if x is None:continue
        if isinstance(x,(int,float)):q.inputs[i].default_value=x
        else:l.new(x,q.inputs[i])
    return q.outputs[0]
def noise(scale,detail):
    q=n.new('ShaderNodeTexNoise');q.inputs['Scale'].default_value=scale;q.inputs['Detail'].default_value=detail;l.new(geo.outputs['Position'],q.inputs['Vector']);return q.outputs['Fac']
def smooth(v,lo,hi):
    q=n.new('ShaderNodeMapRange');q.clamp=True;q.interpolation_type='SMOOTHSTEP';q.inputs['From Min'].default_value=lo;q.inputs['From Max'].default_value=hi;l.new(v,q.inputs['Value']);return q.outputs['Result']
def branch(source):
    oldbs=next(x for x in source.node_tree.nodes if x.type=='BSDF_PRINCIPLED')
    b=n.new('ShaderNodeBsdfPrincipled')
    for key in ('Base Color','Roughness','Normal'):
        inp=oldbs.inputs[key];assert inp.is_linked
        tex=inp.links[0].from_node
        if key=='Normal':
            assert tex.type=='NORMAL_MAP';tex=tex.inputs['Color'].links[0].from_node
        assert tex.type=='TEX_IMAGE' and tex.image.packed_file
        q=n.new('ShaderNodeTexImage');q.image=tex.image
        if key=='Normal':
            nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.7;l.new(q.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],b.inputs[key])
        else:l.new(q.outputs['Color'],b.inputs[key])
    return b.outputs[0]
grassbs,roadbs=branch(grass),branch(road)
# Existing authored ECO moss maps: verify current branch manifest before using.
manifest=json.loads((pkg/'manifest.v2.json').read_text());files={}
uv=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=5;l.new(uv.outputs['UV'],scale.inputs[0])
moss=n.new('ShaderNodeBsdfPrincipled')
for role in ('basecolor','normal','orm'):
    rel='textures/moss_tile_'+role+'.png';p=pkg/rel
    expected=manifest['files'][rel]['sha256'];assert sha(p)==expected;files[rel]=expected
    image=bpy.data.images.load(str(p.resolve()),check_existing=False);image.colorspace_settings.name='sRGB' if role=='basecolor' else 'Non-Color';image.pack()
    q=n.new('ShaderNodeTexImage');q.image=image;l.new(scale.outputs['Vector'],q.inputs['Vector'])
    if role=='basecolor':l.new(q.outputs['Color'],moss.inputs['Base Color'])
    elif role=='normal':
        nm=n.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.45;l.new(q.outputs['Color'],nm.inputs['Color']);l.new(nm.outputs['Normal'],moss.inputs['Normal'])
    else:
        rgb=n.new('ShaderNodeSeparateColor');l.new(q.outputs['Color'],rgb.inputs[0]);l.new(rgb.outputs['Green'],moss.inputs['Roughness'])
# Spatially graded moss/grass intermix; not a blanket tint. Road core remains unchanged.
patch=mathnode('MULTIPLY',smooth(noise(.38,3),.34,.69),.58)
mix=n.new('ShaderNodeMixShader');l.new(patch,mix.inputs[0]);l.new(grassbs,mix.inputs[1]);l.new(moss.outputs[0],mix.inputs[2])
edge=mathnode('ADD',mathnode('ABSOLUTE',sep.outputs['Y']),mathnode('MULTIPLY',mathnode('SUBTRACT',noise(2.2,2),.5),.48))
mask=smooth(edge,2.15,2.65)
final=n.new('ShaderNodeMixShader');l.new(mask,final.inputs[0]);l.new(roadbs,final.inputs[1]);l.new(mix.outputs[0],final.inputs[2]);l.new(final.outputs[0],output.inputs[0])
ground.data.materials.clear();ground.data.materials.append(mat)
for poly in ground.data.polygons:poly.material_index=0
bpy.context.view_layer.update();assert snap()==old and sha(src)==lock
bpy.ops.file.pack_all()
dest=out/'village_verge_v4_UNAPPROVED.blend';assert not dest.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(dest.resolve()),compress=True)
bpy.ops.wm.open_mainfile(filepath=str(dest.resolve()));scene=bpy.context.scene;ground=bpy.data.objects['V3_village_reconstructed_patch']
assert snap()==old and sha(src)==lock
assert len(ground.data.materials)==1 and ground.data.materials[0].name=='V4 continuous verge PBR'
q=dict(status='NATIVE_MATERIAL_FEASIBILITY',source_sha256=lock,protected_meshes=len(old),geometry_uv_transform_unchanged=True,native_reopen='PASS',moss_source_sha256=files,road_blend_band_m=[2.15,2.65],road_boundary_jitter_max_m=.24,limits=['Procedural native PBR material. GLB baking/roundtrip NOT_RUN; preserve V3 GLB separately.','Existing 5m provisional route and vegetation geometry unchanged; no new collision claim.','No new D4/G1/G2/G4 acceptance.'])
def finish():
    q['outputs']={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.blend','.png')}
    (out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
finish()
scene.camera=bpy.data.objects['V3 matched patch'];scene.render.filepath=str((out/'village.png').resolve());bpy.ops.render.render(write_still=True)
d=bpy.data.cameras.new('V4 approach');o=bpy.data.objects.new('V4 approach',d);scene.collection.objects.link(o)
from mathutils import Vector
o.location=(-12,0,2.2);o.rotation_euler=(Vector((5,0,.4))-o.location).to_track_quat('-Z','Y').to_euler();d.lens=25;d.clip_end=500
scene.camera=o;scene.render.filepath=str((out/'approach.png').resolve());bpy.ops.render.render(write_still=True);finish()
