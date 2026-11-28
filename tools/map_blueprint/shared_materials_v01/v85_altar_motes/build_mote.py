"""Generate independent additive-looking translucent light mote prototype, no canonical geometry."""
import argparse, hashlib, json, struct, io, zipfile
from pathlib import Path
import numpy as np
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--rune-zip',required=True,type=Path)
parser.add_argument('--base-glb',required=True,type=Path)
parser.add_argument('--out',required=True,type=Path)
args=parser.parse_args()
p=args.out
p.mkdir(parents=True,exist_ok=True)
assert not any((p/n).exists() for n in ('mote_soft_alpha.png','v85_mote_prototype.glb','qa.json')), 'refusing to overwrite outputs'
with zipfile.ZipFile(args.rune_zip) as archive:
    source=archive.read('v82_altar_rune_vfx.glb')
base_hash=hashlib.sha256(args.base_glb.read_bytes()).hexdigest()
assert base_hash=='47ac77303797e67b1bfe2dd2b67895149ba2d6aec1edef1a0ffcfe31d1050913'
assert hashlib.sha256(source).hexdigest()=='f6a9e4e60f10c85fe9dba133c53831ea46c7f2d96d3597dcf70e7c319a062b86'
n=64;y,x=np.mgrid[:n,:n];r=np.sqrt(((x+.5-n/2)/(n/2))**2+((y+.5-n/2)/(n/2))**2)
a=np.clip(1-r,0,1)**2.6;a[r>=.96]=0
rgba=np.empty((n,n,4),dtype=np.uint8);rgba[:,:,:3]=[161,224,255];rgba[:,:,3]=np.round(a*255).astype('uint8')
image=Image.fromarray(rgba);buf=io.BytesIO();image.save(buf,format='PNG');png=buf.getvalue();(p/'mote_soft_alpha.png').write_bytes(png)
# Three intersecting planes, orientation independent of the camera. Local diameter 0.08.
s=.04;verts=np.array([[-s,-s,0],[s,-s,0],[s,s,0],[-s,s,0],[0,-s,-s],[0,-s,s],[0,s,s],[0,s,-s],[-s,0,-s],[s,0,-s],[s,0,s],[-s,0,s]],dtype='<f4');uv=np.tile(np.array([[0,1],[1,1],[1,0],[0,0]],dtype='<f4'),(3,1));idx=np.array([i+j for i in (0,4,8) for j in (0,1,2,0,2,3)],dtype='<u2')
blob=bytearray();views=[]
def add(raw,target=None):
    while len(blob)%4:blob.append(0)
    d={'buffer':0,'byteOffset':len(blob),'byteLength':len(raw)}
    if target:d['target']=target
    views.append(d);blob.extend(raw);return len(views)-1
pv=add(verts.tobytes(),34962);tv=add(uv.tobytes(),34962);iv=add(idx.tobytes(),34963);imv=add(png)
while len(blob)%4:blob.append(0)
d={'asset':{'version':'2.0','generator':'TWO V85 local mote prototype'},'extensionsUsed':['KHR_materials_unlit'],'extensionsRequired':['KHR_materials_unlit'],'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'V85_mote_prototype'}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'TEXCOORD_0':1},'indices':2,'material':0}]}],'materials':[{'name':'V85_soft_mote_unlit','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}},'alphaMode':'BLEND','doubleSided':True}],'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],'images':[{'bufferView':imv,'mimeType':'image/png'}],'buffers':[{'byteLength':len(blob)}],'bufferViews':views,'accessors':[{'bufferView':pv,'componentType':5126,'count':len(verts),'type':'VEC3','min':verts.min(0).tolist(),'max':verts.max(0).tolist()},{'bufferView':tv,'componentType':5126,'count':len(uv),'type':'VEC2'},{'bufferView':iv,'componentType':5123,'count':len(idx),'type':'SCALAR','min':[0],'max':[11]}]}
j=json.dumps(d,separators=(',',':')).encode();j+=b' '*(-len(j)%4);glb=struct.pack('<4sII',b'glTF',2,12+8+len(j)+8+len(blob))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(blob),0x004e4942)+blob
assert hashlib.sha256(glb).hexdigest()=='c7bca378f35c2c7de86965bcefbe3ba1cdd10292390e78ad6403fb6ce54b4526', 'prototype byte identity differs; inspect encoder version'
file=p/'v85_mote_prototype.glb';file.write_bytes(glb)
# Independent structural readback and pixel guard.
m,v,l=struct.unpack_from('<4sII',glb);assert (m,v,l)==(b'glTF',2,len(glb));length,t=struct.unpack_from('<II',glb,12);assert t==0x4e4f534a;rd=json.loads(glb[20:20+length]);blen,bt=struct.unpack_from('<II',glb,20+length);binary=glb[28+length:];assert bt==0x004e4942 and blen==len(binary)
bv=rd['bufferViews'][rd['images'][0]['bufferView']];assert binary[bv['byteOffset']:bv['byteOffset']+bv['byteLength']]==png
assert np.all(rgba[[0,-1],:,3]==0) and np.all(rgba[:,[0,-1],3]==0)
assert np.all(np.linalg.norm(np.cross(verts[idx.reshape(-1,3)[:,1]]-verts[idx.reshape(-1,3)[:,0]],verts[idx.reshape(-1,3)[:,2]]-verts[idx.reshape(-1,3)[:,0]]),axis=1)>0)
qa={'status':'provisional independent prototype, NOT scene placed','source_vfx_sha256':hashlib.sha256(source).hexdigest(),'base_v84_sha256':base_hash,'glb_sha256':hashlib.sha256(glb).hexdigest(),'bytes':len(glb),'triangles_per_mote':6,'max_particles':24,'floating_core':1,'max_extra_triangles':150,'texture_size':[64,64],'transparent_border':True,'embedded_png_exact':True,'limits':['GLB unlit alpha blend, not actual bloom or dynamic illumination','prototype visible if opened alone; runtime factory must hide before attachment','provisional 0.08 local diameter and core 2.5x scale','actual renderer and Android NOT_RUN']};(p/'qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2))
