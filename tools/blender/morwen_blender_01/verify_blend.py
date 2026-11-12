"""Independent .blend reload, packed-reference, hierarchy and deformation QA."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy

ROOT=Path(__file__).resolve().parents[3]


def verify(output):
    data=json.loads((output/'anchors_candidate.json').read_text())
    contract=json.loads((ROOT/'tools/blender/rigs/humanoid_v1.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(output/'morwen_base_rig_candidate.blend'))
    scene=bpy.context.scene
    assert scene['approval_status']=='FUTURE_CANON_PENDING_APPROVAL'
    arms=[o for o in scene.objects if o.type=='ARMATURE']
    assert len(arms)==4
    assert len([o for o in scene.objects if o.type=='CAMERA'])==5
    packed=[im for im in bpy.data.images if im.packed_file]
    assert len(packed)==4
    assert {hashlib.sha256(bytes(im.packed_file.data)).hexdigest() for im in packed}=={
        entry['source_sha256'] for entry in data['facings'].values()}
    checks={}
    for rig in arms:
        facing=rig['facing']
        assert len(rig.data.bones)==17
        for entry in contract['bones']:
            b=rig.data.bones[entry['id']]
            assert (b.parent.name if b.parent else None)==entry['parent']
            assert b.length>1e-6
            assert all(math.isfinite(v) for v in (*b.head_local,*b.tail_local))
        near=data['facings'][facing]['near_side']
        if near:
            far='R' if near=='L' else 'L'
            assert rig.data.bones['upper_arm.'+near].head_local.y<rig.data.bones['upper_arm.'+far].head_local.y
        body=bpy.data.objects['Morwen_'+facing+'_neutral_proxy']
        assert body.modifiers[0].object==rig
        assert len(body.vertex_groups)==17
        assert all(len(v.groups)==1 and abs(v.groups[0].weight-1)<1e-6 for v in body.data.vertices)
        assert all(p.area>1e-12 for p in body.data.polygons)
        deps=bpy.context.evaluated_depsgraph_get()
        def positions():
            evaluated=body.evaluated_get(deps)
            mesh=evaluated.to_mesh()
            points=[v.co.copy() for v in mesh.vertices]
            evaluated.to_mesh_clear()
            return points
        before=positions()
        pose=rig.pose.bones['forearm.L']
        pose.rotation_mode='XYZ'
        pose.rotation_euler.z=0.18
        bpy.context.view_layer.update()
        after=positions()
        moved=sum((a-b).length>1e-7 for a,b in zip(before,after))
        assert moved>0, 'Proxy must actually deform'
        pose.rotation_euler.z=0
        bpy.context.view_layer.update()
        assert max((a-b).length for a,b in zip(before,positions()))<1e-6
        checks[facing]=dict(bones=17,parent_links=16,weighted_vertices=len(body.data.vertices),
                            forearm_pose_moved_vertices=moved,pose_restoration='PASS',
                            finite_geometry=True,nonzero_area_faces=True,packed_reference_sha='PASS')
    report=dict(status='PASS',blender_version=bpy.app.version_string,
                loaded_from_saved_blend=True,facings=checks,visual_approval=False,
                note='Technical self-QA; does not measure hidden anatomy or approve art.')
    (output/'reload_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    files=['morwen_base_rig_candidate.blend','anchors_candidate.json','source_qa.json',
           'blender_qa.json','reload_qa.json','neutral_proxy_4views.png']
    files += [facing+'_overlay.png' for facing in ('front','right','back','left')]
    artifact_manifest=dict(status='CANDIDATE_NOT_APPROVED',blender_version=bpy.app.version_string,
                           files=[dict(name=name,bytes=(output/name).stat().st_size,
                                       sha256=hashlib.sha256((output/name).read_bytes()).hexdigest()) for name in files])
    (output/'OUTPUT_MANIFEST.json').write_text(json.dumps(artifact_manifest,indent=2)+'\n')
    print('MORWEN_BLENDER_01_RELOAD_PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--output',type=Path,default=ROOT/'assets/candidates/morwen-blender-01')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    verify(args.output.resolve())
