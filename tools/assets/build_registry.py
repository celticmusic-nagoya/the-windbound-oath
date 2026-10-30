#!/usr/bin/env python3
"""ASSET-REGISTRY-01 generator. Builds docs/assets/ASSET_REGISTRY.json (+ .md, ASSET_BACKLOG.md) from:
  1. the image files that really exist on main (working tree) -- sha256 / size / frame groups / runtime references,
  2. docs/assets/inventory_sources.json  (snapshot of branches / PRs / issues + image files that exist ONLY on unmerged branches),
  3. docs/assets/registry_overrides.json (curated facts: adoption, QA, issue links, handoff originals). Overrides never invent file facts;
     unknown stays UNKNOWN.
Rules: a file existing on a branch is NOT 'MAIN'; a manifest entry is NOT 'verified'; nothing is auto-adopted; unused images are never deleted.
usage: build_registry.py [--check]   (--check: exit 1 if the committed registry differs from a fresh build = registry not updated)"""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]; DOCS = ROOT / 'docs/assets'
IMG_EXT = ('.png', '.jpg', '.jpeg', '.webp', '.gif')
APPROVAL = ['PROVISIONAL_ANDROID_QA', 'APPROVED', 'PENDING', 'REJECTED', 'REVISION_REQUIRED', 'UNKNOWN']
IMPL = ['IMPLEMENTED', 'PARTIAL', 'REGISTERED_ONLY', 'NOT_IMPLEMENTED', 'UNKNOWN']
INTEG = ['MAIN', 'BRANCH_ONLY', 'SOURCE_ONLY', 'MISSING', 'UNKNOWN']
QA = ['PASS', 'FAIL', 'CONDITIONAL', 'NOT_RUN', 'UNVERIFIED']
MOTION_WORDS = 'idle attack skill damage guard charge heal prayer blessing rune call corruption enrage evade item victory ko low_hp lowhp draw ready entry wind winddance walk run hit hplow magic dissolve swing support'.split()
CHARS = ['aidan', 'fiona', 'lou', 'goblin_raider', 'tainted_goblin', 'goblin', 'moss_slime', 'leafy_boar', 'forest_bat', 'emma', 'boy_swordsman', 'lind', 'rilde']
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*a): return subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True).stdout
def slug(s): return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')
def category(p):
    if p.startswith('img/battle/backgrounds'): return 'background'
    if p.startswith('img/battle'): return 'battle'
    if p.startswith('img/portraits'): return 'portrait'
    if p.startswith('img/title') or p.startswith('img/ui'): return 'ui'
    if p.startswith('img/field/monsters'): return 'field_monster'
    if p.startswith('img/field/characters'): return 'field_character'
    if '/npc' in p or 'rilde/npc' in p or '/lind/' in p and 'npc' in p: return 'npc'
    if p.startswith('img/field'): return 'field'
    if 'fx_' in p or '/fx' in p or 'effect' in p: return 'effect'
    return 'other'
def character(p):
    low = p.lower()
    for c in CHARS:
        if re.search(r'(^|[/_\-])%s([/_\-.]|$)' % c, low): return c
    return 'UNKNOWN'
def motion(p):
    stem = Path(p).stem.lower()
    for w in sorted(MOTION_WORDS, key=len, reverse=True):
        if re.search(r'(^|_)%s(_|$)' % w, stem): return w
    return 'UNKNOWN'
def is_seq_dir(p):
    return bool(re.search(r'/(motion|idle|idle_v2|walk\w*|run\w*|frames|loop|anim\w*)/', p)) or motion(p) not in ('UNKNOWN',) and re.search(r'_\d{1,3}\.\w+$', p) is not None and category(p) in ('battle', 'field_character', 'field_monster')

def main_files():
    out = [l for l in git('ls-files', 'img').splitlines() if l.lower().endswith(IMG_EXT)]
    return sorted(out)
def first_commits():
    """path -> (first-add commit, date) on the current history (cheap single pass)."""
    res = {}; cur = None
    for line in git('log', '--diff-filter=A', '--name-only', '--format=@@%H|%aI', '--', 'img').splitlines():
        if line.startswith('@@'): cur = line[2:].split('|')
        elif line and cur: res[line] = (cur[0], cur[1][:10])   # log is newest first -> last write wins = oldest
    return res
def corpus():
    files = []
    for pat in ('js/**/*.js', 'css/*.css', 'data/**/*.json', 'img/**/*.json'):
        files += list(ROOT.glob(pat))
    files.append(ROOT / 'index.html')
    return {str(f.relative_to(ROOT)): f.read_text(encoding='utf-8', errors='ignore') for f in files if f.is_file()}

