import json, os, subprocess, time
from pathlib import Path
from shared_factory_stage import execute_factory_stage
from shared_blueprint_contract import digest_record
from session_plan import sha
base=Path(__file__).parent.resolve()
def call(mode,path,value='',deadline=None):
    cmd=[os.environ['BLENDER_530'],'-b','-noaudio','--factory-startup','-t','2','--python-exit-code','9','--python',str(base/'blender_stage.py'),'--',mode,str(path),str(value)]
    out=subprocess.run(cmd,capture_output=True,text=True,check=True,timeout=max(1,deadline-time.monotonic()) if deadline else 60)
    for line in out.stdout.splitlines():
        if line.startswith('NATIVE_JSON '): return json.loads(line.split(' ',1)[1])
class Adapter:
    def edit(self,p,t,*,deadline): call('edit',p,1.4,deadline)
    def measure(self,p,t,*,deadline):
        obs=call('measure',p,deadline=deadline)
        assert obs['topology']==[8,6]
        actual={k:obs[k] for k in t['values']}
        return {**{k:t[k] for k in ('target_id','source_sha256','coordinate_system','units','projection','measurement_id','dependency_fingerprint')},
                'operation_id':t['operation']['id'],'target_contract_sha256':digest_record(t),
                'actual':actual,'residuals':{k:v-t['values'][k] for k,v in actual.items()},
                'uncertainty':{'length':1e-6,'width':1e-6},'native_sha256':sha(p),
                'evidence_sha256':digest_record(obs),'protected_scope_id':'scope','protected_sha256':obs['protected'],'intersections':0}
    def propose_correction(self,p,t,o,k,*,deadline): return -o['residuals'][k]
    def correct_metric(self,p,t,k,amount,*,deadline): call('correct',p,amount,deadline);return amount
    def finish(self,p,t,*,deadline):
        q=p.parent/'preview.png'
        call('preview',p,q,deadline)
        return {q.name:sha(q)}
    reopen=measure
asset = "LIND-HOME"  # Used only against this job's temporary Git transport.
mode, root_argument = __import__("sys").argv[1:]
root = Path(root_argument).resolve()
remote = str(root / "transport.git")
deadline = time.monotonic() + 180
from shared_asset_lease import acquire, git, release
from shared_git_checkpoint_store import GitCheckpointStore, restore_checkpoint
if mode == "seed":
    git("init", "--bare", "-q", remote)
    git("commit", "--allow-empty", "-qm", "Synthetic qualification root")
    source = root / "source.blend"
    call("create", source, deadline=deadline)
    original_sha = sha(source)
    dependency = {"fixture": sha(base / "blender_stage.py")}
    reference = digest_record({"length": 1.2, "width": 1.0})
    target = dict(sha256=reference, target_id="cube", source_sha256=original_sha,
        coordinate_system="object-aligned", units="m", projection="native-3d", measurement_id="bbox",
        values={"length": 1.2, "width": 1.0}, tolerances={"length": 1e-4, "width": 1e-4},
        uncertainty={"length": 0, "width": 0}, intersection_limit=0,
        operation=dict(id="scale-x", qualified=True, evidence_sha256=dependency["fixture"]),
        protection=dict(scope_id="scope", baseline_sha256=call("measure", source, deadline=deadline)["protected"]),
        dependency_fingerprint=digest_record(dependency),
        corrections={"length": dict(operation_id="correct-x", evidence_sha256=dependency["fixture"],
            qualified=True, max_delta=.3, affects=["length"], requires_pass=["width"])})
    request = dict(target_id="cube", asset_id=asset, stage="cube", source_sha256=original_sha,
                   reference_sha256=reference, dependency_hashes=dependency)
    stage = dict(id="cube", fingerprint=digest_record(target), requires_actual_edit=True)
    token = acquire(remote, asset, git("rev-parse", "HEAD"))
    from shared_asset_lease import assert_owned
    result = execute_factory_stage(root, source, stage, target, request, Adapter(), deadline,
                                   lambda: assert_owned(remote, asset, token))
    if sha(source) != original_sha:
        raise RuntimeError("source changed")
    store = GitCheckpointStore(remote, asset, root)
    release(remote, asset, store({"cube": result}, token, deadline))
    git("-C", remote, "bundle", "create", str(root/"checkpoint.bundle"), "--all")
    record = dict(revision=store.previous, bundle_sha256=sha(root/"checkpoint.bundle"),
                  run_id=os.environ["GITHUB_RUN_ID"], native_sha256=result["sha256"])
    (root/"seed.json").write_text(json.dumps(record, indent=2)+"\n")
elif mode == "restore":
    seed = json.loads((root/"seed.json").read_text())
    if seed["run_id"] == os.environ["GITHUB_RUN_ID"] or sha(root/"checkpoint.bundle") != seed["bundle_sha256"]:
        raise RuntimeError("checkpoint origin or digest mismatch")
    git("clone", "--bare", "-q", str(root/"checkpoint.bundle"), remote)
    restored = root/"restored"
    result = restore_checkpoint(remote, asset, seed["revision"], restored, deadline)["cube"]
    native = restored/result["path"]
    observation = call("measure", native, deadline=deadline)
    if (sha(native) != seed["native_sha256"] or observation["protected"] != result["observation"]["protected_sha256"]
            or abs(observation["length"]-1.2)>1e-4 or observation["topology"] != [8,6]):
        raise RuntimeError("independent native reopen mismatch")
    (root/"restore.json").write_text(json.dumps(dict(seed=seed, observation=observation,
         run_id=os.environ["GITHUB_RUN_ID"], completed_edits_executed=0), indent=2)+"\n")
else:
    raise SystemExit("unknown qualification mode")
