#!/usr/bin/env python3
"""Install delivered walk frames by NAME (M6). 1 frame = 1 transparent RGBA PNG.
usage: install_walk_frames.py <src_dir> [--npc ID ...] [--write-bounds] [--dry-run]
Source files are named  <npc_id>_walk_01.png, <npc_id>_walk_02.png ...  (2-6 frames, contiguous, walk-cycle order).
  npc_id: boy girl farmer_female farmer_male young_man young_woman elder_man elder_woman merchant innkeeper caretaker emma
Each frame is validated against the NPC's idle canvas (same W x H, RGBA, no visible pixel cropped), copied next to the idle PNG,
and its alpha>16 bbox is written to js/field/lind-content-bounds.js (keys <id>_walk_NN). The runtime picks the frames up by
those keys - no code change. Replacing an NPC's frames removes stale higher-numbered bounds first."""
import os, re, sys, shutil
from PIL import Image
import numpy as np
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
VIL = 'img/field/lind/npc/villagers/'
def idle_path(npc): return 'img/field/lind/npc/emma/emma_idle.png' if npc == 'emma' else VIL + npc + '_idle.png'
def out_path(npc, n): return (idle_path(npc).replace('_idle.png', '_walk_%02d.png' % n))

def scan(src, only):
    found = {}
    for f in sorted(os.listdir(src)):
        m = re.fullmatch(r'([a-z_]+?)_walk_(\d{1,2})\.png', f)
        if m and (not only or m.group(1) in only): found.setdefault(m.group(1), {})[int(m.group(2))] = f
    return found

def validate(npc, files, src):
    problems, entries = [], {}
    if not os.path.isfile(os.path.join(ROOT, idle_path(npc))): return ['no idle sprite for %s (%s)' % (npc, idle_path(npc))], {}
    W, H = Image.open(os.path.join(ROOT, idle_path(npc))).size
    nums = sorted(files)
    if nums != list(range(1, len(nums) + 1)): problems.append('%s: frames must be numbered 01..NN with no gaps, got %s' % (npc, nums))
    if not 2 <= len(nums) <= 6: problems.append('%s: needs 2-6 frames, got %d' % (npc, len(nums)))
    for n in nums:
        im = Image.open(os.path.join(src, files[n]))
        if im.mode != 'RGBA': problems.append('%s %02d: %s, must be transparent RGBA' % (npc, n, im.mode)); continue
        a = np.array(im)[..., 3]
        if im.size != (W, H):
            if im.size[0] > W and a[:, W:].max() > 16: problems.append('%s %02d: %s is wider than idle %s and would crop visible pixels' % (npc, n, im.size, (W, H))); continue
            if im.size[1] > H and a[H:, :].max() > 16: problems.append('%s %02d: %s is taller than idle %s and would crop visible pixels' % (npc, n, im.size, (W, H))); continue
        if a.max() <= 16: problems.append('%s %02d: fully transparent' % (npc, n)); continue
        canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0)); canvas.paste(im.crop((0, 0, min(W, im.width), min(H, im.height))), (0, 0))
        al = np.array(canvas)[..., 3] > 16; ys, xs = np.where(al)
        entries[n] = (canvas, [W, H, int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)])
        # walking feet must stay near the idle baseline, otherwise the NPC visibly hops: compare bottom edges
        idle_a = np.array(Image.open(os.path.join(ROOT, idle_path(npc))).convert('RGBA'))[..., 3] > 16
        iy = np.where(idle_a)[0]; 
        if abs(int(ys.max()) - int(iy.max())) > max(6, H // 40): problems.append('%s %02d: feet baseline y=%d differs from idle y=%d (NPC would hop)' % (npc, n, ys.max(), iy.max()))
    return problems, entries

def main():
    args = sys.argv[1:]
    if not args or args[0].startswith('--'): print(__doc__); sys.exit(2)
    src = args[0]; only = [args[i + 1] for i, x in enumerate(args) if x == '--npc' and i + 1 < len(args)]
    found = scan(src, only)
    if not found: print('no <npc>_walk_NN.png files found in', src); sys.exit(2)
    bounds = {}; bad = False
    for npc, files in found.items():
        problems, entries = validate(npc, files, src)
        for p in problems: print('ERROR', p); bad = True
        if not problems:
            print('ok   %s: %d frames %s' % (npc, len(entries), [e[1][4:] for e in entries.values()][0]))
            bounds[npc] = entries
    if bad: sys.exit(1)
    if '--dry-run' in args or not bounds: return
    for npc, entries in bounds.items():
        for old in range(1, 7):
            p = os.path.join(ROOT, out_path(npc, old))
            if old > len(entries) and os.path.exists(p): os.remove(p)
        for n, (canvas, _) in entries.items(): canvas.save(os.path.join(ROOT, out_path(npc, n)), optimize=True)
    if '--write-bounds' in args:
        p = os.path.join(ROOT, 'js/field/lind-content-bounds.js'); s = open(p, encoding='utf-8').read()
        for npc in bounds: s = re.sub(r',?\n  "%s_walk_0\d": \[[^\]]*\]' % npc, '', s)
        add = ''.join(',\n  "%s_walk_%02d": [\n    %s\n  ]' % (npc, n, ',\n    '.join(map(str, b))) for npc, es in bounds.items() for n, (_, b) in es.items())
        i = s.rindex('\n};'); open(p, 'w', encoding='utf-8').write(s[:i] + add + s[i:]); print('bounds written for', ', '.join(bounds))
    else: print('files installed; re-run with --write-bounds to register them')
main()
