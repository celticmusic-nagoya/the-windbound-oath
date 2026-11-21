"""Production OS local checkpoint planner; no remote execution or lease acquisition."""
import hashlib
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''): h.update(b)
    return h.hexdigest()

def ready(stages, completed, root, remaining, reserve):
    ids={s['id'] for s in stages}
    if len(ids)!=len(stages): raise ValueError('duplicate stage')
    resolved=set(); pending=list(stages)
    while pending:
        batch=[s for s in pending if set(s['deps'])<=resolved]
        if not batch: raise ValueError('cyclic or missing dependency')
        for s in batch: resolved.add(s['id']); pending.remove(s)
    valid=set()
    pending=list(stages)
    while pending:
        batch=[s for s in pending if not (set(s['deps']) & {x['id'] for x in pending})]
        for s in batch:
            pending.remove(s); c=completed.get(s['id'],{}); p=root/c.get('path','')
            if set(s['deps'])<=valid and c.get('fingerprint')==s['fingerprint'] and c.get('reopened') is True and p.is_file() and sha(p)==c.get('sha256'): valid.add(s['id'])
    return [s['id'] for s in stages if s['id'] not in valid and set(s['deps'])<=valid and s.get('qualified') is True and 0<s['seconds']<=remaining-reserve]
