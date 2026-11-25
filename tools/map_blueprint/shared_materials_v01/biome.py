"""A3 photo-ground tint and moss-rock candidate scene; no native edits. Inputs pinned."""
import sys,json,hashlib,io,zipfile,copy
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Point,Polygon,LineString,MultiPoint,shape
from PIL import Image
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation,LinearTriInterpolator
H=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
O=Path(__file__).resolve().parent
P=list(map(Path,sys.argv[1:])); expected=['79843431c4ddaa6f077483384445f36223546c4ee8573add58882d0d4044bda2','451599a92e375059fda4c11fc9265e35dde547df6dbc65a6f0572b4d72ae9e88','cd1a49b078fc92c23f02e1b05e33ac6ba351c035a30e71eeb3870bb200436564','e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','c3d6c314cc23f50012840a2b81414f46ea638ac6f7917f3ae557394e434d3f32','b4adf3246b4f9c298f4017050966e332af859caf29038468c3e305d726ce78cf','3ab29ffddcaabce5a997e1ce65bd6c55e0f3df2d8e73f00049fb9c6474e9f65e','4d2c308774f3c972c803cd8f74eb006c38dedb81ad45af34479bb612c4f07780','01de928d7f2600a8f7c3d11d592ef15b9e3f0e4d17dab6e0d5c3fe8961de52c8']
assert len(P)==len(expected) and list(map(H,P))==expected
sys.path.insert(0,str(P[-1].parent));from apply import read_glb,write_glb,append
# Reuse source triangle evaluator, not its plotting or candidate search.
args=sys.argv;sys.argv=[str(P[6]),*map(str,P[3:6])];env={'__file__':str(P[6]),'__name__':'a3_source'};exec(compile(P[6].read_text().split('# Arena:')[0],str(P[6]),'exec'),env);sys.argv=args
v,f,road,pad,domain,height,metric,st,r=map(env.get,['v','f','road','pad','domain','height','metric','st','r'])
q=json.loads(P[7].read_text());gate=json.loads(P[8].read_text());arena=Point(q['selected_arena']['center_xy']).buffer(10,quad_segs=64);hero=Point(q['selected_hero']['center_xy']).buffer(8.5,quad_segs=64);gate_p=sh.union_all([shape(gate['gate']),*[shape(x['footprint']) for x in gate['features']]])
protected=sh.union_all([road,pad,arena,hero,gate_p]);# texture-only proxy moisture and moss variation; no hydrology claim
j,raw=read_glb(P[0]);old=copy.deepcopy(j);buf=bytearray(raw);pr=j['meshes'][0]['primitives'][0]
def acc(j,b,i):
 a=j['accessors'][i];w=j['bufferViews'][a['bufferView']];n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];return np.frombuffer(b,dtype=dt,count=a['count']*n,offset=w.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,n)
xyz=acc(j,raw,pr['attributes']['POSITION']);normal=acc(j,raw,pr['attributes']['NORMAL']);xy=xyz[:,[0,2]]*[1,-1]+[600,-400];z=xyz[:,1];grade=np.linalg.norm(normal[:,[0,2]],axis=1)/normal[:,1];X,Y=xy.T
# Low-frequency artistic fields, not measured soil moisture. Smooth terrain-only; no path material replacement.
rng=np.random.default_rng(20261125)
def patch_field(count,lo,hi):
 centers=rng.uniform([500,-500],[700,-400],(count,2));sig=rng.uniform(lo,hi,(count,2));amp=rng.uniform(.3,1,count);d=(xy[:,None,:]-centers[None,:,:])/sig[None,:,:];a=(np.exp(-.5*np.sum(d*d,axis=2))*amp).sum(axis=1);return (a-a.min())/np.ptp(a)
wet=np.clip(.52*(1-(z-z.min())/np.ptp(z))+.40*patch_field(32,8,24),0,1)
moss=np.clip((1-np.minimum(grade/.55,1))*(.25+.65*wet)*(.55+.45*patch_field(75,3,12)),0,1)
# tint factors in linear RGB (glTF COLOR_0); preserve original scan details and UV.
tint=np.clip(1-wet[:,None]*np.array([.23,.19,.14])-moss[:,None]*np.array([.15,.045,.20]),0,1)
def add_attr(name,a,kind):
 a=np.ascontiguousarray(a,dtype='<f4');i=append(j,buf,a.tobytes());j['accessors'].append({'bufferView':i,'componentType':5126,'count':len(a),'type':kind,'min':np.atleast_1d(a.min(axis=0)).tolist(),'max':np.atleast_1d(a.max(axis=0)).tolist()});pr['attributes'][name]=len(j['accessors'])-1
