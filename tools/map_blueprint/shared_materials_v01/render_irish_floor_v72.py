"""V72 render-only recovery from exact already-saved V71 checkpoint. No scene save or re-placement."""
import bpy,sys,hashlib,json
from pathlib import Path
from mathutils import Vector
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
lock='745f3739cf5360b113267003a21b61d0c812abeb7dfb3eecd66a2e558f2bf6bc'
prior=src.parent/'v71_qa.json'
assert sha(src)==lock and sha(prior)=='9aff33210642ddb3acdae13912ad6fe73321382f6073eff8d5b9177d1804013f'
q=json.loads(prior.read_text())
assert bpy.app.version[:3]==(5,3,0)
assert q['protected_meshes_exact']==523 and len(q['placed'])==168 and q['native_sha256']==lock
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
# All Blender ID references must be reacquired after open_mainfile.
scene=bpy.context.scene;terrain=bpy.data.objects['A3 provisional reconstructed terrain'];ext=bpy.data.objects['V58_SCENIC_ONLY_terrain_extension']
assert len([o for o in scene.objects if o.type=='MESH'])==691
assert terrain.data.color_attributes.get('V19_ground_color') and ext.data.color_attributes.get('V19_ground_color')
assert len([o for o in scene.objects if o.name.startswith('V71_') and o.type=='MESH'])==168
for row in q['placed']:
    o=bpy.data.objects[row['name']];ref=bpy.data.objects[row['source']]
    assert o.data==ref.data
    assert max(abs(x-y) for a,b in zip(o.matrix_world,row['matrix']) for x,y in zip(a,b))<1e-5
def ground(x,y):
    inv=terrain.matrix_world.inverted()
    ok,p,n,i=terrain.ray_cast(inv@Vector((x,y,100)),inv.to_3x3()@Vector((0,0,-1)),distance=200)
    assert ok
    return (terrain.matrix_world@p).z
pad=Vector((93.9431596631828,-93.0743278729908,27.988129971478276))
d=Vector((.788631932636555,-.6148655745981655,0));e=pad-d*20;e.z=ground(e.x,e.y)+2.15
views={0:(tuple(e),tuple(pad+Vector((0,0,3))),22),2:((71,-73,53),(96,-96,32),32)}
assert scene.render.engine=='CYCLES' and scene.render.resolution_x==960 and scene.render.resolution_y==540
cam=scene.camera
for i,(a,b,l) in views.items():
    cam.location=a;cam.rotation_euler=(Vector(b)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=l
    scene.render.filepath=str((out/f'v72_view_{i}.png').resolve())
    bpy.ops.render.render(write_still=True)
assert sha(src)==lock
result={'status':'RENDER_ONLY_RECOVERY_COMPLETE','source_sha256':lock,'prior_qa_sha256':sha(prior),'blender':bpy.app.version_string,'mesh_count':691,'linked_instances_verified':168,'views':views,'outputs':{p.name:sha(p) for p in out.glob('*.png')},'limits':['No new placement or save. Prior 523 protected signatures were checked in V71 before its rendering failure. Local feasibility, independent D4/G2 and G4 not run.']}
(out/'v72_render_qa.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
