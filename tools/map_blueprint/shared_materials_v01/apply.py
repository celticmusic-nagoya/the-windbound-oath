"""Non-destructive source recovery and glTF material study. Not final art or native Blender."""
import hashlib, json, struct, zipfile, io, argparse
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image,ImageDraw
H=lambda b:hashlib.sha256(b).hexdigest()
ZSHA='cd1a49b078fc92c23f02e1b05e33ac6ba351c035a30e71eeb3870bb200436564'
TSHA='e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b'
def pad(b,f=b'\0'):return b+f*((-len(b))%4)
def write_glb(j,buf,p):
    j['buffers']=[{'byteLength':len(buf)}];a=pad(json.dumps(j,separators=(',',':')).encode(),b' ');b=pad(bytes(buf));
    p.write_bytes(struct.pack('<4sII',b'glTF',2,28+len(a)+len(b))+struct.pack('<I4s',len(a),b'JSON')+a+struct.pack('<I4s',len(b),b'BIN\0')+b)
def read_glb(p):
    b=p.read_bytes();n,t=struct.unpack_from('<I4s',b,12);assert t==b'JSON';j=json.loads(b[20:20+n]);m,t=struct.unpack_from('<I4s',b,20+n);assert t==b'BIN\0';return j,b[28+n:28+n+m]
def append(j,b,d):
    b.extend(b'\0'*((-len(b))%4));i=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':len(d)});b.extend(d);return i
def image_view(j,b,d,name):
    i=append(j,b,d);j.setdefault('images',[]).append({'bufferView':i,'mimeType':'image/jpeg','name':name});j.setdefault('textures',[]).append({'source':len(j['images'])-1,'sampler':0});return len(j['textures'])-1
def pack_moss(files,out):
    prefix='ph_rock_moss_set_01/';j=json.loads(files[prefix+'rock_moss_set_01_1k.gltf']);src=files[prefix+j['buffers'][0]['uri']];b=bytearray(src);old=json.loads(json.dumps(j));
    for im in j['images']:im['bufferView']=append(j,b,files[prefix+im.pop('uri')])
    b.extend(b'\0'*((-len(b))%4));p=out/'rock_moss_set_01.glb';write_glb(j,b,p);q,r=read_glb(p);assert r[:len(src)]==src
    assert all(q[k]==v for k,v in old.items() if k not in ('images','buffers','bufferViews'))
    for a,c in zip(old['images'],q['images']):
        v=q['bufferViews'][c['bufferView']];assert r[v['byteOffset']:v['byteOffset']+v['byteLength']]==files[prefix+a['uri']]
    s=trimesh.load(p,force='scene',process=False);assert len(s.geometry)==6
    return {'file':p.name,'sha256':H(p.read_bytes()),'geometry_count':len(s.geometry),'vertices':sum(len(m.vertices) for m in s.geometry.values()),'triangles':sum(len(m.faces) for m in s.geometry.values()),'original_buffer_exact':True,'original_images_exact':3,'original_material_exact':True,'reopen':'PASS'}
