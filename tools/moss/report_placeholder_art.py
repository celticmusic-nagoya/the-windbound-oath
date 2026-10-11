#!/usr/bin/env python3
"""Read-only inventory using check_assets.py's first-match coverage semantics."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def report():
    manifest = json.loads((ROOT / 'img/field/moss/manifest.json').read_text())
    used = {'node': {}, 'layer': {}}
    for path in sorted((ROOT / 'data/maps').glob('*.json')):
        data = json.loads(path.read_text())
        entries = [('node', prop['asset']) for prop in data.get('props', [])]
        entries += [('node', 'npc_slot_' + walker['look']) for walker in data.get('walkers', [])]
        entries += [('node' if scatter.get('render') == 'node' else 'layer', asset)
                    for scatter in data.get('scatter', []) for asset in scatter.get('pool', [])]
        for kind, asset in entries:
            used[kind].setdefault(asset, set()).add(data['id'] if 'id' in data else path.stem)
    lines = ['# 仮素材一覧（依頼G）', '',
             '生成: `python3 tools/moss/report_placeholder_art.py --output docs/art/placeholder-inventory.md`', '',
             '`check_assets.py`と同じ先頭一致ルールで分類。standinは明示フラグ、placeholderは一致なし／fileなし。',
             'この分類は画質評価ではありません。gen指定の仮建物など、manifest上でreal扱いの素材は別途目視監査が必要です。', '',
             '優先度: P1＝キャラクター・建物・ランドマーク、P2＝自然・小物。削除・置換は行っていません。', '',
             '| Kind | Asset ID | Classification | File | Priority | Maps |',
             '|---|---|---|---|---|---|']
    counts = {'standin': 0, 'placeholder': 0}
    for kind, assets in used.items():
        for asset, maps in sorted(assets.items()):
            rule = next((r for r in manifest.get(kind, []) if re.search(r['match'], asset)), None)
            classification = 'placeholder' if not rule or not rule.get('file') else 'standin' if rule.get('standin') else 'real'
            if classification == 'real':
                continue
            counts[classification] += 1
            priority = 'P1' if re.search('npc|house|gate|altar|ruin|rune|bridge', asset) else 'P2'
            lines.append('| %s | `%s` | %s | `%s` | %s | %s |' %
                         (kind, asset, classification, rule.get('file', '-') if rule else '-', priority, ', '.join(sorted(maps))))
    lines += ['', '集計（node＋layerのasset ID単位）: ' + ', '.join('%s=%s' % item for item in counts.items()), '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = report()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    else:
        print(text)
