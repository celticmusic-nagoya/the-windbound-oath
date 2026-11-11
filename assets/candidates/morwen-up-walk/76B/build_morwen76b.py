#!/usr/bin/env python3
"""MORWEN-WALK-4DIR-ART-FIX-02 / UP-76B: back view walk, 12 frames, HD pixel re-draw (see hdpix.py / hd_walk.py).
76 is kept unchanged for comparison.
  python3 build_morwen76b.py --official-back <official back png> --out ."""
import argparse
from pathlib import Path
import hd_walk as HW

SEGS = [((0, 385), (2, 52), 0.135), ((385, 1000), (52, 100), 0.072), ((1000, 1300), (100, 113), 0.072)]
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--official-back', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    m = HW.build('back', a.official_back, SEGS, (1150, 380, 650), (250, 395), 512, a.out, 'morwen_up_walk_76B', 'MORWEN-WALK-UP-76B')
    print('ok', len(m['frames']))
