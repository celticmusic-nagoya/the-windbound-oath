#!/usr/bin/env python3
"""Install delivered battle-motion frames BY NAME and register them in img/battle/motion-manifest.json.
usage: install_motion_frames.py <src_dir> [--variant wooden] [--hit N] [--ms 80,80,100 | --ms 90] [--dry-run]
Files:  <actor>_<state>_NN.png   (NN = 01.. contiguous, 2-12 frames, 1 frame = 1 transparent RGBA PNG)
        actor: aidan fiona lou   state: attack skill wind damage guard charge heal prayer blessing rune call enrage ...
Checks per frame: RGBA; SAME canvas size as that state's current still (js/assets.js; the idle still if the state has none - canvases differ per state, e.g. aidan attack is 1312x1199); a note when pixels touch the canvas edge (existing battle art does too, so only a warning);
feet/bottom baseline within 48 px of the still's. Per motion: frame count, hitFrame in range (default ~2/3 of the way), and the total
duration against the state's budget in the battle code (aidan 820 ms, others attack 680 / 760; presentation skills 1200 / 1100).
Replacing a motion removes stale higher-numbered frames. Damage / TP / turn flow are NOT touched (hit timing is an event)."""
import json, os, re, shutil, sys
from PIL import Image
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
MAN = os.path.join(ROOT, 'img/battle/motion-manifest.json')
ASSETS = open(os.path.join(ROOT, 'js/assets.js'), encoding='utf-8').read()
STATES = 'attack skill wind damage guard charge heal prayer blessing rune call corruption enrage evade item victory ko'.split()
def budget(actor, state):
    if state in ('skill', 'wind', 'rune', 'prayer'): return 1200 if actor == 'aidan' else 1100
    if actor == 'aidan': return 820
    return 680 if state == 'attack' else 760
def still_path(actor, state=None):
    dirs = dict(re.findall(r"^\s*(\w+):\s*'(img/battle/[^']+/)'", ASSETS, re.M))
    blk = re.search(r"^\s*%s:\s*\{(.*?)\}" % actor, ASSETS, re.M | re.S)
    f = (re.search(r"\b%s:\s*'([^']+)'" % state, blk.group(1)) if blk and state else None) or (re.search(r"idle:\s*'([^']+)'", blk.group(1)) if blk else None)
    base = dirs.get(actor)
    return os.path.join(ROOT, base, f.group(1)) if base and f else None
def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('--'): print(__doc__); sys.exit(2)
    src = a[0]; opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
    variant, dry = opt('--variant'), '--dry-run' in a
    groups = {}
    for f in sorted(os.listdir(src)):
        m = re.fullmatch(r'([a-z]+)_([a-z_]+?)_(\d{1,2})\.png', f)
        if m and m.group(2) in STATES: groups.setdefault((m.group(1), m.group(2)), {})[int(m.group(3))] = f
    if not groups: print('no <actor>_<state>_NN.png files found in', src); sys.exit(2)
    man = json.load(open(MAN, encoding='utf-8')); bad = False; plan = []
    for (actor, state), files in groups.items():
        nums = sorted(files); prob = []
        if nums != list(range(1, len(nums) + 1)): prob.append('frames must be numbered 01..NN without gaps, got %s' % nums)
        if not 2 <= len(nums) <= 12: prob.append('needs 2-12 frames, got %d' % len(nums))
        sp = still_path(actor, state)
        if not sp or not os.path.isfile(sp): prob.append('cannot find the battle still of %s/%s (js/assets.js) to compare canvas sizes' % (actor, state)); size = None; sbot = None
        else:
            sim = Image.open(sp).convert('RGBA'); size = sim.size; al = np.array(sim)[..., 3] > 16; sbot = int(np.where(al.any(1))[0].max())
        for n in nums:
            im = Image.open(os.path.join(src, files[n]))
            if im.mode != 'RGBA': prob.append('%02d: %s, must be transparent RGBA' % (n, im.mode)); continue
            if size and im.size != size: prob.append('%02d: canvas %s != %s (same canvas as the still, or the pose would jump/scale)' % (n, im.size, size)); continue
            al = np.array(im)[..., 3] > 16
            if not al.any(): prob.append('%02d: fully transparent' % n); continue
            ys, xs = np.where(al)
            if xs.min() <= 0 or ys.min() <= 0 or xs.max() >= im.width - 1 or ys.max() >= im.height - 1: print('warn  %s %s %02d: visible pixels touch the canvas edge (cropped?)' % (actor, state, n))
            if sbot is not None and abs(int(ys.max()) - sbot) > 48: prob.append('%02d: bottom baseline y=%d vs still y=%d (character would hop)' % (n, ys.max(), sbot))
        ms = [int(x) for x in opt('--ms').split(',')] if opt('--ms') else [90]
        msl = ms if len(ms) == len(nums) else [ms[0]] * len(nums)
        total = sum(msl); hit = int(opt('--hit', max(2, round(len(nums) * 2 / 3))))
        if not 1 <= hit <= len(nums): prob.append('--hit %d outside 1..%d' % (hit, len(nums)))
        if total > budget(actor, state): print('warn  %s %s: total %d ms exceeds the state budget %d ms (the pose returns to rest at the budget)' % (actor, state, total, budget(actor, state)))
        for p in prob: print('ERROR', actor, state, p); bad = True
        if not prob: print('ok    %s%s %s: %d frames, %d ms, hit on frame %d' % (actor, ':' + variant if variant else '', state, len(nums), total, hit)); plan.append((actor, state, nums, files, msl if len(set(msl)) > 1 else msl[0], hit))
    if bad or dry: print('dry-run: nothing written' if dry and not bad else 'nothing installed (fix the errors above)'); sys.exit(1 if bad else 0)
    for actor, state, nums, files, ms, hit in plan:
        sub = '%s/motion/' % actor; os.makedirs(os.path.join(ROOT, man['base'], sub), exist_ok=True)
        tag = actor + ('_' + variant if variant else '')
        for old in os.listdir(os.path.join(ROOT, man['base'], sub)):
            if re.fullmatch(r'%s_%s_\d+\.png' % (tag, state), old): os.remove(os.path.join(ROOT, man['base'], sub, old))
        for n in nums: shutil.copy(os.path.join(src, files[n]), os.path.join(ROOT, man['base'], sub, '%s_%s_%02d.png' % (tag, state, n)))
        man['motions'].setdefault(actor + (':' + variant if variant else ''), {})[state] = {'dir': sub, 'pattern': '%s_%s_{n}.png' % (tag, state), 'frames': len(nums), 'ms': ms, 'hitFrame': hit, 'hold': 'last'}
    json.dump(man, open(MAN, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); print('manifest updated')
main()
