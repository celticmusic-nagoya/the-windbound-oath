"""Prepare a separate multi-state sculpt document; never edits original 58 keys.

This is the next method's authoring setup, not an executed deformation trial.
Artist supplies independent contact-compatible lids at 25/50/75/100 percent.
No generated closure target or production binding is assumed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import bpy
import numpy as np
from run_structural_qa_07 import fingerprints


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists() or a.out.resolve()==a.baseline.resolve():raise ValueError('New candidate path required')
    digest=hashlib.sha256(a.baseline.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()))
    before=fingerprints();source=bpy.data.objects['Face'];source.hide_set(True)
    keys=source.data.shape_keys.key_blocks
    neutral=np.array([v.co[:] for v in keys[0].data])
    for key in keys[1:]:
        neutral+=key.value*(np.array([v.co[:] for v in key.data])-np.array([v.co[:] for v in key.relative_key.data]))
    templates=[]
    for percent in (25,50,75,100):
        ob=source.copy();ob.data=source.data.copy();ob.name=f'M07_SCULPT_{percent:03d}_UNAUTHORED'
        bpy.context.scene.collection.objects.link(ob);ob.shape_key_clear()
        ob.data.vertices.foreach_set('co',neutral.ravel())
        ob['authoring_status']='UNAUTHORED_NOT_A_CLOSED_TARGET';ob['source_blend_sha256']=digest
        ob['closure_percent']=percent;ob['method_family']='ARTIST_MULTI_STATE_CONTACT_CAGE'
        tags=[x.value for x in ob.data.attributes['elm_patch'].data]
        for side,pid in (('R',1),('L',2)):
            for name,ids in (('LID_SKIN',[i for i,t in enumerate(tags) if t==pid]),('LID_WALL',[i for i,t in enumerate(tags) if t==pid+10])):
                group=ob.vertex_groups.new(name=f'M07_{side}_{name}');group.add(ids,1,'REPLACE')
        ob.hide_render=True;ob.hide_set(percent!=50);templates.append(ob.name)
    after=fingerprints()
    if any(after.get(n)!=record for n,record in before.items()):raise ValueError('Protected source changed')
    a.out.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(a.out.resolve()),compress=True,copy=True)
    if hashlib.sha256(a.baseline.read_bytes()).hexdigest()!=digest:raise ValueError('Input changed')
    a.out.with_suffix('.json').write_text(json.dumps({'status':'UNAUTHORED_SCULPT_SETUP_NOT_QA_PASS','method_family':'ARTIST_MULTI_STATE_CONTACT_CAGE','source_blend_sha256':digest,'protected_source_keys_unchanged':True,'templates':templates,'G1':'PARTIAL','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN'},indent=2)+'\n')

if __name__=='__main__':main()
