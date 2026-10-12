#!/usr/bin/env python3
"""Own one HTTP server for sequential, unchanged browser tests on a private port."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import socket
import subprocess
import sys
import time
import urllib.request
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[2]
TESTS = ['tests/system/equipment_test.py', 'tests/system/equipment_ui_flow_test.py',
         'tests/moss/m18_moss_scenario.py', 'tests/moss/m20_sword_equipment.py', 'tests/moss/m21_wind_dance.py']


def child(path, port):
    from playwright.sync_api import BrowserType, Page
    launch = BrowserType.launch
    goto = Page.goto
    def browser_launch(self, *args, **kwargs):
        if self.name == 'chromium':
            kwargs.setdefault('executable_path', os.environ.get('PW_CHROMIUM_EXECUTABLE', '/usr/bin/chromium'))
        return launch(self, *args, **kwargs)
    def page_goto(self, url, *args, **kwargs):
        parts = urlsplit(url)
        if parts.hostname in ('localhost', '127.0.0.1') and parts.port == 8765:
            url = urlunsplit((parts.scheme, '127.0.0.1:'+str(port), parts.path, parts.query, parts.fragment))
        return goto(self, url, *args, **kwargs)
    BrowserType.launch = browser_launch
    Page.goto = page_goto
    sys.argv = [str(ROOT/path)]
    sys.path.insert(0, str((ROOT/path).parent))
    runpy.run_path(str(ROOT/path), run_name='__main__')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8783)
    parser.add_argument('--out', type=Path, default=ROOT/'docs/qa/night-verify-20261013')
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--child')
    parser.add_argument('--independent', action='store_true')
    parser.add_argument('--independent-only', action='store_true')
    args = parser.parse_args()
    if args.child:
        child(args.child, args.port); return
    out = args.out.resolve(); out.mkdir(parents=True, exist_ok=True)
    # Fail rather than connecting to another worker's server.
    with socket.socket() as check:
        check.bind(('127.0.0.1', args.port))
    results = []
    tests = ['tools/qa/night_verify_sword.py'] if args.independent_only else TESTS + (['tools/qa/night_verify_sword.py'] if args.independent else [])
    with (out/'server.log').open('w') as log:
        server = subprocess.Popen([sys.executable, '-m', 'http.server', str(args.port), '--bind', '127.0.0.1'], cwd=ROOT, stdout=log, stderr=log)
        try:
            ready = False
            for _ in range(100):
                if server.poll() is not None:
                    raise RuntimeError('Owned server exited before readiness')
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/index.html', timeout=.5) as response:
                        ready = response.status == 200
                    if ready: break
                except OSError:
                    time.sleep(.1)
            if not ready: raise RuntimeError('Owned server readiness timeout')
            for test in tests:
                path = ROOT/test
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                env = dict(os.environ, PORT=str(args.port), OUT=str(out/'screenshots'), NIGHT_OUT=str(out))
                started = time.monotonic(); logfile = out/(test.replace('/', '_')+'.log')
                print('RUN '+test, flush=True)
                with logfile.open('w') as output:
                    proc = subprocess.Popen([sys.executable, '-u', str(Path(__file__).resolve()), '--port', str(args.port), '--child', test], cwd=ROOT, env=env, stdout=output, stderr=output, start_new_session=True)
                    try:
                        code = proc.wait(timeout=args.timeout)
                    except subprocess.TimeoutExpired:
                        import signal
                        os.killpg(proc.pid, signal.SIGTERM)
                        try: proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid, signal.SIGKILL); proc.wait()
                        code = 124
                text = logfile.read_text()
                failures = [line for line in text.splitlines() if line.startswith('FAIL ')]
                # m18 historically prints failures but exits zero; retain raw exit and report separately.
                declared = [int(n) for n in re.findall(r'^FAILS\s+(\d+)\s*$', text, re.MULTILINE)]
                status = 'PASS' if code == 0 and not failures and not any(declared) else 'FAIL'
                healthy = server.poll() is None
                if healthy:
                    try:
                        with urllib.request.urlopen(f'http://127.0.0.1:{args.port}/index.html', timeout=2) as response:
                            healthy = response.status == 200
                    except OSError: healthy = False
                result = {'test': test, 'sha256_before': digest, 'sha256_after': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'exit_code': code, 'seconds': round(time.monotonic()-started, 3), 'status': status,
                          'reported_fails': declared, 'failure_lines': failures, 'server_alive_after': healthy, 'log': logfile.name}
                results.append(result)
                print(f"{status} {test} exit={code} seconds={result['seconds']} fails={len(failures)} server={healthy}", flush=True)
                for line in failures: print(line, flush=True)
                (out/'test-results.json').write_text(json.dumps({'source_commit': 'be6af1f', 'checkout_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), 'port': args.port, 'tests': results}, ensure_ascii=False, indent=2)+'\n')
                if not healthy: raise RuntimeError('Owned server died; remaining tests not run')
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill(); server.wait()
    print('Finished sequential tests; owned server stopped.', flush=True)
    sys.exit(1 if any(r['status'] != 'PASS' for r in results) else 0)


if __name__ == '__main__':
    main()
