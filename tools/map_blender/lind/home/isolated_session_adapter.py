"""Qualification adapter only: isolated bare remote, real bedding native file."""
import os,sys,json,time,subprocess,tempfile
from pathlib import Path
from shared_session_controller import run
from shared_session_contract import fingerprint,verified_file_hashes
from shared_asset_lease import assert_owned
from bounded_operation import run_operation
from session_plan import sha

def main():
    root=Path(sys.argv[1]).resolve()
    source=Path(sys.argv[2]).resolve()
    blender=Path(sys.argv[3]).resolve()
    manifest=Path(sys.argv[4]).resolve()
    root.mkdir(parents=True,exist_ok=True)
    spec=json.loads(manifest.read_text())
    hashes={k:verified_file_hashes(Path(v['root']),v['files']) if v['files'] else {} for k,v in spec.items()}
    assert hashes['inputs'] and str(source.name) in hashes['inputs']
    assert hashes['inputs'][source.name]==sha(source)
    asset='LIND-HOME'
    with tempfile.TemporaryDirectory() as d:
        remote=str(Path(d)/'isolated.git')
        subprocess.run(['git','init','--bare',remote],check=True)
        production_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        tree=subprocess.check_output(['git','mktree'],input='',text=True).strip()
        commit=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@invalid','commit-tree',tree,'-m','Isolated pilot for '+production_head],text=True).strip()
        subprocess.run(['git','push',remote,commit+':refs/heads/pilot'],check=True)
        records={}
        stages=[]
        for k,deps in [('native_reopen',[]),('native_save',['native_reopen'])]:
            stages.append(dict(id=k,deps=deps,seconds=180,qualified=True,fingerprint=fingerprint(asset,k,hashes)))
        def execute(stage,token,deadline):
            assert_owned(remote,asset,token)
            k=stage['id']; target=root/(k+'.blend')
            src=source if not stage['deps'] else root/'native_reopen.blend'
            expr="import bpy; assert 'BED_DRAPE_CANDIDATE' in bpy.data.objects; bpy.ops.wm.save_as_mainfile(filepath="+repr(str(target))+"); bpy.ops.wm.open_mainfile(filepath="+repr(str(target))+"); assert len(bpy.data.objects['BED_DRAPE_CANDIDATE'].data.vertices)==2665"
            run_operation([str(blender),'-b','--disable-autoexec',str(src),'--python-exit-code','1','--python-expr',expr],deadline)
            return dict(path=target.name,reopened=True,sha256=sha(target),fingerprint=stage['fingerprint'])
        def persist(state,token,deadline):
            assert_owned(remote,asset,token)
            # Test only: independent bare Git remote stores verified native bytes.
            ledger=root/'ledger.json';ledger.write_text(json.dumps(state,sort_keys=True))
            env={**os.environ,'GIT_INDEX_FILE':str(Path(d)/'index')}
            def g(*args):
                run_operation(['git',*args],deadline,env=env)
            g('read-tree','--empty')
            for p in [ledger]+[root/v['path'] for v in state.values()]:
                g('--work-tree='+str(root),'add','--',p.name)
            tree=subprocess.check_output(['git','write-tree'],env=env,text=True).strip()
            c=subprocess.check_output(['git','-c','user.name=QA','-c','user.email=qa@invalid','commit-tree',tree,'-m','Isolated native checkpoint','-p',persist.parent],text=True).strip()
            persist.parent=c
            g('push',remote,c+':refs/heads/checkpoint')
            for v in state.values():
                data=subprocess.check_output(['git','--git-dir='+remote,'show',c+':'+v['path']])
                import hashlib
                assert hashlib.sha256(data).hexdigest()==v['sha256']
            return True
        persist.parent=commit
        # Checkpoint branch advances without overwriting prior evidence.
        # Each commit must have the previous checkpoint as parent.
        assert run(remote,asset,commit,root,stages,records,execute,persist,budget=900,reserve=180)==['native_reopen','native_save']
        print('ISOLATED_HOME_NATIVE_PASS')

if __name__=='__main__':main()
