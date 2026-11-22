"""Git transport CAS lease for cooperating writers; no automatic takeover.
Unique annotated tag object prevents ABA even when reacquiring same commit.
Requires authenticated git remote and canonical asset ID.
"""
import subprocess,uuid,re
from shared_asset_reservation import ref_for

def git(*args,stdin=None):
    return subprocess.run(['git',*args],input=stdin,text=True,capture_output=True,check=True).stdout.strip()

def acquire(remote,asset,commit):
    if not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('commit SHA required')
    ref=ref_for(asset)
    obj=lease_object(commit)
    git('push','--porcelain',f'--force-with-lease={ref}:',remote,f'{obj}:{ref}')
    assert_owned(remote,asset,obj)
    return obj

def lease_object(commit):
    nonce=uuid.uuid4().hex
    return git('mktag',stdin=f'object {commit}\ntype commit\ntag two-lease-{nonce}\ntagger TWO lease <lease@invalid> 1700000000 +0000\n\n{nonce}\n')

def assert_owned(remote,asset,obj):
    if not re.fullmatch(r'[0-9a-f]{40}',obj):raise ValueError('lease object required')
    ref=ref_for(asset)
    if git('ls-remote','--refs',remote,ref)!=f'{obj}\t{ref}':raise RuntimeError('lease lost')

def release(remote,asset,obj):
    assert_owned(remote,asset,obj)
    ref=ref_for(asset)
    git('push','--porcelain',f'--force-with-lease={ref}:{obj}',remote,f':{ref}')

def publish_checkpoint(remote, asset, token, checkpoint, previous=None):
    """Publish and rotate the fencing token in the same server-side transaction.

    The owning adapter must save and verify the native outputs before creating
    the checkpoint commit. A failed or disconnected push requires reconciliation.
    """
    if not re.fullmatch(r'[0-9a-f]{40}', checkpoint):
        raise ValueError('checkpoint commit SHA required')
    if previous is not None:
        if not re.fullmatch(r'[0-9a-f]{40}', previous) or checkpoint == previous:
            raise ValueError('previous checkpoint must be a distinct commit SHA')
        git('merge-base', '--is-ancestor', previous, checkpoint)
    lock = ref_for(asset)
    output = 'refs/heads/two-checkpoint/v1/' + lock.rsplit('/', 1)[1]
    assert_owned(remote, asset, token)
    successor = lease_object(checkpoint)
    git('push', '--atomic', '--porcelain',
        f'--force-with-lease={lock}:{token}',
        f'--force-with-lease={output}:{previous or ""}',
        remote, f'{successor}:{lock}', f'{checkpoint}:{output}')
    assert_owned(remote, asset, successor)
    if git('ls-remote', '--refs', remote, output) != f'{checkpoint}\t{output}':
        raise RuntimeError('published checkpoint not confirmed')
    return successor
