"""Technical before/after plots using existing saved renders; no image edits."""
from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/morwen-local-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01';QA=ROOT/'docs/qa/morwen-rebuild-01/body-local-v01'
close=['shoulder_front','shoulder_back','shoulder_right','knee_front','knee_right']
fig,axes=plt.subplots(5,2,figsize=(10,22),facecolor='#ededed')
for i,name in enumerate(close):
 for j,stage in enumerate(('before','after')):
  ax=axes[i,j];ax.set_facecolor('#b9b9b9');ax.imshow(Image.open(OUT/(stage+'_'+name+'.png')));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(stage+' — '+name)
fig.suptitle('Local anatomical surface edit — fixed cameras, same lighting\nActual vertex changes; NOT accepted final art',fontsize=14);fig.tight_layout(rect=(0,0,1,.97));fig.savefig(QA/'local-before-after.png',dpi=115);plt.close(fig)
views=[('front','7809.png'),('back','7810.png'),('right','7807.png'),('left','7808.png')]
fig,axes=plt.subplots(4,3,figsize=(12,20),facecolor='#ededed')
for i,(view,ref) in enumerate(views):
 paths=[ROOT/'tools/blender/production_mesh_08/references'/ref,ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02'/(view+'.png'),OUT/(view+'.png')]
 for j,path in enumerate(paths):
  ax=axes[i,j];ax.set_facecolor('#b9b9b9');ax.imshow(Image.open(path));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(view+' — '+['official','v02 before','local edit after'][j],fontsize=10)
fig.suptitle('Full-body four-view check — local shoulder/knee edit only\nReference illustration is not a calibrated orthographic scan',fontsize=14);fig.tight_layout(rect=(0,0,1,.965));fig.savefig(QA/'four-view-comparison.png',dpi=125);plt.close(fig)
fig,axes=plt.subplots(1,2,figsize=(10,5))
for ax,name in zip(axes,['shoulder_front','knee_front']):
 ax.set_facecolor('#b9b9b9');ax.imshow(Image.open(OUT/('wire_'+name+'.png')));ax.set_xticks([]);ax.set_yticks([]);ax.set_title('Preserved quad connectivity — '+name,fontsize=10)
fig.tight_layout();fig.savefig(QA/'local-topology.png',dpi=130);plt.close(fig)
d=json.loads((QA/'local-technical-qa.json').read_text())
lines=['measurement,target_px,uncertainty_px,v02_before_px,local_after_px,before_error_px,after_error_px']
for x in d['measurements']:lines.append(','.join(str(x[k]) for k in ['measurement','target_px','uncertainty_px','before_px','after_px','before_abs_error_px','after_abs_error_px']))
(QA/'measurement-table.csv').write_text('\n'.join(lines)+'\n')
