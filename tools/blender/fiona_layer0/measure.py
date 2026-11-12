"""Read the approved original only; save annotations/measurements as JSON, never PNG."""
import hashlib
import json
from pathlib import Path
import statistics
import sys

from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OUT=ROOT/'docs/art/blender/fiona-layer0-anchor-01'
SHA='faee95e9e4d9face0219318c7db3ec4847c0186b81dada9bf117d9726e70acb9'
MASTER='assets/characters/fiona/layer0/fiona_layer0_fourview_master.png'
REGIONS={'front':[0,448], 'right':[448,752], 'left':[752,1072], 'back':[1072,1536]}
FACING={'front':'toward_camera','right':'left','left':'right','back':'away_camera'}
NEAR={'front':None,'right':'L','left':'R','back':None}


def main():
    adoption=json.loads((ROOT/'docs/art/blender/FIONA_LAYER0_ADOPTION.json').read_text())
    registration=json.loads((ROOT/'docs/art/blender/FIONA_LAYER0_REGISTRATION_QA.json').read_text())
    assert adoption['binaryStatus']=='REGISTERED_GITHUB_VERIFIED'
    assert registration['status']=='PASS' and registration['sha256']==SHA
    path=ROOT/MASTER
    assert hashlib.sha256(path.read_bytes()).hexdigest()==SHA
    image=Image.open(path);image.load()
    assert image.size==(1536,1024) and image.mode=='RGBA' and image.format=='PNG'
    alpha=image.getchannel('A')
    annotations=json.loads((HERE/'PIXEL_ANNOTATIONS.json').read_text())
    assert annotations['sourceSha256']==SHA
    topology_path=ROOT/'tools/blender/shared_rig_topology.json'
    topology=json.loads(topology_path.read_text())
    compat=json.loads((HERE/'COMMON_17BONE_COMPATIBILITY.json').read_text())
    assert len(compat['bones'])==17
    sys.path.insert(0,str(HERE.parent))
    from shared_rig_adapter import validate
    result=dict(schema='fiona/layer0-anchor-candidate/01',task='FIONA-BLENDER-ANCHOR-01',
                status='PIXEL_ANNOTATED_CANDIDATE_NOT_VISUAL_APPROVAL',sourcePath=MASTER,
                sourceSha256=SHA,sourceSize=[1536,1024],sourceMode='RGBA',
                coordinateSystem='original_sheet_pixels_xy_top_left_y_down',
                originalImageModified=False,sourceCroppedOrResampled=False,
                sourceRegistrationCommit=registration['registrationCommitSha'],
                commonRig=dict(path='tools/blender/shared_rig_topology.json',schema=topology['schema'],
                               sha256=hashlib.sha256(topology_path.read_bytes()).hexdigest(),
                               jointCount=len(topology['joints']),settingsModified=False),
                common17BoneContract=compat,
                viewOrder=['front','right','left','back'],
                sideConvention='Director view labels retained. Anatomical L/R follows screen-facing, not label text. No image mirroring.',
                views={})
    for view,(lo,hi) in REGIONS.items():
        # Read source pixels directly: variable-width analysis regions are not
        # image crops, and do not clip the front figure at a 384px quarter cut.
        pixels=[(x,y) for y in range(1024) for x in range(lo,hi) if alpha.getpixel((x,y))>=128]
        xmin=min(x for x,y in pixels);xmax=max(x for x,y in pixels)
        ymin=min(y for x,y in pixels);ymax=max(y for x,y in pixels)
        points=dict(annotations['views'][view])
        points['headTop']=[statistics.median(x for x,y in pixels if y==ymin),ymin]
        assert set(points)==set(topology['joints'])
        observations={}
        for name,point in points.items():
            hidden=(NEAR[view] and name.endswith('R' if NEAR[view]=='L' else 'L'))
            if view=='back' and name in {'chin','jawL','jawR','neckTop','neckBase'}:
                hidden=True
            if view=='back' and name.startswith(('toe','ball')):
                hidden=True
            observations[name]=dict(sheetPixels=point,normalizedSheet=[point[0]/1536,point[1]/1024],
                visibility='OCCLUDED_INFERRED' if hidden else 'VISIBLE_PIXEL_ANNOTATION',
                method='alpha>=128 hair silhouette top' if name=='headTop' else 'manual pixel annotation candidate',
                uncertaintyPx=30 if hidden else 12,
                anatomicalAccuracy='NOT_INDEPENDENTLY_VALIDATED')
            assert lo<=point[0]<hi and 0<=point[1]<1024
        observations['headTop']['visibility']='MEASURED_SOURCE_FEATURE'
        observations['headTop']['uncertaintyPx']=None
        contacts={}
        for side in ['L','R']:
            candidates=[(x,y) for x,y in pixels if y>=900]
            inferred=bool(NEAR[view] and side!=NEAR[view])
            if NEAR[view] is None:
                left_half=(side=='R') if view=='front' else (side=='L')
                center=points['pelvis'][0]
                candidates=[(x,y) for x,y in candidates if (x<center)==left_half]
            bottom=max(y for x,y in candidates)
            contact=[statistics.median(x for x,y in candidates if y==bottom),bottom]
            contacts[side]=dict(sheetPixels=contact,
                status='OCCLUDED_INFERRED_FROM_VISIBLE_PROFILE_CONTACT' if inferred else 'MEASURED_ALPHA_SILHOUETTE_CONTACT',
                alphaThreshold=128,notPhysicalForcePlateMeasurement=True)
        payload=dict(schema='cas/blender-measured/01',characterId='fiona_'+view,
                     sourceSha256=SHA,rigSize=[1536,1024],joints=points,
                     annotationStatus='CANDIDATE_SOURCE_PIXEL_ANNOTATIONS_WITH_EXPLICIT_HIDDEN_INFERENCE')
        # Legacy schema name is an adapter interface, not an assertion that
        # occluded anatomical joint centres have been physically measured.
        validate(topology,payload)
        endpoints={'pelvis':('pelvis','waist'),'spine':('waist','neckBase'),
                   'neck':('neckBase','neckTop'),'head':('neckTop','headTop')}
        for side in ['L','R']:
            for bone,a,b in [('upper_arm','shoulder','elbow'),('forearm','elbow','wrist'),
                             ('hand','wrist','hand'),('thigh','hip','knee'),
                             ('shin','knee','ankle'),('foot','ankle','toe')]:
                endpoints[bone+'.'+side]=(a+side,b+side)
        bone_map=[]
        for bone in compat['bones']:
            if bone['id']=='root':
                start=[points['pelvis'][0],ymax];end=[points['pelvis'][0],ymax-30]
            else:
                a,b=endpoints[bone['id']];start,end=points[a],points[b]
            assert start!=end
            bone_map.append(dict(id=bone['id'],parent=bone['parent'],headSheetPixels=start,
                                 tailSheetPixels=end,status='FIONA_ANNOTATION_DERIVED_CANDIDATE'))
        result['views'][view]=dict(label=view,screenFacing=FACING[view],nearAnatomicalSide=NEAR[view],
            analysisRegion=[lo,0,hi,1024],alphaBBox=[xmin,ymin,xmax+1,ymax+1],
            landmarks=observations,contacts=contacts,adapterPayload=payload,common17BoneMap=bone_map)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'anchors.json').write_text(json.dumps(result,indent=2)+'\n')
    print('FIONA_ANCHOR_JSON_PASS',len(result['views']),len(topology['joints']))


if __name__=='__main__':
    main()
