"""CLI adapter for candidate artifact manifests. No automatic render skipping."""
import argparse
import json
import os
from pathlib import Path
from two_task_manifest import build
from two_task_artifact import verify
from two_task_key import task_key

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['manifest','verify'])
    parser.add_argument('--root',required=True,type=Path)
    parser.add_argument('--spec',required=True,type=Path)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--output',action='append',default=[])
    parser.add_argument('--qa',type=Path)
    args=parser.parse_args(argv)
    spec=json.loads(args.spec.read_text())
    if args.mode=='manifest':
        if args.qa is None:
            parser.error('technical QA JSON required')
        qa=json.loads(args.qa.read_text())
        if qa.get('technical_status')!='PASS' or qa.get('task_key')!=task_key(spec):
            parser.error('technical QA does not match task')
        m=build(args.root,spec,args.output,os.environ['GITHUB_SHA'],int(os.environ['GITHUB_RUN_ID']),qa['technical_status'])
        with args.manifest.open('x',encoding='utf-8') as f:
            json.dump(m,f,indent=2)
    else:
        verify(args.root,json.loads(args.manifest.read_text()),task_key(spec))
    print('Candidate artifact manifest '+args.mode+' PASS')

if __name__=='__main__':
    main()
