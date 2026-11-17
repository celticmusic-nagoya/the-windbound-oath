"""RB01 full-body vertex editing from reviewed source/reference landmarks.
No primitive generation, face-feature fitting, or source reacquisition.
"""
import json, math
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'assets/candidates/morwen-rebuild-01/body-fit-v02'
QA=ROOT/'docs/qa/morwen-rebuild-01/body-fit-v02'
OUT.mkdir(parents=True,exist_ok=True);QA.mkdir(parents=True,exist_ok=True)
source=ROOT/'assets/candidates/morwen-rebuild-01/body-workspace/MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
o=bpy.data.objects['MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED'];bpy.context.view_layer.update()
assert o.data.shape_keys is None
v=np.array([list(o.matrix_world@p.co) for p in o.data.vertices],dtype=float)
before=v.copy()
# Front drawing coordinate registration: center x=213.5, sole y=1003.
# Hair-obscured scalp crown y=57 is inferred, NOT directly measured.
H=946.0
Z=lambda y:(1003.0-y)/H
# source normalized world -> image-derived anatomical height targets.
zsrc=np.array([0,.05,.29,.4887,.53,.6,.70,.775,.80,.8254,1.0])
ztgt=np.array([0,Z(955),Z(695),Z(499),Z(460),Z(383),Z(285),Z(225),Z(207),Z(183),1.0])
def pchip(x,xp,yp):
    """Monotone cubic Hermite interpolation, no overshoot at cage stations."""
    h=np.diff(xp);d=np.diff(yp)/h;m=np.zeros(len(xp));m[0]=d[0];m[-1]=d[-1]
    for i in range(1,len(xp)-1):
        if d[i-1]*d[i]>0:
            w1=2*h[i]+h[i-1];w2=h[i]+2*h[i-1]
            m[i]=(w1+w2)/(w1/d[i-1]+w2/d[i])
    k=np.clip(np.searchsorted(xp,x)-1,0,len(xp)-2);t=np.clip((x-xp[k])/h[k],0,1)
    return (2*t**3-3*t**2+1)*yp[k]+(t**3-2*t**2+t)*h[k]*m[k]+(-2*t**3+3*t**2)*yp[k+1]+(t**3-t**2)*h[k]*m[k+1]
def smooth(a,b,x):
    t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)
x,y,z=v.T;ax=np.abs(x)
# Separate arms from torso by source anatomical envelope, feathered at shoulder.
threshold=np.interp(z,[0,.40,.50,.60,.68,.73,.78,.81,1],[.13,.13,.125,.095,.095,.075,.045,.045,.10])
arm=smooth(threshold,threshold+.008,ax)*(1-smooth(.78,.815,z))
arm*=smooth(.38,.43,z)
# Torso/hip/knee/ankle front half-widths in registered source and target.
# Targets measured from visible front outline, not underwear trim.
zs=np.array([0,.05,.15,.29,.40,.4887,.53,.60,.70,.775,.80,.8254,.90,1])
width_scale=np.array([.96,1.00,.97,1.10,1.10,1.09,1.08,.84,.94,.86,.86,.82,.70,.70])
# Side depth and center curve: profile x increases towards anatomical front (-Y).
depth_scale=np.array([1.10,1.02,1.07,1.10,1.18,1.26,1.30,1.30,1.25,1.12,1.03,.85,.83,.83])
src_ycenter=np.array([-.018,.024,.034,.009,.006,.017,.021,.006,.006,.027,.025,.003,.010,.018])
tgt_ycenter=np.array([-.007,.025,.029,.018,.006,0,0,-.018,-.028,-.014,-.009,-.008,-.004,.002])
body=np.zeros_like(v)
body[:,0]=x*pchip(z,zs,width_scale)
body[:,1]=(y-pchip(z,zs,src_ycenter))*pchip(z,zs,depth_scale)+pchip(z,zs,tgt_ycenter)
body[:,2]=pchip(z,zsrc,ztgt)
# Arm centerline maps shoulder/elbow/wrist/finger stations into the observed pose.
armz=np.array([.43,.48,.53,.64,.72,.78])
armx=np.array([.211,.216,.218,.181,.138,.090])
armtx=np.array([.143,.150,.143,.112,.096,.080])
armtz=np.array([Z(569),Z(540),Z(500),Z(376),Z(285),Z(225)])
arms=np.zeros_like(v)
arms[:,0]=np.sign(x)*(pchip(z,armz,armtx)+(ax-pchip(z,armz,armx))*.91)
arms[:,1]=y*.96-.006
arms[:,2]=pchip(z,armz,armtz)
# Above shoulder transition, use torso so neck/head cannot be classified as arms.
after=body*(1-arm[:,None])+arms*arm[:,None]
# Preserve skull expression topology; this is global head scale, not feature fitting.
# No mirroring: source left/right differences and source topology are retained.
inv=o.matrix_world.inverted()
for vert,p in zip(o.data.vertices,after):vert.co=inv@Vector(tuple(p))
o.data.update();o.name='MORWEN_BODY_FIT_V02_UNAPPROVED'
o['method']='Measured full-body semantic cage; direct vertex edits'
o['reference_scope']='Approved Layer0 body structure only'
o['head_crown']='INFERRED pixel y57 ±20; head-count confidence limited'
o['art_status']='REQUIRES_INDEPENDENT_QA'
# Use the existing cameras, materials, framing and light layout from the source
# intake. Only after-mesh views are rendered; existing before PNGs are reused.
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=False
scene.render.resolution_x=512;scene.render.resolution_y=768;scene.render.resolution_percentage=100
for view in ('front','back','right','left'):
    scene.camera=bpy.data.objects['SOURCE_REVIEW_'+view]
    scene.render.filepath=str(OUT/(view+'.png'))
    bpy.ops.render.render(write_still=True)
