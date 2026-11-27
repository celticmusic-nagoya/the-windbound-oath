"""Restore the exact preserved face checkpoint using the existing private Release transport."""
import hashlib
import io
import json
import os
import subprocess
import sys
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


def restore(api, token, stage=lambda _: None):
    require(bool(token), 'private read credential required')
    stage('PRIVATE_REPO_METADATA')
    repo = api(token, 'GET', BASE)
    require(repo.get('full_name') == DEST and repo.get('private') is True, 'destination privacy')
    stage('PRIVATE_RELEASE_METADATA')
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
    stage('PRIVATE_ARCHIVE_DOWNLOAD')
    raw = api(token, 'GET', BASE + f'/releases/assets/{ASSET_ID}', binary=True, limit=ARCHIVE_BYTES)
    stage('ARCHIVE_NATIVE_INTEGRITY')
    return read_native(raw)


def main(stage=lambda _: None, *, source='private_release'):
    # Alternate source is an explicit reviewed caller choice; no fallback.
    require(source in ('private_release', 'actions_artifact'), 'unknown restore source')
    stage('WORKER_IDENTITY')
    from release_transport import request
    from morwen_transfer_claim import verify
    env = os.environ
    require(env.get('GITHUB_REPOSITORY') == 'celticmusic-nagoya/the-windbound-oath' and
            env.get('GITHUB_REF') == 'refs/heads/main' and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
            env.get('GITHUB_RUN_ATTEMPT') == '1' and env.get('GITHUB_ACTOR_ID') == '41898282' and
            env.get('MORWEN_PRIVATE_TRANSFER_APPROVED') == 'true', 'worker identity')
    require(bool(env.get('DEST_TOKEN')), 'private read credential required')
    def fence():
        verify('origin', env['TRANSFER_ASSET'], env['MORWEN_BOUND_FENCE'], env['GITHUB_SHA'],
               env['REQUEST_ID'], env['GITHUB_RUN_ID'], env['GITHUB_RUN_ATTEMPT'])
    stage('DISPOSABLE_TARGET_PREFLIGHT')
    root = Path(env['RUNNER_TEMP']).resolve(strict=True)
    target = root / 'Morwen-resume.vroid'
    require(not os.path.lexists(target), 'existing native output')
    stage('FENCE_BEFORE_RESTORE')
    fence()
    if source == 'private_release':
        native = restore(request, env['DEST_TOKEN'], stage)
    else:
        from restore_morwen_artifact_preflight import load, bounded_gh
        require(bool(env.get('GH_TOKEN')), 'artifact read credential required')
        native = load(lambda p: json.loads(bounded_gh(p, 2 * 1024 * 1024, 30)),
                      lambda p, n: bounded_gh(p, n, 90), stage=stage)
    require(sha(native) == NATIVE_SHA, 'verified native identity before save')
    stage('FENCE_BEFORE_LOCAL_SAVE')
    fence()
    stage('LOCAL_EXCLUSIVE_SAVE')
    os.umask(0o077)
    with target.open('xb') as output:
        output.write(native)
        output.flush()
        os.fsync(output.fileno())
    stage('LOCAL_SAVE_READBACK')
    require(sha(target.read_bytes()) == NATIVE_SHA, 'restore readback')
    stage('FENCE_AFTER_LOCAL_SAVE')
    fence()


if __name__ == '__main__':
    current = ['STARTUP']
    def stage(name):
        current[0] = name
        print('PRIVATE_CHECKPOINT_STAGE', name, flush=True)
    try:
        args = sys.argv[1:]
        require(not args or (len(args) == 2 and args[0] == '--source' and args[1] in ('private_release', 'actions_artifact')), 'invalid explicit restore source')
        main(stage, source=args[1] if args else 'private_release')
    except Exception as exc:
        from release_transport import TransportError
        # Never print exception text, URL, environment, raw output or secrets.
        if isinstance(exc, (TimeoutError, subprocess.TimeoutExpired)):
            kind = 'TIMEOUT'
        elif isinstance(exc, subprocess.CalledProcessError):
            kind = 'GIT_COMMAND_FAILED'
        elif isinstance(exc, TransportError):
            kind = 'TRANSPORT_HTTP_' + str(exc.status)
        elif isinstance(exc, (ValueError, KeyError, zipfile.BadZipFile)):
            kind = 'VALIDATION_FAILED'
        elif isinstance(exc, OSError):
            kind = 'LOCAL_IO_FAILED'
        elif isinstance(exc, RuntimeError):
            kind = 'FENCE_OR_RUNTIME_FAILED'
        else:
            kind = 'UNCLASSIFIED'
        print('PRIVATE_CHECKPOINT_RESTORE_BLOCKED_NO_RETRY', current[0], kind, flush=True)
        raise SystemExit(1) from None
    print('PRIVATE_CHECKPOINT_RESTORE_VERIFIED')
