"""Read-only A2 spur fillet and minimal ecology reservation relocation. No native edit."""
import sys,hashlib,json,csv
from pathlib import Path
OUT=Path(__file__).resolve().parent
P,V,T,C,D,S=map(Path,sys.argv[1:7]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D)=='473f56f4d2a5f206607966c6a2255f4c9f3c6e323233eeefc0dc17c87fa27962'
assert sha(S)=='8136ad145a9eef636fb9780927f0232cf0b7553793c6d2794833cf7f6822f548'
# Reuse only exact geometry setup and sight functions; no previous graph search.
source=S.read_text();sys.argv=[str(S),str(P),str(V),str(T),str(C)];exec(compile(source.split('# 2m radius viewing pad')[0],str(S),'exec'))
old=json.loads(D.read_text());path=np.array(old['selected']['route_xy']);pos=path[-1];pad=Point(pos).buffer(2,quad_segs=64);orig=xy.copy();origz=z.copy();original_rows=[dict(r) for r in rows]
# Remove redundant collinear vertices before fitting circular fillets.
def simplify(path):
 keep=[0]
 for i in range(1,len(path)-1):
  a=path[i]-path[i-1];b=path[i+1]-path[i];a/=np.linalg.norm(a);b/=np.linalg.norm(b)
  if a@b<1-1e-10:keep.append(i)
 keep.append(len(path)-1);return path[keep]
path=simplify(path)

def align(radius):
 pieces=[];last=path[0];angles=[];curves=[]
 def line(a,b):
  l=np.linalg.norm(b-a)
  if l<1e-9:return
  d=(b-a)/l;u=np.linspace(0,1,max(2,int(np.ceil(l/.15))+1));pieces.append((a+u[:,None]*(b-a),np.tile(d,(len(u),1))))
 for i in range(1,len(path)-1):
  a,b,c=path[i-1:i+2];u=(b-a)/np.linalg.norm(b-a);w=(c-b)/np.linalg.norm(c-b);ang=np.arccos(np.clip(u@w,-1,1));sg=np.sign(u[0]*w[1]-u[1]*w[0]);l=radius*np.tan(ang/2);p=b-u*l;q=b+w*l
  if l>np.linalg.norm(c-b) or (p-last)@u<1e-8:return None
  line(last,p);center=p+sg*radius*np.array([-u[1],u[0]]);a0=np.arctan2(*(p-center)[::-1]);theta=a0+sg*np.linspace(0,ang,max(3,int(np.ceil(radius*ang/.15))+1));arc=center+radius*np.c_[np.cos(theta),np.sin(theta)];tangent=sg*np.c_[-np.sin(theta),np.cos(theta)];pieces.append((arc,tangent));last=q;angles.append(float(np.degrees(ang)))
 line(last,path[-1]);c=np.vstack([a if i==0 else a[1:] for i,(a,b) in enumerate(pieces)]);d=np.vstack([b if i==0 else b[1:] for i,(a,b) in enumerate(pieces)]);n=np.c_[-d[:,1],d[:,0]];q=c[:,None,:]+np.linspace(-1,1,9)[None,:,None]*n[:,None,:];h=ground(q.reshape(-1,2)).reshape(q.shape[:2]);tri=grid_tri(q,h);nn=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);sign=np.sign(np.median(nn[:,2]));folds=int(np.sum(nn[:,2]*sign<=1e-9));footprint=Polygon(np.vstack([q[:,0],q[::-1,-1]]));
 if not footprint.is_valid or not np.isfinite(h).all():return None
 # Conservative exact source triangle gradient screen per ribbon interval including directional rotation.
 L=X=0.
 for i in range(len(c)-1):
  p=Polygon([q[i,0],q[i,-1],q[i+1,-1],q[i+1,0]]);u=d[i];w=n[i];a=np.arccos(np.clip(d[i]@d[i+1],-1,1))
  for tr,pl in layers:
   ix=tr.query(p,predicate='intersects');gg=pl[ix,:2]
   if len(gg):
    # Exact maximum absolute dot product on the shorter angular arc.
    def bound(u,v):
     aa=np.arctan2(u[1],u[0]);bb=np.arctan2(v[1],v[0]);delta=(bb-aa+np.pi)%(2*np.pi)-np.pi;phi=np.arctan2(gg[:,1],gg[:,0]);lo=min(0,delta);hi=max(0,delta);angle=(phi-aa-lo)%np.pi;extremum=angle<=hi-lo+1e-12
     return float(np.max(np.where(extremum,np.linalg.norm(gg,axis=1),np.maximum(abs(gg@u),abs(gg@v)))))
    L=max(L,bound(u,d[i+1]));X=max(X,bound(w,n[i+1]))
 overlap=footprint.intersection(road);entry_zone=Point(path[0]).buffer(7.5);rec=dict(radius_m=radius,length_m=float(np.linalg.norm(np.diff(c,axis=0),axis=1).sum()),long_pct=100*L,cross_pct=100*X,folds=folds,water_overlap_m2=footprint.intersection(water_reserve).area,outside_m2=footprint.difference(domain).area,road_overlap_m2=overlap.area,road_overlap_outside_entry_m2=overlap.difference(entry_zone).area,entry_center_residual_m=float(abs(h[0,4]-ground(path[:1])[0])),sample_count=int(h.size),triangle_count=len(tri));rec['pass']=L<=.15 and X<=.10 and not folds and rec['water_overlap_m2']<1e-8 and rec['outside_m2']<1e-8 and rec['road_overlap_outside_entry_m2']<1e-8
 return rec,c,q,h,footprint