blend=OUT/'MORWEN_BODY_FIT_V02_UNAPPROVED.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
delta=np.linalg.norm(after-before,axis=1)
landmarks=[]
for name,sz,py,kind in [('sole',0,1003,'visible outline'),('ankle',.05,955,'joint center inferred'),('knee',.29,695,'joint center inferred from contour'),('crotch',.4887,499,'clothed outline; underlying joint inferred'),('pelvis',.53,460,'contour station'),('waist',.6,383,'visible silhouette'),('chest',.7,285,'garment-covered silhouette'),('shoulder',.775,225,'joint inferred from visible shoulder'),('neck',.8,207,'visible contour'),('chin',.8254,183,'visible contour'),('skull_crown',1,57,'INFERRED hidden by hair')]:
    target=Z(py);pred=float(pchip(np.array([sz]),zsrc,ztgt)[0]);landmarks.append({'landmark':name,'reference_y_px':py,'measurement_type':kind,'source_z':sz,'target_z':target,'cage_after_z':pred,'before_error_px':abs(sz-target)*H,'after_cage_error_px':abs(pred-target)*H})
report={'task':'MORWEN-REBUILD-01-ACTUAL-BODY-FIT','method':'RB01-SEMANTIC-FULLBODY-CAGE-02','source':str(source.relative_to(ROOT)),'vertex_count':len(v),'faces':len(o.data.polygons),'changed_vertices':int((delta>1e-7).sum()),'max_vertex_delta_normalized':float(delta.max()),'mean_vertex_delta_normalized':float(delta.mean()),'finite':bool(np.isfinite(after).all()),'topology_preserved':True,'skull_head_count_before':1/(1-.8254),'skull_head_count_after_estimate':1/(1-Z(183)),'skull_head_count_after_is_inferred':True,'crown_uncertainty_px':20,'landmarks':landmarks,'warning':'Cage-station error is not independent silhouette accuracy. Head crown and anatomical joint centers are inferred; drawing views are not calibrated orthographic scans.','G1_body_reference':'PASS','G1_final_design':'BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN','independent_art_qa':'PENDING_HANDOFF'}
(QA/'mesh-edit.json').write_text(json.dumps(report,indent=2)+'\n')
np.savez(QA/'vertex-delta.npz',before_world=before,after_world=after)
print('ACTUAL_BODY_VERTEX_EDIT_SAVED',report['changed_vertices'],report['max_vertex_delta_normalized'])
