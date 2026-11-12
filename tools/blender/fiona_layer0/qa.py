"""Recheck immutable master, registration evidence, annotation and scope guards."""
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
BASE='654b612e8c7a5392f81856e41c7e1b1856d2a817'
SHA='faee95e9e4d9face0219318c7db3ec4847c0186b81dada9bf117d9726e70acb9'
PATH='assets/characters/fiona/layer0/fiona_layer0_fourview_master.png'


def git(*args):
    return subprocess.check_output(['git','-C',str(ROOT),*args])


def main():
    source=ROOT/PATH;data=source.read_bytes()
    assert len(data)==2114467 and hashlib.sha256(data).hexdigest()==SHA
    image=Image.open(source);image.load()
    assert image.format=='PNG' and image.size==(1536,1024) and image.mode=='RGBA'
    adoption=json.loads((ROOT/'docs/art/blender/FIONA_LAYER0_ADOPTION.json').read_text())
    registered=json.loads((ROOT/'docs/art/blender/FIONA_LAYER0_REGISTRATION_QA.json').read_text())
    assert adoption['status']==adoption['directorDecision']=='APPROVED'
    assert adoption['binaryStatus']=='REGISTERED_GITHUB_VERIFIED'
    assert adoption['assetPath']==PATH
    assert adoption['views']==['front','right','left','back']
    assert registered['status']=='PASS' and registered['sha256']==SHA
    assert adoption['registrationCommitSha']==registered['registrationCommitSha']
    assert git('show',registered['registrationCommitSha']+':'+PATH)==data
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blob==registered['gitBlobSha']==adoption['githubVerification']['gitBlobSha']
    for name in ['shared_rig_topology.json','shared_rig_adapter.py']:
        path='tools/blender/'+name
        assert (ROOT/path).read_bytes()==git('show',BASE+':'+path),path
    annotations=json.loads((ROOT/'docs/art/blender/fiona-layer0-anchor-01/anchors.json').read_text())
    assert annotations['sourceSha256']==SHA and annotations['originalImageModified'] is False
    assert len(annotations['views'])==4
    topology=json.loads((ROOT/'tools/blender/shared_rig_topology.json').read_text())
    for view,entry in annotations['views'].items():
        assert set(entry['landmarks'])==set(topology['joints'])
        for side,contact in entry['contacts'].items():
            assert contact['sheetPixels'][1]>=900
        assert entry['adapterPayload']['rigSize']==[1536,1024]
        assert len(entry['common17BoneMap'])==17
        assert {b['id']:b['parent'] for b in entry['common17BoneMap']}=={
            b['id']:b['parent'] for b in annotations['common17BoneContract']['bones']}
        assert all(b['headSheetPixels']!=b['tailSheetPixels'] for b in entry['common17BoneMap'])
    changes=[r.split('\t') for r in git('diff','--name-status',BASE).decode().splitlines()]
    modified={p for status,p in changes if status=='M'}
    assert modified<= {'docs/art/blender/FIONA_LAYER0_ADOPTION.json','tools/blender/test_shared_rig_adapter.py'}
    assert not any(status=='D' for status,p in changes)
    assert not any(status=='M' and p.startswith('assets/') for status,p in changes)
    assert not any(p.startswith(('js/','css/','web/','data/','img/')) for status,p in changes)
    assert not any('morwen' in p.lower() for status,p in changes)
    result=dict(status='PASS',task='FIONA-LAYER0-MASTER-REGISTER-01',sha256=SHA,
                dimensions=[1536,1024],mode='RGBA',sizeBytes=len(data),
                immutableRegistrationCommit=registered['registrationCommitSha'],
                githubReadback='PASS_RECORDED_AT_IMMUTABLE_COMMIT',sourcePngUnmodified=True,
                existingAssetChanges=0,existingAssetDeletions=0,morwenChanges=0,
                commonRigDefinitionAndAdapterUnmodified=True,
                nextStage='4-view annotated candidates; exact silhouette crown/contact measurements; hidden joints inferred')
    (ROOT/'docs/art/blender/fiona-layer0-anchor-01/qa.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
