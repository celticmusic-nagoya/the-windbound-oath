"""Actual saved-model candidate QA + five-view renders. Failures remain failures."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from build_structural_candidate_07 import install,set_control

HERE=Path(__file__).resolve().parent
VIEWS={'front':0,'q3L':-45,'q3R':45,'left':-90,'right':90}


def fingerprints():
    result={}
    for ob in bpy.data.objects:
        if ob.type!='MESH':continue
        result[ob.name]={'vertex_count':len(ob.data.vertices),'shape_keys':{}}
        if ob.data.shape_keys:
            for k in ob.data.shape_keys.key_blocks:
                h=hashlib.sha256()
                for v in k.data:h.update(struct.pack('<3d',*v.co))
                result[ob.name]['shape_keys'][k.name]=h.hexdigest()
    return result


def evaluated(face):
    face.update_tag();bpy.context.view_layer.update()
    ev=face.evaluated_get(bpy.context.evaluated_depsgraph_get())
    return np.array([tuple(ev.matrix_world@v.co) for v in ev.data.vertices])


def normal(points):
    n=np.sum(np.cross(points,np.roll(points,-1,axis=0)),axis=0)
    return n/max(np.linalg.norm(n),1e-15)


def numeric(face,world,rest,meta):
    me=face.data; tags=[a.value for a in me.attributes['elm_patch'].data]
    selected=[p for p in me.polygons if all(tags[v] in (1,2,11,12) for v in p.vertices)]
    flips=[];zero=[]
    for p in selected:
        points=world[list(p.vertices)];nr=normal(points);nb=normal(rest[list(p.vertices)])
        if np.linalg.norm(np.sum(np.cross(points,np.roll(points,-1,axis=0)),axis=0))<1e-12:zero.append(p.index)
        if nr@nb<0:flips.append(p.index)
    skin=[p.vertices[:] for p in me.polygons if 'SKIN' in me.materials[p.material_index].name]
    bvh=BVHTree.FromPolygons([Vector(p) for p in world],skin)
    eye=bpy.data.objects['MORWEN_Eyes'];eye.data.calc_loop_triangles()
    # Fixed deterministic surface samples include vertices and triangle centroids.
    eyepts=[eye.matrix_world@v.co for v in eye.data.vertices]
    eyepts += [sum((eye.matrix_world@eye.data.vertices[v].co for v in t.vertices),Vector())/3 for t in eye.data.loop_triangles]
    visible={}
    for name,angle in VIEWS.items():
        d=Vector((math.sin(math.radians(angle)),math.cos(math.radians(angle)),0))
        count={'R':0,'L':0}
        for p in eyepts:
            hit=bvh.ray_cast(p+d*1e-5,d)[0]
            if hit is None:count['R' if p.x>0.00026 else 'L']+=1
        visible[name]=count
    return {'patch_flipped_faces':flips,'patch_degenerate_faces':zero,
            'eye_samples_per_view':len(eyepts),'visible_eye_surface_samples':visible,
            'surface_self_intersection':'NOT_RUN','socket_backface_rays':'NOT_RUN',
            'canthus_max_displacement_m':{s:max(float(np.linalg.norm(world[v]-rest[v])) for v in m['anchors_source_confirmed_not_art_approved']) for s,m in meta.items()}}


def stage():
    scene=bpy.context.scene
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=384;scene.render.resolution_y=384;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('M07_REVIEW_WORLD');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(0.72,0.75,0.8,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0.7
    light=bpy.data.lights.new('M07_KEY','AREA');light.energy=50;light.shape='DISK';light.size=0.6
    ob=bpy.data.objects.new('M07_KEY',light);scene.collection.objects.link(ob);ob.location=(0.3,0.5,1.8)
    ob.rotation_euler=(Vector((0,0,1.45))-ob.location).to_track_quat('-Z','Y').to_euler()
    cam=bpy.data.objects.new('M07_REVIEW_CAMERA',bpy.data.cameras.new('M07_REVIEW_CAMERA'))
    scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=0.20
    return cam


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=Path,required=True);parser.add_argument('--evidence',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);parser.add_argument('--renders',action='store_true');parser.add_argument('--attempt',default='M07-HARMONIC-02')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    original_hash=hashlib.sha256(args.model.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(args.model.resolve()))
    before=fingerprints(); expected=json.loads((args.evidence/'SHAPE_KEY_FINGERPRINTS_07.json').read_text())
    if before!=expected['objects']:raise ValueError('Baseline differs from latest 58-key fingerprints')
    face=bpy.data.objects['Face'];key_order=[k.name for k in face.data.shape_keys.key_blocks]
    uv_before=[tuple(x.uv) for x in face.data.uv_layers.active.data]
    rest=evaluated(face)
    topology=json.loads((args.evidence/'EYELID_07_TOPOLOGY_MAP.json').read_text())
    baseline=json.loads((args.evidence/'EYELID_05_REPORT.json').read_text())
    modifier,controls,meta=install(face,topology,baseline)
    report={'method_family':'DIRICHLET_HARMONIC_INDEPENDENT_LID_FIELDS','attempt':args.attempt,
            'status':'QA_IN_PROGRESS_NOT_ADOPTED','source_blend_sha256':original_hash,
            'latest_diagnostic_blend_sha256':expected['input_blend_sha256'],'blender':bpy.app.version_string,
            'key_count':len(key_order),'key_order':key_order,'anchors':meta,'states':{},'renders':[],
            'G1':'PARTIAL_FULL_CANON_BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'}
    cam=stage() if args.renders else None
    cases=[('neutral',{},(0,0)),('blink',{'target_13':1},(1,1)),('blink_l',{'target_15':1},(0,1)),('blink_r',{'target_14':1},(1,0)),('joy',{'target_3':1},(1,1)),('blink_joy',{'target_13':1,'target_3':1},(1,1)),('half_blink',{'target_13':0.5},(0.5,0.5))]
    for state,keys,closure in cases:
        for k in face.data.shape_keys.key_blocks:
            if k.name!='Basis':k.value=0.5 if k.name=='MORWEN_DESIGN_NoseDepth' else keys.get(k.name,0)
        for name,identifier in controls.items():set_control(modifier,identifier,closure[0 if name.startswith('R') else 1])
        world=evaluated(face);report['states'][state]=numeric(face,world,rest,meta)
        if cam:
            for view,angle in VIEWS.items():
                center=Vector((0.00026,0.06,1.445))
                d=Vector((math.sin(math.radians(angle)),math.cos(math.radians(angle)),0))
                cam.location=center+d*0.6;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
                path=args.out/(state+'_'+view+'.png');bpy.context.scene.render.filepath=str(path.resolve())
                bpy.ops.render.render(write_still=True)
                report['renders'].append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        (args.out/'STRUCTURAL_QA_07.json').write_text(json.dumps(report,indent=2)+'\n')
    # All 56 isolated keys, controls disabled: modifier must be identity.
    max_error=0
    for key in [f'target_{i}' for i in range(56)]:
        for k in face.data.shape_keys.key_blocks:
            if k.name!='Basis':k.value=0.5 if k.name=='MORWEN_DESIGN_NoseDepth' else float(k.name==key)
        for identifier in controls.values():set_control(modifier,identifier,0)
        a=evaluated(face);modifier.show_viewport=False;b=evaluated(face);modifier.show_viewport=True
        max_error=max(max_error,float(np.max(np.abs(a-b))))
    report['inactive_modifier_max_error_all_56_keys_m']=max_error
    report['protected_key_fingerprints_unchanged']=fingerprints()==before
    report['protected_key_order_unchanged']=[k.name for k in face.data.shape_keys.key_blocks]==key_order
    report['uv_coordinates_unchanged']=[tuple(x.uv) for x in face.data.uv_layers.active.data]==uv_before
    report['input_file_unchanged']=hashlib.sha256(args.model.read_bytes()).hexdigest()==original_hash
    report['G3']='FAIL' # Unrun collision/socket tests can never yield a full PASS.
    report['status']='DIAGNOSTIC_CANDIDATE_NOT_ADOPTED'
    # Deliberately save a disabled candidate modifier for further inspection only.
    for k in face.data.shape_keys.key_blocks:
        if k.name!='Basis':k.value=0.5 if k.name=='MORWEN_DESIGN_NoseDepth' else 0
    for identifier in controls.values():set_control(modifier,identifier,0)
    bpy.ops.wm.save_as_mainfile(filepath=str((args.out/'CANDIDATE_DISABLED_07.blend').resolve()),compress=True,copy=True)
    (args.out/'STRUCTURAL_QA_07.json').write_text(json.dumps(report,indent=2)+'\n')

if __name__=='__main__':main()
