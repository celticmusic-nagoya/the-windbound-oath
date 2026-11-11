#!/usr/bin/env python3
"""ART-74D Android / third-party art QA page (single self-contained HTML, no network).
  python3 make_qa_preview74d.py --art <74D dir> --c74 <74C dir> --right72 <72 dir> --ground <repo>/img/field/moss/art --out qa_preview_74D.html"""
import argparse, base64, json
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ('art', 'c74', 'right72', 'ground', 'out'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
b64 = lambda p: 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
meta = json.loads((a.c74 / 'build_meta_74c.json').read_text())
V = {  # key: (label, n, path fn, ground speed px/frame at 96)
    'C8': ('ART-74C 8f', 8, lambda f, s: a.c74 / f'morwen_left_walk_8f_{f:02d}_{s}.png', meta['motion_8f']['ground_speed_px_per_frame']['96x128']),
    'D8': ('ART-74D 8f', 8, lambda f, s: a.art / f'morwen_left_walk_8f_{f:02d}_{s}.png', meta['motion_8f']['ground_speed_px_per_frame']['96x128']),
    'D12': ('ART-74D 12f', 12, lambda f, s: a.art / f'morwen_left_walk_12f_{f:02d}_{s}.png', meta['motion_12f']['ground_speed_px_per_frame']['96x128']),
    'R72': ('右72（正式・参考、色未変更）', 6, lambda f, s: a.right72 / f'morwen_right_walk_{f:02d}_{s}.png', -6.0),
}
DATA = {k: {'label': v[0], 'n': v[1], 'speed': v[3], **{s: [b64(v[2](f, s)) for f in range(v[1])] for s in ('96x128', '48x64')}} for k, v in V.items()}
MOSS = b64(a.ground / 'ground_moss.png')
ITEMS = [
    ('C-1', '色彩', '帽子：落ち着いた濃紫＋自然な金刺繍（公式左向きと比べて）'),
    ('C-2', '色彩', '髪：暗い紫系、ピンクが強すぎない'),
    ('C-3', '色彩', '首元のリボン：公式の紫系'),
    ('C-4', '色彩', '上着：濃紫の面積と金装飾のバランス'),
    ('C-5', '色彩', 'スカート：マゼンタの過剰なハイライトがない'),
    ('C-6', '色彩', 'マント：深い紫と金縁'),
    ('C-7', '色彩', '全体の紫・マゼンタの過剰さが改善され、ドット絵として鮮明さを保っている'),
    ('B-1', 'ブーツ', 'ショートブーツと認識できる丈（履き口が脛の中ほど）'),
    ('B-2', 'ブーツ', 'ブーツ上端とニーソックスの境界が全フレームで保たれる'),
    ('B-3', 'ブーツ', '足首の形・接地位置が自然（滑り・浮きがない）'),
    ('S-1', 'ニーソックス', '膝上までの丈・スカート裾との間の脚（肌の帯）が正しい'),
    ('S-2', 'ニーソックス', 'ニーソックスとブーツの色・明度の差が分かる（48×64原寸でも）'),
    ('S-3', 'ニーソックス', '歩行中にニーソックスの丈が不自然に変化しない'),
    ('M-1', '歩行', '74Cの8コマ歩行（周期・重心・腕・接地・歩幅・頭・遅延動作）が保たれている'),
    ('M-2', '歩行', '最終コマ→F00の継ぎ目に跳びがない'),
    ('X-1', '表示', 'Android幅で崩れず、明・暗・苔の背景で読める（暗背景での濃紫の輪郭も確認）'),
]
HTML = r'''<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MORWEN-ASSET-74D 左向き歩行QA</title><style>
body{margin:0;background:#15141a;color:#eee;font:14px/1.5 system-ui,sans-serif}header{padding:12px 16px;border-bottom:1px solid #333}
h1{font-size:17px;margin:0 0 4px}.note{color:#bbb;font-size:12px}.ctl{display:flex;flex-wrap:wrap;gap:10px;padding:12px 16px;border-bottom:1px solid #333}
label{display:flex;flex-direction:column;font-size:12px;color:#aaa}select,button{font:inherit;min-height:40px;background:#222;color:#eee;border:1px solid #555;border-radius:6px;padding:0 8px}
button.on{border-color:#e0a030;color:#e0a030}#stage{display:flex;flex-wrap:wrap;gap:12px;padding:12px 16px}figure{margin:0;background:#1d1c24;border:1px solid #333;border-radius:8px;padding:8px}
figcaption{font-size:12px;color:#ccc;margin-bottom:4px}canvas{image-rendering:pixelated;display:block}.strip{display:flex;flex-wrap:wrap;gap:4px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #333;padding:6px 4px;vertical-align:top;font-size:13px}td select{min-height:36px}
section{padding:12px 16px}textarea,input{width:100%;box-sizing:border-box;background:#222;color:#eee;border:1px solid #555;border-radius:6px;font:inherit;padding:6px}
</style></head><body><header><h1>MORWEN-ASSET-74D 公式色彩・ブーツ・ニーソックス 第三者美術QA／Android QA</h1>
<div class="note">候補のみ・本番未反映。74D＝74Cの8コマ歩行のまま公式色彩・ショートブーツ・ニーソックスを修正。右72は向き違い・色未変更の参考表示です。</div></header>
<div class="ctl">
<label>比較<select id="ver"><option value="C8,D8" selected>74C 8f｜74D 8f</option><option value="D8,D12">74D 8f｜74D 12f</option><option value="D8">74D 8f</option><option value="C8">74C 8f</option><option value="R72">右72</option></select></label>
<label>表示<select id="mode"><option value="loop" selected>ループ（その場）</option><option value="walk">ループ＋地面スクロール</option><option value="strip">静止コマ一覧</option><option value="seam">継ぎ目（最終→F00→F01）</option></select></label>
<label>周期<select id="cyc"><option value="1440">1.44秒（低速）</option><option value="900">0.90秒</option><option value="720" selected>0.72秒（標準）</option><option value="600">0.60秒</option></select></label>
<label>サイズ<select id="size"><option value="96x128">96×128</option><option value="48x64" selected>48×64</option></select></label>
<label>倍率<select id="zoom"><option>1</option><option>2</option><option selected>3</option><option>4</option></select></label>
<label>背景<select id="bg"><option value="moss" selected>苔の地面</option><option value="light">明るい</option><option value="dark">暗い</option></select></label>
<label>再生<button id="play" class="on">一時停止</button></label></div>
<div id="stage"></div>
<section><h2 style="font-size:15px">QA記録（端末に保存・JSONで書き出し）</h2>
<p class="note">判定：PASS／FAIL／BLOCKED／NOT_RUN。未確認はNOT_RUNのまま。</p>
<label>確認者<input id="who"></label><label>端末・ブラウザ（例：Pixel 7 / Chrome 130）<input id="dev"></label>
<table><thead><tr><th>ID</th><th>区分</th><th>項目</th><th>判定</th><th>メモ</th></tr></thead><tbody id="items"></tbody></table>
<p><button id="exp">JSONを書き出し（コピー）</button></p><textarea id="out" rows="6" readonly></textarea></section>
<script>
const D=__DATA__,MOSS='__MOSS__',ITEMS=__ITEMS__,KEY='morwen74d-qa';
const $=id=>document.getElementById(id);const IMG={};let moss=new Image();moss.src=MOSS;
for(const k in D)for(const s of ['96x128','48x64'])IMG[k+s]=D[k][s].map(u=>{const i=new Image();i.src=u;return i;});
let playing=true,t0=performance.now(),cv=[];
function bgFill(c,x,scroll,sc){const g=c.getContext('2d');const b=$('bg').value;
 if(b==='moss'&&moss.complete&&moss.naturalWidth){const p=g.createPattern(moss,'repeat');g.save();g.translate(scroll*sc,0);g.fillStyle=p;g.fillRect(-scroll*sc-2000,0,c.width+4000,c.height);g.restore();}
 else{g.fillStyle=b==='light'?'#ece8dc':b==='dark'?'#282434':'#4a5a3a';g.fillRect(0,0,c.width,c.height);}
 // ground ruler (marks every 16 px of the 96 scale)
 g.fillStyle=b==='light'?'#887':'#cbb';const step=16*sc,h=c.height;for(let x0=((scroll*sc)%step+step)%step-step;x0<c.width;x0+=step)g.fillRect(Math.round(x0),h-4,2,4);}
function build(){const st=$('stage');st.innerHTML='';cv=[];const s=$('size').value,z=+$('zoom').value,[w,h]=s==='96x128'?[96,128]:[48,64];
 for(const k of $('ver').value.split(',')){const fg=document.createElement('figure');const cap=document.createElement('figcaption');cap.textContent=D[k].label+'｜'+s+'｜×'+z;fg.appendChild(cap);
  if($('mode').value==='strip'){const d=document.createElement('div');d.className='strip';for(let i=0;i<D[k].n;i++){const c=document.createElement('canvas');c.width=w*z;c.height=h*z;bgFill(c,0,0,z*(w/96));c.getContext('2d').imageSmoothingEnabled=false;
   const im=IMG[k+s][i];const draw=()=>c.getContext('2d').drawImage(im,0,0,w*z,h*z);im.complete?draw():im.onload=draw;const f=document.createElement('div');f.appendChild(c);const t=document.createElement('div');t.className='note';t.textContent='F'+String(i).padStart(2,'0');f.appendChild(t);d.appendChild(f);}fg.appendChild(d);}
  else{const c=document.createElement('canvas');c.width=w*z;c.height=h*z;fg.appendChild(c);const lb=document.createElement('div');lb.className='note';fg.appendChild(lb);cv.push({k,c,lb,w,h,z,s});}
  st.appendChild(fg);}}
function frame(now){requestAnimationFrame(frame);if(playing){const cyc=+$('cyc').value,mode=$('mode').value;const ph=((now-t0)%cyc)/cyc,cycles=(now-t0)/cyc;
 for(const o of cv){const n=D[o.k].n;let f=Math.floor(ph*n);let label='F'+String(f).padStart(2,'0');
  if(mode==='seam'){const q=Math.floor((now-t0)/700)%3;f=[n-1,0,1][q];label=['F'+(n-1)+'（最終）','F00','F01'][q];}
  const sc=o.w/96;const scroll=mode==='walk'?(D[o.k].speed*n*cycles)%1e6:0;
  bgFill(o.c,0,scroll,o.z*sc);const g=o.c.getContext('2d');g.imageSmoothingEnabled=false;const im=IMG[o.k+o.s][f];if(im.complete&&im.naturalWidth)g.drawImage(im,0,0,o.w*o.z,o.h*o.z);o.lb.textContent=label;}}}
['ver','mode','size','zoom','bg'].forEach(id=>$(id).onchange=build);$('cyc').onchange=()=>{t0=performance.now();};
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'一時停止':'再生';$('play').classList.toggle('on',playing);};
let rec={};try{rec=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(rec))}catch(e){}};
for(const [id,cat,txt] of ITEMS){const tr=document.createElement('tr');const v=(rec[id]||{});tr.innerHTML=`<td>${id}</td><td>${cat}</td><td>${txt}</td><td><select>${['NOT_RUN','PASS','FAIL','BLOCKED'].map(x=>`<option${(v.r||'NOT_RUN')===x?' selected':''}>${x}</option>`).join('')}</select></td><td><input value="${(v.m||'').replace(/"/g,'&quot;')}"></td>`;
 const [sel,inp]=[tr.querySelector('select'),tr.querySelector('input')];sel.onchange=inp.oninput=()=>{rec[id]={r:sel.value,m:inp.value};save();};$('items').appendChild(tr);}
$('who').value=rec._who||'';$('dev').value=rec._dev||'';$('who').oninput=()=>{rec._who=$('who').value;save()};$('dev').oninput=()=>{rec._dev=$('dev').value;save()};
$('exp').onclick=()=>{const o={task:'MORWEN-ASSET-74D third-party art / Android QA',candidate:'MORWEN-ASSET-74D (feature/morwen-asset-74a-left-walk)',date:new Date().toISOString(),reviewer:rec._who||'',device:rec._dev||'',viewport:innerWidth+'x'+innerHeight,
 items:ITEMS.map(([id,cat,txt])=>({id,cat,item:txt,result:(rec[id]||{}).r||'NOT_RUN',note:(rec[id]||{}).m||''}))};const s=JSON.stringify(o,null,1);$('out').value=s;try{navigator.clipboard.writeText(s)}catch(e){}};
build();requestAnimationFrame(frame);
</script></body></html>'''
html = HTML.replace('__DATA__', json.dumps(DATA)).replace('__MOSS__', MOSS).replace('__ITEMS__', json.dumps(ITEMS, ensure_ascii=False))
a.out.write_text(html, encoding='utf-8')
print(a.out, len(html))
