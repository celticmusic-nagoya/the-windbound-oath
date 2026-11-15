"""Replay QA/render of an already-built failed candidate; no deformation retry."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from build_structural_candidate_07 import set_control
from run_structural_qa_07 import VIEWS,stage,evaluated,numeric,fingerprints
from surface_checks_07 import proper_crossing


def crossings(face,world):
    me=face.data;me.calc_loop_triangles();tags=[x.value for x in me.attributes['elm_patch'].data]
    triangles=[t for t in me.loop_triangles if all(tags[v] in (1,2,11,12) for v in t.vertices)]
    bvh=BVHTree.FromPolygons([Vector(p) for p in world],[t.vertices[:] for t in triangles],all_triangles=True)
    overlap=bvh.overlap(bvh);seen=set();bad=[];contacts=0
    for a,b in overlap:
        if a>=b or (a,b) in seen:continue
        seen.add((a,b));ta,tb=triangles[a],triangles[b]
        if ta.polygon_index==tb.polygon_index or set(ta.vertices)&set(tb.vertices):continue
        if proper_crossing(world[list(ta.vertices)],world[list(tb.vertices)]):bad.append([ta.polygon_index,tb.polygon_index])
        else:contacts+=1
    return {'proper_noncoplanar_triangle_crossings':bad,'unclassified_contacts_or_coplanar_pairs':contacts,
            'coplanar_positive_area_overlap':'NOT_RUN','scope':'lid skin and wall triangles; cards and global head intersections NOT_RUN'}


def socket(face,meta,rest):
    dg=bpy.context.evaluated_depsgraph_get();ev=face.evaluated_get(dg);scene=bpy.context.scene
    skip={i for i,m in enumerate(ev.data.materials) if any(x in m.name for x in ('Eyeline','Eyelash','Brow','EyeExtra'))}
    result={}
    for side,data in meta.items():
        pts=rest[data['upper']+data['lower']];low=pts.min(axis=0);high=pts.max(axis=0)
        result[side]={}
        for view,angle in VIEWS.items():
            d=Vector((math.sin(math.radians(angle)),math.cos(math.radians(angle)),0))
            back=miss=eye=0
            for x in np.linspace(low[0]-0.003,high[0]+0.003,25):
                for z in np.linspace(low[2]-0.003,high[2]+0.003,25):
                    origin=Vector((x,(low[1]+high[1])/2,z))+d*0.3
                    for _ in range(32):
                        hit,loc,norm,index,ob,_=scene.ray_cast(dg,origin,-d)
                        if hit and ob.original==face and index<len(ev.data.polygons) and ev.data.polygons[index].material_index in skip:
                            origin=loc-d*1e-5;continue
                        break
                    if not hit:miss+=1
                    elif ob.original==face and norm.dot(d)<0:back+=1
                    elif ob.name.startswith('MORWEN_Eyes'):eye+=1
            result[side][view]={'backface_first_hits':back,'no_hit_rays':miss,'eye_first_hits':eye,'rays':625}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--qa',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--renders',action='store_true');a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    source_hash=hashlib.sha256(a.model.read_bytes()).hexdigest();report=json.loads(a.qa.read_text())
    bpy.ops.wm.open_mainfile(filepath=str(a.model.resolve()));before=fingerprints()
    face=bpy.data.objects['Face'];mod=face.modifiers['M07_HARMONIC_CANDIDATE'];controls={s.name:s.identifier for s in mod.node_group.interface.items_tree if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name!='Geometry'}
    rest=evaluated(face);cam=stage() if a.renders else None
    report['replay_of_attempt']='M07-HARMONIC-02';report['states']={};report['renders']=[]
    cases=[('neutral',{},(0,0)),('blink',{'target_13':1},(1,1)),('blink_l',{'target_15':1},(0,1)),('blink_r',{'target_14':1},(1,0)),('joy',{'target_3':1},(1,1)),('blink_joy',{'target_13':1,'target_3':1},(1,1)),('half_blink',{'target_13':0.5},(0.5,0.5))]
    for state,keys,closed in cases:
        for k in face.data.shape_keys.key_blocks:
            if k.name!='Basis':k.value=0.5 if k.name=='MORWEN_DESIGN_NoseDepth' else keys.get(k.name,0)
        for name,identifier in controls.items():set_control(mod,identifier,closed[0 if name.startswith('R') else 1])
        w=evaluated(face);q=numeric(face,w,rest,report['anchors']);q['surface_self_intersection']=crossings(face,w);q['socket_backface_rays']=socket(face,report['anchors'],rest);report['states'][state]=q
        if cam:
            for view,angle in VIEWS.items():
                center=Vector((0.00026,0.06,1.445));d=Vector((math.sin(math.radians(angle)),math.cos(math.radians(angle)),0))
                cam.location=center+d*0.6;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
                path=a.out/(state+'_'+view+'.png');bpy.context.scene.render.filepath=str(path.resolve());bpy.ops.render.render(write_still=True)
                report['renders'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        (a.out/'STRUCTURAL_QA_07.json').write_text(json.dumps(report,indent=2)+'\n')
    report['replay_protected_fingerprints_unchanged']=before==fingerprints()
    report['replay_source_unchanged']=hashlib.sha256(a.model.read_bytes()).hexdigest()==source_hash
    report['G3']='FAIL';report['status']='STOPPED_AFTER_TWO_FAILED_ATTEMPTS'
    (a.out/'STRUCTURAL_QA_07.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
