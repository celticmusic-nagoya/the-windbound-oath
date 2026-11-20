#!/usr/bin/env python3
"""Bounded, offline QA using audited existing tests; never repair or retry."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from run_regressions import classification

ROOT = Path(__file__).resolve().parents[2]


def check_json():
    paths = subprocess.check_output(
        ['git', 'ls-files', '-z', '--', '*.json'], cwd=ROOT
    ).decode().split('\0')
    failures = []
    for name in filter(None, paths):
        try:
            # Match the strict JSON syntax already consumed by JS JSON.parse.
            json.loads((ROOT / name).read_text(encoding='utf-8'),
                       parse_constant=lambda value: (_ for _ in ()).throw(
                           ValueError('Invalid JSON constant: ' + value)))
        except (OSError, ValueError) as exc:
            failures.append(f'FAIL {name}: {exc}')
    print('\n'.join(failures) if failures else f'PASS tracked JSON syntax ({len(paths)-1} files)')
    return bool(failures)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=Path('/tmp/windbound-nightly-qa'))
    parser.add_argument('--json-only', action='store_true')
    args = parser.parse_args()
    if args.json_only:
        return check_json()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    tests = json.loads((ROOT / 'tools/qa/nightly-tests.json').read_text())
    commands = [('json-syntax', [sys.executable, str(Path(__file__).resolve()), '--json-only'])]
    commands += [(name, ['node', name]) for name in tests]
    rows = []
    started = time.monotonic()
    metadata = {'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
                'node': subprocess.check_output(['node', '--version']).decode().strip(),
                'python': sys.version.split()[0], 'run_id': os.environ.get('GITHUB_RUN_ID'),
                'run_attempt': os.environ.get('GITHUB_RUN_ATTEMPT'), 'retries': 0}

    def report():
        (out / 'results.json').write_text(json.dumps({**metadata, 'results': rows}, indent=2) + '\n')
        lines = ['# Nightly QA', '', f"Source: `{metadata['source_head']}`", '',
                 'One attempt per check; no automated fixes. Failure excerpts are observations, not an AI diagnosis.', '',
                 '| Check | Result | Exit | Seconds | Log |', '|---|---|---|---|---|']
        for row in rows:
            lines.append(f"| {row['check']} | {row['status']} | {row['exit_code']} | {row['seconds']} | {row['log']} |")
        for row in rows:
            if row['status'] != 'PASS':
                lines += ['', '## ' + row['check'], '', '```text', row['cause'], '```']
        (out / 'report.md').write_text('\n'.join(lines) + '\n')

    report()
    for index, (name, command) in enumerate(commands):
        log = out / f'{index:02d}.log'
        before = time.monotonic()
        remaining = 300 - (before - started)
        code, cause = 125, ''
        if remaining <= 0:
            output = 'NOT_RUN: suite exceeded 300-second budget\n'
        else:
            try:
                with log.open('w') as stream:
                    result = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                            timeout=min(20, remaining), check=False)
                code = result.returncode
                output = log.read_text(errors='replace')
            except subprocess.TimeoutExpired:
                code, cause = 124, 'TIMEOUT: per-check or suite time budget exceeded'
                output = log.read_text(errors='replace') + '\n' + cause + '\n'
            except OSError as exc:
                output = cause = str(exc)
        log.write_text(output)
        category, failures, counts = classification(name, code, output)
        passed = category == '合格'
        rows.append({'check': name, 'command': command, 'status': 'PASS' if passed else 'FAIL',
                     'exit_code': code, 'seconds': round(time.monotonic() - before, 3), 'log': log.name,
                     'cause': '' if passed else cause or '\n'.join(failures) or output[-6000:]})
        report()
        print(f"{rows[-1]['status']} {name} (exit {code})", flush=True)
    return int(any(row['status'] != 'PASS' for row in rows))


if __name__ == '__main__':
    sys.exit(main())
