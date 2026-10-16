#!/usr/bin/env python3
"""CI tier runner (proposal AUT-01). Serial, bounded, no test edits, no hidden passes.

Reads one or more tier files (one test per line: `path [VAR=value ...]`, `#` comments). For each test it runs the SAME command the repo already uses
(`python3 -u tests/run_python.py <test>` / `node <test>`), with a static server on 127.0.0.1:8765 started and owned by this runner.
Verdict per test: FAIL if exit != 0, or the output prints `FAIL ...` / `FAILS n` (n>0) (a traceback on an otherwise clean exit-0 run is only a warning, as in tools/qa/run_regressions.py), or the test file is missing (a listed test is NEVER skipped).
A failed test is re-run once only when --rerun-failed is given; the re-run is DIAGNOSTIC (flake evidence) and never turns a FAIL into a pass.
Special variable BYPASS=1 adds tools/ci/shim to PYTHONPATH (localhost-only BattleLoading bypass for tests that start battles directly).
Exit codes: 0 all pass | 1 test failure(s) | 3 infrastructure error (server/browser) | 4 listed test missing | 5 time budget exceeded (remaining = NOT_RUN, not a pass)."""
import argparse, json, os, re, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def discover(exclude):
    found = sorted(str(p.relative_to(ROOT)) for p in (ROOT / 'tests').rglob('*') if (p.suffix == '.py' or p.name.endswith('.test.js')) and '__pycache__' not in p.parts and p.name != 'run_python.py')
    return [(f, {}) for f in found if f not in exclude]


