"""A3 localized gate landscape reserves and isolated progression contract tests. No runtime or native writes."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent
inputs=list(map(Path,sys.argv[1:6]));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest(); hashes=list(map(sha,inputs))
assert hashes==['e955b7ba95c01520b867dc7279b23ec8b18dd4da26e9764d31b69e1369dee98b','67add93ee010f0c8bb19d2385c2159587e0ad3fc10082a0043bc4d50b9393653','c3d6c314cc23f50012840a2b81414f46ea638ac6f7917f3ae557394e434d3f32','3ab29ffddcaabce5a997e1ce65bd6c55e0f3df2d8e73f00049fb9c6474e9f65e','b4adf3246b4f9c298f4017050966e332af859caf29038468c3e305d726ce78cf']
src=inputs[4].read_text();exec(src[:src.index('# Arena: circular')]);O=Path(__file__).resolve().parent
from shapely.ops import unary_union
from shapely.geometry import mapping
q=json.loads(inputs[3].read_text());bc=np.array(q['selected_barrier']['center_xy']);ac=np.array(q['selected_arena']['center_xy']);hc=np.array(q['selected_hero']['center_xy']);arena=Point(ac).buffer(10,quad_segs=64);hero=Point(hc).buffer(5,quad_segs=64);gate=Polygon([bc+a*d+b*n for a,b in [(-1,-2.5),(1,-2.5),(1,2.5),(-1,2.5)]])
protected=unary_union([road,pad,arena,hero]);actor=.65;steep=unary_union(list(P[0][np.linalg.norm(G[0],axis=1)>.15]));base=domain.buffer(-actor).difference(steep.buffer(actor));start=Point(bc-5*d);goal=Point(ac)
def connected(g,a,b):return any(p.covers(a) and p.covers(b) for p in sh.get_parts(g))
def poly(coords):return Polygon([bc+a*d+b*n for a,b in coords])
# Artist-directed asymmetric silhouettes; roots belong to flank trees, not the distant sacred tree.
# local axes a forward, b left. All footprints are reservations, not meshes.
rock_L=[(-3.8,0),(-2.4,-.4),(.2,-.6),(2.4,.1),(3.9,1.6),(2.5,3.3),(-.9,4.2),(-3.5,2.4)]
rock_R=[(-4.6,1.1),(-2.5,-.3),(0,-.5),(2.7,.2),(4.0,1.9),(2.6,3.6),(-.4,3.1),(-3.7,2.7)]
root_L=[(-3.9,4.0),(-2.5,3.3),(-1.5,3.0),(-.6,4.0),(.4,4.7),(-1.0,5.4),(-3.1,5.9),(-4.6,5.3)]
root_R=[(1.9,3.3),(2.8,2.8),(4.1,3.3),(5.5,4.1),(6.2,5.5),(4.4,5.8),(2.3,4.9)]
rows=[];shapes=[]
for offset in [3.5,4,4.5,5]:
 for scale in [.7,.85,1.]:
  items=[]
  for name,side,coords,h in [('rock_L',1,rock_L,3.2),('rock_R',-1,rock_R,2.6),('root_L',1,root_L,1.1),('root_R',-1,root_R,.9)]:
   p=poly([(a*scale,side*(offset+b*scale)) for a,b in coords]);m=metric(p);items.append((name,p,h*scale,m))
  group=unary_union([p for _,p,_,_ in items]);rocks=unary_union([p for name,p,h,m in items if name.startswith('rock')]);roots=unary_union([p for name,p,h,m in items if name.startswith('root')]);over=group.intersection(protected).area;sep=group.distance(protected);out=group.difference(domain).area
  op=connected(base.difference(group.buffer(actor)),start,goal);cl=connected(base.difference(group.union(gate).buffer(actor)),start,goal)
  # gate centreline clearance for a swept disk, excluding gate itself
  line=LineString([bc-5*d,bc+5*d]);clear=line.distance(group)-actor
  row=dict(offset_m=offset,scale=scale,area_m2=group.area,rock_area_m2=rocks.area,root_area_m2=roots.area,protected_overlap_m2=over,protected_clearance_m=sep,outside_m2=out,max_grade_pct=max(m['grade_pct'] for _,_,_,m in items),max_relief_m=max(m['relief_m'] for _,_,_,m in items),open_connected=op,closed_bypass_connected=cl,swept_centerline_clearance_m=clear,flank_nearest_m=float(Point(bc).distance(group)))
  row['pass_local_art_screen']=bool(out<1e-8 and over<1e-8 and sep>=.25 and clear>=.5 and op and row['max_grade_pct']<=15 and row['max_relief_m']<=1.5)
  rows.append(row);shapes.append((items,group))
valid=[i for i,row in enumerate(rows) if row['pass_local_art_screen']];assert valid
# Prefer largest landscape silhouette while retaining margins, then closest to path.
i=min(valid,key=lambda i:(-rows[i]['scale'],rows[i]['flank_nearest_m']));sel=rows[i];items,group=shapes[i]
# State contract: authoritative event flags are required; location alone never enables battle/altar.
# Only proposed decisions, no claim about engine or exact canon one-way release condition.
def permit(state,action):
 if action=='enter_via_gate':return state in ('UNSEALED','INSIDE','ENCOUNTER_DONE','OATH_DONE')
 if action=='enter_via_bypass':return False
 if action=='reverse_via_gate':return False if state in ('INSIDE','ENCOUNTER_DONE') else None # post-oath policy not defined
 if action=='encounter':return state=='INSIDE'
 if action=='altar':return state=='ENCOUNTER_DONE'
 if action=='grant_sword':return state=='ENCOUNTER_DONE'
 raise ValueError(action)
states=['SEALED','UNSEALED','INSIDE','ENCOUNTER_DONE','OATH_DONE'];actions=['enter_via_gate','enter_via_bypass','reverse_via_gate','encounter','altar','grant_sword']
expected=[[False,False,None,False,False,False],[True,False,None,False,False,False],[True,False,False,True,False,False],[True,False,False,False,True,True],[True,False,None,False,False,False]]
tests=[dict(state=s,action=a,expected=expected[j][k],actual=permit(s,a)) for j,s in enumerate(states) for k,a in enumerate(actions)];assert all(x['expected']==x['actual'] for x in tests)
# Test pure transitions, including idempotent reward and denial of out-of-order calls.
def step(s,event):
 return {('SEALED','unseal'):'UNSEALED',('UNSEALED','cross_authorized_gate'):'INSIDE',('INSIDE','encounter_complete'):'ENCOUNTER_DONE',('ENCOUNTER_DONE','oath_reward_committed'):'OATH_DONE'}.get((s,event),s)
seqs=[(['cross_authorized_gate','encounter_complete','oath_reward_committed'],'SEALED'),(['unseal','oath_reward_committed'],'UNSEALED'),(['unseal','cross_authorized_gate','encounter_complete','oath_reward_committed','oath_reward_committed'],'OATH_DONE'),(['unseal','cross_authorized_gate','oath_reward_committed'],'INSIDE')]
transition=[]
for events,exp in seqs:
 s='SEALED';trail=[s]
 for e in events:s=step(s,e);trail.append(s)
 assert s==exp;transition.append(dict(events=events,states=trail,expected=exp))
geometry=dict(frame='provisional metres X east Y north Z up',gate=mapping(gate),features=[dict(id=name,footprint=mapping(p),height_reserve_m=h,ground=m) for name,p,h,m in items],contract=dict(states=states,actions=actions,tests=tests,transitions=transition,unknowns=['Actual state IDs/save schema and event owner validation','Full-world navigation boundary and bypass prevention','Reverse release after oath','Whether gate reopening is allowed; no new canon']))
(O/'gate_local_contract.json').write_text(json.dumps(geometry,indent=2)+'\n');assert all(sh.geometry.shape(x['footprint']).equals(p) for x,(_,p,_,_) in zip(geometry['features'],items))
fig,(ax,bx)=plt.subplots(1,2,figsize=(13,6),layout='constrained');ax.tripcolor(v[:,0],v[:,1],f,v[:,2],cmap='terrain',shading='gouraud');ax.plot(*r[st>=330].T,c='white',lw=1.4,label='Existing trail');
for p,col,l in [(arena,'#c07a4a','Arena'),(hero,'#32683a','Sacred tree reserve'),(gate,'#8054b0','Gate'),(pad,'#dab648','Altar approach')]:ax.fill(*p.exterior.xy,color=col,alpha=.65,label=l)
for name,p,h,m in items:ax.fill(*p.exterior.xy,color='#505963' if name.startswith('rock') else '#8a6340',alpha=.85);ax.annotate(name,xy=p.centroid.coords[0],fontsize=8)
ax.set(xlim=(625,700),ylim=(-500,-435),aspect='equal',title='A | Local rock and root reserves',xlabel='X east (m)',ylabel='Y north (m)');ax.legend(fontsize=8,loc='upper right')
# local cross-section at gate: sampled ground, maximum authored envelopes of actual cross-section footprints
bs=np.linspace(-12,12,241);xy=bc+bs[:,None]*n;zs=height(xy);bx.plot(bs,zs,c='#465b40',label='Measured ground');bx.axvspan(-2.5,2.5,color='#8054b0',alpha=.18,label='Gate reserve')
for name,p,h,m in items:
 mask=sh.covers(p,sh.points(xy));bx.fill_between(bs,zs,zs+h,where=mask,color='#505963' if name.startswith('rock') else '#8a6340',alpha=.7,label=name)
bx.set(title='B | Gate section — height reserves, not mesh',xlabel='Local transverse distance (m)',ylabel='Z (m)');bx.grid(alpha=.2);bx.legend(fontsize=8);fig.suptitle('MOSS FOREST A3 | V04 • LOCAL LANDSCAPE / PROGRESSION CONTRACT');fig.savefig(O/'gate_local_v04.png',dpi=155);plt.close(fig)
report=dict(status='LOCAL_RESERVES_PASS_GLOBAL_BYPASS_HOLD',input_sha256=hashes,candidate_count=len(rows),pass_count=len(valid),selected=sel,features=[dict(id=name,height_reserve_m=h,footprint_m2=p.area,ground=m) for name,p,h,m in items],candidates=rows,contract_tests=len(tests),contract_transition_sequences=len(transition),inputs_unchanged=list(map(sha,inputs))==hashes,limits=['Provisional planar footprint and height reserves; no geometry, climbing, collision, runtime integration or full-world bypass proof. The closed gate remains bypassable physically. State contract tests only proposed pure functions, not actual game. No official CG or D4.'])
(O/'qa.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='candidates'},indent=2))
