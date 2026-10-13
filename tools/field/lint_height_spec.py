#!/usr/bin/env python3
"""Lint an opt-in overlay with the production FieldCollision/FieldHeight modules."""
import argparse,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('map_id');p.add_argument('--out',type=Path);a=p.parse_args()
 if Path(a.map_id).name!=a.map_id: p.error('map_id must be a filename stem')
 r=subprocess.run(['node',str(Path(__file__).with_name('height_spec_engine.js')),str(ROOT),a.map_id],capture_output=True,text=True,timeout=180)
 if r.returncode: raise SystemExit(r.stderr)
 result=json.loads(r.stdout);result['source_commit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
 if a.out:a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 for c in result['checks']:print(('ok   ' if c['ok'] else 'FAIL ')+c['label'])
 for w in result['warnings']:print('WARN '+json.dumps(w,ensure_ascii=False))
 bad=sum(not c['ok'] for c in result['checks']);print('FAILS',bad);raise SystemExit(1 if bad else 0)
if __name__=='__main__':main()
