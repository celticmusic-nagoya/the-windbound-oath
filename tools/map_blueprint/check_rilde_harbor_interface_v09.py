"""Read-only measurement plus isolated road surface calibration; not production terrain."""
import json,hashlib,sys
from pathlib import Path
import numpy as np,trimesh
from shapely.geometry import Polygon,LineString,box
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
O=Path(__file__).resolve().parent
P,V,Q=map(Path,sys.argv[1:4]);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected=['52e447d0ffa806ecc49b8bb9737420bee7cfb1f6b0315e6677a962e21d7313ea','e9101ea9c35ac68d432a9449bba8c79b95da0456302a15d1c920e74ef2258470','4103b8cd1e974677bf2c7134622542ceefda78e43852fbd27d120c9b98cc5175'];assert list(map(sha,(P,V,Q)))==expected
s=trimesh.load(P,force='scene',process=False);R=np.array([[1.,0,0],[0,0,1],[0,-1,0]])
t,g=s.graph['RILDE_VILLAGE'];v=trimesh.transform_points(s.geometry[g].vertices,t)@R
edge=v[np.isclose(v[:,1],-125)];edge=edge[edge[:,0].argsort()];assert len(edge)==121
A=np.array(json.loads(V.read_text())['road_cross_sections_s_offset_xyz']);road=A[:,:,2:].copy();stations=A[:,0,0];orig=road.copy();assert road.shape==(520,13,3)
entry=road[0];assert np.allclose(entry[:,1],-125);target=np.interp(entry[:,0],edge[:,0],edge[:,2]);delta=target-entry[:,2];fade=1-np.clip(stations/10,0,1)**2*(3-2*np.clip(stations/10,0,1));road[:,:,2]+=fade[:,None]*delta
# Check actual continuous edge compatibility: include every old village edge breakpoint in road width.
xx=np.unique(np.r_[entry[:,0],edge[(edge[:,0]>=entry[:,0].min())&(edge[:,0]<=entry[:,0].max()),0]]);old=np.interp(xx,edge[:,0],edge[:,2]);new=np.interp(xx,road[0,:,0],road[0,:,2]);assert np.max(abs(old-new))<1e-6
long=np.abs(np.diff(road[:,:,2],axis=0))/np.linalg.norm(np.diff(road[:,:,:2],axis=0),axis=2)*100;cross=np.abs(np.diff(road[:,:,2],axis=1))/np.linalg.norm(np.diff(road[:,:,:2],axis=1),axis=2)*100
assert long.max()<15 and cross.max()<10 and np.array_equal(road[stations>=10],orig[stations>=10])
# Determine planned subdivision of existing south boundary, never edit recovered source.
a,b=entry[:,0].min(),entry[:,0].max();covered=edge[(edge[:,0]>=a)&(edge[:,0]<=b),0];missing=[float(x) for x in xx if np.min(abs(edge[:,0]-x))>1e-8]
# All 13 road vertices are positions on village edge, not welded until adjacent triangles are split.
# Road surface is an open design/calibration mesh, not terrain or final geometry.
N,M=road.shape[:2];i=(np.arange(N-1)[:,None]*M+np.arange(M-1)).ravel();f=np.stack([np.stack([i,i+M,i+M+1],1),np.stack([i,i+M+1,i+1],1)],1).reshape(-1,3)
# Ensure upward-facing normals in authored Z-up frame, preserve topology.
w=road.reshape(-1,3);norm=np.cross(w[f[:,1]]-w[f[:,0]],w[f[:,2]]-w[f[:,0]]);f[norm[:,2]<0]=f[norm[:,2]<0][:,[0,2,1]];assert np.all(np.cross(w[f[:,1]]-w[f[:,0]],w[f[:,2]]-w[f[:,0]])[:,2]>0)
m=trimesh.Trimesh(w@R.T,f,process=False);m.visual.face_colors=[157,134,100,255];assert m.is_winding_consistent and m.area_faces.min()>0
out=O/'harbor_road_interface_calibration.glb';out.write_bytes(m.export(file_type='glb'));z=trimesh.load(out,force='mesh',process=False);assert np.array_equal(z.faces,m.faces);re=z.vertices@R;err=np.max(abs(re-w));assert err<2e-5
# Test apron interface, footprint and original land coverage (schematic).
apron=Polygon(json.loads(Q.read_text())['geometry']['apron_polygon_xy']);end=LineString(road[-1,:,:2]);foot=Polygon(np.vstack([road[:,0,:2],road[::-1,-1,:2]]));village=box(-150,-125,150,112.5);assert foot.is_valid and foot.intersection(village).area<1e-8 and end.difference(apron).length<1e-8
# Road-to-natural-ground gap outside the village: no recovered terrain here, do not extrapolate as evidence.
q=dict(status='ISOLATED_INTERFACE_CALIBRATION_NOT_ADOPTED',inputs_sha256=expected,checks=dict(village_boundary_vertices=len(edge),entry_samples=len(xx),entry_width_m=float(b-a),before_max_seam_m=float(max(abs(delta))),after_max_seam_m=float(max(abs(new-old))),reopened_entry_max_seam_m=float(max(abs(re[:M,2]-target))),road_long_max_pct=float(long.max()),road_cross_max_pct=float(cross.max()),unchanged_stations=int(sum(stations>=10)),road_vertices=len(w),road_triangles=len(f),reopen_max_xyz_m=float(err),road_village_overlap_m2=foot.intersection(village).area,apron_end_width_m=end.intersection(apron).length,apron_end_height_residual_m=float(max(abs(road[-1,:,2]-2))),village_mesh_unchanged=True),seam_contract=dict(existing_edge_breakpoints_x_m=covered.tolist(),required_insert_x_m=missing,entry_xyz_m=road[0].tolist(),operation='Future D4-qualified split of adjacent village triangles at inserted vertices; no original edit',weld_status='NOT_RUN_T_JUNCTION_REMAINS'),design=dict(D0='PARTIAL',D1='PARTIAL_RECOVERED_BASELINE',D2='PARTIAL_INTERFACE',D3='HOLD_TERRAIN_EXTENSION_AND_WELD',D4='NOT_RUN'),gates=dict(G1='BLOCKED',G2='NOT_RUN',G3='PARTIAL_CALIBRATION',G4='NOT_RUN'),limits=['Open road surface only; no supporting ground, cut/fill, collision, native or gameplay validation.','Actual recovered mesh is not original V03. Village edge remains unmodified; no topological weld.','Apron is a plan at +2 m, not native geometry.'],outputs=dict(glb_sha256=sha(out),script_sha256=sha(Path(__file__))))
assert list(map(sha,(P,V,Q)))==expected
fig,ax=plt.subplots(1,3,figsize=(13,4.8),layout='constrained');a0=ax[0];a0.fill(*village.exterior.xy,color='#c1ceaf',label='Recovered village');a0.fill(*foot.exterior.xy,color='#a78b65',label='Road calibration');a0.fill(*apron.exterior.xy,color='#d9c9ae',label='Quay plan');a0.set(xlim=(-190,-95),ylim=(-230,-112),aspect='equal',title='A | Local interface plan',xlabel='East X (m)',ylabel='North Y (m)');a0.legend(fontsize=8,loc='lower right');a0.grid(alpha=.2)
a0=ax[1];a0.plot(xx,(old-old[0])*1000,label='Recovered edge',lw=3);a0.plot(entry[:,0],(orig[0,:,2]-old[0])*1000,'--',label='V07 analytic');a0.scatter(road[0,:,0],(road[0,:,2]-old[0])*1000,s=13,label='V09 snapped');a0.set(title='B | Actual south edge',xlabel='East X (m)',ylabel='Relative elevation (mm)');a0.legend(fontsize=8);a0.grid(alpha=.2)
a0=ax[2];a0.plot(stations,road[:,6,2],label='Road center');a0.fill_between(stations,road[:,:,2].min(1),road[:,:,2].max(1),alpha=.4,label='Full-width range');a0.set(title='C | Road longitudinal profile',xlabel='Station (m)',ylabel='Z (m)');a0.grid(alpha=.2);a0.legend(fontsize=8);fig.suptitle('RILDE V09 | RECOVERED VILLAGE SEAM — CALIBRATION ONLY');fig.savefig(O/'harbor_interface_v09.png',dpi=150);plt.close(fig);q['outputs']['png_sha256']=sha(O/'harbor_interface_v09.png');(O/'harbor_interface_v09.json').write_text(json.dumps(q,indent=2)+'\n');print(json.dumps(q,indent=2))
