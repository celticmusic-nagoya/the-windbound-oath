import json, os, subprocess, time
from shared_session_contract import asset_key
from pathlib import Path
from shared_factory_stage import execute_factory_stage
from shared_blueprint_contract import digest_record
from session_plan import sha
base=Path(__file__).parent.resolve()
def call(mode,path,value='',deadline=None):
    cmd=[os.environ['BLENDER_530'],'-b','-noaudio','--factory-startup','-t','2','--python-exit-code','9','--python',str(base/'blender_stage.py'),'--',mode,str(path),str(value)]
    env = {k: v for k, v in os.environ.items() if k != "TWO_CHECKPOINT_TOKEN"}
    out=subprocess.run(cmd,capture_output=True,text=True,check=True,env=env,timeout=max(1,deadline-time.monotonic()) if deadline else 60)
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
from shared_asset_lease import acquire, assert_owned, claim_reservation, git, release
from shared_git_checkpoint_store import GitCheckpointStore, restore_checkpoint
def contract(source, stage_id, length):
    original_sha = sha(source)
    dependency = {"fixture": sha(base / "blender_stage.py")}
    reference = digest_record({"length": length, "width": 1.0})
    target = dict(sha256=reference, target_id=stage_id, source_sha256=original_sha,
        coordinate_system="object-aligned", units="m", projection="native-3d", measurement_id="bbox",
        values={"length": length, "width": 1.0}, tolerances={"length": 1e-4, "width": 1e-4},
        uncertainty={"length": 0, "width": 0}, intersection_limit=0,
        operation=dict(id="scale-x", qualified=True, evidence_sha256=dependency["fixture"]),
        protection=dict(scope_id="scope", baseline_sha256=call("measure", source, deadline=deadline)["protected"]),
        dependency_fingerprint=digest_record(dependency),
        corrections={"length": dict(operation_id="correct-x", evidence_sha256=dependency["fixture"],
            qualified=True, max_delta=.3, affects=["length"], requires_pass=["width"])})
    request = dict(target_id=stage_id, asset_id=asset, stage=stage_id, source_sha256=original_sha,
                   reference_sha256=reference, dependency_hashes=dependency)
    stage = dict(id=stage_id, fingerprint=digest_record(target), requires_actual_edit=True)
    return stage, target, request

if mode == "seed":
    git("init", "--bare", "-q", remote)
    git("commit", "--allow-empty", "-qm", "Synthetic qualification root")
    source = root / "source.blend"
    call("create", source, deadline=deadline)
    original_sha = sha(source)
    stage, target, request = contract(source, "cube", 1.2)
    token = acquire(remote, asset, git("rev-parse", "HEAD"))
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
    if os.environ.get("TWO_RESUME_PENDING") != "1":
        raise RuntimeError("restore phase requires the pending native stage")
    stage_id = "cube-continuation"
    stage, target, request = contract(native, stage_id, 1.3)
    token = acquire(remote, asset, seed["revision"])
    continued = execute_factory_stage(restored, native, stage, target, request, Adapter(), deadline,
                                      lambda: assert_owned(remote, asset, token))
    if sha(native) != seed["native_sha256"]:
        raise RuntimeError("restored predecessor changed")
    store = GitCheckpointStore(remote, asset, restored, previous=seed["revision"])
    release(remote, asset, store({"cube": result, stage_id: continued}, token, deadline))
    verified = restore_checkpoint(remote, asset, store.previous, root/"verified", deadline)
    if verified["cube"] != result or verified[stage_id] != continued:
        raise RuntimeError("continuation checkpoint readback mismatch")
    git("-C", remote, "bundle", "create", str(root/"checkpoint.bundle"), "--all")
    (root/"restore.json").write_text(json.dumps(dict(seed=seed, observation=observation,
         run_id=os.environ["GITHUB_RUN_ID"], completed_edits_executed=0, pending_edits_executed=1,
         continuation=continued, checkpoint_revision=store.previous,
         bundle_sha256=sha(root/"checkpoint.bundle")), indent=2)+"\n")
elif mode == "shared-resume":
    asset = asset_key("QA-ENG-468-REMOTE-01")
    remote = "https://github.com/celticmusic-nagoya/the-windbound-oath-handoff.git"
    revision = "9438b32eacf64050f4b90b1fbba5768b60f7c3ef"
    expected_sha = "6d921d4a104bc88c99e3a904357a354e82039f799bdd4a4598c0913e5fb561b2"
    predecessor = "engine-acceptance-correction"
    stage_id = "engine-acceptance-resume"
    restored = root / "restored"
    records = restore_checkpoint(remote, asset, revision, restored, deadline)
    if set(records) != {predecessor} or records[predecessor]["sha256"] != expected_sha:
        raise RuntimeError("unexpected shared checkpoint contents")
    native = restored / records[predecessor]["path"]
    before = call("measure", native, deadline=deadline)
    if abs(before["length"] - 1.45) > 1e-4 or before["width"] != 1.0:
        raise RuntimeError("unexpected predecessor measurement")
    stage, target, request = contract(native, stage_id, 1.35)
    reservation = acquire(remote, asset, revision)
    token = claim_reservation(remote, asset, reservation, revision)
    try:
        assert_owned(remote, asset, reservation, deadline=deadline)
    except RuntimeError as exc:
        if str(exc) != "lease lost":
            raise
    else:
        raise RuntimeError("stale reservation retained write authority")
    continued = execute_factory_stage(restored, native, stage, target, request, Adapter(), deadline,
                                      lambda: assert_owned(remote, asset, token, deadline=deadline))
    if sha(native) != expected_sha or continued["observation"]["protected_sha256"] != before["protected"]:
        raise RuntimeError("predecessor or protected geometry changed")
    successor_records = {**records, stage_id: continued}
    store = GitCheckpointStore(remote, asset, restored, previous=revision)
    successor = store(successor_records, token, deadline)
    verified = restore_checkpoint(remote, asset, store.previous, root / "verified", deadline)
    if verified != successor_records:
        raise RuntimeError("shared continuation checkpoint readback mismatch")
    release(remote, asset, successor)
    from shared_asset_reservation import ref_for
    if git("ls-remote", "--refs", remote, ref_for(asset), deadline=deadline):
        raise RuntimeError("shared verification lease was not released")
    observation = continued["observation"]
    (root / "restore.json").write_text(json.dumps(dict(
        run_id=os.environ["GITHUB_RUN_ID"], head=os.environ["GITHUB_SHA"], asset=asset,
        predecessor_revision=revision, predecessor_sha256=expected_sha,
        checkpoint_revision=store.previous, native_sha256=continued["sha256"],
        protected_sha256=before["protected"], actual=observation["actual"],
        residuals=observation["residuals"], completed_edits_executed=0,
        pending_edits_executed=1, stale_reservation_rejected=True,
        lease_released=True, checkpoint_readback=True), indent=2)+"\n")
else:
    raise SystemExit("unknown qualification mode")
