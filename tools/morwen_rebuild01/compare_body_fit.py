"""Technical comparison plots and measured residuals; no image/source edits."""
from pathlib import Path
import json,numpy as np
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
qa=ROOT/'docs/qa/morwen-rebuild-01/body-fit-v02'
v=np.load(qa/'vertex-delta.npz');a=v['before_world'];b=v['after_world'];H=946.
# Manually observed visible contour stations. ± pixels expresses drawing/selection uncertainty.
# These are not calibrated anatomical joints; shaded/garment edges can differ.
refs=[('shoulder_width',.775,225,180,10),('waist_width',.600,383,100,6),('pelvis_width',.530,460,198,8),('chest_width',.700,285,140,10),('knee_outer_width',.290,695,124,10),('foot_pair_width',.025,979,116,8)]
rows=[]
for name,z,py,target,unc in refs:
    sel=np.abs(a[:,2]-z)<.008
    if name in ('waist_width','pelvis_width','chest_width'):sel &= np.abs(a[:,0])<(.10 if name=='chest_width' else .125)
    aa=a[sel];bb=b[sel]
    before=float(np.ptp(aa[:,0])*H);after=float(np.ptp(bb[:,0])*H)
    rows.append({'measurement':name,'reference_y_px':py,'target_width_px':target,'reference_uncertainty_px':unc,'source_station_world_z':z,'source_vertices_in_station':len(aa),'before_width_registered_px':before,'after_width_registered_px':after,'before_abs_error_px':abs(before-target),'after_abs_error_px':abs(after-target),'absolute_error_improvement_px':abs(before-target)-abs(after-target),'method':'same source vertex ring band tracked through edit; not alpha silhouette IoU'})
# Arm/hand locations use identifiable anatomical regions, not minimum-alpha bounds.
for name,z,target_x,target_y in [('wrist',.53,143,500),('fingertips',.43,143,569)]:
    sel=(abs(a[:,2]-z)<.012)&(a[:,0]>.16)
    aa=a[sel].mean(0);bb=b[sel].mean(0)
    rows.append({'measurement':name,'target_abs_x_registered_px':target_x,'target_y_px':target_y,'selection':'positive-X source arm band; region centroid, not exact joint','source_vertices':int(sel.sum()),'before_abs_x_px':float(aa[0]*H),'after_abs_x_px':float(bb[0]*H),'before_y_px':float(1003-aa[2]*H),'after_y_px':float(1003-bb[2]*H)})
for name,z,py,target in [('waist_depth',.600,383,110),('pelvis_depth',.530,460,140),('chest_depth',.700,285,142)]:
    sel=(abs(a[:,2]-z)<.008)&(abs(a[:,0])<.075)
    before=float(np.ptp(a[sel,1])*H);after=float(np.ptp(b[sel,1])*H)
    rows.append({'measurement':name,'reference_y_px':py,'target_depth_px':target,'reference_uncertainty_px':12,'before_depth_registered_px':before,'after_depth_registered_px':after,'before_abs_error_px':abs(before-target),'after_abs_error_px':abs(after-target),'absolute_error_improvement_px':abs(before-target)-abs(after-target),'method':'source torso band depth; image profiles not calibrated orthographic scans'})
(qa/'measured-residuals.json').write_text(json.dumps({'scope':'manually selected drawing contour stations; uncertainty retained; not independent art PASS','measurements':rows},indent=2)+'\n')
# Display the actual old PNGs and actual edited PNGs. Do not regenerate baseline.
views=[('front','7809.png'),('back','7810.png'),('right','7807.png'),('left','7808.png')]
fig,axes=plt.subplots(4,3,figsize=(12,20),facecolor='#e6e6e6')
for row,(view,ref) in enumerate(views):
    paths=[ROOT/'tools/blender/production_mesh_08/references'/ref,ROOT/'assets/candidates/morwen-rebuild-01/base-source-intake'/(view+'.png'),ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02'/(view+'.png')]
    for col,path in enumerate(paths):
        ax=axes[row,col];ax.set_facecolor('#b8b8b8');ax.imshow(Image.open(path));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f'{view}: '+['Official Layer 0','Before (existing render)','After v02 (actual edited mesh)'][col],fontsize=10)
fig.suptitle('MORWEN REBUILD01 — body proportion edit / NOT final art\nReference and render canvases differ; side-by-side review, not calibrated silhouette IoU',fontsize=13)
fig.tight_layout(rect=(0,0,1,.965));fig.savefig(qa/'four-view-comparison.png',dpi=130);plt.close(fig)
# Registered anatomical Z station plot: before vs reference target vs edited cage.
d=json.loads((qa/'mesh-edit.json').read_text());lm=d['landmarks']
fig,ax=plt.subplots(figsize=(10,6));idx=np.arange(len(lm));ax.scatter([x['source_z'] for x in lm],idx,label='Before',c='#a33');ax.scatter([x['target_z'] for x in lm],idx,label='Reference target (some inferred)',marker='x',c='#222');ax.scatter([x['cage_after_z'] for x in lm],idx,label='Edited cage station (not contour QA)',facecolors='none',edgecolors='#237a4f',s=85);ax.set_yticks(idx,[x['landmark'] for x in lm]);ax.set_xlabel('Normalized anatomical height (sole=0, inferred scalp crown=1)');ax.grid(alpha=.2);ax.legend(fontsize=8);fig.tight_layout();fig.savefig(qa/'landmark-height-comparison.png',dpi=140)
print(json.dumps(rows,indent=2))
