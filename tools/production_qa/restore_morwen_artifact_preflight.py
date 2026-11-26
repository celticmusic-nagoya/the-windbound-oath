"""Read-only alternate source preflight. No lease acquisition, save or dispatch."""
import datetime as dt
import json
import os
import selectors
import subprocess
import time
from restore_morwen_preserved import ARCHIVE_BYTES, ARCHIVE_SHA, read_native

REPO = 'celticmusic-nagoya/the-windbound-oath'
RID = 1408120919
RUN = 45605491226
ARTIFACT = 15018109141
REV = '6b8d3e00f590df9bd9b5c86758ed3fbc6e652b00'
BASE = 'repos/' + REPO


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def load(api, download, now=None, stage=lambda _: None):
    """Return verified native bytes in memory, only from the pinned historical source."""
    now = now or dt.datetime.now(dt.timezone.utc)
    stage('ARTIFACT_SOURCE_RUN')
    run = api(f'{BASE}/actions/runs/{RUN}')
    need(run.get('id') == RUN and run.get('head_sha') == REV and
         run.get('head_branch') == 'main' and run.get('event') == 'workflow_dispatch' and
         run.get('status') == 'completed' and run.get('conclusion') == 'success' and
         run.get('run_attempt') == 1 and run.get('workflow_id') == 424712879 and
         run.get('path') == '.github/workflows/morwen-vroid-macos-probe.yml' and
         run.get('repository', {}).get('id') == RID and
         run.get('head_repository', {}).get('id') == RID, 'SOURCE_RUN_MISMATCH')
    stage('ARTIFACT_SOURCE_METADATA')
    inventory = api(f'{BASE}/actions/runs/{RUN}/artifacts?per_page=100')
    rows = inventory.get('artifacts')
    need(isinstance(rows, list) and inventory.get('total_count') == len(rows), 'INVENTORY_INCOMPLETE')
    matches = [a for a in rows if a.get('id') == ARTIFACT]
    need(len(matches) == 1, 'ARTIFACT_MISSING_OR_AMBIGUOUS')
    a = matches[0]
    need(a.get('name') == 'morwen-isolated-vroid-reopen-review' and
         a.get('size_in_bytes') == ARCHIVE_BYTES and a.get('digest') == 'sha256:' + ARCHIVE_SHA and
         a.get('expired') is False and a.get('workflow_run') == dict(id=RUN, repository_id=RID,
             head_repository_id=RID, head_branch='main', head_sha=REV), 'ARTIFACT_METADATA_MISMATCH')
    expiry = dt.datetime.fromisoformat(a['expires_at'].replace('Z', '+00:00'))
    need(expiry > now, 'ARTIFACT_EXPIRED')
    stage('ARTIFACT_DOWNLOAD')
    raw = download(f'{BASE}/actions/artifacts/{ARTIFACT}/zip', ARCHIVE_BYTES)
    stage('ARTIFACT_NATIVE_INTEGRITY')
    return read_native(raw)


def bounded_gh(path, cap, timeout):
    """Capture only bounded stdout, never stderr, URL redirects or credentials."""
    deadline = time.monotonic() + timeout
    data = bytearray()
    with subprocess.Popen(['gh', 'api', path], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(proc.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not sel.select(remaining):
                        raise TimeoutError('ARTIFACT_TRANSPORT_TIMEOUT')
                    block = os.read(proc.stdout.fileno(), min(65536, cap + 1 - len(data)))
                    if not block:
                        break
                    data.extend(block)
                    need(len(data) <= cap, 'ARTIFACT_TRANSPORT_SIZE')
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('ARTIFACT_TRANSPORT_TIMEOUT')
            need(proc.wait(timeout=remaining) == 0, 'ARTIFACT_TRANSPORT_FAILED')
            return bytes(data)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


def main():
    # Reuse the already-qualified GH_TOKEN; do not request or print credentials.
    need(bool(os.environ.get('GH_TOKEN')), 'MISSING_EXISTING_CREDENTIAL')
    load(lambda p: json.loads(bounded_gh(p, 2 * 1024 * 1024, 30)),
         lambda p, n: bounded_gh(p, n, 90), stage=lambda s: print(s, flush=True))
    print('ARTIFACT_BYTE_PREFLIGHT_PASS', flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # Fixed exception class only; no private data or subprocess output.
        print('ARTIFACT_BYTE_PREFLIGHT_HOLD', type(exc).__name__, flush=True)
        raise SystemExit(1) from None
