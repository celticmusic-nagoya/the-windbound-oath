#!/usr/bin/env python3
"""source_guard.py - full-source integrity guard for Full-regression runs (INT-02-P0-D, answers Codex FULL_SOURCE_INTEGRITY_FINDING).
 preflight --root R [--protect P ...]   : R must be a git work tree whose git commands WORK (rev-parse/status/ls-files), HEAD readable, and the protected paths clean.
                                          Otherwise exit 3 = 'full verification NOT ESTABLISHED' (tests that restore files with git would silently fail without .git).
 snapshot  --root R --out M.json        : SHA-256 of every file under R (excluding .git, __pycache__, *.pyc, --exclude globs)  -> M.json
 verify    --root R --manifest M.json   : re-hash; report changed / missing / added files, grouped (npc-art, bounds, battle-code, tests, other). exit 0 only if identical, else 1.
Exit codes: 0 ok, 1 differences, 3 preflight failed, 2 usage.  Never modifies R."""
import argparse, fnmatch, hashlib, json, os, subprocess, sys
DEF_PROTECT = ['img/field/lind/npc', 'js/field/lind-content-bounds.js']
GROUPS = [('npc-art', 'img/field/lind/npc/'), ('bounds', 'js/field/lind-content-bounds.js'), ('battle-code', 'js/battle'), ('battle-code', 'js/prologue-combat.js'), ('tests', 'tests/'), ('ci-tools', 'tools/')]
def sh(root, *a):
    r = subprocess.run(['git', '-C', root] + list(a), capture_output=True, text=True); return r.returncode, r.stdout, r.stderr
def walk(root, excl):
    out = {}
    for d, ds, fs in os.walk(root):
        ds[:] = [x for x in ds if x not in ('.git', '__pycache__', 'node_modules', 'test-results')]
        for f in fs:
            if f.endswith('.pyc'): continue
            p = os.path.join(d, f); rel = os.path.relpath(p, root).replace(os.sep, '/')
            if any(fnmatch.fnmatch(rel, g) for g in excl) or os.path.islink(p): continue
            h = hashlib.sha256()
            with open(p, 'rb') as fh:
                for ch in iter(lambda: fh.read(1 << 20), b''): h.update(ch)
            out[rel] = h.hexdigest()
    return out
def group(rel):
    for g, pre in GROUPS:
        if rel.startswith(pre): return g
    return 'other'
def main():
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    a = sp.add_parser('preflight'); a.add_argument('--root', required=True); a.add_argument('--protect', nargs='*', default=DEF_PROTECT)
    b = sp.add_parser('snapshot'); b.add_argument('--root', required=True); b.add_argument('--out', required=True); b.add_argument('--exclude', nargs='*', default=[])
    c = sp.add_parser('verify'); c.add_argument('--root', required=True); c.add_argument('--manifest', required=True); c.add_argument('--exclude', nargs='*', default=[])
    n = ap.parse_args()
    if n.cmd == 'preflight':
        rc, o, e = sh(n.root, 'rev-parse', 'HEAD')
        if rc: print('PREFLIGHT FAIL: git metadata unusable (%s) -> Full verification NOT ESTABLISHED' % e.strip()[:120]); return 3
        head = o.strip()
        for args in (('status', '--porcelain'), ('ls-files', '-s', '--', *n.protect)):
            rc, o2, e = sh(n.root, *args)
            if rc: print('PREFLIGHT FAIL: git %s failed (%s)' % (args[0], e.strip()[:120])); return 3
        rc, o3, _ = sh(n.root, 'status', '--porcelain', '--', *n.protect)
        if o3.strip(): print('PREFLIGHT FAIL: protected paths are dirty:\n' + o3[:400]); return 3
        rc, o4, _ = sh(n.root, 'ls-files', '--', *n.protect)
        if not o4.strip(): print('PREFLIGHT FAIL: protected paths not tracked by git (restore impossible)'); return 3
        print('PREFLIGHT OK head=%s protected_tracked=%d' % (head, len(o4.split()))); return 0
    if n.cmd == 'snapshot':
        m = walk(n.root, n.exclude); json.dump({'root_files': len(m), 'files': m}, open(n.out, 'w'), indent=0, sort_keys=True)
        print('SNAPSHOT files=%d sha256(manifest)=%s' % (len(m), hashlib.sha256(json.dumps(m, sort_keys=True).encode()).hexdigest())); return 0
    base = json.load(open(n.manifest))['files']; now = walk(n.root, n.exclude)
    ch = sorted(k for k in base if k in now and base[k] != now[k]); mi = sorted(k for k in base if k not in now); ad = sorted(k for k in now if k not in base)
    for tag, lst in (('CHANGED', ch), ('MISSING', mi), ('ADDED', ad)):
        by = {}
        for k in lst: by.setdefault(group(k), []).append(k)
        for g, ks in sorted(by.items()): print('%s %s %d  e.g. %s' % (tag, g, len(ks), ', '.join(ks[:3])))
    if ch or mi or ad: print('VERIFY FAIL: changed=%d missing=%d added=%d -> source NOT identical to the fixed snapshot' % (len(ch), len(mi), len(ad))); return 1
    print('VERIFY OK files=%d identical' % len(base)); return 0
sys.exit(main())