attempts=[];best=None;choice=None
# Causal switch: other V06 alignments, not repeated tuning of rejected near route.
for candidate in sorted(old['all_terrain_clear_routes'],key=lambda r:(-r['angular_span_deg'],r['length_m'])):
 path=simplify(np.array(candidate['route_xy']));pos=path[-1]
 for radius in [3,2.5,2]:
  a=align(radius)
  if a is None:attempts.append(dict(view_xy=pos.tolist(),radius_m=radius,status='GEOMETRIC_REJECT'));continue
  a[0]['view_xy']=pos.tolist();attempts.append(a[0]);print(a[0],flush=True)
  if a[0]['pass'] and best is None:best=a;choice=candidate
 if best is not None:break
if best is None:
 (OUT/'qa.json').write_text(json.dumps(dict(status='ALIGNMENT_HOLD',attempts=attempts),indent=2)+'\n');sys.exit(0)
rec,c,q,h,spur=best;pos=c[-1];pad=Point(pos).buffer(2,quad_segs=64);rec['target_range_m']=choice['target_range_m'];rec['angular_span_deg']=choice['angular_span_deg'];rec['entry_station_m']=choice['entry_station_m'];rec['view_grade_pct']=choice['view']['grade_pct'];rec['sampled_terrain_ray_clearance_m']=choice['view']['min_clearance_m']
# Preserve original reserve plus V04 plan view reservation and new spur/pad/sight lines.
from shapely.ops import nearest_points
trail=LineString(B['road_xy'][:,4]);fall=Point(480-12.25,-385);vp=nearest_points(trail.intersection(domain),fall)[0];view0=LineString([vp,fall]).buffer(2.5).intersection(domain);new=spur.union(pad);observer=np.r_[pos,ground(pos[None,:])[0]+1.65];sightlines=unary_union([LineString([pos,a[:2]]) for a in targets]);hit=set(np.flatnonzero(sh.distance(new,sh.points(xy))<rad+1e-6));hit.update(i for a in targets for i in blockers(observer,a));move=sorted(hit);active=np.ones(len(rows),dtype=bool);active[move]=False;changes=[];rng=np.random.default_rng(20261125)
# Largest envelopes first, closest feasible sites on 0.5m grid up to 35m. All unchanged reservations remain fixed.
for i in sorted(move,key=lambda i:-rad[i]):
 r=rad[i];k=kind[i];is_tree=k in ['ancient_tree_reserve','forest_tall','deciduous'];ex=reserved.union(new).union(sightlines.buffer(.1));ex=ex.union(view0) if is_tree or k=='rock_reserve' else ex
 dx,dy=np.meshgrid(np.arange(-35,35.01,.5),np.arange(-35,35.01,.5));p=orig[i]+np.c_[dx.ravel(),dy.ravel()];order=np.argsort(np.linalg.norm(p-orig[i],axis=1),kind='stable');found=False
 for x0,y0 in p[order]:
  pt=Point(x0,y0)
  if not domain.covers(pt) or pt.distance(domain.boundary)<r+1e-5 or pt.distance(ex)<r+1e-5:continue
  if np.any(np.linalg.norm(xy[active]-[x0,y0],axis=1)<rad[active]+r+(.3 if is_tree else .1)):continue
  ii=tree.query(pt.buffer(r,quad_segs=64),predicate='intersects');grade=float(np.linalg.norm(g[ii],axis=1).max());
  if grade>(.25 if is_tree else .40):continue
  zz=float(ground(np.array([[x0,y0]]))[0]);xy[i]=[x0,y0];z[i]=zz;active[i]=True;rows[i].update(x_m=str(x0),y_m=str(y0),z_m=str(zz),max_source_grade_pct=str(grade*100),exclusion_clearance_m=str(pt.distance(ex)-r));changes.append(dict(id=str(ids[i]),kind=str(k),old_xy=orig[i].tolist(),new_xy=xy[i].tolist(),distance_m=float(np.linalg.norm(xy[i]-orig[i]))));found=True;break
 if not found:changes.append(dict(id=str(ids[i]),status='NO_LOCATION_WITHIN_35M'))
 print(changes[-1],flush=True)
