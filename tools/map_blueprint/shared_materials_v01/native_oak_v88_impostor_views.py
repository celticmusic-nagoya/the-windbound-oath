"""V88 far oak: reuse verified V82-D source views; render missing 45-degree azimuths.
Exact source mesh bounds from saved native reference. No geometry mutation/world placement.
"""
import bpy,sys,hashlib,json,math,shutil
from pathlib import Path
from mathutils import Vector
from array import array
src,out=map(Path,sys.argv[sys.argv.index('--')+1:])
out.mkdir(parents=True,exist_ok=True)
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(src)=='e2b777f32b17dfa5f1a671b734d5f1f92123a4d93982b5a016d00d8e31629145'
assert bpy.app.version[:3]==(5,3,0)
manifest={n.strip().removeprefix('./'):h for h,n in (l.split(None,1) for l in (src.parent/'SHA256SUMS').read_text().splitlines())}
def verify(n):
    f=src.parent/n;assert sha(f)==manifest[n],n;return f
qa0=json.loads(verify('v82d_oak_qa.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(src.resolve()))
study=bpy.data.scenes['V82D_OAK_ASSET_STUDY']
reference=study.objects['V82D_oak_reference'];candidate=study.objects['V82D_oak_candidate'];camera=study.camera
assert reference.data.name==qa0['source_mesh'] and study.render.engine=='CYCLES' and study.cycles.samples==24
assert study.render.resolution_x==study.render.resolution_y==512 and study.render.resolution_percentage==100 and study.render.film_transparent
assert camera.data.type=='ORTHO' and reference.matrix_world==candidate.matrix_world
assert all(abs(reference.matrix_world[i][j]-(1 if i==j else 0))<1e-7 for i in range(4) for j in range(4))
mesh=reference.data;mesh.calc_loop_triangles();assert len(mesh.loop_triangles)==qa0['source_triangles']
v=array('f',[0])*(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',v)
digest=hashlib.sha256(v.tobytes()).hexdigest()
lo=Vector(tuple(min(v[i::3]) for i in range(3)));hi=Vector(tuple(max(v[i::3]) for i in range(3)))
center=(lo+hi)*.5;extent=(hi-lo).length;span=extent*1.05
assert abs(span-camera.data.ortho_scale)<1e-5 and abs(extent-qa0['calibration'][0]['cell_size_local']/.015)<1e-5
qa={'candidate_only':True,'source_native_sha256':sha(src),'source_vertex_sha256':digest,'source_triangles':len(mesh.loop_triangles),'bounds_blender':[list(lo),list(hi)],'center_gltf':[center.x,center.z,-center.y],'ortho_span_local':span,'views':[],'limits':['Native source measured; no game placement or actual Android test','Adjacent alpha metrics not intermediate-view error','No new geometry or material changes']}
def checkpoint():
    (out/'v88_native_qa.json').write_text(json.dumps(qa,indent=2));print('V88_CHECKPOINT',len(qa['views']),flush=True)
reference.hide_render=False;candidate.hide_render=True
for angle in range(0,360,45):
    for elevation in (-35,0,35):
        name=f'oak_{angle}_{elevation}_source.png';f=out/name;assert not f.exists()
        if angle%90==0:
            shutil.copyfile(verify(name),f);reused=True
        else:
            az=math.radians(angle);el=math.radians(elevation);direction=Vector((math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)))
            camera.location=center+direction*(extent*2+1);camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
            study.render.filepath=str(f.resolve());study.render.image_settings.file_format='PNG';study.render.image_settings.color_mode='RGBA'
            with bpy.context.temp_override(scene=study):bpy.ops.render.render(write_still=True,scene=study.name)
            reused=False
        qa['views'].append({'azimuth_deg':angle,'elevation_deg':elevation,'file':name,'sha256':sha(f),'reused':reused});checkpoint()
mesh.vertices.foreach_get('co',v);assert hashlib.sha256(v.tobytes()).hexdigest()==digest
assert sha(src)==qa['source_native_sha256']
qa['source_unchanged']=True;checkpoint()
print('V88_NATIVE_DONE',json.dumps(qa),flush=True)
