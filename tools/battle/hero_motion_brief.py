#!/usr/bin/env python3
"""Hero battle-motion delivery brief + plan validation.
usage: hero_motion_brief.py [--check] [--md]     (default: print the brief; --check exits 1 when the plan breaks a rule)
Reads docs/battle/hero-motion-plan.json and, per actor/state/variant, prints the exact files to deliver
(<actor>[_<variant>]_<state>_NN.png), the canvas (= that state's current still), hit frame and per-frame ms, so the artist / generator needs no further spec.
Rules: frames 2-12, hitFrame within frames (or null), len(ms)==frames, sum(ms) <= the state's budget (install_motion_frames.budget), canvas known."""
import json, os, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import install_motion_frames as I
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
PLAN = json.load(open(os.path.join(ROOT, 'docs/battle/hero-motion-plan.json'), encoding='utf-8'))
def rows():
    for actor, a in PLAN['actors'].items():
        for state, s in a['states'].items():
            for variant in ([None] + (a.get('variants') or [] if state == 'attack' else [])):
                yield actor, state, variant, s
def validate():
    bad = []
    for actor, state, variant, s in rows():
        tag = '%s%s.%s' % (actor, ':' + variant if variant else '', state)
        if not 2 <= s['frames'] <= 12: bad.append('%s: frames %d outside 2-12' % (tag, s['frames']))
        if s['hitFrame'] is not None and not 1 <= s['hitFrame'] <= s['frames']: bad.append('%s: hitFrame %s outside 1..%d' % (tag, s['hitFrame'], s['frames']))
        if len(s['ms']) != s['frames']: bad.append('%s: ms has %d entries for %d frames' % (tag, len(s['ms']), s['frames']))
        if len(s.get('poses', [])) != s['frames']: bad.append('%s: %d pose notes for %d frames' % (tag, len(s.get('poses', [])), s['frames']))
        if sum(s['ms']) > I.budget(actor, state): bad.append('%s: %d ms exceeds the %d ms budget' % (tag, sum(s['ms']), I.budget(actor, state)))
        if not I.still_path(actor, state) or not os.path.isfile(I.still_path(actor, state)): bad.append('%s: no still to take the canvas from (js/assets.js)' % tag)
    return bad
def main():
    bad = validate()
    if '--check' in sys.argv:
        print('\n'.join('ERROR ' + b for b in bad) or 'plan ok'); sys.exit(1 if bad else 0)
    print('# 主人公 戦闘モーション納品ブリーフ (1コマ=1枚の透過RGBA PNG / 足元基準は静止画±48px)\n')
    for actor, a in PLAN['actors'].items():
        print('## %s' % actor)
        for state, s in a['states'].items():
            p = I.still_path(actor, state); size = Image.open(p).size if p and os.path.isfile(p) else '?'
            print('### %s — %d枚 / キャンバス %s / hit=%s / 合計%dms (上限%d) / 踏み込み: %s' % (state, s['frames'], '%dx%d' % size if size != '?' else '?', s['hitFrame'] or 'なし', sum(s['ms']), I.budget(actor, state), s['lunge']))
            for i, (pose, ms) in enumerate(zip(s['poses'], s['ms']), 1): print('  %02d  %4dms  %s' % (i, ms, pose))
            names = ['%s_%s_01..%02d.png' % (actor, state, s['frames'])] + (['同名ファイルを variant 別フォルダで納品 → install_motion_frames.py <dir> --variant %s' % v for v in (a.get('variants') or [])] if state == 'attack' else [])
            print('  files: ' + ' / '.join(names))
        print()
    if bad: print('PLAN PROBLEMS:\n' + '\n'.join(bad))
if __name__ == '__main__': main()
