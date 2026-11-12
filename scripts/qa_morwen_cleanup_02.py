#!/usr/bin/env python3
"""Validate preserved ZIP references, bounded deletion, and runtime asset edges."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

OUT = Path('docs/qa/morwen-canon-cleanup-02')
ROOT = Path('assets/references/morwen/reference_20261112')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-zip', type=Path, required=True)
    args = parser.parse_args()
    reference = json.loads((ROOT/'MANIFEST.json').read_text())
    inventory = json.loads((OUT/'INVENTORY.json').read_text())
    removed = json.loads((OUT/'DELETED_PATHS.json').read_text())
    assert digest(args.source_zip.read_bytes()) == reference['source']['sha256']
    with zipfile.ZipFile(args.source_zip) as archive:
        assert archive.testzip() is None
        assert len([i for i in archive.infolist() if not i.is_dir()]) == 12
        for entry in reference['files']:
            original = archive.read(entry['archiveMember'])
            assert Path(entry['path']).read_bytes() == original
            assert digest(original) == entry['sha256']
    for entry in inventory['entries']:
        path = Path(entry['path'])
        if entry['action'] == 'DELETE':
            assert not path.exists(), path
        else:
            assert digest(path.read_bytes()) == entry.get('afterSha256', entry['sha256']), path
    assert inventory['counts'] == dict(Counter(e['action'] for e in inventory['entries']))
    baseline = inventory['baseline']
    expected_deletions = {e['path'] for e in removed['entries']}
    expected_modifications = {
        'AGENTS.md',
        'assets/candidates/morwen-right-walk/70/art/README_ART70.md',
        'assets/candidates/morwen-right-walk/71/README.md',
    }
    changes = [row.split('\t') for row in git('diff', '--name-status', baseline).decode().splitlines()]
    assert {p for status,p in changes if status == 'D'} == expected_deletions
    assert {p for status,p in changes if status == 'M'} == expected_modifications
    assert all(status in {'A', 'M', 'D'} for status,p in changes)
    for status,path in changes:
        if status == 'A':
            assert (path.startswith(str(ROOT)+'/') or path.startswith(str(OUT)+'/') or
                    path in {'scripts/qa_morwen_cleanup_02.py', 'docs/design/MORWEN_CANONICAL_INDEX.md'}), path
    # Compare literal runtime paths against the baseline's tracked file set.
    # Generated/pre-existing missing edges are reported, not hidden or repaired.
    files = git('ls-tree', '-r', '--name-only', baseline).decode().splitlines()
    tracked = set(files)
    runtime = [p for p in files if
               (p == 'index.html' or p.startswith(('js/', 'css/', 'data/'))) and
               Path(p).suffix in {'.html', '.js', '.css', '.json'}]
    pattern = re.compile(r'\b(?:img|assets|data|js|css)/[\w./-]+\.(?:png|webp|jpe?g|gif|json|js|css|html)')
    before_missing, after_missing = set(), set()
    for source in runtime:
        before = git('show', baseline+':'+source).decode('utf-8', errors='replace')
        after = Path(source).read_text(errors='replace')
        assert before == after, source
        for target in pattern.findall(before):
            if target not in tracked:
                before_missing.add((source,target))
        for target in pattern.findall(after):
            if not Path(target).is_file():
                after_missing.add((source,target))
    new_missing = after_missing-before_missing
    assert not new_missing, new_missing
    result = dict(status='PASS', archiveCRC='PASS', referenceOriginals=12,
                  inventoryEntries=len(inventory['entries']), counts=inventory['counts'],
                  deletedPaths=len(expected_deletions), deletedBytes=removed['bytesRemoved'],
                  runtimeSourceFilesUnchanged=len(runtime), newBrokenRuntimeReferences=len(new_missing),
                  preexistingMissingLiteralEdges=len(before_missing),
                  protectedScope='No runtime, scenario, save, website or other-character file modified.',
                  independentVisualQA='NOT_RUN', androidDeviceQA='NOT_RUN')
    (OUT/'QA_RESULTS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
