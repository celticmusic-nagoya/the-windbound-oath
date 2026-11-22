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
    nonce=uuid.uuid4().hex
    obj=git('mktag',stdin=f'object {commit}\ntype commit\ntag two-lease-{nonce}\ntagger TWO lease <lease@invalid> 1700000000 +0000\n\n{nonce}\n')
    git('push','--porcelain',f'--force-with-lease={ref}:',remote,f'{obj}:{ref}')
    assert_owned(remote,asset,obj)
    return obj

def assert_owned(remote,asset,obj):
    if not re.fullmatch(r'[0-9a-f]{40}',obj):raise ValueError('lease object required')
    ref=ref_for(asset)
    if git('ls-remote','--refs',remote,ref)!=f'{obj}\t{ref}':raise RuntimeError('lease lost')

def release(remote,asset,obj):
    assert_owned(remote,asset,obj)
    ref=ref_for(asset)
    git('push','--porcelain',f'--force-with-lease={ref}:{obj}',remote,f':{ref}')
