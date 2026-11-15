"""Read-only geometry inspection plus review renders; disables failed delivery."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from qa_geometry_08 import edge_audit,proper_triangle_crossing,coplanar_overlap_area

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(HERE.parent/'eyelid_sculpt'))
from run_structural_qa_07 import stage,fingerprints
VIEWS={'front':0,'q3L':-45,'q3R':45,'left':-90,'right':90}


def mesh_snapshot(ob,basis=False,skin_only=False):
    me=ob.data;me.calc_loop_triangles()
    if basis:verts=np.array([tuple(ob.matrix_world@v.co) for v in me.shape_keys.key_blocks[0].data])
    else:
        ob.update_tag();bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());verts=np.array([tuple(ev.matrix_world@v.co) for v in ev.data.vertices])
    ts=[t for t in me.loop_triangles if not skin_only or 'SKIN' in me.materials[t.material_index].name]
    tris=np.array([t.vertices[:] for t in ts],dtype=int)
    bvh=BVHTree.FromPolygons([Vector(p) for p in verts],tris.tolist(),all_triangles=True)
    return verts,tris,ts,bvh


def intersection_audit(a,b=None):
    va,ta,_,ba=a;vb,tb,_,bb=b if b else a;proper=[];coplanar=[]
    for i,j in ba.overlap(bb):
        if b is None and i>=j:continue
        aa,bc=va[ta[i]],vb[tb[j]]
        if proper_triangle_crossing(aa,bc):proper.append([int(i),int(j)])
        if coplanar_overlap_area(aa,bc)>1e-13:coplanar.append([int(i),int(j)])
    return {'proper_crossing_pairs':proper,'coplanar_positive_area_pairs':coplanar}


def mesh_checks(ob,roles):
    current=mesh_snapshot(ob);neutral=mesh_snapshot(ob,basis=True)
    verts,tris,ts,_=current;rest=neutral[0];normals=np.cross(verts[tris[:,1]]-verts[tris[:,0]],verts[tris[:,2]]-verts[tris[:,0]])
    baseline=np.cross(rest[tris[:,1]]-rest[tris[:,0]],rest[tris[:,2]]-rest[tris[:,0]])
    areas=np.linalg.norm(normals,axis=1)/2
    me=ob.data;faces=[list(p.vertices) for p in me.polygons];topology=edge_audit(faces)
    signed_volume=float(np.sum(np.einsum('ij,ij->i',verts[tris[:,0]],np.cross(verts[tris[:,1]],verts[tris[:,2]])))/6)
    front=[i for i,t in enumerate(ts) if roles[t.polygon_index]=='front'];rear=[i for i,t in enumerate(ts) if roles[t.polygon_index]=='rear']
    front_units=normals[front]/np.linalg.norm(normals[front],axis=1)[:,None]
    uv=me.uv_layers.active.data;uv_areas=[]
    for t in ts:
        p=np.array([uv[i].uv[:] for i in t.loops]);a,b=p[1]-p[0],p[2]-p[0];uv_areas.append(float(a[0]*b[1]-a[1]*b[0])/2)
    uv_areas=np.array(uv_areas);front_uv=uv_areas[front];sign=1 if sum(front_uv)>0 else -1
    stride=len(verts)//2;thickness=np.linalg.norm(verts[:stride]-verts[stride:],axis=1)
    return {'basis_pose':ob.get('basis_pose','NEUTRAL_REFERENCE'),'vertices':len(verts),'polygons':len(faces),'triangles':len(tris),'euler_characteristic':len(verts)-topology['edge_count']+len(faces),**topology,
            'signed_volume_m3':signed_volume,'degenerate_triangles':int(sum(areas<1e-12)),
            'flipped_triangles_vs_basis':int(sum(np.einsum('ij,ij->i',normals,baseline)<0)),
            'front_nonanterior_triangles':int(sum(normals[front,1]<=0)),'rear_nonposterior_triangles':int(sum(normals[rear,1]>=0)),
            'front_uv_orientation_disagreements':int(sum(front_uv*sign<=0)),'degenerate_uv_triangles':int(sum(abs(uv_areas)<1e-14)),
            'thickness_anterior_m':{'min':float(min(thickness)),'max':float(max(thickness))},
            'minimum_projected_normal_thickness_m':float(.0006*min(front_units[:,1])),
            'self_intersections':intersection_audit(current)},current


def view_rays(preview,cages,metadata):
    snapshots=[mesh_snapshot(preview,skin_only=True)]+[mesh_snapshot(ob) for ob in cages]+[mesh_snapshot(bpy.data.objects['MORWEN_Eyes'])]
    # Render-eligible engineering geometry, explicitly excluding hidden source Face
    # and the four unmodified sculpt templates. Alpha cards are excluded here.
    verts=[];tris=[];labels=[];count=0
    for label,(v,t,_,_) in enumerate(snapshots):
        verts.extend(v);tris.extend((t+count).tolist());labels.extend([label]*len(t));count+=len(v)
    bvh=BVHTree.FromPolygons([Vector(p) for p in verts],tris,all_triangles=True)
    result={}
    for side,m in metadata.items():
        points=np.array(m['neutral_margin_upper']+m['neutral_margin_lower']);center=points.mean(axis=0)
        result[side]={}
        for name,degrees in VIEWS.items():
            angle=math.radians(degrees);d=np.array([math.sin(angle),math.cos(angle),0]);h=np.array([math.cos(angle),-math.sin(angle),0])
            horizontal=(points-center)@h;z=points[:,2]-center[2];back=eyes=miss=0
            for x in np.linspace(min(horizontal)-.003,max(horizontal)+.003,33):
                for y in np.linspace(min(z)-.003,max(z)+.003,33):
                    origin=Vector(center+h*x+np.array([0,0,y])+d*.3)
                    point,normal,idx,_=bvh.ray_cast(origin,Vector(-d))
                    if point is None:miss+=1
                    elif labels[idx]==len(snapshots)-1:eyes+=1
                    elif normal.dot(Vector(d))<0:back+=1
            result[side][name]={'rays':1089,'backface_first_hits':back,'eye_first_hits_expected_in_half_aperture':eyes,'background_misses':miss,'sampling':'camera-plane orthographic grid, no degenerate profile projection'}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--design',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--renders',action='store_true');a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);before_file=hashlib.sha256(a.candidate.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(a.candidate.resolve()));before=fingerprints();face=bpy.data.objects['Face'];key_order=[k.name for k in face.data.shape_keys.key_blocks]
    design=json.loads(a.design.read_text());metadata=design['sides'];preview=bpy.data.objects[design['preview_object']];cages=[bpy.data.objects[f'M08_{s}_CONTACT_CAGE_050'] for s in ('R','L')]
    report={'status':'QA_IN_PROGRESS_NOT_ADOPTED','attempt_id':design['attempt_id'],'method_family':design['method_family'],'source_sha256':design['source_sha256'],'candidate_input_sha256':before_file,'blender':bpy.app.version_string,'neutral_to_half_animation':design.get('neutral_to_half_animation','NOT_RUN_FULL_SWEEP'),'sides':{},'renders':[],'G1':'PARTIAL_FULL_CANON_BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'}
    # Replay the saved disabled snapshot for diagnostic renders only. Restoring
    # visibility is not a new cage/deformation build; disable again before save.
    face.hide_render=True;face.hide_set(True)
    for ob in cages+[preview]:ob.hide_render=False;ob.hide_set(False)
    for ob in bpy.data.objects:
        if ob.name.startswith('M07_SCULPT_'):ob.hide_render=True;ob.hide_set(True)
    snap=mesh_snapshot(preview,skin_only=True)
    for side,ob in zip(('R','L'),cages):
        checks,current=mesh_checks(ob,metadata[side]['face_roles']);checks['attachment_surface_intersections']=intersection_audit(current,snap)
        m=metadata[side];up,lo=np.array(m['half_margin_upper']),np.array(m['half_margin_lower']);nu,nl=np.array(m['neutral_margin_upper']),np.array(m['neutral_margin_lower']);gap=np.linalg.norm(up-lo,axis=1);neutralgap=np.linalg.norm(nu-nl,axis=1);valid=neutralgap>1e-9
        checks['gap_ratio_min_max']=[float(min(gap[valid]/neutralgap[valid])),float(max(gap[valid]/neutralgap[valid]))]
        projected=np.linalg.norm((up-lo)[:,[0,2]],axis=1);base_projected=np.linalg.norm((nu-nl)[:,[0,2]],axis=1);use=base_projected>1e-9
        checks['projected_xz_aperture_ratio_min_max']=[float(min(projected[use]/base_projected[use])),float(max(projected[use]/base_projected[use]))]
        checks['fixed_canthus_max_error_m']=float(max(np.linalg.norm(up[[0,-1]]-nu[[0,-1]],axis=1)))
        report['sides'][side]=checks
    report['socket_rays']=view_rays(preview,cages,metadata)
    failure=[]
    for side,c in report['sides'].items():
        for field in ('boundary_or_nonmanifold_edges','inconsistent_edge_directions','degenerate_triangles','flipped_triangles_vs_basis','front_nonanterior_triangles','rear_nonposterior_triangles','front_uv_orientation_disagreements','degenerate_uv_triangles'):
            if c[field]:failure.append(f'{side}: {field}={c[field]}')
        for key in ('self_intersections','attachment_surface_intersections'):
            if any(c[key].values()):failure.append(f'{side}: {key}')
        if c['signed_volume_m3']<=0:failure.append(f'{side}: nonpositive volume')
    if any(q['backface_first_hits'] for v in report['socket_rays'].values() for q in v.values()):failure.append('socket backface first hits')
    report['failures']=failure;report['G3']='FAIL' if failure else 'PARTIAL_CAGE_CHECKS_PASS_CARD_AND_GLOBAL_QA_PENDING'
    if a.renders:
        for ob in list(bpy.data.objects):
            if ob.type in ('LIGHT','CAMERA') and (ob.name.startswith('M07_KEY') or ob.name.startswith('M07_REVIEW_CAMERA')):
                bpy.data.objects.remove(ob,do_unlink=True)
        cam=stage()
        for name,degrees in VIEWS.items():
            angle=math.radians(degrees);d=Vector((math.sin(angle),math.cos(angle),0));center=Vector((.00026,.06,1.445));cam.location=center+d*.6;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
            path=a.out/f'half_050_{name}.png';bpy.context.scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
            report['renders'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    report['protected_fingerprints_unchanged']=all(fingerprints().get(k)==v for k,v in before.items());report['protected_key_order_unchanged']=[k.name for k in face.data.shape_keys.key_blocks]==key_order;report['protected_face_key_count']=len(key_order)
    assert report['protected_fingerprints_unchanged'] and report['protected_key_order_unchanged']
    assert hashlib.sha256(a.candidate.read_bytes()).hexdigest()==before_file
    report['input_file_unchanged']=True
    # Every unadopted delivery is disabled by default. Keep a reviewable preview
    # object hidden as well; source Face becomes the visible reference again.
    for ob in cages+[preview]:ob.hide_render=True;ob.hide_set(True);ob['enabled_for_production']=False
    face.hide_render=False;face.hide_set(False)
    report['status']='DISABLED_FAILED_CANDIDATE' if failure else 'DISABLED_CANDIDATE_PENDING_REMAINING_QA'
    bpy.ops.wm.save_as_mainfile(filepath=str((a.out/'CONTACT_CAGE_DISABLED_08.blend').resolve()),compress=True,copy=True)
    (a.out/'CONTACT_CAGE_QA_08.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'failures':failure}))

if __name__=='__main__':main()
