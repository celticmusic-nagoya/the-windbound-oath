"""Create-only Git ref reservation. Fail closed; no automatic stale takeover.
All writers must use the same canonical asset key. Release only after durable
handoff, by the acquiring owner, while no other process can release this ref.
"""
import hashlib, re, subprocess, json
def ref_for(asset):
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9_-]{2,100}',asset): raise ValueError('canonical asset key required')
    return 'refs/tags/two-asset-lease/v1/'+hashlib.sha256(asset.encode()).hexdigest()
def acquire(repo,asset,commit):
    if not re.fullmatch(r'[0-9a-f]{40}',commit): raise ValueError('commit SHA required')
    ref=ref_for(asset)
    p=subprocess.run(['gh','api','--method','POST',f'repos/{repo}/git/refs','-f',f'ref={ref}','-f',f'sha={commit}'],capture_output=True,text=True)
    if p.returncode: raise RuntimeError('Reservation not confirmed; reconcile before any write')
    x=json.loads(p.stdout)
    if x['ref']!=ref or x['object']['sha']!=commit: raise RuntimeError('Unexpected reservation response')
    return ref
def inspect(repo,asset):
    return json.loads(subprocess.check_output(['gh','api',f'repos/{repo}/git/ref/{ref_for(asset)[5:]}'],text=True))
# No DELETE helper: GitHub refs API does not offer compare-and-delete.
# Explicit reconciled release required; never auto-expire a live writer.
