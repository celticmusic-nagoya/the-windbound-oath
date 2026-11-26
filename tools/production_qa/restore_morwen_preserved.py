"""Restore the exact preserved face checkpoint using the existing private Release transport."""
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

DEST = 'celticmusic-nagoya/the-windbound-oath-handoff'
BASE = 'https://api.github.com/repos/' + DEST
TAG = 'preserved-artifact-15018109141'
RELEASE_ID = 458656076
ASSET_ID = 793164898
ARCHIVE_BYTES = 11811300
ARCHIVE_SHA = 'b210fb4907d11d24c79a35f58edb689b0958bf34d222b614256dd94e13b19588'
NATIVE_SHA = 'acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a'
PARENT_SHA = '55cf70f24f55577d81ad7a4c54b20abe4d682e7c4c2688c0a87be1dd1125c541'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_native(raw):
    require(len(raw) == ARCHIVE_BYTES and sha(raw) == ARCHIVE_SHA, 'archive identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(archive.testzip() is None, 'archive CRC')
        native = archive.read('face-mouth-candidate-not-adopted.vroid')
        receipt = json.loads(archive.read('mouth-candidate-receipt.json'))
        require(receipt['candidate_sha256'] == sha(native) == NATIVE_SHA and
                receipt['source_sha256'] == PARENT_SHA, 'native lineage')
        require(receipt['scope'] == 'EXPLORATORY_NOT_ADOPTED' and
                receipt['after'] == receipt['reopened'], 'checkpoint reopen receipt')
    with zipfile.ZipFile(io.BytesIO(native)) as original:
        require(original.testzip() is None, 'native CRC')
    return native


def restore(api, token):
    require(bool(token), 'private read credential required')
    repo = api(token, 'GET', BASE)
    require(repo.get('full_name') == DEST and repo.get('private') is True, 'destination privacy')
    release = api(token, 'GET', BASE + '/releases/tags/' + TAG)
    require(release.get('id') == RELEASE_ID and release.get('tag_name') == TAG and
            release.get('draft') is False and release.get('prerelease') is True and
            release.get('target_commitish') == '241760938b0901b95a11ecbe31736ff89ad32661', 'release identity')
    assets = release.get('assets', [])
    require(len(assets) == 1, 'asset inventory')
    asset = assets[0]
    require(asset.get('id') == ASSET_ID and asset.get('name') == '15018109141.zip' and
            asset.get('state') == 'uploaded' and asset.get('size') == ARCHIVE_BYTES and
            asset.get('digest') == 'sha256:' + ARCHIVE_SHA, 'asset identity')
    raw = api(token, 'GET', BASE + f'/releases/assets/{ASSET_ID}', binary=True, limit=ARCHIVE_BYTES)
    return read_native(raw)


def main():
    from release_transport import request
    from morwen_transfer_claim import verify
    env = os.environ
    require(env.get('GITHUB_REPOSITORY') == 'celticmusic-nagoya/the-windbound-oath' and
            env.get('GITHUB_REF') == 'refs/heads/main' and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
            env.get('GITHUB_RUN_ATTEMPT') == '1' and env.get('GITHUB_ACTOR_ID') == '41898282' and
            env.get('MORWEN_PRIVATE_TRANSFER_APPROVED') == 'true', 'worker identity')
    def fence():
        verify('origin', env['TRANSFER_ASSET'], env['MORWEN_BOUND_FENCE'], env['GITHUB_SHA'],
               env['REQUEST_ID'], env['GITHUB_RUN_ID'], env['GITHUB_RUN_ATTEMPT'])
    root = Path(env['RUNNER_TEMP']).resolve(strict=True)
    target = root / 'Morwen-resume.vroid'
    require(not os.path.lexists(target), 'existing native output')
    fence()
    native = restore(request, env['DEST_TOKEN'])
    fence()
    os.umask(0o077)
    with target.open('xb') as output:
        output.write(native)
        output.flush()
        os.fsync(output.fileno())
    require(sha(target.read_bytes()) == NATIVE_SHA, 'restore readback')
    fence()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('PRIVATE_CHECKPOINT_RESTORE_BLOCKED_NO_RETRY')
        raise SystemExit(1) from None
    print('PRIVATE_CHECKPOINT_RESTORE_VERIFIED')