def terrain_study(files,source,out):
    j,raw=read_glb(source);old=json.loads(json.dumps(j));b=bytearray(raw);pr=j['meshes'][0]['primitives'][0];ac=j['accessors'][pr['attributes']['POSITION']];v=j['bufferViews'][ac['bufferView']];pos=np.frombuffer(raw,dtype='<f4',offset=v['byteOffset']+ac.get('byteOffset',0),count=ac['count']*3).reshape(-1,3)
    # Reconstructed local XZ plane. Actual provider scale unknown; 2m is an authored test value.
    uv=np.ascontiguousarray(pos[:,[0,2]]/2,dtype='<f4');i=append(j,b,uv.tobytes());j['accessors'].append({'bufferView':i,'componentType':5126,'count':len(uv),'type':'VEC2','min':uv.min(axis=0).tolist(),'max':uv.max(axis=0).tolist()});pr['attributes']['TEXCOORD_0']=len(j['accessors'])-1;pr['attributes'].pop('COLOR_0');
    # Explicit smooth normals and tangents for the planar X/Z mapping.
    srcmesh=next(iter(trimesh.load(source,force='scene',process=False).geometry.values()));norm=np.asarray(srcmesh.vertex_normals); assert np.all(norm[:,1]>0)
    tangent=np.cross(np.tile([0.,0.,1.],(len(norm),1)),norm)*-1; tangent/=np.linalg.norm(tangent,axis=1)[:,None]; bitangent=np.cross(norm,tangent); sign=np.where(bitangent[:,2]>=0,1.,-1.);assert np.all(sign==-1)
    for name,arr,typ in [('NORMAL',norm,'VEC3'),('TANGENT',np.column_stack((tangent,sign)),'VEC4')]:
        arr=np.ascontiguousarray(arr,dtype='<f4'); idx=append(j,b,arr.tobytes());j['accessors'].append({'bufferView':idx,'componentType':5126,'count':len(arr),'type':typ});pr['attributes'][name]=len(j['accessors'])-1
    j['samplers']=[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}]
    pref='ph_forrest_ground_01/forrest_ground_01_';d=image_view(j,b,files[pref+'diff_2k.jpg'],'Forest ground base color');n=image_view(j,b,files[pref+'nor_gl_2k.jpg'],'Forest ground normal GL');arm=image_view(j,b,files[pref+'arm_2k.jpg'],'Forest ground ARM');
    j['materials']=[{'name':'FOREST_GROUND_PHOTO_STUDY_2M','pbrMetallicRoughness':{'baseColorTexture':{'index':d},'metallicRoughnessTexture':{'index':arm},'metallicFactor':0,'roughnessFactor':1},'normalTexture':{'index':n},'occlusionTexture':{'index':arm},'doubleSided':True}];pr['material']=0
    b.extend(b'\0'*((-len(b))%4));p=out/'a3_forest_ground_photo_study.glb';write_glb(j,b,p);q,r=read_glb(p);assert r[:len(raw)]==raw and q['nodes']==old['nodes']
    for k in ['POSITION']:assert q['meshes'][0]['primitives'][0]['attributes'][k]==old['meshes'][0]['primitives'][0]['attributes'][k]
    assert q['meshes'][0]['primitives'][0]['indices']==old['meshes'][0]['primitives'][0]['indices']
    for k,tex in enumerate((pref+'diff_2k.jpg',pref+'nor_gl_2k.jpg',pref+'arm_2k.jpg')):
        v=q['bufferViews'][q['images'][k]['bufferView']];assert r[v['byteOffset']:v['byteOffset']+v['byteLength']]==files[tex]
    a=trimesh.load(source,force='scene',process=False);c=trimesh.load(p,force='scene',process=False);m=next(iter(a.geometry.values()));k=next(iter(c.geometry.values()));assert np.array_equal(m.vertices,k.vertices) and np.array_equal(m.faces,k.faces)
    return {'file':p.name,'sha256':H(p.read_bytes()),'vertices':len(k.vertices),'triangles':len(k.faces),'uv_count':len(k.visual.uv),'normal_count':len(norm),'tangent_count':len(tangent),'max_normal_tangent_dot':float(np.abs(np.sum(norm*tangent,axis=1)).max()),'mesh_and_face_exact':True,'old_buffer_exact':True,'original_images_exact':3,'uv_tile_m':2,'source_scale_verified':False,'reopen':'PASS'}
