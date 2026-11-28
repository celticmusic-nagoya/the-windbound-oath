"""Joint dry-land reservation re-layout, no native edits."""
import sys,hashlib,json,csv
from pathlib import Path
OUT=Path(__file__).resolve().parent
P,V,T,C,S,U=map(Path,sys.argv[1:7]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S)=='8136ad145a9eef636fb9780927f0232cf0b7553793c6d2794833cf7f6822f548'
assert sha(U)=='40f8ea9359aeb3cd69c742fb366728c89b1a80670059cd7e40a263a790db9c03'
sys.argv=[str(S),str(P),str(V),str(T),str(C)];exec(compile(S.read_text().split('# 2m radius viewing pad')[0],str(S),'exec'))
from shapely.ops import nearest_points
from matplotlib.patches import Circle
orig=xy.copy();origz=z.copy();D=np.load(U);q=D['xy'];c=D['center'];pos=c[-1];spur=Polygon(np.vstack([q[:,0],q[::-1,-1]]));pad=Point(pos).buffer(2,quad_segs=64);new=spur.union(pad)
trail=LineString(B['road_xy'][:,4]);fall=Point(467.75,-385);vp=nearest_points(trail.intersection(domain),fall)[0];view0=LineString([vp,fall]).buffer(2.5).intersection(domain)
observer=np.r_[pos,ground(pos[None,:])[0]+1.65];sightlines=unary_union([LineString([pos,a[:2]]) for a in targets]);tall=np.isin(kind,['ancient_tree_reserve','forest_tall','deciduous','rock_reserve']);trees=np.isin(kind,['ancient_tree_reserve','forest_tall','deciduous']);ex=reserved.union(new).union(sightlines.buffer(.1));ex_tall=ex.union(view0)
xg,yg=np.meshgrid(np.arange(400.5,600,1),np.arange(-399.5,-300,1));grid=np.vstack([np.c_[xg.ravel(),yg.ravel()],orig]);pts=sh.points(grid);in_dom=sh.covers(domain,pts);bd=sh.distance(domain.boundary,pts);de=sh.distance(ex,pts);dt=sh.distance(ex_tall,pts);origpts=sh.points(orig)
mandatory=set(np.flatnonzero(np.where(tall,sh.distance(ex_tall,origpts),sh.distance(ex,origpts))<rad+1e-6));mandatory.update(i for a in targets for i in blockers(observer,a));assert mandatory
report=[];best=None
for halo in [18,35]:
 region=new.buffer(halo).union(sightlines.buffer(halo)).intersection(domain);moving=np.flatnonzero((sh.distance(region,origpts)<rad)|np.isin(np.arange(len(rows)),list(mandatory)));fixed=np.setdiff1d(np.arange(len(rows)),moving);allowed=sh.covers(region,pts)&in_dom
 for seed in [0,1]:
  rng=np.random.default_rng(20261125+seed);xy[:]=orig;z[:]=origz;active=np.zeros(len(rows),bool);active[fixed]=True;margin=np.full(len(grid),np.inf)
  for i in fixed:margin=np.minimum(margin,np.hypot(grid[:,0]-xy[i,0],grid[:,1]-xy[i,1])-rad[i])
  order=sorted(moving,key=lambda i:(kind[i]!='ancient_tree_reserve',not trees[i],-rad[i]*(1+rng.uniform(-.08,.08)),ids[i]));failed=[]
  for i in order:
   r=rad[i];gap=.3 if trees[i] else .1;ok=allowed&(bd>=r+1e-5)&((dt if tall[i] else de)>=r+1e-5)&(margin>=r+gap)
   candidates=np.flatnonzero(ok);cost=np.hypot(grid[candidates,0]-orig[i,0],grid[candidates,1]-orig[i,1]);idx=candidates[np.argsort(cost,kind='stable')];found=False
   for k in idx:
    ii=tree.query(pts[k],predicate='dwithin',distance=float(r));grade=float(np.linalg.norm(g[ii],axis=1).max()) if len(ii) else np.inf
    if grade>(.25 if trees[i] else .40):continue
    xy[i]=grid[k];z[i]=ground(grid[k:k+1])[0];active[i]=True;found=True;margin=np.minimum(margin,np.hypot(grid[:,0]-xy[i,0],grid[:,1]-xy[i,1])-r);break
   if not found:failed.append(i)
  score=(len(failed),int(sum(trees[failed])),float(np.linalg.norm(xy-orig,axis=1)[active].sum()));row=dict(halo_m=halo,seed=seed,group_count=len(moving),failed_ids=ids[failed].tolist(),total_displacement_m=score[2]);report.append(row);print(row,flush=True)
  if best is None or score<best[0]:best=(score,xy.copy(),z.copy(),active.copy(),moving.copy(),row)
 if best[0][0]==0:break
