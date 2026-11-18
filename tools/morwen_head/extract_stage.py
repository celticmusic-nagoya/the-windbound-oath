"""Extract exact handoff stage and small evidence files; never execute ZIP content."""
import hashlib
import json
import pathlib
import sys
import zipfile

src, out = map(pathlib.Path, sys.argv[1:])
records = []
with zipfile.ZipFile(src) as archive:
    total = 0
    for info in archive.infolist():
        parts = pathlib.PurePosixPath(info.filename).parts
        if '..' in parts or info.filename.startswith('/') or '\\' in info.filename:
            raise ValueError('unsafe ZIP path')
        total += info.file_size
        if total > 500_000_000:
            raise ValueError('archive too large')
        records.append({'path': info.filename, 'bytes': info.file_size})
        name = pathlib.PurePosixPath(info.filename).name
        if name == 'morwen_head_landmark_review_UNAPPROVED.blend':
            dest = out / 'stage' / name
        elif info.filename.endswith('.json') and info.file_size < 5_000_000:
            dest = out / 'evidence' / info.filename
        else:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(archive.read(info))
        records[-1]['sha256'] = hashlib.sha256(dest.read_bytes()).hexdigest()
    assert len(list((out/'stage').glob('*.blend'))) == 1
(out/'evidence'/'recovery_archive_inventory.json').write_text(json.dumps({
    'source_artifact': 14298561244,
    'zip_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
    'entries': records,
}, indent=2)+'\n')
