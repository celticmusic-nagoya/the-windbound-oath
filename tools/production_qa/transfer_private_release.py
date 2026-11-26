"""VRM candidate transport via the existing private handoff REST transport.
Call only from the reviewed, protected transfer stage. No public artifact.
"""
import hashlib
import io
import json
import re
import struct
import zipfile
from pathlib import Path
import os
import sys

DEST = 'celticmusic-nagoya/the-windbound-oath-handoff'
BASE = 'https://api.github.com/repos/' + DEST
SOURCE = 'acc7805b6a5b63913bccb7c28e30e1c9e4da6473ed083b5c0673f73cdca9e23a'
CAP = 128 * 1024 * 1024
DIAGNOSTIC_CAP = 2 * 1024 * 1024
NAMES = {'Morwen-transfer.vrm', 'transfer-receipt.json', 'SHA256SUMS.json',
         *('views/'+v+'.png' for v in ('front','left4','left8','right4'))}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def package(raw, expected_source=SOURCE):
    require(0 < len(raw) <= CAP, 'package size')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        require(len(infos) == len(NAMES) and set(z.namelist()) == NAMES, 'package inventory')
        require(sum(i.file_size for i in infos) <= CAP and all(i.external_attr >> 16 == 0o100600 and not i.flag_bits & 1 for i in infos), 'package member safety')
        require(z.testzip() is None, 'package CRC')
        manifest = json.loads(z.read('SHA256SUMS.json'))
        require(set(manifest) == NAMES - {'SHA256SUMS.json'}, 'manifest inventory')
        require(all(sha(z.read(n)) == v for n,v in manifest.items()), 'member digest mismatch')
        receipt = json.loads(z.read('transfer-receipt.json'))
        require(receipt.get('scope') == 'PRIVATE_TRANSFER_CANDIDATE_REVIEW_REQUIRED' and receipt.get('native_sha256') == expected_source, 'source binding')
        require(receipt.get('vrm_structure', {}).get('version') == '1.0' and receipt.get('vrm_sha256') == manifest['Morwen-transfer.vrm'], 'VRM binding')
        require(receipt.get('capture_sha256') == {v:manifest['views/'+v+'.png'] for v in ('front','left4','left8','right4')}, 'capture binding')
    return receipt


def transfer(raw, token, run_id, revision, request_id, api, *, expected_source=SOURCE):
    """api is the existing bounded HTTPS request function; no retries or overwrite."""
    package(raw, expected_source)
    return publish_package(raw, token, run_id, revision, request_id, api, kind='vrm')


def metadata_diagnostic(raw):
    require(0 < len(raw) <= DIAGNOSTIC_CAP, 'diagnostic size')
    expected = {'diagnostic.json', 'dialog.png', 'dialog.txt'}
    field_files = {'field.png', 'field.txt'}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)) and set(names) in (expected, expected | field_files),
                'diagnostic inventory')
        require(sum(i.file_size for i in archive.infolist()) <= DIAGNOSTIC_CAP
                and archive.testzip() is None, 'diagnostic integrity')
        receipt = json.loads(archive.read('diagnostic.json'))
        require(receipt.get('source_sha256') == SOURCE
                and receipt.get('field') in ('name', 'version', 'creator')
                and receipt.get('phase') in ('before', 'after'), 'diagnostic source or stage')
        for name, size in [('dialog.png', (510, 610)), ('field.png', (476, 46 if receipt['field'] == 'creator' else 44))]:
            if name in names:
                header = archive.read(name)[:24]
                require(header[:16] == b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
                        and struct.unpack('>II', header[16:]) == size, 'diagnostic crop dimensions')