def build():
    DOCS.mkdir(parents=True, exist_ok=True)
    ov = json.load(open(DOCS / 'registry_overrides.json', encoding='utf-8'))
    src = json.load(open(DOCS / 'inventory_sources.json', encoding='utf-8'))
    files = main_files(); fc = first_commits(); cp = corpus()
    # ---- group frame sequences
    groups = {}; single = []
    for f in files:
        m = re.match(r'^(.*?)[_\-]?(\d{1,3})\.(png|jpg|jpeg|webp|gif)$', f, re.I)
        if m and is_seq_dir(f): groups.setdefault(m.group(1), []).append((int(m.group(2)), f))
        else: single.append(f)
    assets = []
    def reference(keys):
        refs = []
        for path, text in cp.items():
            if any(k in text for k in keys): refs.append(path)
        return sorted(refs)
    def mk(aid, name, paths, seqprefix=None):
        p0 = paths[0]; im = Image.open(ROOT / p0)
        keys = [Path(p0).name] if not seqprefix else [Path(seqprefix).name]
        if not seqprefix: keys.append(Path(p0).stem) if len(Path(p0).stem) > 8 else None
        # frame files addressed by a template (manifest walk.file 'x_f{n}.png', 'x_{n}.png'): also match the templated name
        tk = re.sub(r'\d+(\.\w+)$', r'{n}\1', Path(p0).name)
        if tk != Path(p0).name: keys.append(tk)
        refs = reference(keys)
        # manifests referencing a sequence by pattern ("<prefix>_{n}.png")
        e = {'asset_id': aid, 'name': name, 'category': category(p0), 'character': character(p0), 'motion': motion(p0),
             'delivery_date': fc.get(p0, (None, 'UNKNOWN'))[1], 'source_path': p0, 'source_branch': 'main', 'source_commit': fc.get(p0, ('UNKNOWN',))[0],
             'source_sha256': sha(ROOT / p0) if len(paths) == 1 else 'see frames_sha256', 'width': im.size[0], 'height': im.size[1], 'frame_count': len(paths),
             'approval_status': 'UNKNOWN', 'implementation_status': 'IMPLEMENTED' if refs else 'NOT_IMPLEMENTED', 'integration_status': 'MAIN',
             'runtime_reference': refs[:6] if refs else [], 'arena_available': 'UNKNOWN', 'qa_status': 'UNVERIFIED', 'android_status': 'UNVERIFIED', 'issue': '',
             'notes': 'existing asset on main; adoption record not re-verified' + ('' if refs else '; no runtime reference found (may be original storage / future use - not deleted)')}
        if len(paths) > 1:
            e['frames'] = paths; e['frames_sha256'] = [sha(ROOT / p) for p in paths]
        return e
    for prefix, items in sorted(groups.items()):
        items.sort(); paths = [p for _, p in items]; nums = [n for n, _ in items]
        if len(paths) < 2: single.append(paths[0]); continue
        e = mk('seq:' + slug(prefix), Path(prefix).name + ' (frames)', paths, prefix)
        if nums != list(range(nums[0], nums[0] + len(nums))): e['notes'] += '; frame numbers not contiguous %s' % nums
        assets.append(e)
    for f in single: assets.append(mk('file:' + slug(f[:-len(Path(f).suffix)]), Path(f).name, [f]))
    # ---- unmerged-branch-only image files (snapshot)
    for b in src.get('branch_only_assets', []):
        for f in b['files']:
            assets.append({'asset_id': 'branch:%s:%s' % (slug(b['branch']), slug(f)), 'name': Path(f).name, 'category': category(f) if f.startswith('img') else ('portrait' if 'portrait' in f else 'delivered'),
                           'character': character(f), 'motion': motion(f), 'delivery_date': b['date'], 'source_path': f, 'source_branch': b['branch'], 'source_commit': b['commit'],
                           'source_sha256': 'UNKNOWN', 'width': 'UNKNOWN', 'height': 'UNKNOWN', 'frame_count': 'UNKNOWN', 'approval_status': 'UNKNOWN', 'implementation_status': 'NOT_IMPLEMENTED',
                           'integration_status': 'BRANCH_ONLY', 'runtime_reference': [], 'arena_available': 'NO', 'qa_status': 'UNVERIFIED', 'android_status': 'UNVERIFIED', 'issue': '',
                           'notes': 'exists only on branch %s (not merged to main)' % b['branch']})
    # ---- curated extra entries (handoff originals, delivered sheets)
    assets += ov.get('extra_assets', [])
    # ---- curated patches
    for patch in ov.get('patches', []):
        rx = re.compile(patch['match'])
        hit = [a for a in assets if rx.search(a['source_path']) or rx.search(a['asset_id'])]
        for a in hit:
            for k, v in patch['set'].items():
                if k == 'notes_append': a['notes'] = (a['notes'] + '; ' + v).strip('; ')
                else: a[k] = v
        patch['_hits'] = len(hit)
    # ---- arena availability: battle assets that BattleMotion / BATTLE_ASSETS / idle loops can play
    man = json.load(open(ROOT / 'img/battle/motion-manifest.json', encoding='utf-8'))
    played = set()
    for actor, st in man['motions'].items():
        for s, d in st.items():
            for n in range(1, d['frames'] + 1): played.add(man['base'] + d['dir'] + d['pattern'].replace('{n}', '%02d' % n))
    assets_js = cp.get('js/assets.js', '')
    for a in assets:
        if a['integration_status'] != 'MAIN': continue
        paths = a.get('frames') or [a['source_path']]
        norm = [os.path.normpath(p) for p in paths]
        a['arena_available'] = 'YES' if any(os.path.normpath(p) in {os.path.normpath(x) for x in played} for p in paths) or (a['category'] == 'battle' and Path(a['source_path']).name in assets_js) else ('NO' if a['category'] == 'battle' else 'N/A')
    ids = [a['asset_id'] for a in assets]
    assert len(ids) == len(set(ids)), 'duplicate asset ids: %s' % sorted({i for i in ids if ids.count(i) > 1})[:5]
    assets.sort(key=lambda a: a['asset_id'])
    return assets, src, ov

