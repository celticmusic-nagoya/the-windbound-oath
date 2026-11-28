"""Pack 24 matched oak views; compare old/new bin switch alpha at same display sizes.
This is a diagnostic, not actual temporal renderer QA.
"""
import sys,json,hashlib,struct,io
from pathlib import Path
import numpy as np
from PIL import Image
out=Path(sys.argv[1]);qa=json.loads((out/'v88_native_qa.json').read_text())
assert qa['source_unchanged'] and len(qa['views'])==24 and sum(v['reused'] for v in qa['views'])==12
sha=lambda b:hashlib.sha256(b).hexdigest()
atlas=Image.new('RGBA',(2048,1024));images={};rows=[]
for v in qa['views']:
    a,e=v['azimuth_deg'],v['elevation_deg'];b=(out/v['file']).read_bytes();assert sha(b)==v['sha256']
    im=Image.open(io.BytesIO(b)).convert('RGBA');assert im.size==(512,512)
    im=im.resize((256,256),Image.Resampling.LANCZOS);images[a,e]=im
    col=a//45;row=[-35,0,35].index(e);atlas.paste(im,(col*256,row*256))
    rows.append({'azimuth_deg':a,'elevation_deg':e,'uv_rect':[col/8,row/4,(col+1)/8,(row+1)/4],'source_sha256':v['sha256']})
atlasfile=out/'oak_v88_atlas.png';atlas.save(atlasfile)
re=Image.open(atlasfile).convert('RGBA')
assert all(re.crop((a//45*256,[-35,0,35].index(e)*256,(a//45+1)*256,([-35,0,35].index(e)+1)*256)).tobytes()==im.tobytes() for (a,e),im in images.items())
metrics={}
for px in (12,16,24,32,48,64):
    downs={k:np.asarray(v.getchannel('A').resize((px,px),Image.Resampling.BOX),dtype=float)/255 for k,v in images.items()}
    def measure(step):
        pairs=[]
        for a in range(0,360,step):
            for e in (-35,0,35):
                pairs.append(((a,e),((a+step)%360,e)))
                if e<35:pairs.append(((a,e),(a,e+35)))
        diffs=[np.abs(downs[a]-downs[b]) for a,b in pairs]
        return {'pairs':len(pairs),'worst_equivalent_alpha_pixels':max(float(x.sum()) for x in diffs),'worst_strong_change_pixels':max(int((x>.25).sum()) for x in diffs)}
    metrics[str(px)]={'old_12_views':measure(90),'new_24_views':measure(45)}
# Standalone default +X view, local pivot from exact source (not canonical world placement).
span=qa['ortho_span_local'];s=span/2
verts=np.array([[0,-s,-s],[0,-s,s],[0,s,s],[0,s,-s]],dtype='<f4')
uv=np.array([[0,.5],[.125,.5],[.125,.25],[0,.25]],dtype='<f4');idx=np.array([0,1,2,0,2,3],dtype='<u2')
buf=bytearray();views=[]
def add(raw,target=None):
    while len(buf)%4:buf.append(0)
    q={'buffer':0,'byteOffset':len(buf),'byteLength':len(raw)}
    if target:q['target']=target
    views.append(q);buf.extend(raw);return len(views)-1
pv=add(verts.tobytes(),34962);tv=add(uv.tobytes(),34962);iv=add(idx.tobytes(),34963);imv=add(atlasfile.read_bytes())
while len(buf)%4:buf.append(0)
d={'asset':{'version':'2.0','generator':'TWO V88 candidate'},'extensionsUsed':['KHR_materials_unlit'],'extensionsRequired':['KHR_materials_unlit'],'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'mesh':0,'name':'V88_far_oak','translation':qa['center_gltf']}],'meshes':[{'primitives':[{'attributes':{'POSITION':0,'TEXCOORD_0':1},'indices':2,'material':0}]}],'materials':[{'name':'V88_oak_unlit','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':0,'roughnessFactor':1},'extensions':{'KHR_materials_unlit':{}},'alphaMode':'BLEND','doubleSided':True}],'textures':[{'source':0,'sampler':0}],'samplers':[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071}],'images':[{'bufferView':imv,'mimeType':'image/png'}],'buffers':[{'byteLength':len(buf)}],'bufferViews':views,'accessors':[{'bufferView':pv,'componentType':5126,'count':4,'type':'VEC3','min':verts.min(0).tolist(),'max':verts.max(0).tolist()},{'bufferView':tv,'componentType':5126,'count':4,'type':'VEC2'},{'bufferView':iv,'componentType':5123,'count':6,'type':'SCALAR','min':[0],'max':[3]}]}
j=json.dumps(d,separators=(',',':')).encode();j+=b' '*(-len(j)%4);g=struct.pack('<4sII',b'glTF',2,28+len(j)+len(buf))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(buf),0x004e4942)+buf
(out/'oak_v88_preview.glb').write_bytes(g)
contract={'source_native_sha256':qa['source_native_sha256'],'pivot_gltf':qa['center_gltf'],'ortho_span_local':span,'atlas_sha256':sha(atlasfile.read_bytes()),'glb_sha256':sha(g),'atlas_size':[2048,1024],'tile_size':256,'views':rows,'triangles':2,'source_views_reused':12,'new_views':12,'atlas_tile_readback':24,'adjacent_switch_metrics':metrics,'provisional_max_span_pixels':max([int(k) for k,m in metrics.items() if m['new_24_views']['worst_equivalent_alpha_pixels']<=8],default=None),'limits':['Provisional diagnostic <=8 equivalent alpha pixels, not G2/G4','No actual camera facing orientation adapter, world placement, light parity, or Android measurement','Ambient-lit source images; no mipmap filtering']}
(out/'v88_oak_contract.json').write_text(json.dumps(contract,indent=2));print('V88_PACK_DONE',json.dumps(contract),flush=True)