def preview(files,out):
    # Fixed light, top-down tangent-plane material study using source normal+ARM. No geometry claim.
    N=512; canvas=Image.new('RGB',(1600,1230),'#202520');d=ImageDraw.Draw(canvas);d.text((32,18),'TWO | photo-derived material study (same directional light)',fill='white');
    for r,aid in enumerate(('forrest_ground_01','grassy_cobblestone')):
        prefix='ph_'+aid+'/'+aid+'_';maps={}
        for s in ('diff','nor_gl','arm','disp','rough','ao'):
            with Image.open(io.BytesIO(files[prefix+s+'_2k.jpg'])) as im: maps[s]=np.asarray(im.convert('RGB').resize((N,N),Image.Resampling.LANCZOS),dtype=float)/255
        # sRGB exact transfer to linear; tangent-plane approximation, glTF normal + AO + roughness specular.
        rgb=maps['diff'];base=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4);normal=maps['nor_gl']*2-1;normal/=np.maximum(np.linalg.norm(normal,axis=-1,keepdims=True),1e-9);light=np.array([-.45,.35,.82]);light/=np.linalg.norm(light);half=light+np.array([0,0,1]);half/=np.linalg.norm(half);nd=np.clip(normal@light,0,1);nh=np.clip(normal@half,0,1);ao=maps['arm'][...,0];rough=np.maximum(maps['arm'][...,1],.07);spec=.04*nh**(2/rough**2);lin=base*(.28*ao+.72*nd)[...,None]+spec[...,None];srgb=np.where(lin<=.0031308,12.92*lin,1.055*np.maximum(lin,0)**(1/2.4)-.055);final=np.uint8(np.clip(srgb*255,0,255));gray=np.uint8(np.clip(np.full((N,N,3),.64)*(.28+.72*light[2])*255,0,255));
        y=72+r*565;d.text((32,y-22),aid.replace('_',' ').upper(),fill='white');
        for i,(title,img) in enumerate((('Neutral plane',gray),('Original base color',np.uint8(rgb*255)),('Normal + ARM lighting study',final))):
            x=32+i*520;canvas.paste(Image.fromarray(img),(x,y));d.text((x,y+518),title,fill='white')
    canvas.save(out/'photo_material_comparison.png')
def main():
    p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('terrain',type=Path);p.add_argument('out',type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);assert H(a.archive.read_bytes())==ZSHA and H(a.terrain.read_bytes())==TSHA
    with zipfile.ZipFile(a.archive) as z:
        assert len(z.namelist())==len(set(z.namelist()));report=json.loads(z.read('material-recovery.json'));assert report['complete'] and len(report['files'])==17
        files={};img_counts={}
        for row in report['files']:
            f=row['path'];assert not f.startswith('/') and '..' not in Path(f).parts;data=z.read('two-material-cache/'+f);assert len(data)==row['bytes'] and H(data)==row['sha256'];assert not row.get('provider_md5') or hashlib.md5(data).hexdigest()==row['provider_md5'];files[f]=data
            if f.endswith('.jpg'):
                with Image.open(io.BytesIO(data)) as im: im.load();assert im.size==((1024,1024) if 'rock_moss_set' in f else (2048,2048));img_counts[f]=list(im.size)
        assert set(z.namelist())=={'material-recovery.json'}|{'two-material-cache/'+f for f in files}
    assert len(img_counts)==15
    m=pack_moss(files,a.out);t=terrain_study(files,a.terrain,a.out);preview(files,a.out)
    q={'status':'PHOTO_SOURCE_RECOVERY_AND_MATERIAL_STUDY_ONLY','source_archive_sha256':ZSHA,'terrain_sha256':TSHA,'files_verified':17,'image_sizes':img_counts,'source_lock_rows':report['files'],'moss_model':m,'terrain_study':t,'preview_sha256':H((a.out/'photo_material_comparison.png').read_bytes()),'source_unchanged':H(a.archive.read_bytes())==ZSHA and H(a.terrain.read_bytes())==TSHA,'limits':['No formal adoption, native Blender or runtime render. Fixed tangent-plane lighting diagnostic only, not full glTF renderer. 2m UV scale provisional, forest ground is not final mixed biome. Cobblestone is a village/fortress material candidate, not automatically a forest trail. Moss source mesh needs LOD/contact/placement QA.']}
    (a.out/'qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k not in ('source_lock_rows','image_sizes')},indent=2))
if __name__=='__main__':main()
