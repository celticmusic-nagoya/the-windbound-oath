"""Fail-closed recovery of exact run-bound leases. No retry or native mutation."""
import json
import re
import subprocess
import os
import sys
import hashlib

REPO = 'celticmusic-nagoya/the-windbound-oath'
RID = 1408120919
BOT = 41898282
OWNER = 315379131
FAILED = {'failure', 'cancelled', 'timed_out', 'startup_failure'}
# An explicit reviewed route; generic leases and later write phases are not qualified yet.
ROUTES = {424712879: dict(asset='MORWEN', path='.github/workflows/morwen-vroid-macos-probe.yml',
    blob='5671b2256dcc2d0b20020d99fe6406fb5eef2618', schema='morwen-transfer-v1',
    title=r'Morwen VRoid / vrm_export request:([1-9][0-9]{0,19})', pr=427,
    job='VRM export and private transfer (reopen)',
    skipped_steps=('Restore preserved native checkpoint from existing private Release',
                   'Launch signed application and collect evidence',
                   'Transfer candidate directly to reviewed private handoff'),
    skipped_jobs=('matrix.lane', 'blender-transfer-protected', 'complete-morwen-transfer'))}

class Hold(Exception):
    pass

def need(ok, reason):
    if not ok:
        raise Hold(reason)

def sha(s):
    return isinstance(s, str) and re.fullmatch(r'[0-9a-f]{40}', s) is not None

def ref_for(asset):
    return 'refs/tags/two-asset-lease/v1/' + hashlib.sha256(asset.encode()).hexdigest()

def qualify(api, run_id):
    base = 'repos/' + REPO
    run = api(f'{base}/actions/runs/{run_id}')
    route = ROUTES.get(run.get('workflow_id'))
    need(route is not None, 'unqualified workflow')
    need(run.get('id') == run_id and run.get('run_attempt') == 1 and
         run.get('status') == 'completed' and run.get('conclusion') in FAILED and
         run.get('head_branch') == 'main' and run.get('event') == 'workflow_dispatch' and
         run.get('path') == route['path'] and run.get('repository', {}).get('id') == RID and
         run.get('head_repository', {}).get('id') == RID and run.get('actor', {}).get('id') == BOT and
         run.get('actor', {}).get('login') == 'github-actions[bot]',
         'run identity or termination not qualified')
    revision = run.get('head_sha')
    need(sha(revision), 'invalid revision')
    title = re.fullmatch(route['title'], run.get('display_title', ''))
    need(title is not None, 'unqualified mode')
    request = title.group(1)
    worker = api(f'{base}/contents/{route["path"]}?ref={revision}')
    need(worker.get('sha') == route['blob'], 'worker revision not qualified')
    comment = api(f'{base}/issues/comments/{request}')
    need(comment.get('id') == int(request) and comment.get('user', {}).get('id') == OWNER and
         comment.get('author_association') == 'OWNER' and
         comment.get('created_at') == comment.get('updated_at') and
         comment.get('issue_url') == f'https://api.github.com/{base}/issues/{route["pr"]}' and
         comment.get('body') == '/two-morwen-launch vrm_export main=' + revision,
         'owner request mismatch')
    response = api(f'{base}/actions/runs/{run_id}/attempts/1/jobs?per_page=100')
    jobs = response.get('jobs', [])
    need(len(jobs) == response.get('total_count') and len(jobs) == 4 and
         all(j.get('status') == 'completed' and j.get('run_id') == run_id and j.get('run_attempt') == 1 for j in jobs),
         'incomplete or unexpected job inventory')
    primary = [j for j in jobs if j.get('name') == route['job']]
    others = [j for j in jobs if j.get('name') != route['job']]
    need(len(primary) == 1 and primary[0].get('conclusion') in FAILED and
         sorted(j.get('name') for j in others) == sorted(route['skipped_jobs']) and
         all(j.get('conclusion') == 'skipped' for j in others), 'later job or unknown job ran')
    steps = primary[0].get('steps', [])
    for name in route['skipped_steps']:
        found = [s for s in steps if s.get('name') == name]
        need(len(found) == 1 and found[0].get('status') == 'completed' and
             found[0].get('conclusion') == 'skipped', 'native/private write phase not proven skipped')
    for status in ('queued', 'in_progress', 'waiting', 'requested', 'pending'):
        active = api(f'{base}/actions/workflows/{run["workflow_id"]}/runs?status={status}&per_page=1')
        need(active.get('total_count') == 0 and active.get('workflow_runs') == [],
             'active or ambiguous worker inventory')
    ref = ref_for(route['asset'])
    matches = api(f'{base}/git/matching-refs/{ref[5:]}')
    if not matches:
        return None
    need(len(matches) == 1 and matches[0].get('ref') == ref, 'ambiguous lease')
    obj = matches[0].get('object', {})
    token = obj.get('sha')
    need(obj.get('type') == 'tag' and sha(token), 'unqualified lease object')
    tag = api(f'{base}/git/tags/{token}')
    need(tag.get('sha') == token and tag.get('object', {}).get('sha') == revision and
         tag.get('object', {}).get('type') == 'commit', 'lease revision mismatch')
    body = json.loads(tag['message'])
    expected = dict(schema=route['schema'], asset=route['asset'], revision=revision,
                    request=request, run=str(run_id), attempt='1')
    parent = body.pop('reservation', None)
    nonce = body.pop('nonce', None)
    need(sha(parent) and isinstance(nonce, str) and re.fullmatch(r'[0-9a-f]{32}', nonce) and
         body == expected, 'lease run binding mismatch')
    prior = api(f'{base}/git/tags/{parent}')
    need(prior.get('sha') == parent and prior.get('object', {}).get('sha') == revision and
         prior.get('object', {}).get('type') == 'commit', 'reservation object mismatch')
    reserved = json.loads(prior['message'])
    prior_nonce = reserved.pop('nonce', None)
    need(isinstance(prior_nonce, str) and re.fullmatch(r'[0-9a-f]{32}', prior_nonce) and
         reserved == dict(expected, run=None, attempt=None), 'reservation lineage mismatch')
    return dict(asset=route['asset'], ref=ref, token=token, run_id=run_id,
                revision=revision, request=request, attempt=1, reservation=parent, phase='PRE_NATIVE_WRITE')