def read_tiers(files):
    items = []
    for f in files:
        if f == 'ALL':          # every test in the tree except those already pinned by T0-T2 tier files (listed with --exclude-tiers)
            items.append(('ALL', {}))
            continue
        for raw in Path(f).read_text().splitlines():
            line = raw.split('#', 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            env = dict(p.split('=', 1) for p in parts[1:] if '=' in p)
            items.append((parts[0], env))
    return items


def verdict(code, text):
    fails = re.findall(r'^FAIL(?!S)\b.*$', text, re.M)
    counts = [int(n) for n in re.findall(r'^FAILS:?\s+(\d+)', text, re.M)]
    # Same convention as tools/qa/run_regressions.py: a traceback alone does not fail a test that exited 0 with no FAIL lines (Playwright prints CancelledError/BrokenPipe
    # noise when a page is closed with a request in flight); it is recorded as a warning.
    bad = code != 0 or bool(fails) or any(counts)
    return ('FAIL' if bad else 'PASS'), fails, counts


def start_server(port, log):
    with socket.socket() as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('127.0.0.1', port))
        except OSError:
            raise SystemExit('port %d already in use - refusing to attach to a foreign server' % port)
    p = subprocess.Popen([sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1'], cwd=ROOT, stdout=log, stderr=log, start_new_session=True)
    for _ in range(80):
        if p.poll() is not None:
            break
        try:
            urllib.request.urlopen('http://127.0.0.1:%d/index.html' % port, timeout=.5).close()
            return p
        except OSError:
            time.sleep(.1)
    raise RuntimeError('static server not ready')


def kill(p):
    if p and p.poll() is None:
        try:
            os.killpg(p.pid, signal.SIGTERM)
            p.wait(timeout=5)
        except Exception:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except Exception:
                pass


def run_one(path, env_extra, timeout, out, port, tag=''):
    cmd = ['node', path] if path.endswith('.js') else [sys.executable, '-u', 'tests/run_python.py', path]
    env = dict(os.environ)
    env.pop('PORT', None)     # tests that own a server pick their own port; only the static server on 8765 is shared
    if path == 'tests/moss/walk_map.py':
        cmd.append('moss_forest_02_mossy_ravine.json')
    for k, v in env_extra.items():
        if k == 'BYPASS':
            env['PYTHONPATH'] = os.pathsep.join(filter(None, [str(HERE / 'shim'), env.get('PYTHONPATH', '')]))
        else:
            env[k] = v
    log = out / (path.replace('/', '_') + ''.join('_%s-%s' % kv for kv in sorted(env_extra.items())) + tag + '.log')
    t0 = time.monotonic()
    with log.open('w') as lf:
        p = subprocess.Popen(cmd, cwd=ROOT, env=env, stdout=lf, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill(p)
            code = 124
            lf.write('\nTIMEOUT: exceeded %ds\n' % timeout)
    text = log.read_text(errors='replace')
    v, fails, counts = verdict(code, text)
    return {'test': path, 'env': env_extra, 'verdict': v, 'exit': code, 'seconds': round(time.monotonic() - t0, 1), 'fail_lines': fails[:8], 'fails_counts': counts, 'log': log.name,
            'ok_lines': len(re.findall(r'^(?:ok|PASS)\b', text, re.M)), 'traceback_warnings': text.count('Traceback (most recent call last)')}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tiers', nargs='+')
    ap.add_argument('--out', default=str(ROOT / 'ci-results'))
    ap.add_argument('--timeout', type=int, default=int(os.environ.get('TEST_TIMEOUT_SECONDS', '420')), help='per-test seconds')
    ap.add_argument('--budget', type=int, default=0, help='total seconds for this run (0 = unlimited); the rest is NOT_RUN')
    ap.add_argument('--port', type=int, default=8765)
    ap.add_argument('--rerun-failed', action='store_true')
    ap.add_argument('--fail-fast', action='store_true')
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--exclude-tiers', nargs='*', default=[], help='with ALL: tier files whose tests are already covered')
    ap.add_argument('--shard', default='', help='K/N: run every N-th test starting at K (1-based) of the final list')
    a = ap.parse_args()
    items = read_tiers(a.tiers)
    if ('ALL', {}) in items:
        covered = {p for p, _ in read_tiers(a.exclude_tiers)}
        items = [i for i in items if i[0] != 'ALL'] + discover(covered)
    if a.shard:
        k, n = (int(x) for x in a.shard.split('/'))
        items = [it for i, it in enumerate(items) if i % n == k - 1]
    if a.list:
        for p, e in items:
            print(p, e or '')
        return 0
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    missing = [p for p, _ in items if not (ROOT / p).is_file()]
    rows, srv, code_out, t_start = [], None, 0, time.monotonic()
    if missing:
        for p in missing:
            print('MISSING', p)
        rows = [{'test': p, 'env': {}, 'verdict': 'MISSING', 'exit': 4, 'seconds': 0} for p in missing]
        write(out, rows, a)
        return 4
    uses_static = any(p.endswith('.py') for p, _ in items)
    slog = (out / 'static-server.log').open('w')
    try:
        if uses_static:
            try:
                srv = start_server(a.port, slog)
            except RuntimeError as e:
                print('INFRA', e)
                return 3
        for i, (p, e) in enumerate(items):
            if a.budget and time.monotonic() - t_start > a.budget:
                rows += [{'test': q, 'env': f, 'verdict': 'NOT_RUN', 'exit': None, 'seconds': 0} for q, f in items[i:]]
                code_out = 5
                break
            print('[%d/%d] %s %s' % (i + 1, len(items), p, e or ''), flush=True)
            r = run_one(p, e, a.timeout, out, a.port)
            if r['verdict'] == 'FAIL' and a.rerun_failed:
                r2 = run_one(p, e, a.timeout, out, a.port, '.rerun')
                r['rerun'] = {'verdict': r2['verdict'], 'seconds': r2['seconds'], 'note': 'diagnostic only; the first result stands'}
            rows.append(r)
            print('   ->', r['verdict'], r['seconds'], 's', ('rerun:' + r['rerun']['verdict']) if 'rerun' in r else '', flush=True)
            if r['verdict'] == 'FAIL':
                code_out = code_out or 1
                if a.fail_fast:
                    rows += [{'test': q, 'env': f, 'verdict': 'NOT_RUN', 'exit': None, 'seconds': 0} for q, f in items[i + 1:]]
                    break
    finally:
        kill(srv)
        slog.close()
    write(out, rows, a)
    return code_out


def write(out, rows, a):
    n = {k: sum(r['verdict'] == k for r in rows) for k in ('PASS', 'FAIL', 'MISSING', 'NOT_RUN')}
    (out / 'results.json').write_text(json.dumps({'counts': n, 'results': rows}, ensure_ascii=False, indent=1))
    md = ['## CI tier result', '', 'PASS %(PASS)d / FAIL %(FAIL)d / MISSING %(MISSING)d / NOT_RUN %(NOT_RUN)d' % n, '', '| test | env | verdict | s | tb-warn | first failing lines |', '|---|---|---|---:|---:|---|']
    for r in rows:
        md.append('| `%s` | %s | **%s** | %s | %s | %s |' % (r['test'], ' '.join('%s=%s' % kv for kv in r.get('env', {}).items()), r['verdict'], r['seconds'], r.get('traceback_warnings', ''), '<br>'.join(l[:110] for l in r.get('fail_lines', [])[:3])))
    (out / 'summary.md').write_text('\n'.join(md) + '\n')
    (out / 'results.tsv').write_text('test\tenv\tverdict\tseconds\n' + ''.join('%s\t%s\t%s\t%s\n' % (r['test'], ' '.join('%s=%s' % kv for kv in r.get('env', {}).items()), r['verdict'], r['seconds']) for r in rows))
    print((out / 'summary.md').read_text())


if __name__ == '__main__':
    sys.exit(main())
