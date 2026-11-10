#!/usr/bin/env python3
"""MORWEN-WALK-4DIR-ART-FIX-02 / DOWN-77B: front view walk, 12 frames, HD pixel re-draw with a constructed face
(round gold glasses, violet eyes with catch-light) at the side walks' proportions. 77 is kept for comparison.
  python3 build_morwen77b.py --front ../77/reference/morwen_front_candidate_73e99f19.png --out ."""
import argparse, os, sys
from pathlib import Path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'morwen-up-walk', '76B'))
import hd_walk as HW

SEGS = [((0, 345), (2, 52), 0.13), ((345, 850), (52, 100), 0.08), ((850, 1420), (100, 113), 0.08)]
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--front', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    m = HW.build('front', a.front, SEGS, (855, 380, 645), (100, 400), 511, a.out, 'morwen_down_walk_77B', 'MORWEN-WALK-DOWN-77B')
    print('ok', len(m['frames']))
