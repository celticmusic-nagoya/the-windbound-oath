"""Bridge verified native checkpoint evidence to the Production OS planner."""
from pathlib import Path
from session_checkpoint import publish
from session_plan import ready

def checkpoint_and_select(source, reopened, root, stage, fingerprint, stages, completed, remaining, reserve, *, ui_reopen_verified):
    if ui_reopen_verified is not True:
        raise ValueError('native UI reopen evidence required')
    root=Path(root).resolve()
    if stage not in {s['id'] for s in stages}:
        raise ValueError('unknown stage')
    target=next(s for s in stages if s['id']==stage)
    if target['fingerprint']!=fingerprint:
        raise ValueError('stale stage fingerprint')
    if stage not in ready(stages,completed,root,remaining,reserve):
        raise ValueError('stage unavailable')
    manifest=publish(source,reopened,root,stage,fingerprint)
    manifest['reopened']=True
    state=dict(completed)
    state[stage]=manifest
    return state,ready(stages,state,root,remaining,reserve)