def priority(a):
    if a['approval_status'] == 'APPROVED' and a['implementation_status'] in ('NOT_IMPLEMENTED', 'PARTIAL', 'REGISTERED_ONLY'): return 'P0'
    if a['approval_status'] == 'APPROVED' and a['implementation_status'] == 'IMPLEMENTED' and a['integration_status'] == 'BRANCH_ONLY': return 'P1'
    if a['approval_status'] == 'PENDING': return 'P2'
    if a['approval_status'] == 'REVISION_REQUIRED' and a['implementation_status'] != 'IMPLEMENTED' and 'superseded' not in a['notes']: return 'P3'
    if a['integration_status'] == 'MISSING': return 'P4'
    return None

def summary(assets):
    c = lambda f: sum(1 for a in assets if f(a))
    return {'total': len(assets),
            'approved_implemented': c(lambda a: a['approval_status'] == 'APPROVED' and a['implementation_status'] == 'IMPLEMENTED'),
            'approved_not_implemented': c(lambda a: a['approval_status'] == 'APPROVED' and a['implementation_status'] in ('NOT_IMPLEMENTED', 'PARTIAL', 'REGISTERED_ONLY')),
            'delivered_not_merged': c(lambda a: a['integration_status'] in ('BRANCH_ONLY', 'SOURCE_ONLY')),
            'pending_adoption': c(lambda a: a['approval_status'] == 'PENDING'),
            'source_missing': c(lambda a: a['integration_status'] == 'MISSING'),
            'approval_unknown': c(lambda a: a['approval_status'] == 'UNKNOWN'),
            'on_main': c(lambda a: a['integration_status'] == 'MAIN'),
            'implemented_on_main': c(lambda a: a['integration_status'] == 'MAIN' and a['implementation_status'] == 'IMPLEMENTED'),
            'unreferenced_on_main': c(lambda a: a['integration_status'] == 'MAIN' and a['implementation_status'] == 'NOT_IMPLEMENTED')}

def render_md(assets, src, ov):
    s = summary(assets); L = ['# ASSET REGISTRY（人間用総合台帳）', '', '> 生成物: `tools/assets/build_registry.py`（機械用 `ASSET_REGISTRY.json` と同内容）。手で直す場合は `registry_overrides.json` を編集して再生成する。運用: `ASSET_REGISTRY_GUIDE.md`。',
                              '> 状態は独立管理: 採用 / 実装 / 統合 / QA。不明は `UNKNOWN`。ブランチにあるだけで MAIN とは扱わない。manifest登録だけで検証済みとは扱わない。', '',
                              '## 集計（%s）' % src.get('snapshot_date', ''), '']
    for k, v in s.items(): L.append('- %s: **%d**' % (k, v))
    L += ['', '調査範囲: リモートブランチ %d（main未統合 %d）、PR %d、Issue %d、`docs/art/delivered/` 13ディレクトリ、handoff原本。' % (src['branches_total'], src['branches_unmerged'], src['prs_total'], src['issues_total']), '']
    cats = {}
    for a in assets: cats.setdefault(a['category'], []).append(a)
    for cat, items in sorted(cats.items()):
        L += ['## %s（%d）' % (cat, len(items)), '', '| asset_id | character | motion | frames | size | 採用 | 実装 | 統合 | QA | arena | 参照 / 備考 |', '|---|---|---|---|---|---|---|---|---|---|---|']
        for a in items:
            ref = ', '.join(a['runtime_reference'][:2]) if a['runtime_reference'] else '-'
            L.append('| %s | %s | %s | %s | %sx%s | %s | %s | %s | %s | %s | %s %s |' % (a['asset_id'], a['character'], a['motion'], a['frame_count'], a['width'], a['height'], a['approval_status'], a['implementation_status'], a['integration_status'], a['qa_status'], a['arena_available'], ref, ('/ ' + a['notes'][:90]) if a['notes'] else ''))
        L.append('')
    return '\n'.join(L)