def recover(api, remote_ref, compare_delete, run_id, apply=False):
    evidence = qualify(api, run_id)
    if evidence is None:
        return {'status': 'NO_LEASE_API', 'run_id': run_id}
    need(remote_ref(evidence['ref']) == evidence['token'], 'lease changed before release')
    if not apply:
        return dict(evidence, status='DRY_RUN_ELIGIBLE')
    need(qualify(api, run_id) == evidence, 'run or lease changed during verification')
    compare_delete(evidence['asset'], evidence['token'])
    need(remote_ref(evidence['ref']) is None, 'lease absent readback not confirmed; reconcile')
    return dict(evidence, status='RELEASED')

def main():
    def api(path):
        return json.loads(subprocess.check_output(['gh', 'api', path], text=True, timeout=20))
    def remote_ref(ref):
        value = subprocess.check_output(['git','ls-remote','--refs','origin',ref], text=True, timeout=20).strip()
        if not value:
            return None
        parts = value.split('\t')
        need(len(parts) == 2 and sha(parts[0]) and parts[1] == ref, 'ambiguous git ref')
        return parts[0]
    def compare_delete(asset, token):
        # Invoke the existing CAS routine with a bounded subprocess, not REST DELETE.
        subprocess.run([sys.executable, '-c', 'from shared_asset_lease import release; import sys; release("origin",sys.argv[1],sys.argv[2])', asset, token], check=True, timeout=30,
                       cwd=os.path.dirname(os.path.abspath(__file__)))
    event = json.load(open(os.environ['GITHUB_EVENT_PATH'], encoding='utf-8'))
    need(os.environ.get('GITHUB_REPOSITORY') == REPO, 'wrong recovery repository')
    if os.environ.get('GITHUB_EVENT_NAME') == 'workflow_run':
        need(event.get('action') == 'completed', 'not completed event')
        run_id = event['workflow_run']['id']
        apply = os.environ.get('TWO_FAILURE_RECOVERY_ENABLED') == 'true'
    elif os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch':
        run_id = int(event['inputs']['run_id']); apply = False
    else:
        raise Hold('unsupported trigger')
    try:
        print(json.dumps(recover(api, remote_ref, compare_delete, run_id, apply), sort_keys=True))
    except Hold as exc:
        print(json.dumps({'status':'HOLD', 'run_id':run_id, 'reason':str(exc)}))
        sys.exit(2)

if __name__ == '__main__':
    main()
