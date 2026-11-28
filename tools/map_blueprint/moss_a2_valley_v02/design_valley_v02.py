"""A2 local watercourse design feasibility on exact reconstructed source, no native edit."""
import hashlib,json,sys
from pathlib import Path
import numpy as np,trimesh,shapely as sh
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent; P,A=map(Path,sys.argv[1:3]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['2f08043e4f4ecb8c0c1104e48cba0b331cdb3f57afbee6692279031d6d2400fc','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653'];assert [sha(p) for p in (P,A)]==expected
m=trimesh.load(P,force='mesh',process=False);v=m.vertices@np.array([[1.,0,0],[0,0,1],[0,-1,0]])+[500,-300,0];f=m.faces;t=v[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);assert (n[:,2]>0).all();g=-n[:,:2]/n[:,2,None];planes=np.c_[g,t[:,0,2]-(g*t[:,0,:2]).sum(1)];polys=sh.polygons(t[:,:,:2]);tree=sh.STRtree(polys);domain=box(*np.r_[v[:,:2].min(0),v[:,:2].max(0)])
def z(x):
 a,b=tree.query(sh.points(x),predicate='intersects');o=np.full(len(x),np.nan);o[a]=(planes[b,:2]*x[a]).sum(1)+planes[b,2];assert np.isfinite(o).all();return o
B=np.load(A);protected=unary_union([Polygon(np.vstack([B[k][:,0],B[k][::-1,-1]])) for k in ['road_xy','left_xy','right_xy']]).buffer(1)
# Straight reach candidates on west side. Reserve 2m bed, 2m shoulder either side; no road edits.
attempts=[];best=None
for half in [4.,5.,6.]:
 for y in [-365,-375,-385]:
  for x0 in [480,490,500]:
   for x1 in [435,445]:
    for dy in [-5,0,5]:
     start=np.array([x0,y],float);end=np.array([x1,y+dy],float);L=np.linalg.norm(end-start);d=(end-start)/L;nn=np.array([-d[1],d[0]]);s=np.linspace(0,L,int(np.ceil(L/.25))+1);off=np.linspace(-half,half,int(half*8)+1);Q=start+s[:,None,None]*d+off[None,:,None]*nn;foot=Polygon(np.vstack([Q[:,0],Q[::-1,-1]]));over=foot.intersection(protected).area
     if over>1e-9 or foot.difference(domain).area>1e-9:continue
     H=z(Q.reshape(-1,2)).reshape(Q.shape[:2]);center=H[:,len(off)//2];# 0.25m depth, 2% minimum-slope reaches; local 2m fall with a 1m-long rock step
     for k in [.35,.45,.55,.65]:
      p=L*k;fall=2.;# grade chosen to minimize squared discrepancy to source, constrained 2-8%
      step=np.clip((s-(p-.5))/1,0,1);x=np.c_[np.ones(len(s)),-s];target=center-.30+fall*step
      fit=np.linalg.lstsq(x,target,rcond=None)[0];grade=np.clip(fit[1],.02,.08);base=np.mean(target+grade*s);bed=base-grade*s-fall*step
      # Bed cross-section and smooth shoulder tie-in, exactly matching sampled outer terrain. Wet strip is +-1m.
      ab=abs(off);bank=np.interp(ab,[0,.5,1,1.5],[0,0,.25,.45]);blend=np.clip((half-ab)/(half-1.5),0,1);blend=blend**2*(3-2*blend);Z=H+(bed[:,None]+bank[None,:]-H)*blend[None,:];delta=Z-H;N,M=Z.shape;i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();faces=np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3);V=np.dstack([Q,Z]).reshape(-1,3);tt=V[faces];norm=np.cross(tt[:,1]-tt[:,0],tt[:,2]-tt[:,0]);gg=-norm[:,:2]/norm[:,2,None];slope=np.linalg.norm(gg,axis=1);st=np.repeat((s[:-1]+s[1:])/2,2*(M-1));cross=np.tile(np.repeat((off[:-1]+off[1:])/2,2),N-1);# rock step excluded from ordinary shoulder criterion only within 1.5m of fall
      ordinary=(abs(st-p)>1.5)&(abs(cross)>1.5);maxsh=float(slope[ordinary].max()*100);vol=float(np.sum(abs(delta[:-1,:-1]+delta[1:,:-1]+delta[:-1,1:]+delta[1:,1:])/4)*np.diff(s).mean()*.25);# estimate absolute change via cell avg
      rec=dict(half_width_m=half,min_bank_freeboard_m=float(np.min(Z[:,np.isclose(abs(off),1.5)]-(bed[:,None]+.25))),start=start.tolist(),end=end.tolist(),length_m=float(L),fall_station_m=float(p),fall_m=fall,reach_grade_pct=float(grade*100),max_abs_cut_fill_m=float(abs(delta).max()),max_cut_m=float(max(0,-delta.min())),max_fill_m=float(max(0,delta.max())),ordinary_shoulder_max_pct=maxsh,approx_abs_change_m3=vol,source_height_range_m=[float(center.min()),float(center.max())],protected_overlap_m2=over,outer_sample_residual_m=float(abs(delta[:,[0,-1]]).max()),upstream_water_z_m=float(bed[0]+.25),downstream_water_z_m=float(bed[-1]+.25))
      # provisional art screening: preserve broad landform; no >1.5m correction, shoulders <=50% except rock fall
      rec['candidate_pass']=bool(rec['max_abs_cut_fill_m']<=1.5 and maxsh<=50 and rec['min_bank_freeboard_m']>=.19);attempts.append(rec)
      score=(not rec['candidate_pass'],max(0,maxsh-50),max(0,rec['max_abs_cut_fill_m']-1.5),vol)
      if best is None or score<best[0]:best=(score,rec,s,Q,H,Z,bed,off,faces)
assert best;_,rec,s,Q,H,Z,bed,off,faces=best
# This is water stage design only. Endpoint inflow/outflow and rock waterfall actual topology not established.
assert [sha(p) for p in (P,A)]==expected
np.savez_compressed(O/'a2_valley_design_v02.npz',station=s,xy=Q,source_z=H,design_z=Z,bed_z=bed,water_stage_z=bed+.25,faces=faces);assert np.array_equal(np.load(O/'a2_valley_design_v02.npz')['design_z'],Z)
fig,(ax,bx,cx)=plt.subplots(1,3,figsize=(15,5.6),layout='constrained');ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud');ax.plot(*B['road_xy'][:,4].T,c='#63472e',lw=2,label='Protected forest trail');ax.plot(*Q[:,len(off)//2].T,c='#1871a4',lw=2,label='Watercourse candidate');k=np.argmin(abs(s-rec['fall_station_m']));ax.scatter(*Q[k,len(off)//2],c='#e9f6ff',edgecolor='k',s=60,label='Proposed rock fall');ax.set(xlim=(400,600),ylim=(-400,-300),aspect='equal',title='A | A2 valley composition',xlabel='East X (m)',ylabel='North Y (m)');ax.legend(fontsize=7);bx.plot(s,H[:,len(off)//2],label='Source ground',c='#7a694e');bx.plot(s,bed,c='#483b2e',label='Proposed channel bed');bx.plot(s,bed+.25,c='#1b82a9',label='Water stage');bx.set(title='B | Longitudinal rock-step design',xlabel='Station (m)',ylabel='Z (m)');bx.legend(fontsize=8);bx.grid(alpha=.2);im=cx.pcolormesh(s,off,(Z-H).T,cmap='RdBu',shading='auto',vmin=-abs(Z-H).max(),vmax=abs(Z-H).max());cx.set(title='C | Proposed local ground adjustment',xlabel='Station (m)',ylabel='Cross offset (m)');fig.colorbar(im,ax=cx,label='Design minus source (m)');fig.suptitle('MOSS FOREST A2 | WATERCOURSE / ROCK FALL FEASIBILITY — NOT NATIVE',weight='bold');fig.savefig(O/'a2_valley_v02.png',dpi=150);plt.close(fig)
q=dict(status='LOCAL_WATERCOURSE_DESIGN_NOT_ADOPTED',source_sha256=expected,terrain_vertices=len(v),terrain_triangles=len(f),terrain_bounds=np.r_[v.min(0),v.max(0)].tolist(),frame='provisional m X east Y north Z up',candidate_count=len(attempts),candidate_pass_count=sum(a['candidate_pass'] for a in attempts),selected=rec,design_triangles=len(faces),sample_count=H.size,attempts=attempts,source_unchanged=True,limits=['2m fall, 2m water-stage width, 0.25m depth, 0.2m bank crest freeboard, 50% non-rock shoulder, 1.5m correction thresholds are proposed art targets, not formal canon or hydrological engineering.','No water source, drainage outlet, plunge pool volume, continuous shoreline, source CG, actual waterfall mesh or simulation. Rock-step region and inner bank are deliberately excluded from ordinary outer shoulder threshold; exact rock topology needs independent D4. Sampled outer seam only.'],outputs={p.name:sha(p) for p in [Path(__file__),O/'a2_valley_design_v02.npz',O/'a2_valley_v02.png']});(O/'a2_valley_v02.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='attempts'},indent=2))
