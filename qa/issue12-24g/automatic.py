from pathlib import Path
import subprocess,json,time,sys
r=Path(sys.argv[1]).resolve();o=Path(sys.argv[2]).resolve();(o/'logs').mkdir(parents=True,exist_ok=True);(o/'reports').mkdir(parents=True,exist_ok=True);rows=[]
cmds=[['node',str(f.relative_to(r))] for f in sorted((r/'tests').rglob('*')) if f.name.endswith(('.test.cjs','.test.js'))]
cmds += [['python3','tests/battle/hero_motion_plan.py'],['python3','tests/moss/m9_hero_intake.py'],['python3','tests/system/asset_registry_audit.py'],['python3','tests/battle/battle_opening.py','--self-test'],['python3','tools/qa/run_regressions.py','--self-test'],['node','--check','js/prologue-progress.js'],['node','--check','tests/save_compatibility.test.cjs'],['git','diff','--check']]
cmds += [['node','--check',f] for f in ['js/loading-input.js','js/loading-view.js','js/load-coordinator.js','js/battle-loading.js','js/save-continue.js','js/field/moss-forest-runtime.js','js/field/field-scene.js','js/field/field-choreo.js','js/field/field-talk.js']]
(o/'reports/environment.json').write_text(json.dumps({'logical_cpus':__import__('os').cpu_count(),'platform':__import__('platform').platform(),'scope':'CI runner capacity; no product/test assertions changed'},indent=2)+'\n')
for cmd in cmds:
 start=time.monotonic();p=subprocess.run(cmd,cwd=r,capture_output=True,text=True,timeout=240);name='_'.join(cmd[1:]).replace('/','_')+'.log';(o/'logs'/name).write_text(p.stdout+p.stderr)
 failed=p.returncode!=0 or any(x.startswith('FAIL ') for x in p.stdout.splitlines());row={'command':cmd,'status':'FAIL' if failed else 'PASS','exit':p.returncode,'seconds':round(time.monotonic()-start,3),'log':name};rows.append(row);(o/'reports/qa-results.json').write_text(json.dumps(rows,indent=2)+'\n');print(row,flush=True)
 if failed:raise SystemExit(1)
print('ALL '+str(len(rows))+' EXECUTABLE COMMANDS PASS')
