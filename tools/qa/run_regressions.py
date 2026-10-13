#!/usr/bin/env python3
"""Run every standalone regression sequentially, detecting printed failures even at exit 0."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import signal
import socket
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.request
from urllib.parse import urlsplit, urlunsplit

ROOT=Path(__file__).resolve().parents[2]
KNOWN={'tests/moss/m13_elder_attack_text.py':r'peaceful elder cycles to the morning line',
       'tests/moss/m4_e2e.py':r'Fiona stage-9 line \(elder/Emma warning wording\)'}


def classification(path, code, output):
    fails=re.findall(r'^FAIL .*$',output,re.MULTILINE)
    counts=[int(n) for n in re.findall(r'^FAILS\s+(\d+)(?=\s|$)',output,re.MULTILINE)]
    bad=code!=0 or bool(fails) or any(counts)
    if not bad:return '合格',fails,counts
    infrastructure=code in (124,125,126,127) or 'Traceback (most recent call last)' in output or 'PAGEERR' in output or bool(re.search(r'(?:errors|errs|CONSOLE)\s+\[(?!\s*\])',output))
    known=KNOWN.get(path)
    if known and fails and all(re.search(known,line)for line in fails) and not infrastructure and (not counts or max(counts)==len(fails)):
        return 'main既存',fails,counts
    return '新規',fails,counts


def child(root, path, port, extra):
    from playwright.sync_api import BrowserType,Page
    launch=BrowserType.launch;goto=Page.goto
    def browser_launch(self,*a,**kw):
        if self.name=='chromium' and os.environ.get('PW_CHROMIUM_EXECUTABLE'):kw.setdefault('executable_path',os.environ['PW_CHROMIUM_EXECUTABLE'])
        return launch(self,*a,**kw)
    def page_goto(self,url,*a,**kw):
        parts=urlsplit(url)
        if parts.hostname in ('localhost','127.0.0.1') and parts.port==8765:
            url=urlunsplit((parts.scheme,'127.0.0.1:'+str(port),parts.path,parts.query,parts.fragment))
        return goto(self,url,*a,**kw)
    BrowserType.launch=browser_launch;Page.goto=page_goto
    os.chdir(root);sys.argv=[str(root/path)]+extra;sys.path.insert(0,str((root/path).parent))
    runpy.run_path(str(root/path),run_name='__main__')


def stop(proc):
    if proc and proc.poll() is None:
        os.killpg(proc.pid,signal.SIGTERM)
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()


def report(out,meta,rows):
    (out/'results.json').write_text(json.dumps({**meta,'results':rows},ensure_ascii=False,indent=2)+'\n')
    text='# 全回帰結果（O）\n\n'+f"source HEAD `{meta['source_head']}` / main基準 `{meta['main_base']}`、port {meta['port']}、直列、各test自前server、timeout {meta['timeout']}秒。\n\n"
    text+='合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。\n\n| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |\n|---|---|---|---|---|---|\n'
    for r in rows:text+=f"| {r['test']} | {r['classification']} | {r.get('exit_code','—')} | {r.get('seconds','—')} | {len(r.get('failure_lines',[]))} / {r.get('reported_fails',[])} | {r.get('log','—')} |\n"
    counts={k:sum(r['classification']==k for r in rows)for k in ('合格','main既存','新規','未実施')}
    text+='\n集計: '+', '.join(f'{k} {v}'for k,v in counts.items())+'。\n'
    text+='\n原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。\n'
    (out/'results.md').write_text(text)
    with (out/'results.tsv').open('w')as f:
        f.write('test\tclassification\texit_code\tseconds\n')
        for r in rows:f.write(f"{r['test']}\t{r['classification']}\t{r.get('exit_code','')}\t{r.get('seconds','')}\n")


def self_test():
    assert classification('tests/x.py',0,'FAIL wrong\nFAILS 1\n')[0]=='新規'
    assert classification('tests/x.py',0,'FAILS 0\nok\n')[0]=='合格'
    assert classification('tests/x.py',0,'FAILS 2 hidden context\n')[0]=='新規'
    assert classification('tests/moss/m4_e2e.py',0,'FAIL Fiona stage-9 line (elder/Emma warning wording)\nFAILS 1\n')[0]=='main既存'
    assert classification('tests/moss/m4_e2e.py',124,'FAIL Fiona stage-9 line (elder/Emma warning wording)\n')[0]=='新規'
    assert classification('tests/moss/m13_elder_attack_text.py',0,'FAIL unrelated\n')[0]=='新規'
    print('PASS printed failure / exit / strict known-failure / timeout classification checks')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tests',nargs='*')
    parser.add_argument('--port',type=int,default=8783)
    parser.add_argument('--timeout',type=int,default=int(os.environ.get('TEST_TIMEOUT_SECONDS','900')))
    parser.add_argument('--out',type=Path,default=ROOT/'docs/qa/regression-20261013')
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--child');parser.add_argument('--root',type=Path);parser.add_argument('--extra-json',default='[]')
    args=parser.parse_args()
    if args.self_test:self_test();return
    if args.child:child(args.root,args.child,args.port,json.loads(args.extra_json));return
    # Snapshot contract: never silently test an older HEAD while application work is uncommitted.
    dirty=subprocess.run(['git','diff','--quiet','HEAD','--'],cwd=ROOT).returncode
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    if dirty or any(p and not p.startswith('docs/') for p in untracked):
        raise SystemExit('Commit tracked work and non-doc new files to a WIP commit before snapshot testing (no push required).')
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    base=subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
    metadata={'source_head':head,'main_base':base,'port':args.port,'timeout':args.timeout,'known_failures':KNOWN,'snapshot_mode':'git archive committed HEAD'}
    with tempfile.TemporaryDirectory(prefix='codex-regression-') as temporary:
        snapshot=Path(temporary)/'repo';snapshot.mkdir()
        archive=Path(temporary)/'source.tar'
        subprocess.run(['git','archive','--format=tar','--output',str(archive),head],cwd=ROOT,check=True)
        with tarfile.open(archive)as tar:tar.extractall(snapshot,filter='data')
        paths=args.tests or sorted(str(p.relative_to(snapshot))for p in (snapshot/'tests').rglob('*')if p.suffix=='.py' or p.name.endswith('.test.js'))
        paths=[p for p in paths if p!='tests/run_python.py' and '__pycache__'not in p]
        if not paths:raise SystemExit('No tests discovered')
        rows=[{'test':path,'classification':'未実施'}for path in paths];report(out,metadata,rows)
        Path('/tmp/claude-0').mkdir(exist_ok=True)
        for i,path in enumerate(paths):
            if not (snapshot/path).is_file():raise SystemExit('Unknown test '+path)
            logpath=out/(path.replace('/','_')+'.log');serverlog=out/(path.replace('/','_')+'.server.log')
            artifacts=out/'artifacts'/Path(path).stem;artifacts.mkdir(parents=True,exist_ok=True)
            extra=[]
            if path=='tests/moss/walk_map.py':extra=['moss_forest_02_mossy_ravine.json']
            if path=='tests/moss/m19_plan_bench.py':extra=['--out',str(artifacts)]
            env=dict(os.environ,PORT=str(args.port),OUT=str(artifacts/'perf.json')if path=='tests/moss/m19_perf.py'else str(artifacts))
            before=hashlib.sha256((snapshot/path).read_bytes()).hexdigest()
            started=time.monotonic();server=None;process=None;code=125
            print(f'[{i+1}/{len(paths)}] RUN {path}',flush=True)
            with logpath.open('w')as log,serverlog.open('w')as slog:
                try:
                    with socket.socket()as sock:
                        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('127.0.0.1',args.port))
                    server=subprocess.Popen([sys.executable,'-m','http.server',str(args.port),'--bind','127.0.0.1'],cwd=snapshot,stdout=slog,stderr=slog,start_new_session=True)
                    ready=False
                    for _ in range(50):
                        if server.poll()is not None:break
                        try:
                            urllib.request.urlopen(f'http://127.0.0.1:{args.port}/index.html',timeout=.5).close();ready=True;break
                        except OSError:time.sleep(.1)
                    if not ready:raise RuntimeError('Owned server failed readiness')
                    command=['node',path]if path.endswith('.test.js')else[sys.executable,'-u',str(Path(__file__).resolve()),'--child',path,'--root',str(snapshot),'--port',str(args.port),'--extra-json',json.dumps(extra)]
                    process=subprocess.Popen(command,cwd=snapshot,env=env,stdout=log,stderr=log,start_new_session=True)
                    try:code=process.wait(timeout=args.timeout)
                    except subprocess.TimeoutExpired:stop(process);code=124;log.write('\nTIMEOUT: test exceeded configured limit\n')
                    if server.poll()is not None:code=125;log.write('\nOwned server died during test\n')
                except Exception as exc:code=125;log.write(str(exc)+'\n')
                finally:stop(process);stop(server)
            output=logpath.read_text();category,failures,counts=classification(path,code,output)
            after=hashlib.sha256((snapshot/path).read_bytes()).hexdigest()
            if after!=before:category='新規';failures.append('FAIL test source mutated')
            rows[i]={'test':path,'classification':category,'exit_code':code,'seconds':round(time.monotonic()-started,3),'failure_lines':failures,'reported_fails':counts,
                     'log':logpath.name,'test_sha256_before':before,'test_sha256_after':after,'server_stopped':server is None or server.poll()is not None}
            report(out,metadata,rows)
            print(f"{category} {path} exit={code} seconds={rows[i]['seconds']}",flush=True)
            for f in failures:print(f,flush=True)
        print('Finished: '+str({k:sum(r['classification']==k for r in rows)for k in ('合格','main既存','新規','未実施')}),flush=True)
        sys.exit(1 if any(r['classification']!='合格'for r in rows)else 0)

if __name__=='__main__':main()
