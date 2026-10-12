#!/usr/bin/env python3
"""Add the pure-profile Fiona walk frames (used only for horizontal movement) to the installed manifest as fiona_side_<left|right>_NN.
usage: merge_fiona_side_frames.py <side_out_dir> <side_manifest.js>   (output of install_hero_frames.py --out-dir/--js-out run on the 'side' set)"""
import sys, re, json, os, shutil
ROOT = os.path.join(os.path.dirname(__file__), '..', '..'); OUT = 'img/field/moss/real/fiona/'; JS = os.path.join(ROOT, 'js/field/fiona-field-assets.js')
def main():
    side_dir, side_js = sys.argv[1:3]
    base = json.loads(re.search(r'frames: Object\.freeze\((\{.*\})\)\}\);', open(JS, encoding='utf-8').read(), re.S).group(1))
    side = json.loads(re.search(r'frames: Object\.freeze\((\{.*\})\)\}\);', open(side_js, encoding='utf-8').read(), re.S).group(1))
    for k in [k for k in base if k.startswith('fiona_side_')]: del base[k]
    for k, v in side.items():
        m = re.fullmatch(r'fiona_walk_(left|right)_(\d\d)', k)
        if not m: continue
        nk = 'fiona_side_%s_%s' % m.groups(); src = os.path.join(side_dir, k + '.png'); dst = os.path.join(ROOT, OUT, nk + '.png')
        shutil.copy(src, dst); v = dict(v); v['path'] = re.sub(r'fiona_walk_', 'fiona_side_', v['path']); base[nk] = v
    head = open(JS, encoding='utf-8').read().split('window.FionaFieldAssets')[0]
    open(JS, 'w', encoding='utf-8').write(head + 'window.FionaFieldAssets = Object.freeze({frames: Object.freeze(' + json.dumps(base, indent=1) + ')});\n')
    print('frames:', len(base))
main()