_,xy,z,active,moving,selected=best
ix=np.flatnonzero(active);dd=np.linalg.norm(xy[ix,None]-xy[None,ix],axis=2)-rad[ix,None]-rad[None,ix];np.fill_diagonal(dd,np.inf);clear=float(dd.min());p=sh.points(xy[ix]);ec=np.where(tall[ix],sh.distance(ex_tall,p),sh.distance(ex,p))-rad[ix];bc=sh.distance(domain.boundary,p)-rad[ix];grades=[]
for i in ix:
 ii=tree.query(Point(xy[i]),predicate='dwithin',distance=float(rad[i]));grades.append(float(np.linalg.norm(g[ii],axis=1).max())*100)
blocks=sorted(set(int(i) for a in targets for i in blockers(observer,a) if active[i]));outside=int(np.sum(bc<0));exfail=int(np.sum(ec<0));gradefail=int(np.sum(np.array(grades)>np.where(trees[ix],25,40)+1e-8));assert clear>0 and outside==0 and exfail==0 and gradefail==0 and not blocks
name='placements_candidate.csv' if active.all() else 'placements_reduced_candidate.csv'
for i,gr,e in zip(ix,grades,ec):rows[i].update(x_m=str(xy[i,0]),y_m=str(xy[i,1]),z_m=str(z[i]),max_source_grade_pct=str(gr),exclusion_clearance_m=str(e))
with (OUT/name).open('w',newline='') as o:
 w=csv.DictWriter(o,fieldnames=list(rows[0]));w.writeheader();w.writerows([rows[i] for i in ix])
colors={'ancient_tree_reserve':'#c99a40','forest_tall':'#355b41','deciduous':'#80a657','rock_reserve':'#7d828a','fern_cluster':'#65a48a','moss_patch':'#beca78'}
fig,(ax,bx)=plt.subplots(1,2,figsize=(14,7),layout='constrained')
for a,coords,indices in [(ax,orig,np.arange(len(rows))),(bx,xy,ix)]:
 a.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud',alpha=.5);a.plot(*trail.xy,c='#785432');a.plot(*spur.exterior.xy,c='#a35e2d');a.plot(*pad.exterior.xy,c='#a35e2d');a.plot(*foot.exterior.xy,c='#236a99');a.plot(*c.T,c='#a35e2d',lw=2)
 for line in sh.get_parts(sightlines):a.plot(*line.xy,ls='--',c='#9f5926')
 for i in indices:a.add_patch(Circle(coords[i],rad[i],fc=colors[kind[i]],ec='#354337',lw=.35,alpha=.8))
 a.set(xlim=(400,600),ylim=(-400,-300),aspect='equal',xlabel='X (m)',ylabel='Y (m)')
ax.set_title('A | V04 original reserves');bx.set_title(f'B | Joint re-layout: {len(ix)} / {len(rows)} reserves');fig.suptitle('MOSS A2 V09 | PLACEMENT DESIGN ONLY — NOT NATIVE');fig.savefig(OUT/'relayout_v09.png',dpi=150);plt.close(fig)
assert [sha(p) for p in (P,V,T,C)]==expected
counts={k:int(sum(kind[ix]==k)) for k in sorted(set(kind))};changed=np.flatnonzero(active&(np.linalg.norm(xy-orig,axis=1)>1e-8));result=dict(status='FULL_COUNT_SCREEN_PASS' if active.all() else 'REDUCED_DENSITY_ALTERNATIVE_ONLY',input_sha256=expected+[sha(S),sha(U)],attempts=report,selected=selected,mandatory_ids=ids[sorted(mandatory)].tolist(),placed=len(ix),original=len(rows),counts=counts,unplaced_ids=ids[~active].tolist(),changed=len(changed),max_move_m=float(np.linalg.norm(xy[changed]-orig[changed],axis=1).max()) if len(changed) else 0,min_pair_clearance_m=clear,min_exclusion_clearance_m=float(ec.min()),min_boundary_clearance_m=float(bc.min()),max_grade_pct=max(grades),sight_blockers=blocks,grade_failures=gradefail,exclusion_failures=exfail,outside=outside,limits=['Finite 1m grid, bounded group, conservative plan and cylinder envelopes, provisional thresholds. No actual asset mesh, camera, junction, hydrology, D4 or native work. Any unplaced ID is explicitly withheld from reduced-density alternative, not deleted from V04.'],outputs={p.name:sha(p) for p in [Path(__file__),OUT/name,OUT/'relayout_v09.png']});(OUT/'qa.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
