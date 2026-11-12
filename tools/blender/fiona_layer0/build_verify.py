"""Blender execution of the unchanged common landmark adapter, not a final deform rig."""
import hashlib
import json
from pathlib import Path
import sys

import bpy

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'assets/candidates/fiona-layer0-anchor-01'
DATA=ROOT/'docs/art/blender/fiona-layer0-anchor-01/anchors.json'
sys.path.insert(0,str(ROOT/'tools/blender'))
from shared_rig_adapter import build, validate


def check(data,topology):
    objects=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
    assert len(objects)==4
    summary={}
    for view,entry in data['views'].items():
        obj=bpy.data.objects['SHARED_RIG_FIONA_'+view.upper()+'_CANDIDATE']
        assert len(obj.data.bones)==len(topology['joints'])
        max_error=0
        for name,point in entry['adapterPayload']['joints'].items():
            bone=obj.data.bones[name]
            actual=[bone.head_local.x*1536+768,1024-bone.head_local.z*1536]
            max_error=max(max_error,max(abs(a-b) for a,b in zip(actual,point)))
            assert (bone.parent.name if bone.parent else None)==topology['joints'][name]['parent']
        assert max_error<0.001
        summary[view]=dict(jointMarkers=len(obj.data.bones),projectionErrorPx=max_error,
                           parentGraph='PASS',sourceSha256=obj['sourceSha256'])
    packed=[im for im in bpy.data.images if im.packed_file]
    assert len(packed)==1
    assert hashlib.sha256(bytes(packed[0].packed_file.data)).hexdigest()==data['sourceSha256']
    return summary


data=json.loads(DATA.read_text());source=ROOT/data['sourcePath']
assert hashlib.sha256(source.read_bytes()).hexdigest()==data['sourceSha256']
topology_path=ROOT/'tools/blender/shared_rig_topology.json'
assert hashlib.sha256(topology_path.read_bytes()).hexdigest()==data['commonRig']['sha256']
topology=json.loads(topology_path.read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version=0
for view,entry in data['views'].items():
    validate(topology,entry['adapterPayload'])
    bpy.ops.object.select_all(action='DESELECT')
    obj=build(topology,entry['adapterPayload'])
    obj['viewLabel']=view
    obj['screenFacing']=entry['screenFacing']
    obj['landmark_status']='PIXEL_ANNOTATED_CANDIDATE_WITH_OCCLUSION_INFERENCE'
    obj.show_in_front=True
image=bpy.data.images.load(str(source));image.pack()
assert hashlib.sha256(bytes(image.packed_file.data)).hexdigest()==data['sourceSha256']
image.filepath='//../../characters/fiona/layer0/fiona_layer0_fourview_master.png'
reference=bpy.data.objects.new('FIONA_APPROVED_L0_ORIGINAL',None)
bpy.context.collection.objects.link(reference)
reference.empty_display_type='IMAGE';reference.data=image;reference.empty_display_size=1
reference.location=(0,0.05,1024/(2*1536))
import math
reference.rotation_euler=(math.pi/2,0,0)
reference.empty_image_depth='BACK'
reference['sourceStatus']='APPROVED_ORIGINAL_BYTES_UNMODIFIED'
bpy.context.scene['task']='FIONA-BLENDER-ANCHOR-01'
bpy.context.scene['candidateRigNotApproved']=True
check(data,topology)
OUT.mkdir(parents=True,exist_ok=True)
blend=OUT/'fiona_layer0_anchor_candidate.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
summary=check(data,topology)
report=dict(status='PASS',blenderVersion=bpy.app.version_string,facings=summary,
            savedSceneReload='PASS',packedMasterSha256=data['sourceSha256'],
            originalPngModified=False,sharedRigSettingsModified=False,
            markerRigOnly=True,productionDeformationRig='NOT_RUN_NOT_PART_OF_ANCHOR_REGISTRATION',
            anatomicalIndependentQA='NOT_RUN',pngProcessing='NONE',
            blendSha256=hashlib.sha256(blend.read_bytes()).hexdigest())
(ROOT/'docs/art/blender/fiona-layer0-anchor-01/blender_qa.json').write_text(json.dumps(report,indent=2)+'\n')
print('FIONA_BLENDER_ANCHOR_PASS')