def render_backlog(assets, src):
    L = ['# ASSET BACKLOG（未実装・未統合・未採用・修正待ち）', '', '> 自動抽出（`build_registry.py`）。優先度: P0 採用済み・納品済み・未実装 / P1 採用済み・実装済み・未マージ / P2 納品済み・採用判断待ち / P3 仕様不一致・修正待ち / P4 原本未発見・未納品。',
         '> 採用状態が UNKNOWN のものは自動では P0〜P4 に入れない（採用判断が必要 → 下の「採用状態 UNKNOWN（ブランチのみ）」）。', '']
    for p in ('P0', 'P1', 'P2', 'P3', 'P4'):
        items = [a for a in assets if priority(a) == p]
        L += ['## %s（%d）' % (p, len(items)), '']
        for a in items: L.append('- `%s` %s / %s / %s — 採用 %s・実装 %s・統合 %s｜%s' % (a['asset_id'], a['character'], a['motion'], a['source_path'], a['approval_status'], a['implementation_status'], a['integration_status'], a['notes']))
        L.append('')
    sup = [a for a in assets if 'superseded' in a['notes'] and a['approval_status'] == 'REVISION_REQUIRED']
    L += ['## 置換済み（改訂版が採用され本件は未使用・原本保管）（%d）' % len(sup), ''] + ['- `%s` %s' % (a['asset_id'], a['source_path']) for a in sup] + ['']
    bo = [a for a in assets if a['integration_status'] in ('BRANCH_ONLY', 'SOURCE_ONLY') and a['approval_status'] == 'UNKNOWN']
    L += ['## 採用状態 UNKNOWN（ブランチ/原本のみ）（%d）' % len(bo), '']
    byb = {}
    for a in bo: byb.setdefault(a['source_branch'], []).append(a)
    for b, items in sorted(byb.items()): L.append('- `%s`: %d ファイル（例 `%s`）' % (b, len(items), items[0]['source_path']))
    un = [a for a in assets if a['integration_status'] == 'MAIN' and a['implementation_status'] == 'NOT_IMPLEMENTED']
    L += ['', '## main上で参照が見つからない画像（%d）— 原本保管/将来用の可能性があり自動削除しない' % len(un), '']
    byd = {}
    for a in un: byd.setdefault(str(Path(a['source_path']).parent), []).append(a)
    for d, items in sorted(byd.items()): L.append('- `%s`: %d 件' % (d, len(items)))
    L += ['', '## 未実装モーション（戦闘）', '', '`ASSET_REGISTRY.json` の `motion_gaps` を参照（アリーナ「モーションテスト」と同じ分類）。']
    return '\n'.join(L)

def main():
    assets, src, ov = build()
    reg = {'schema': 'asset-registry-v1', 'snapshot_date': src.get('snapshot_date'), 'enums': {'approval_status': APPROVAL, 'implementation_status': IMPL, 'integration_status': INTEG, 'qa_status': QA},
           'sources': {k: src[k] for k in ('branches_total', 'branches_unmerged', 'prs_total', 'issues_total')}, 'summary': summary(assets), 'motion_gaps': ov.get('motion_gaps', []), 'assets': assets}
    out = {'ASSET_REGISTRY.json': json.dumps(reg, ensure_ascii=False, indent=1) + '\n', 'ASSET_REGISTRY.md': render_md(assets, src, ov) + '\n', 'ASSET_BACKLOG.md': render_backlog(assets, src) + '\n'}
    if '--check' in sys.argv:
        bad = [k for k, v in out.items() if not (DOCS / k).exists() or (DOCS / k).read_text(encoding='utf-8') != v]
        print('registry up to date' if not bad else 'REGISTRY STALE (regenerate with tools/assets/build_registry.py): %s' % bad); sys.exit(1 if bad else 0)
    for k, v in out.items(): (DOCS / k).write_text(v, encoding='utf-8')
    print(json.dumps(reg['summary'], indent=1))
if __name__ == '__main__': main()
