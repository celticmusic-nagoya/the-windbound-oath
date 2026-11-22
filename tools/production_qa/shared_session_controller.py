"""Budget-aware sequential controller using the shared planner.
Adapter callbacks must verify native reopen and return checkpoint metadata.
No automatic takeover; retain lease on failure until reconciled.
"""
import time
from session_plan import ready,sha
from shared_asset_lease import acquire,assert_owned,release

def run(remote,asset,commit,root,stages,completed,execute,persist,budget=19800,reserve=1800):
    if not 0<reserve<budget<=21600: raise ValueError('invalid budget')
    started=time.monotonic()
    token=acquire(remote,asset,commit)
    executed=[]
    while True:
        assert_owned(remote,asset,token)
        available=ready(stages,completed,root,budget-(time.monotonic()-started),reserve)
        if not available:break
        stage=next(s for s in stages if s['id']==available[0])
        result=execute(stage,token)
        assert_owned(remote,asset,token)
        p=(root/result['path']).resolve()
        if not p.is_relative_to(root.resolve()) or result.get('reopened') is not True or sha(p)!=result.get('sha256') or result.get('fingerprint')!=stage['fingerprint']:raise RuntimeError('invalid checkpoint')
        updated={**completed,stage['id']:result}
        # Must confirm durable off-runner persistence before advancing.
        if persist(updated,token) is not True:raise RuntimeError('durability unconfirmed')
        completed.update(updated)
        executed.append(stage['id'])
    if persist(completed,token) is not True:raise RuntimeError('handoff unconfirmed')
    release(remote,asset,token)
    return executed