def publish_package(raw, token, run_id, revision, request_id, api, *, kind):
    """Transport only; caller must validate the exact package before invoking."""
    require(bool(token) and all(re.fullmatch(r'[1-9][0-9]{0,19}', v) for v in (run_id, request_id)) and re.fullmatch(r'[0-9a-f]{40}',revision), 'identity')
    require(0 < len(raw) <= CAP and kind in ('vrm', 'blend', 'metadata-diagnostic'), 'package size or kind')
    digest = sha(raw)
    prefix, name = {
        'vrm': ('morwen-transfer-run-', 'Morwen-transfer.zip'),
        'blend': ('morwen-blender-run-', 'Morwen-blender.zip'),
        'metadata-diagnostic': ('morwen-metadata-diagnostic-run-', 'Morwen-metadata-diagnostic.zip'),
    }[kind]
    tag = prefix + run_id
    repo = api(token,'GET',BASE)
    require(repo.get('full_name') == DEST and repo.get('private') is True, 'destination not private')
    ref = api(token,'GET',BASE+'/git/ref/heads/main')
    target = ref.get('object',{}).get('sha','')
    require(ref.get('ref') == 'refs/heads/main' and ref.get('object',{}).get('type') == 'commit' and re.fullmatch(r'[0-9a-f]{40}',target), 'destination revision')
    # Include drafts: release-by-tag may not resolve an unpublished draft.
    # A bounded list must prove absence before any write.
    for page in range(1, 21):
        rows = api(token,'GET',BASE+f'/releases?per_page=100&page={page}')
        require(isinstance(rows,list) and len(rows)<=100, 'release listing invalid')
        require(not any(row.get('tag_name')==tag for row in rows), 'destination draft or release exists')
        if len(rows)<100:
            break
    else:
        raise ValueError('release inventory not fully verified')
    # A failed attempt is reconciled manually, never retried with another tag.
    from release_transport import TransportError
    for endpoint in ('/releases/tags/'+tag, '/git/ref/tags/'+tag):
        try:
            api(token,'GET',BASE+endpoint)
        except TransportError as exc:
            require(exc.status == 404, 'absence not confirmed')
        else:
            raise ValueError('destination already exists')
    notes = f'Private candidate, NOT_ADOPTED. Run {run_id}; request {request_id}; source revision {revision}; ZIP SHA256 {digest}.'
    body = dict(tag_name=tag,target_commitish=target,name=tag,body=notes,draft=True,prerelease=True,make_latest='false')
    rel = api(token,'POST',BASE+'/releases',json.dumps(body).encode())
    rid = rel.get('id')
    require(type(rid) is int and rid>0 and rel.get('tag_name')==tag and rel.get('draft') is True, 'draft creation receipt')
    upload = 'https://uploads.github.com/repos/'+DEST+f'/releases/{rid}/assets?name={name}'
    asset = api(token,'POST',upload,raw,'application/zip')
    aid = asset.get('id')
    require(type(aid) is int and aid>0 and asset.get('name')==name and asset.get('state')=='uploaded' and asset.get('size')==len(raw) and asset.get('digest')=='sha256:'+digest, 'asset receipt')
    asset_url = BASE+f'/releases/assets/{aid}'
    require(api(token,'GET',asset_url,binary=True,limit=len(raw)) == raw, 'draft readback mismatch')
    rel = api(token,'PATCH',BASE+f'/releases/{rid}',json.dumps(dict(draft=False,prerelease=True,make_latest='false')).encode())
    require(rel.get('id')==rid and rel.get('tag_name')==tag and rel.get('draft') is False and rel.get('prerelease') is True, 'private prerelease receipt')
    require(api(token,'GET',asset_url,binary=True,limit=len(raw)) == raw, 'final readback mismatch')
    return dict(scope='PRIVATE_CANDIDATE_READBACK_VERIFIED',release_id=rid,asset_id=aid,sha256=digest,bytes=len(raw),run_id=run_id,request_id=request_id,adoption='NOT_ADOPTED')


def main():
    """Only the separately approved protected stage may invoke this CLI."""
    from release_transport import request
    from morwen_transfer_claim import verify
    env = os.environ
    require(env.get('MORWEN_PRIVATE_TRANSFER_APPROVED') == 'true'
            and env.get('GITHUB_REPOSITORY') == 'celticmusic-nagoya/the-windbound-oath'
            and env.get('GITHUB_REF') == 'refs/heads/main'
            and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch'
            and env.get('GITHUB_RUN_ATTEMPT') == '1'
            and env.get('GITHUB_ACTOR_ID') == '41898282', 'protected stage identity')
    args = sys.argv[1:]
    diagnostic = args[:1] == ['--metadata-diagnostic']
    if diagnostic:
        args = args[1:]
    require(len(args) == 2, 'usage: transfer_private_release.py [--metadata-diagnostic] PACKAGE NEW_RECEIPT')
    path, receipt = map(Path, args)
    require(path.is_file() and not path.is_symlink() and path.parent.stat().st_mode & 0o077 == 0
            and receipt.parent.resolve() == path.parent.resolve() and not os.path.lexists(receipt), 'private input/output')
    def fence():
        verify('origin',env['TRANSFER_ASSET'],env['MORWEN_BOUND_FENCE'],env['GITHUB_SHA'],
               env['REQUEST_ID'],env['GITHUB_RUN_ID'],env['GITHUB_RUN_ATTEMPT'])
    fence()
    def guarded_api(token,method,url,*args,**kwargs):
        if method in ('POST','PATCH'):
            fence()
        return request(token,method,url,*args,**kwargs)
    raw = path.read_bytes()
    identity = (env['DEST_TOKEN'], env['GITHUB_RUN_ID'], env['GITHUB_SHA'], env['REQUEST_ID'], guarded_api)
    if diagnostic:
        metadata_diagnostic(raw)
        result = publish_package(raw, *identity, kind='metadata-diagnostic')
    else:
        result = transfer(raw, *identity)
    fence()
    with receipt.open('x',encoding='utf-8') as f:
        json.dump(result,f,indent=2)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        # Never put private URLs, credentials, paths or response bodies in public logs.
        print('PRIVATE_TRANSFER_BLOCKED_RECONCILE_NO_RETRY')
        raise SystemExit(1) from None
    print('PRIVATE_TRANSFER_READBACK_VERIFIED')
