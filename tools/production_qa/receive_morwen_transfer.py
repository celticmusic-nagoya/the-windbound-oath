"""Read a completed Morwen transfer from the existing private Release transport."""
import io
import json
import os
from pathlib import Path
import re
import sys
import zipfile

from transfer_private_release import BASE, DEST, CAP, SOURCE, package, require, sha


def receive(api, token, run, request_id, revision, digest, *, expected_source=SOURCE):
    require(bool(token) and all(re.fullmatch(r'[1-9][0-9]{0,19}', v) for v in (run, request_id))
            and re.fullmatch(r'[0-9a-f]{40}', revision) and re.fullmatch(r'[0-9a-f]{64}', digest), 'identity')
    repo = api(token, 'GET', BASE)
    require(repo.get('full_name') == DEST and repo.get('private') is True, 'destination not private')
    tag = 'morwen-transfer-run-' + run
    rel = api(token, 'GET', BASE + '/releases/tags/' + tag)
    notes = f'Private candidate, NOT_ADOPTED. Run {run}; request {request_id}; source revision {revision}; ZIP SHA256 {digest}.'
    require(type(rel.get('id')) is int and rel['id'] > 0 and rel.get('tag_name') == tag and
            rel.get('draft') is False and rel.get('prerelease') is True and rel.get('body') == notes, 'release binding')
    assets = rel.get('assets', [])
    require(len(assets) == 1, 'asset inventory')
    asset = assets[0]
    aid, size = asset.get('id'), asset.get('size')
    require(type(aid) is int and aid > 0 and type(size) is int and 0 < size <= CAP and
            asset.get('name') == 'Morwen-transfer.zip' and asset.get('state') == 'uploaded' and
            asset.get('digest') == 'sha256:' + digest, 'asset binding')
    raw = api(token, 'GET', BASE + f'/releases/assets/{aid}', binary=True, limit=size)
    require(len(raw) == size and sha(raw) == digest, 'archive digest')
    receipt = package(raw, expected_source)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        vrm = z.read('Morwen-transfer.vrm')
    return vrm, dict(scope='PRIVATE_VRM_INPUT_VERIFIED_NOT_IMPORTED', run_id=run, request_id=request_id,
                     revision=revision, release_id=rel['id'], asset_id=aid, archive_sha256=digest,
                     native_sha256=expected_source, vrm_sha256=receipt['vrm_sha256'])


def main():
    from release_transport import request
    from morwen_transfer_claim import verify
    env = os.environ
    require(env.get('GITHUB_REPOSITORY') == 'celticmusic-nagoya/the-windbound-oath' and
            env.get('GITHUB_REF') == 'refs/heads/main' and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
            env.get('GITHUB_RUN_ATTEMPT') == '1' and env.get('GITHUB_ACTOR_ID') == '41898282' and
            env.get('MORWEN_PRIVATE_TRANSFER_APPROVED') == 'true', 'worker identity')
    require(len(sys.argv) == 3, 'usage: receive_morwen_transfer.py ZIP_SHA NEW_PRIVATE_DIR')
    digest, destination = sys.argv[1:]
    root = Path(env['RUNNER_TEMP']).resolve(strict=True)
    target = Path(destination)
    require(target.is_absolute() and target.parent.resolve(strict=True) == root and not os.path.lexists(target), 'private output')
    def fence():
        verify('origin', env['TRANSFER_ASSET'], env['MORWEN_BOUND_FENCE'], env['GITHUB_SHA'],
               env['REQUEST_ID'], env['GITHUB_RUN_ID'], env['GITHUB_RUN_ATTEMPT'])
    fence()
    vrm, receipt = receive(request, env['DEST_TOKEN'], env['GITHUB_RUN_ID'], env['REQUEST_ID'], env['GITHUB_SHA'], digest)
    fence()
    os.umask(0o077)
    target.mkdir(mode=0o700)
    path = target / 'Morwen-transfer.vrm'
    with path.open('xb') as f:
        f.write(vrm)
        f.flush()
        os.fsync(f.fileno())
    require(sha(path.read_bytes()) == receipt['vrm_sha256'], 'VRM readback')
    with (target / 'input-receipt.json').open('x', encoding='utf-8') as f:
        json.dump(receipt, f, indent=2)
    fence()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('PRIVATE_VRM_RECEIVE_BLOCKED_NO_RETRY')
        raise SystemExit(1) from None
    print('PRIVATE_VRM_RECEIVE_VERIFIED_NOT_IMPORTED')
