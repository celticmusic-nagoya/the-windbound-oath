#!/usr/bin/env python3
"""ART-74A QA preview (single HTML, PC/Android): ART-74A left vs DEV mirror vs official right 72; record form.
  python3 make_qa_preview74a.py --art <o74> --dev <DEV dir> --right72 <72 dir> --ground <img/field/moss/art> --out <html>"""
import os as _os, sys as _sys
_HERE=_os.path.dirname(_os.path.abspath(__file__))
_PIPE=_os.environ.get('MORWEN72_PIPELINE', _os.path.join(_HERE,'..','..','morwen-right-walk','72'))
_sys.path[:0]=[_HERE,_PIPE]
import argparse, base64, io, json, sys
from pathlib import Path
from PIL import Image
pass
from make_qa_preview69 import PAGE
ITEMS = [('EQ-1','左右装備','鞄・肩掛けベルト・瓶・帽子装飾の左右関係が正本と整合（鞄・紋章・花・リボンは右側＝左向きでは奥側）'),
         ('EQ-2','左右装備','ベルト（左肩→右腰）の向きが自然に読める'),('EQ-3','左右装備','未確認部分（左肩の装飾・左耳イヤリング）の扱いが妥当'),
         ('ID-1','同一性','顔・眼鏡・髪・帽子・ニーソックス・ブーツが右向き72と同じ公式造形'),
         ('PX-1','ドット','花・リボン・鞄を除いた跡（帽子・後頭部・肩・腰）に不自然な塊やノイズがない'),
         ('PX-2','ドット','48×64でも装飾が判別でき、ちらつかない'),('PX-3','ドット','明・暗・苔背景で輪郭が読める'),
         ('LP-1','ループ','F00〜F05の連続性、F05→F00に跳びがない'),('LP-2','ループ','接地・歩幅・シルエットが右向き72と同等')]
def b64(p): return 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
def crop(p, box):
    im = Image.open(p).convert('RGB').crop(box); b = io.BytesIO(); im.save(b, 'PNG'); return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()
ap = argparse.ArgumentParser()
for k in ('art', 'dev', 'right72', 'ground', 'out'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
D = {}
for f in range(6): pass
D['L74_96x128'] = [b64(a.art / f'morwen_left_walk_{f:02d}_96x128.png') for f in range(6)]
D['L74_48x64'] = [b64(a.art / f'morwen_left_walk_{f:02d}_48x64.png') for f in range(6)]
D['DEV_96x128'] = [b64(a.dev / f'm96_left_DEV_F{f:02d}.png') for f in range(6)]
D['DEV_48x64'] = [b64(a.dev / f'm48_left_DEV_F{f:02d}.png') for f in range(6)]
D['R72_96x128'] = [b64(a.right72 / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)]
D['R72_48x64'] = [b64(a.right72 / f'morwen_right_walk_{f:02d}_48x64.png') for f in range(6)]
D['bg_moss'] = crop(a.ground / 'ground_moss.png', (0, 0, 192, 192)); D['bg_dirt'] = crop(a.ground / 'ground_mossdirt.png', (0, 0, 192, 192))
s = PAGE.replace('__DATA__', json.dumps(D)).replace('__ITEMS__', json.dumps(ITEMS, ensure_ascii=False))
s = s.replace('<option value="68">68（候補）</option><option value="67">67（前版）</option><option value="both" selected>67｜68 並列</option>',
              '<option value="L74">ART-74A 左（候補）</option><option value="c3" selected>DEVミラー｜ART-74A｜右72</option><option value="c2">DEVミラー｜ART-74A</option><option value="DEV">DEVミラー（参考・非正式）</option><option value="R72">右72（正式）</option>')
s = s.replace("function vers(){const v=$('ver').value;return v==='both'?['67','68']:[v];}", "function vers(){const v=$('ver').value;return v==='c3'?['DEV','L74','R72']:v==='c2'?['DEV','L74']:[v];}")
s = s.replace('MORWEN-PIXEL-69 第三者美術QAプレビュー', 'MORWEN-ASSET-74 ART-74A 左向き歩行 第三者美術QA').replace('<title>MORWEN-PIXEL-69 美術QAプレビュー（67/68 右向き歩行）</title>', '<title>MORWEN-ASSET-74 ART-74A 左向き歩行QA</title>')
s = s.replace('候補のみ・本番未反映。68 = 現行候補（PR #205）、67 = 前版（PR #204）。', '候補のみ・本番未反映。ART-74A = 正式左向き候補（鞄・紋章・花・リボンは奥側で見えない／ベルトは左肩→右腰）。DEVミラー = 単純反転の参考（非正式）。右72 = 正式右向き。')
s = s.replace("candidate:'MORWEN-PIXEL-68 (PR #205 head 51b15ad)'", "candidate:'MORWEN-ASSET-74 ART-74A (feature/morwen-asset-74a-left-walk)'").replace("const KEY='morwen69-qa'", "const KEY='morwen74a-qa'").replace("task:'MORWEN-PIXEL-69/70 third-party art QA'", "task:'MORWEN-ASSET-74 ART-74A third-party art QA'")
a.out.write_text(s, encoding='utf-8'); print(a.out, len(s))
