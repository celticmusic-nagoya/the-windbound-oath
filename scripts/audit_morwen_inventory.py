#!/usr/bin/env python3
"""Read-only, pinned Git snapshot inventory. Never moves or deletes assets.

Run from repo root with Pillow installed:
  python scripts/audit_morwen_inventory.py --website /path/to/website
First run records fetched refs; later runs use SNAPSHOTS.json commit IDs.
References are conservative lexical evidence, not a runtime reachability proof.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess

OUT = Path('docs/qa/morwen-canon-cleanup-01')
TEXT = {'.md', '.txt', '.json', '.js', '.cjs', '.mjs', '.html', '.css',
        '.py', '.yml', '.yaml', '.svg', '.sh', '.toml', '.csv'}
IMAGES = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def tree(repo, commit):
    result = {}
    for entry in git(repo, 'ls-tree', '-r', '-z', commit).split(b'\0'):
        if not entry:
            continue
        meta, path = entry.split(b'\t', 1)
        _, kind, oid = meta.decode().split()
        if kind == 'blob':
            result[path.decode()] = oid
    return result


def blobs(repo, oids):
    # A file avoids pipe-buffer deadlocks on large batch results.
    import tempfile
    with tempfile.TemporaryFile() as output:
        subprocess.run(['git', '-C', str(repo), 'cat-file', '--batch'],
                       input=('\n'.join(sorted(oids))+'\n').encode(),
                       stdout=output, check=True)
        output.seek(0)
        result = {}
        for _ in oids:
            oid, kind, length = output.readline().decode().split()
            assert kind == 'blob'
            result[oid] = output.read(int(length))
            assert output.read(1) == b'\n'
        return result


def write(name, value):
    # One record per line keeps large machine inventories reviewable in Git.
    dump = lambda v: json.dumps(v, ensure_ascii=False, separators=(',', ':'))
    fields = []
    for key, data in value.items() if isinstance(value, dict) else []:
        if isinstance(data, list) and len(data) > 20:
            body = '[\n'+',\n'.join('    '+dump(v) for v in data)+'\n  ]'
        elif isinstance(data, dict) and len(data) > 20:
            body = '{\n'+',\n'.join('    '+dump(k)+':'+dump(v) for k,v in data.items())+'\n  }'
        else:
            body = dump(data)
        fields.append('  '+dump(key)+': '+body)
    content = '{\n'+',\n'.join(fields)+'\n}' if isinstance(value, dict) else json.dumps(value, ensure_ascii=False, indent=2)
    (OUT/name).write_text(content+'\n')


def main():
    from PIL import Image
    args = argparse.ArgumentParser()
    args.add_argument('--website', required=True, type=Path)
    args = args.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    prs = json.loads((OUT/'OPEN_PRS.json').read_text())
    pin = OUT/'SNAPSHOTS.json'
    if pin.exists():
        snapshots = json.loads(pin.read_text())
    else:
        refs = sorted({r for p in prs for r in [p['headRefName'], p['baseRefName']]
                       if any(s in r for s in ['morwen', 'blender', 'character-asset-studio', 'anchor-rig'])})
        snapshots = [dict(repository='game', ref='main', commit=git('.', 'rev-parse', 'origin/main').decode().strip())]
        snapshots += [dict(repository='game', ref=r, commit=git('.', 'rev-parse', 'origin/'+r).decode().strip()) for r in refs]
        snapshots += [dict(repository='website', ref='main', commit=git(args.website, 'rev-parse', 'HEAD').decode().strip())]
        write('SNAPSHOTS.json', snapshots)
    repos = {'game': Path('.'), 'website': args.website}
    trees = {(s['repository'], s['ref']): tree(repos[s['repository']], s['commit']) for s in snapshots}
    wanted = defaultdict(set)
    occurrences = defaultdict(set)
    texts = defaultdict(set)
    for (repo, ref), files in trees.items():
        for path, oid in files.items():
            scoped = ('morwen' in path.lower() or
                      path.startswith(('tools/blender/', 'tools/character-asset-studio/')) or
                      path == 'assets/companions/MANIFEST.json')
            # Include all files in Morwen-named folders (masks, sources, evidence).
            if scoped:
                occurrences[(repo, path, oid)].add(ref)
                wanted[repo].add(oid)
            if Path(path).suffix.lower() in TEXT or path == 'AGENTS.md':
                texts[(repo, path, oid)].add(ref)
                wanted[repo].add(oid)
    raw = {r: blobs(repos[r], wanted[r]) for r in repos}
    docs = {}
    text_rows = []
    for (repo, path, oid), refs in sorted(texts.items()):
        body = raw[repo][oid]
        if b'\0' in body:
            continue
        content = body.decode('utf-8', errors='replace')
        # Decode JSON escaped slashes; HTML/URL paths also matched below.
        content = content.replace('\\/', '/')
        key = f'D{len(docs):05d}'
        docs[key] = dict(repository=repo, path=path, gitBlob=oid,
                         snapshots=sorted(refs), kind=('workflow' if path.startswith('.github/') else
                         'test' if path.startswith('tests/') else
                         'documentation' if path.endswith(('.md', '.txt')) else
                         'manifest' if path.endswith('.json') else 'code'),
                         content=content)
        text_rows.append((key, docs[key]))
    # Deduplicate source text variants. Use exact path, basename, containing
    # folder and relative path; folder matches also cover glob/f-string loaders.
    entries = []
    reference_cache = {}
    for (repo, path, oid), refs in sorted(occurrences.items()):
        data = raw[repo][oid]
        sha = hashlib.sha256(data).hexdigest()
        image = None
        if Path(path).suffix.lower() in IMAGES:
            with Image.open(io.BytesIO(data)) as im:
                im.load()
                alpha = (im.convert('RGBA').getchannel('A').getextrema()
                         if 'A' in im.getbands() or 'transparency' in im.info else None)
                image = dict(format=im.format, width=im.width, height=im.height,
                             mode=im.mode, hasAlpha=alpha is not None,
                             alphaRange=list(alpha) if alpha else None)
        refs_found = []
        parent = str(Path(path).parent)
        for key, doc in ([] if (repo, path) in reference_cache else text_rows):
            if doc['repository'] == repo and doc['path'] == path:
                continue
            content = doc['content']
            # Basename is conservative (can overmatch across versions).
            if path in content:
                match = 'path'
            elif Path(path).name in content:
                match = 'basename_conservative'
            elif parent+'/' in content and len(parent.split('/')) >= 3:
                match = 'directory_conservative'
            elif len(Path(path).stem) >= 5 and Path(path).stem in content:
                match = 'stem_conservative'
            elif (doc['repository'] == repo and
                  doc['path'].startswith(str(Path(parent).parent)+'/') and
                  any(x in content for x in ['.glob(', '.rglob(', 'iterdir(', 'os.listdir('])):
                match = 'local_dynamic_loader_conservative'
            else:
                continue
            refs_found.append(dict(document=key, match=match))
        if (repo, path) in reference_cache:
            refs_found = reference_cache[(repo, path)]
        else:
            reference_cache[(repo, path)] = refs_found
        category = ('official_reference' if path.startswith('assets/official/') else
                    'approved_v3' if path.startswith('assets/companions/') else
                    'website_asset' if repo == 'website' and image else
                    'portrait_derivative' if path.startswith('web/companions/') else
                    'experimental_candidate' if path.startswith('assets/candidates/') else
                    'pipeline_or_metadata')
        if category in {'official_reference', 'approved_v3', 'website_asset', 'portrait_derivative'}:
            action, reason = 'KEEP', 'Protected source/reference or website asset; duplicates do not authorize removal.'
        elif path.startswith('tools/') or path.startswith(('scripts/', 'tests/', '.github/', 'data/')):
            action, reason = 'KEEP', 'Shared tooling, contract, metadata or QA dependency; preserve pipeline.'
        elif category == 'experimental_candidate':
            if refs_found:
                action, reason = 'BLOCKED', 'Referenced candidate/evidence; lexical or directory dependency unresolved. No deletion.'
            else:
                action, reason = 'ARCHIVE', 'Historical candidate/evidence; no lexical hit, but dynamic loading and adoption not proven absent. Retain bytes in place.'
        else:
            action, reason = 'KEEP', 'Canon decision or QA record; preserve provenance.'
        entries.append(dict(repository=repo, path=path, gitBlob=oid, snapshots=sorted(refs),
                            sha256=sha, bytes=len(data), image=image, category=category,
                            action=action, reason=reason, references=refs_found))
    groups = defaultdict(list)
    for i, e in enumerate(entries):
        groups[e['sha256']].append(i)
    duplicates = []
    for sha, ids in sorted(groups.items()):
        if len({(entries[i]['repository'], entries[i]['path']) for i in ids}) > 1:
            key = f'SHA256:{sha}'
            duplicates.append(dict(id=key, sha256=sha, entries=ids,
                                   recoverableBytesUpperBound=sum(entries[i]['bytes'] for i in ids[1:])))
            for i in ids:
                entries[i]['duplicateGroup'] = key
    # Candidates for future deletion review: exact duplicate is necessary but
    # never sufficient. Referenced copies stay BLOCKED. No unsafe promotion.
    pending = [dict(repository=e['repository'], path=e['path'], sha256=e['sha256'],
                    snapshots=e['snapshots'], reason=e['reason'],
                    duplicateGroup=e['duplicateGroup'], action=e['action'])
               for e in entries if e['category'] == 'experimental_candidate' and 'duplicateGroup' in e]
    write('MORWEN_ASSET_INVENTORY.json', dict(schemaVersion=1,
          task='MORWEN-CANON-CLEANUP-01', snapshots=snapshots,
          scope='Morwen-named paths including all children; tools/blender shared tools; all tracked text scanned for references in pinned snapshots.',
          limitations=['Lexical conservative scan; cannot prove dynamic references absent.',
                       'No external chat/Drive attachment or private handoff source read.',
                       'No asset adoption, deletion, relocation or branch rewrite.',
                       'No new Claude independent visual QA or Android device QA.'],
          counts={a:sum(e['action'] == a for e in entries) for a in ['KEEP', 'ARCHIVE', 'DELETE_CANDIDATE', 'BLOCKED']},
          entries=entries, duplicateGroups=duplicates))
    write('DEPENDENCIES.json', dict(method='exact path / conservative basename / containing directory; scans all tracked recognized text extensions in every pinned snapshot',
          documents={k:{a:b for a,b in v.items() if a != 'content'} for k,v in docs.items()},
          openPRs=prs))
    write('DELETION_MANIFEST.json', dict(status='REVIEW_ONLY_NO_DELETION_AUTHORIZED',
          approvedDeletionPaths=[], deleteCandidates=[],
          blockedOrArchiveExactDuplicates=pending,
          gates=['Director approves exact repo/ref/path/SHA list after dependency resolution.',
                 'Re-audit current main, open PRs and website; preserve QA and source manifests.',
                 'Separate cleanup commit/PR only; never delete shared pipeline or approved art.']))
    print(json.dumps(dict(entries=len(entries), counts=dict(Counter(e['action'] for e in entries)),
                          duplicates=len(duplicates), pendingDuplicateCopies=len(pending))))


if __name__ == '__main__':
    main()
