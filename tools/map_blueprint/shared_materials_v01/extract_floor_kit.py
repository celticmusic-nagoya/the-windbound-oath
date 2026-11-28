"""Lossless isolated V15C understory rock/moss/stump kit; no source overwrite."""
import sys,copy,hashlib,json,struct,collections
from pathlib import Path
import trimesh,numpy as np
SRC_SHA='09366ffaf5b1f6657b1b9ca158c9681d0d52537a4a90bf94f7ac25ec6f2162f1'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):
 b=p.read_bytes(); assert b[:4]==b'glTF' and struct.unpack_from('<I',b,4)[0]==2
 l=struct.unpack_from('<I',b,12)[0]; j=json.loads(b[20:20+l]); bl,typ=struct.unpack_from('<I4s',b,20+l); assert typ==b'BIN\0' and len(b)==28+l+bl
 return j,b[28+l:]
def select(n):
 name=n.get('name','');return 'mesh' in n and (name.startswith('MOSS_ROCK_') or name.endswith('_moss_cushion_a') or name.startswith('V12_STUMP_'))
def pack(j,b):
 a=json.dumps(j,separators=(',',':'),ensure_ascii=True).encode();a+=b' '*((-len(a))%4);b+=b'\0'*((-len(b))%4)
 return struct.pack('<4sII',b'glTF',2,28+len(a)+len(b))+struct.pack('<I4s',len(a),b'JSON')+a+struct.pack('<I4s',len(b),b'BIN\0')+b
def main(src,out):
 assert sha(src.read_bytes())==SRC_SHA; assert not out.exists()
 j,b=read(src); assert not j.get('extensionsUsed') and not j.get('extensionsRequired') and len(j['buffers'])==1
 selected=[i for i,n in enumerate(j['nodes']) if select(n)];assert len(selected)==85
 nj={'asset':copy.deepcopy(j['asset']),'scene':0,'scenes':[{'name':'V15C isolated floor asset kit','nodes':list(range(len(selected)))}]}
 remap={};binary=bytearray()
 def get(kind,i):
  if kind not in remap: remap[kind]={};nj[kind]=[]
  if i in remap[kind]: return remap[kind][i]
  d=copy.deepcopy(j[kind][i]);idx=len(nj[kind]);remap[kind][i]=idx;nj[kind].append(d)
  if kind=='meshes':
   for p in d['primitives']:
    assert not p.get('extensions') and not p.get('targets')
    p['attributes']={k:get('accessors',v) for k,v in p['attributes'].items()}
    if 'indices' in p:p['indices']=get('accessors',p['indices'])
    if 'material' in p:p['material']=get('materials',p['material'])
  elif kind=='accessors':
   assert not d.get('sparse');d['bufferView']=get('bufferViews',d['bufferView'])
  elif kind=='bufferViews':
   assert d['buffer']==0;old=d.get('byteOffset',0);l=d['byteLength'];assert old+l<=len(b)
   binary.extend(b'\0'*((-len(binary))%4));d['byteOffset']=len(binary);binary.extend(b[old:old+l])
  elif kind=='materials':
   def walk(x):
    for k,v in x.items():
     if isinstance(v,dict):
      if k.endswith('Texture'):v['index']=get('textures',v['index'])
      else:walk(v)
   walk(d)
  elif kind=='textures':
   d['source']=get('images',d['source']);
   if 'sampler' in d:d['sampler']=get('samplers',d['sampler'])
  elif kind=='images':
   assert 'uri' not in d;d['bufferView']=get('bufferViews',d['bufferView'])
  return idx
 nj['nodes']=[]
 for i in selected:
  n=copy.deepcopy(j['nodes'][i]);assert not n.get('children') and 'skin' not in n
  n['mesh']=get('meshes',n['mesh']);nj['nodes'].append(n)
 nj['buffers']=[{'byteLength':len(binary)}]
 out.write_bytes(pack(nj,bytes(binary)))
 actual,ab=read(out)
 # Exact preserved buffer views; compare all non-index fields as well.
 for old,new in remap['bufferViews'].items():
  a=j['bufferViews'][old];c=actual['bufferViews'][new]
  assert b[a.get('byteOffset',0):a.get('byteOffset',0)+a['byteLength']]==ab[c.get('byteOffset',0):c.get('byteOffset',0)+c['byteLength']]
  assert {k:v for k,v in a.items() if k!='byteOffset'}=={k:v for k,v in c.items() if k!='byteOffset'}
 for old,n in zip(selected,actual['nodes']):
  assert {k:v for k,v in j['nodes'][old].items() if k!='mesh'}=={k:v for k,v in n.items() if k!='mesh'}
 # Compare actual decoded geometry/transform multiset against source for named selected nodes.
 s=trimesh.load(src,force='scene',process=False);t=trimesh.load(out,force='scene',process=False)
 names={j['nodes'][i]['name'] for i in selected}
 def sig(sc):
  result=collections.Counter()
  for node in sc.graph.nodes_geometry:
   if node not in names:continue
   mat,g=sc.graph[node];m=sc.geometry[g];h=hashlib.sha256();h.update(np.asarray(m.vertices,dtype='<f8').tobytes());h.update(np.asarray(m.faces,dtype='<i8').tobytes());h.update(np.asarray(mat,dtype='<f8').tobytes());result[(node,h.hexdigest(),len(m.faces))]+=1
  return result
 a,c=sig(s),sig(t);assert len(a)==len(c)==85 and a==c
 q={'source_sha256':SRC_SHA,'output_sha256':sha(out.read_bytes()),'output_bytes':out.stat().st_size,'nodes':len(selected),'unique_meshes':len(actual['meshes']),'placed_triangles':sum(k[2]*v for k,v in c.items()),'types':{'rock':12,'moss':70,'stump':3},'verified_buffer_views':len(remap['bufferViews']),'images':len(actual['images']),'source_and_output_decoded_geometry_transform_exact':True,'source_unchanged':sha(src.read_bytes())==SRC_SHA,'note':'Exact V15C subset, no terrain; standalone asset kit only, not validated placement in V19 or native rendering.'}
 out.with_suffix('.qa.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
if __name__=='__main__':main(*map(Path,sys.argv[1:3]))