clear=np.linalg.norm(xy[:,None]-xy[None,:],axis=2)-rad[:,None]-rad[None,:];np.fill_diagonal(clear,np.inf);remaining=sorted(set(i for a in targets for i in blockers(observer,a)));pair=float(clear.min());encroach=int(np.sum(sh.distance(new,sh.points(xy))<rad-1e-8));nmove=len([x for x in changes if 'new_xy'in x]);status='CANDIDATE_PASS_SCREEN' if active.all() and pair>0 and not remaining and encroach==0 else 'RELOCATION_HOLD'
with (OUT/'placements_v07.csv').open('w',newline='') as out:
 w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
np.savez_compressed(OUT/'spur_v07.npz',xy=q,design_z=h,center=c)
assert np.array_equal(np.load(OUT/'spur_v07.npz')['design_z'],h)
from matplotlib.patches import Circle
fig,(ax,bx)=plt.subplots(1,2,figsize=(13,7),layout='constrained')
for a in [ax,bx]:
 a.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud',alpha=.55);a.plot(*trail.xy,c='#69472c',lw=1.8);a.plot(*foot.exterior.xy,c='#276e99');a.plot(*c.T,c='#ab5f28',lw=2.5);a.plot(*spur.exterior.xy,c='#ab5f28',lw=.7);a.plot(*pad.exterior.xy,c='#40311d');a.scatter(*targets[:,:2].T,marker='*',c='#2369a4',s=90)
 for i in range(len(xy)):
  if i in move:a.add_patch(Circle(orig[i],rad[i],fill=False,ec='#ad4435',lw=1));a.plot([orig[i,0],xy[i,0]],[orig[i,1],xy[i,1]],c='#a54e31',ls='--',lw=.8)
  a.add_patch(Circle(xy[i],rad[i],fc='#527b49' if i not in move else '#e0b652',ec='#34482d',lw=.3,alpha=.6))
 a.set(aspect='equal',xlabel='X (m)',ylabel='Y (m)')
ax.set(xlim=(400,600),ylim=(-400,-300),title='A | Preserved ecology reservations');bx.set(xlim=(440,515),ylim=(-390,-325),title='B | Filleted spur and proposed relocations');fig.suptitle('MOSS A2 V07 | GEOMETRIC DESIGN SCREEN — NOT NATIVE');fig.savefig(OUT/'overlook_v07.png',dpi=150);plt.close(fig)
assert [sha(p) for p in (P,V,T,C)]==expected
report=dict(status=status,inputs_sha256=expected+[sha(D),sha(S)],attempts=attempts,selected=rec,relocations=changes,counts_preserved=len(rows)==451,successful_moves=nmove,remaining_sight_blocker_ids=ids[remaining].tolist(),remaining_spur_pad_encroachments=encroach,min_pair_clearance_m=pair,source_unchanged=True,limits=['Sampled ribbon on existing layered terrain, not conforming native mesh or continuous seam proof. Entry overlap allowed within 7.5m radius; junction partition and drainage unresolved. Circular envelopes and sampled 3-target visibility only, no actual trees or camera. Radius and grade limits are provisional. No D4, native, G2-G4 or adoption.'],outputs={p.name:sha(p) for p in [Path(__file__),OUT/'placements_v07.csv',OUT/'spur_v07.npz',OUT/'overlook_v07.png']});(OUT/'qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
