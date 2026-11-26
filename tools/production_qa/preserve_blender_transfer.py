"""Pack and preserve the actual Blender output through the existing private Release transport."""
import io
import json
import os
from pathlib import Path
import re
import struct
import sys
import zipfile
import zlib

from transfer_private_release import CAP, SOURCE, publish_package, require, sha

VIEWS = ('minus-y', 'plus-x', 'plus-y', 'minus-x')


def png_ok(raw):
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        return False
    offset = 8
    count = 0
    idat = False
    while offset + 12 <= len(raw):
        length, kind = struct.unpack_from('>I4s', raw, offset)
        end = offset + 12 + length
        if end > len(raw):
            return False
        data = raw[offset+8:end-4]
        if zlib.crc32(kind + data) != struct.unpack_from('>I', raw, end-4)[0]:
            return False
        if count == 0 and (kind != b'IHDR' or length != 13 or struct.unpack_from('>II', data) != (1024,1024)):
            return False
        if kind == b'IDAT':
            idat = True
        if kind == b'IEND':
            return length == 0 and end == len(raw) and idat
        offset = end
        count += 1
    return False


def read_regular(path):
    require(path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= CAP, 'unsafe member')
    return path.read_bytes()


def build(source, root, run, request, revision, archive_sha):
    require(root.is_dir() and not root.is_symlink() and root.stat().st_mode & 0o077 == 0, 'private root')
    require(source.is_dir() and not source.is_symlink() and source.stat().st_mode & 0o077 == 0, 'private input')
    require(all(re.fullmatch(r'[1-9][0-9]{0,19}', v) for v in (run,request)) and
            re.fullmatch(r'[0-9a-f]{40}',revision) and re.fullmatch(r'[0-9a-f]{64}',archive_sha), 'identity')
    native_receipt = read_regular(source/'input-receipt.json')
    receipt = json.loads(native_receipt)
    vrm = read_regular(source/'Morwen-transfer.vrm')
    require(receipt['scope'] == 'PRIVATE_VRM_INPUT_VERIFIED_NOT_IMPORTED' and
            receipt['native_sha256'] == SOURCE and receipt['run_id'] == run and receipt['request_id'] == request and
            receipt['revision'] == revision and receipt['archive_sha256'] == archive_sha and receipt['vrm_sha256'] == sha(vrm), 'input binding')
    result = read_regular(root/'transfer-receipt.json')
    report = json.loads(result)
    blend = read_regular(root/'Morwen-transfer.blend')
    require(report['scope'] == 'STRUCTURAL_IMPORT_AND_REOPEN_NOT_ART_ACCEPTANCE' and
            report['blender'] == '5.3.0' and report['addon'] == '4.10.5' and report['vrm_sha256'] == sha(vrm) and
            report['blend_sha256'] == sha(blend), 'Blender receipt binding')
    inventory = report['saved_and_reopened']
    require(all(inventory.get(k) for k in ('meshes','armatures','images')), 'empty inventory')
    files = {'Morwen-transfer.blend': blend, 'input-receipt.json': native_receipt, 'transfer-receipt.json': result}
    views = root/'views'
    require(views.is_dir() and not views.is_symlink(), 'views directory')
    for name in VIEWS:
        raw = read_regular(views/(name+'.png'))
        require(png_ok(raw), 'invalid render PNG')
        files['views/'+name+'.png'] = raw
    require(len({sha(files['views/'+v+'.png']) for v in VIEWS}) == 4, 'duplicate render')
    files['SHA256SUMS.json'] = (json.dumps({k:sha(v) for k,v in files.items()},sort_keys=True,indent=2)+'\n').encode()
    require(sum(map(len,files.values())) <= CAP, 'uncompressed package budget')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name, raw in files.items():
            info = zipfile.ZipInfo(name,(2026,1,1,0,0,0))
            info.external_attr = 0o100600 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info,raw)
    data = buf.getvalue()
    require(len(data) <= CAP, 'compressed package budget')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        require(z.testzip() is None and set(z.namelist()) == set(files) and all(z.read(k)==v for k,v in files.items()), 'ZIP readback')
    return data


def main():
    from release_transport import request as api
    from morwen_transfer_claim import verify
    env = os.environ
    require(env.get('MORWEN_PRIVATE_TRANSFER_APPROVED') == 'true' and
            env.get('GITHUB_REPOSITORY') == 'celticmusic-nagoya/the-windbound-oath' and
            env.get('GITHUB_REF') == 'refs/heads/main' and env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch' and
            env.get('GITHUB_RUN_ATTEMPT') == '1' and env.get('GITHUB_ACTOR_ID') == '41898282', 'worker identity')
    require(len(sys.argv)==4, 'usage: preserve_blender_transfer.py INPUT OUTPUT PRODUCER_ZIP_SHA')
    source, root = map(Path,sys.argv[1:3])
    temp = Path(env['RUNNER_TEMP']).resolve(strict=True)
    require(source.parent.resolve()==temp and root.parent.resolve()==temp and source!=root, 'private runner paths')
    def fence():
        verify('origin',env['TRANSFER_ASSET'],env['MORWEN_BOUND_FENCE'],env['GITHUB_SHA'],env['REQUEST_ID'],env['GITHUB_RUN_ID'],env['GITHUB_RUN_ATTEMPT'])
    fence()
    data = build(source,root,env['GITHUB_RUN_ID'],env['REQUEST_ID'],env['GITHUB_SHA'],sys.argv[3])
    def guarded(token,method,url,*args,**kwargs):
        fence()
        return api(token,method,url,*args,**kwargs)
    result = publish_package(data,env['DEST_TOKEN'],env['GITHUB_RUN_ID'],env['GITHUB_SHA'],env['REQUEST_ID'],guarded,kind='blend')
    fence()
    result.update(kind='blend', revision=env['GITHUB_SHA'], source_archive_sha256=sys.argv[3])
    with (root/'private-blender-receipt.json').open('x',encoding='utf-8') as output:
        json.dump(result,output,indent=2)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('PRIVATE_BLENDER_PRESERVATION_BLOCKED_RECONCILE_NO_RETRY')
        raise SystemExit(1) from None
    print('PRIVATE_BLENDER_READBACK_VERIFIED_NOT_ADOPTED')