add_attr('COLOR_0',tint,'VEC3');add_attr('_WETNESS',wet,'SCALAR');add_attr('_MOSS',moss,'SCALAR');j['materials'][0]['name']='FOREST_PHOTO_MACRO_TINT_STUDY';j['extras']={'scope':'candidate; vertex tint is standard glTF; custom scalar masks require renderer integration; roughness unchanged','source_scale_m':2,'moisture':'artistic proxy not hydrology'}
out=O/'a3_photo_biome_tint.glb';write_glb(j,buf,out);k,b=read_glb(out);assert b[:len(raw)]==raw and k['nodes']==old['nodes'] and k['meshes'][0]['primitives'][0]['indices']==old['meshes'][0]['primitives'][0]['indices'];assert np.array_equal(acc(k,b,k['meshes'][0]['primitives'][0]['attributes']['COLOR_0']),tint.astype('f4'))
# Reversible moss-rock placement study, original UV buffers and mesh/material definitions preserved.
rj,rb=read_glb(P[1]);rold=copy.deepcopy(rj);rj['nodes']=[];rj['scenes']=[{'name':'A3 rock placement study local frame','nodes':[]}];rj['scene']=0;placements=[];hulls=[];candidates=0
for i in range(12):
 mi=i%6;rp=rj['meshes'][mi]['primitives'][0];pts=acc(rj,rb,rp['attributes']['POSITION']).astype(float);scale=[.58,.72,.62,.53,.68,.57][mi];angle=(i*137.507764)%360;theta=np.deg2rad(angle);c,s=np.cos(theta),np.sin(theta);rot=np.array([[c,0,s],[0,1,0],[-s,0,c]]);p3=pts@rot.T*scale;p2=p3[:,[0,2]]*[1,-1]
 # candidate search near existing route, dry terrain, no protected overlaps. Proxy contact evaluated on all mesh vertices.
 stations=np.arange(290+i*7,390,3);chosen=None
 for ss in stations:
  idx=np.argmin(abs(st-ss));center=r[idx];direction=r[min(idx+1,len(r)-1)]-r[max(idx-1,0)];direction/=np.linalg.norm(direction);n=np.array([-direction[1],direction[0]])
  for off in [6,9,12,15,-6,-9,-12,-15]:
   candidates+=1;pos=center+off*n;coords=p2+pos;hull=MultiPoint(coords).convex_hull
   if not domain.contains(hull) or hull.distance(domain.boundary)<1 or hull.distance(protected)<.6 or any(hull.distance(h)<1 for h in hulls):continue
   g=metric(hull)
   if g['grade_pct']>20:continue
   ground=height(coords);delta=p3[:,1]-ground;burial=min(.15,.12*np.ptp(p3[:,1]));tz=-delta.min()-burial;gap=delta+tz;near=np.abs(gap)<=.08
   if np.count_nonzero(near)<5 or np.mean(gap<-.01)>.20:continue
   chosen=(pos,hull,tz,g,gap,near,burial,ss);break
  if chosen:break
 if not chosen:continue
 pos,hull,tz,g,gap,near,burial,ss=chosen;hulls.append(hull);idx=len(rj['nodes']);rj['nodes'].append({'name':f'MOSS_ROCK_{i+1:02d}','mesh':mi,'translation':[float(pos[0]-600),float(tz),float(-pos[1]-400)],'rotation':[0,float(np.sin(theta/2)),0,float(np.cos(theta/2))],'scale':[scale]*3});rj['scenes'][0]['nodes'].append(idx)
 placements.append({'id':f'MOSS_ROCK_{i+1:02d}','mesh':mi,'center_xy':pos.tolist(),'yaw_gltf_y_deg':float(angle),'scale':scale,'translation_gltf':rj['nodes'][-1]['translation'],'station_m':float(ss),'footprint':sh.geometry.mapping(hull),'clearance_m':float(hull.distance(protected)),'grade_pct':g['grade_pct'],'sample_count':len(gap),'sample_min_gap_m':float(gap.min()),'near_ground_vertices':int(near.sum()),'buried_vertex_fraction':float(np.mean(gap<-.01)),'triangles':int(rj['accessors'][rp['indices']]['count']//3)})
assert placements;rp=O/'a3_moss_rock_placement_study.glb';write_glb(rj,rb,rp);rr,rb2=read_glb(rp);assert rb2[:len(rb)]==rb and rr['meshes']==rold['meshes'] and rr['materials']==rold['materials'] and rr['images']==rold['images'];scene=trimesh.load(rp,force='scene',process=False);assert len(scene.graph.nodes_geometry)==len(placements)
# Raster preview: true scanned basecolor sampled at 2m with interpolated vertex tint. Planar diagnostic, not final rendered scene.
with zipfile.ZipFile(P[2]) as zipf: im=np.asarray(Image.open(io.BytesIO(zipf.read('two-material-cache/ph_forrest_ground_01/forrest_ground_01_diff_2k.jpg'))).convert('RGB'))/255
xx=np.linspace(620,699,1000);yy=np.linspace(-499,-435,810);gx,gy=np.meshgrid(xx,yy);tri=Triangulation(xy[:,0],xy[:,1],f);interp=lambda a:np.asarray(LinearTriInterpolator(tri,a)(gx,gy).filled(np.nan));uvx=((gx-600)/2)%1;uvy=(-(gy+400)/2)%1;N=len(im);tex=im[np.floor(uvy*N).astype(int)%N,np.floor(uvx*N).astype(int)%N];lin=np.where(tex<=.04045,tex/12.92,((tex+.055)/1.055)**2.4);color=lin*np.stack([interp(tint[:,i]) for i in range(3)],axis=-1);srgb=np.clip(np.where(color<=.0031308,12.92*color,1.055*np.maximum(color,0)**(1/2.4)-.055),0,1)
fig,axs=plt.subplots(2,2,figsize=(14,10),layout='constrained');ext=[xx[0],xx[-1],yy[0],yy[-1]]
for ax,img,title in [(axs[0,0],tex,'A | Original scanned forest ground'),(axs[0,1],srgb,'B | Photo ground + macro vertex tint')]:
 ax.imshow(img,origin='lower',extent=ext);ax.set_title(title);ax.set_aspect('equal')
mx,my=np.meshgrid(np.linspace(500,700,1001),np.linspace(-500,-400,501))
for ax,val,title in [(axs[1,0],wet,'C | Artistic moisture proxy (not hydrology)'),(axs[1,1],moss,'D | Moss tendency and rock placement')]:
 mask=LinearTriInterpolator(tri,val)(mx,my);im0=ax.imshow(mask,origin='lower',extent=[500,700,-500,-400],vmin=0,vmax=1,cmap='YlGn');fig.colorbar(im0,ax=ax,shrink=.7);ax.set_title(title)
for ax in axs.flat:
 for poly in [road,pad,arena,hero,gate_p]:
  for pp in sh.get_parts(poly):
   if pp.geom_type=='Polygon':ax.plot(*pp.exterior.xy,c='#e0ae72',lw=.8)
 ax.set(xlim=(620,699) if ax in axs[0] else (500,700),ylim=(-499,-435) if ax in axs[0] else (-500,-400),xlabel='X east (m)',ylabel='Y north (m)')
for a,h in zip(placements,hulls):axs[1,1].fill(*h.exterior.xy,color='#34322d');axs[1,1].text(*a['center_xy'],a['id'][-2:],fontsize=7,color='white')
fig.suptitle('TWO | A3 photo-biome and scanned moss rock study • provisional',fontsize=16);fig.savefig(O/'biome_comparison.png',dpi=145);plt.close(fig)
qa={'status':'PHOTO_TINT_AND_ROCK_PLACEMENT_CANDIDATE','inputs_sha256':expected,'ground':{'vertices':len(xyz),'triangles':len(f),'source_buffer_exact':True,'nodes_and_indices_exact':True,'wet_range':[float(wet.min()),float(wet.max())],'moss_range':[float(moss.min()),float(moss.max())],'tint_min_rgb':tint.min(0).tolist(),'actual_gltf_color0':True,'roughness_unchanged':True},'rock':{'candidates_checked':candidates,'placed':len(placements),'unique_meshes':len(set(x['mesh'] for x in placements)),'total_instance_triangles':sum(x['triangles'] for x in placements),'min_protected_clearance_m':min(x['clearance_m'] for x in placements),'min_pair_gap_m':min((a.distance(b) for i,a in enumerate(hulls) for b in hulls[i+1:]),default=None),'original_mesh_material_image_exact':True,'reopen_nodes':len(scene.graph.nodes_geometry),'placements':placements},'limits':['No independent D4; no precision native edits. Moisture/moss masks are authored artistic proxies, not hydrology. COLOR_0 only modulates basecolor; custom masks do not change roughness in standard glTF. Actual moss surface blending and physical wetness pending. Rocks are provisional placement study with sampled vertex contact only, no continuous collision or gameplay visibility proof; no LOD reduction or Android measurement. Preview is top-down texture diagnostic, not Blender or glTF render. Source terrain reconstructed, no CG verification.'],'inputs_unchanged':list(map(H,P))==expected,'outputs':{p.name:H(p) for p in [out,rp,O/'biome_comparison.png',Path(__file__)]}}
a=trimesh.load(P[0],force='scene',process=False);b=trimesh.load(out,force='scene',process=False);xm,ym=next(iter(a.geometry.values())),next(iter(b.geometry.values()));assert np.array_equal(xm.vertices,ym.vertices) and np.array_equal(xm.faces,ym.faces)
qa['ground']['reopen_mesh_exact']=True;qa['rock']['minimum_near_ground_vertices']=min(x['near_ground_vertices'] for x in placements);qa['rock']['max_buried_vertex_fraction']=max(x['buried_vertex_fraction'] for x in placements);qa['rock']['max_sampled_penetration_m']=-min(x['sample_min_gap_m'] for x in placements)
(O/'qa.json').write_text(json.dumps(qa,indent=2)+'\n');print(json.dumps({**qa,'rock':{k:v for k,v in qa['rock'].items() if k!='placements'}},indent=2))
