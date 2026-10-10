#!/usr/bin/env python3
"""Report walk-frame coverage per field NPC and verify what is installed (M6).
Exit 1 when a registered bounds key has no PNG, a PNG has no bounds, numbering has gaps, or a frame is not the idle canvas size."""
import os, re, sys
from PIL import Image
ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
NPCS = ['boy','girl','farmer_female','farmer_male','young_man','young_woman','elder_man','elder_woman','merchant','innkeeper','caretaker','emma']
VIL = 'img/field/lind/npc/villagers/'
bounds = open(os.path.join(ROOT, 'js/field/lind-content-bounds.js'), encoding='utf-8').read()
keys = set(re.findall(r'^  "([a-z_0-9]+)": \[', bounds, re.M))
bad = 0
print('%-14s %-6s %s' % ('npc', 'walk', 'status'))
for npc in NPCS:
    idle = 'img/field/lind/npc/emma/emma_idle.png' if npc == 'emma' else VIL + npc + '_idle.png'
    W, H = Image.open(os.path.join(ROOT, idle)).size
    nums = sorted(int(k[-2:]) for k in keys if re.fullmatch(npc + r'_walk_\d\d', k))
    files = [n for n in range(1, 7) if os.path.isfile(os.path.join(ROOT, idle.replace('_idle.png', '_walk_%02d.png' % n)))]
    status = 'ok'
    if nums != files: status = 'MISMATCH bounds=%s files=%s' % (nums, files); bad += 1
    elif nums and nums != list(range(1, len(nums) + 1)): status = 'GAP %s' % nums; bad += 1
    else:
        for n in nums:
            if Image.open(os.path.join(ROOT, idle.replace('_idle.png', '_walk_%02d.png' % n))).size != (W, H): status = 'SIZE frame %d != idle %s' % (n, (W, H)); bad += 1
    legacy = ' (legacy single walk)' if npc == 'farmer_male' and npc + '_walk' in keys else ''
    print('%-14s %-6s %s%s' % (npc, len(nums) or '-', status if nums or bad else 'WAITING (idle only)', legacy))
sys.exit(1 if bad else 0)
