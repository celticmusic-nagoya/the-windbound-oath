"""Scientific review plots of the fixed failed reconstruction; no retouching."""
from pathlib import Path
import json,os
os.environ.setdefault('MPLCONFIGDIR','/tmp/morwen-quad-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2];Q=ROOT/'docs/qa/morwen-rebuild-01/body-quad-v01';A=ROOT/'assets/candidates/morwen-rebuild-01/body-quad-v01';B=ROOT/'assets/candidates/morwen-rebuild-01/body-local-v01'
views=[('front','7809.png'),('back','7810.png'),('right','7807.png'),('left','7808.png')]
fig,axes=plt.subplots(4,3,figsize=(12,20),facecolor='#ededed')
for i,(view,ref) in enumerate(views):
 for j,p in enumerate([ROOT/'tools/blender/production_mesh_08/references'/ref,B/(view+'.png'),A/(view+'.png')]):
  ax=axes[i,j];ax.set_facecolor('#b8b8b8');ax.imshow(Image.open(p));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(view+' — '+['official reference','before local checkpoint','quad reconstruction — FAIL'][j],fontsize=9)
fig.suptitle('MORWEN quad reconstruction — failed candidate, not accepted\nReference drawings are not calibrated orthographic scans',fontsize=13);fig.tight_layout(rect=(0,0,1,.965));fig.savefig(Q/'four-view-comparison.png',dpi=120);plt.close(fig)
close=['shoulder_front','shoulder_back','shoulder_right','knee_front','knee_right']
fig,axes=plt.subplots(5,2,figsize=(10,22),facecolor='#ededed')
for i,name in enumerate(close):
 for j,p in enumerate([B/('after_'+name+'.png'),A/('after_'+name+'.png')]):
  ax=axes[i,j];ax.set_facecolor('#b8b8b8');ax.imshow(Image.open(p));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(('before — ' if j==0 else 'quad candidate — ')+name)
fig.suptitle('Local before/after — G2 FAIL retained',fontsize=14);fig.tight_layout(rect=(0,0,1,.975));fig.savefig(Q/'local-before-after.png',dpi=110);plt.close(fig)
fig,axes=plt.subplots(3,2,figsize=(10,13))
for i,name in enumerate(['shoulder_front','shoulder_back','knee_front']):
 for j,phase in enumerate(['before','after']):
  ax=axes[i,j];ax.set_facecolor('#b8b8b8');ax.imshow(Image.open(A/(phase+'_wire_'+name+'.png')));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(phase+' actual polygon edges — '+name,fontsize=9)
fig.tight_layout();fig.savefig(Q/'topology-before-after.png',dpi=125);plt.close(fig)
fig,axes=plt.subplots(4,2,figsize=(10,17))
for i,(kind,deg,full) in enumerate([('shoulder',30,'front'),('shoulder',60,'front'),('knee',45,'right'),('knee',90,'right')]):
 for j,suffix in enumerate([full,'close']):
  ax=axes[i,j];ax.set_facecolor('#b8b8b8');ax.imshow(Image.open(A/f'pose_{kind}_{deg}_{suffix}.png'));ax.set_xticks([]);ax.set_yticks([]);ax.set_title(f'QA only {kind} {deg}deg — '+suffix,fontsize=10)
fig.suptitle('Diagnostic bends — FAIL / not a production rig\nShoulder60 full camera enlarged; closeups intentionally crop outside joint',fontsize=12);fig.tight_layout(rect=(0,0,1,.965));fig.savefig(Q/'bend-diagnostics.png',dpi=115);plt.close(fig)
c=json.loads((Q/'correspondence-qa.json').read_text());w=c['warnings'];before=json.loads((Q/'INDEPENDENT_WARNING_ANALYSIS.json').read_text());old={x['face_id']:x['rest_angle_after'] for x in before['new_first_triangle_normal_flags']}
fig,ax=plt.subplots(figsize=(11,7));ys=np.arange(len(w));ax.barh(ys-.18,[old[x['old_face_id']] for x in w],height=.35,label='Before: old first-triangle normal',color='#888');ax.barh(ys+.18,[max(z['angle_vs_original_source_normal'] for z in x['samples']) for x in w],height=.35,label='After: worst of 4 tracked UV samples',color=['#b23a32' if not x['resolved_at_all_samples'] else '#54866f' for x in w]);ax.axvline(90,c='black',ls='--',lw=1);ax.set_yticks(ys,[str(x['old_face_id']) for x in w]);ax.set_xlabel('Degrees against original source normal; not a standalone intersection test');ax.set_ylabel('Old warning face ID (retired but traced)');ax.legend(fontsize=8);ax.set_title('13/15 tracked warning regions below threshold — 2 remain');fig.tight_layout();fig.savefig(Q/'warning15-correspondence.png',dpi=135);plt.close(fig)
rows=['measurement,target_px,before_px,after_correspondence_px,before_error_px,after_error_px']
for x in c['measurements']:rows.append(','.join(str(x[k]) for k in ['measurement','target_px','before_px','after_correspondence_px','before_error_px','after_error_px']))
(Q/'measurement-table.csv').write_text('\n'.join(rows)+'\n')
