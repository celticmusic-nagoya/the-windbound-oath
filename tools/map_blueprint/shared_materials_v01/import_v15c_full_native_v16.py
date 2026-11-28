"""Isolated full V15C native import. Blender 5.3.0 only; never overwrite sources."""
import bpy, hashlib, json, sys, math
from pathlib import Path
from mathutils import Vector
src,out=map(Path,sys.argv[sys.argv.index('--')+1:]);out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(src)=='09366ffaf5b1f6657b1b9ca158c9681d0d52537a4a90bf94f7ac25ec6f2162f1'
assert bpy.app.version[:3]==(5,3,0)
for name in ('forest_v15c_full.blend','view_01.png','view_02.png','qa.json'):
    assert not (out/name).exists(),name
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(src.resolve()))
scene=bpy.context.scene
# Count instantiated triangles, not unique mesh data.
def stats():
    objs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    for o in objs:o.data.calc_loop_triangles()
    return dict(mesh_objects=len(objs),triangles=sum(len(o.data.loop_triangles) for o in objs),materials=len(bpy.data.materials),packed_images=sum(bool(i.packed_file) for i in bpy.data.images),external_images=[i.name for i in bpy.data.images if i.source=='FILE' and not i.packed_file])
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=960;scene.render.resolution_y=540;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.world=bpy.data.worlds.new('Forest sky study');scene.world.use_nodes=True
scene.world.node_tree.nodes.get('Background').inputs[0].default_value=(.40,.52,.70,1)
scene.world.node_tree.nodes.get('Background').inputs[1].default_value=.38
sun=bpy.data.lights.new('Warm afternoon sun','SUN');sun.energy=2.0;sun.angle=.08;sun.color=(1,.86,.67)
so=bpy.data.objects.new('Sun',sun);scene.collection.objects.link(so);so.rotation_euler=Vector((-.55,.30,-.76)).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.cameras.new('V15 matched camera');co=bpy.data.objects.new('V15 matched camera',cam);scene.collection.objects.link(co);scene.camera=co
cam.sensor_fit='VERTICAL';cam.lens=cam.sensor_height/(2*math.tan(math.radians(60)/2));cam.clip_start=.08;cam.clip_end=250
views=[((8,35.00075988769531,36),(12.2,33.3,38.5)),((18,34.22273864746094,37),(12,33.2,42))]
def conv(v):return Vector((v[0],-v[2],v[1]))
def camera(i):
    e,a=views[i];co.location=conv(e);co.rotation_euler=(conv(a)-co.location).to_track_quat('-Z','Y').to_euler()
camera(0);bpy.ops.file.pack_all();before=stats()
assert before['triangles']==828894,before
assert not before['external_images'],before
bpy.ops.wm.save_as_mainfile(filepath=str((out/'forest_v15c_full.blend').resolve()))
bpy.ops.wm.open_mainfile(filepath=str((out/'forest_v15c_full.blend').resolve()))
scene=bpy.context.scene;co=scene.camera;after=stats();assert before==after,(before,after)
for i in range(2):
    camera(i);scene.render.filepath=str((out/f'view_{i+1:02d}.png').resolve());bpy.ops.render.render(write_still=True)
q=dict(status='FULL_GLTF_NATIVE_IMPORT_CANDIDATE',source_sha256=sha(src),blender=bpy.app.version_string,before=before,after=after,views=views,outputs={p.name:sha(p) for p in out.iterdir() if p.suffix in ('.png','.blend')},limits=['Native save/reopen and render only; independent G2, exact shape roundtrip, G4 and final adoption not certified.'])
(out/'qa.json').write_text(json.dumps(q,indent=2)+'\n')
