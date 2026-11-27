"""Pack already-reviewed image bytes for transfer, not publication."""
import argparse, hashlib, io, json, os, re, stat, tempfile, zipfile
from pathlib import Path, PurePosixPath

MAX_IMAGE = 8 * 1024**2
MAX_TOTAL = 32 * 1024**2
MAX_ARCHIVE = 512 * 1024**2
HEX = re.compile(r'[0-9a-f]{64}\Z')
HEAD = re.compile(r'[0-9a-f]{40}\Z')
REPO = 'celticmusic-nagoya/the-windbound-oath'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def valid_name(name):
    return (isinstance(name, str) and 0 < len(name) <= 240
            and all(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', p) for p in name.split('/'))
            and PurePosixPath(name).suffix.lower() in ('.png', '.jpg', '.jpeg'))

def pack(source, spec, output):
    source, output = Path(source), Path(output)
    if source.is_symlink() or output.exists() or output.is_symlink():
        raise ValueError('unsafe source or output already exists')
    if spec.get('repository') != REPO or type(spec.get('pr')) is not int or spec['pr'] < 1 or not HEAD.fullmatch(spec.get('head', '')):
        raise ValueError('invalid provenance')
    if spec.get('content_reviewed') is not True or spec.get('rights_reviewed') is not True:
        raise ValueError('explicit review record required')
    for key in ('stage', 'review_ref', 'rights_note'):
        if not isinstance(spec.get(key), str) or not spec[key].strip() or len(spec[key]) > 1000:
            raise ValueError('missing review record: '+key)
    if spec.get('g2') not in ('PASS', 'HOLD', 'FAIL', 'NOT_RUN') or spec.get('adoption') not in ('NOT_ADOPTED', 'UNDETERMINED', 'ADOPTED'):
        raise ValueError('invalid state')
    pins = spec.get('entry_sha256')
    if not isinstance(pins, dict) or not 1 <= len(pins) <= 24 or not all(valid_name(n) and isinstance(h, str) and HEX.fullmatch(h) for n,h in pins.items()):
        raise ValueError('invalid image selection')
    if len(set(pins.values())) != len(pins):
        raise ValueError('duplicate image bytes')
    data = {}
    archive = None
    try:
        if source.is_dir():
            if 'archive_sha256' in spec or 'artifact_id' in spec or 'run_id' in spec:
                raise ValueError('directory cannot claim archive provenance')
        else:
            if not source.is_file() or not 0 < source.stat().st_size <= MAX_ARCHIVE:
                raise ValueError('invalid archive size')
            if any(type(spec.get(k)) is not int or spec[k] <= 0 for k in ('artifact_id','run_id')):
                raise ValueError('missing archive IDs')
            with source.open('rb') as f:
                archive_sha = hashlib.file_digest(f, 'sha256').hexdigest()
            if archive_sha != spec.get('archive_sha256') or source.stat().st_size != spec.get('archive_bytes'):
                raise ValueError('archive mismatch')
            archive = zipfile.ZipFile(source)
        total = 0
        for name, expected in sorted(pins.items()):
            if archive is not None:
                matches = [i for i in archive.infolist() if i.filename == name]
                if len(matches) != 1:
                    raise ValueError('missing or ambiguous exact entry: '+name)
                i = matches[0]
                if i.is_dir() or i.flag_bits & 1 or stat.S_ISLNK(i.external_attr >> 16) or not 0 < i.file_size <= MAX_IMAGE:
                    raise ValueError('unsupported entry: '+name)
                with archive.open(i) as f:
                    raw = f.read(MAX_IMAGE+1)
                if len(raw) != i.file_size:
                    raise ValueError('entry length mismatch')
            else:
                p = source / name
                if any((source.joinpath(*PurePosixPath(name).parts[:j])).is_symlink() for j in range(1,len(PurePosixPath(name).parts)+1)) or not p.is_file() or not 0 < p.stat().st_size <= MAX_IMAGE:
                    raise ValueError('invalid local image: '+name)
                with p.open('rb') as f:
                    raw = f.read(MAX_IMAGE+1)
            total += len(raw)
            if not 0 < len(raw) <= MAX_IMAGE or total > MAX_TOTAL or digest(raw) != expected:
                raise ValueError('image size or SHA mismatch: '+name)
            signature = b'\x89PNG\r\n\x1a\n' if name.lower().endswith('.png') else b'\xff\xd8\xff'
            if not raw.startswith(signature):
                raise ValueError('image signature mismatch: '+name)
            data[name] = raw
    finally:
        if archive is not None:
            archive.close()
    receipt = {'schema':'two.studio.review_image_handoff.v2','transport_only':True,
               'publication_authorized_by_tool':False,
               'source':{k:spec[k] for k in ('repository','pr','head','run_id','artifact_id','archive_sha256','archive_bytes') if k in spec},
               'stage':spec['stage'],'g2':spec['g2'],'adoption':spec['adoption'],
               'review_ref':spec['review_ref'],'rights_note':spec['rights_note'],
               'entries':[{'name':n,'sha256':pins[n],'bytes':len(b)} for n,b in data.items()]}
    data['receipt.json'] = (json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    data['SHA256SUMS.txt'] = ''.join(f'{digest(b)}  {n}\n' for n,b in sorted(data.items())).encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp = tempfile.mkstemp(dir=output.parent,prefix='.review-')
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for n,b in sorted(data.items()):
                info = zipfile.ZipInfo(n, (1980,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(info,b)
        with zipfile.ZipFile(tmp) as z:
            if z.testzip() is not None or set(z.namelist()) != set(data) or any(z.read(n)!=b for n,b in data.items()):
                raise ValueError('output readback mismatch')
        os.link(tmp,output)  # exclusive, no overwrite
    finally:
        os.unlink(tmp)
    with output.open('rb') as f:
        return {'images':len(pins),'bytes':output.stat().st_size,'sha256':hashlib.file_digest(f,'sha256').hexdigest()}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('spec',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args()
    print(json.dumps(pack(args.source,json.loads(args.spec.read_text()),args.output)))

if __name__=='__main__':
    main()
