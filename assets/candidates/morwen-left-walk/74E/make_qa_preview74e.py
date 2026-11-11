#!/usr/bin/env python3
"""ART-74E Android / third-party art QA page (single self-contained HTML, no network).
  python3 make_qa_preview74e.py --art <74E dir> --d74 <74D dir> --c74 <74C dir> --right72 <72 dir> --ground <repo>/img/field/moss/art --out qa_preview_74E.html"""
import argparse, base64, json
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ('art', 'd74', 'c74', 'right72', 'ground', 'out'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
b64 = lambda p: 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
meta = json.loads((a.art / 'build_meta_74e.json').read_text())
V = {  # key: (label, n, path fn, ground speed px/frame at 96)
    'D8': ('ART-74D 8f', 8, lambda f, s: a.d74 / f'morwen_left_walk_8f_{f:02d}_{s}.png', 34.0 / 8),
    'E8': ('ART-74E 8f', 8, lambda f, s: a.art / f'morwen_left_walk_8f_{f:02d}_{s}.png', meta['motion_8f']['ground_speed_px_per_frame']['96x128']),
    'E12': ('ART-74E 12f', 12, lambda f, s: a.art / f'morwen_left_walk_12f_{f:02d}_{s}.png', meta['motion_12f']['ground_speed_px_per_frame']['96x128']),
}
DATA = {k: {'label': v[0], 'n': v[1], 'speed': v[3], **{s: [b64(v[2](f, s)) for f in range(v[1])] for s in ('96x128', '48x64')}} for k, v in V.items()}
MOSS = b64(a.ground / 'ground_moss.png')
ITEMS = [
    ('V-1', '動画', '動画解析の資料（VIDEO_KEYPOSES / VIDEO_SERIES / VIDEO_vs_74E_POSES）と74Eの動きが対応している'),
    ('W-1', '歩行', 'かかと接地→足裏全体→つま先離地が連続して見え、接地中の足が滑らない（地面スクロール表示）'),
    ('W-2', '歩行', '支持脚が安定し、膝・足首の曲げ伸ばしが自然'),
    ('W-3', '歩行', '遊脚の通過（脚が前後に入れ替わる瞬間）のシルエットが読める'),
    ('W-4', '歩行', '腕振りが控えめで脚と逆位相'),
    ('W-5', '歩行', '頭部が過剰に上下せず、上半身が硬直して見えない'),
    ('W-6', '歩行', 'スカート・マント・髪が身体より少し遅れて動く'),
    ('W-7', '歩行', '最終コマ→F00の継ぎ目が自然'),
    ('W-8', '歩行', '8コマと12コマの差（12コマ＝つま先離地とリーチのコマが入る）が品質向上になっている'),
    ('A-1', '美術', '女性らしい自然な姿勢・歩行（誇張や性的強調なし、公式体型・頭身を維持）'),
    ('A-2', '美術', '74Dの色彩（落ち着いた紫・金・リボン）・ショートブーツ・ニーソックスが保たれている'),
    ('A-3', '美術', '輪郭・金装飾の連続性、1pxノイズがない'),
    ('A-4', '美術', '48×64原寸で歩行姿勢が読める'),
    ('X-1', '表示', '明るい草原・苔の森・暗い洞窟・夜のフィールドで輪郭と脚運びが読める'),
    ('X-2', '表示', 'Android幅で崩れない'),
]
HTML = r'''<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MORWEN-ASSET-74E 左向き歩行QA</title><style>
body{margin:0;background:#15141a;color:#eee;font:14px/1.5 system-ui,sans-serif}header{padding:12px 16px;border-bottom:1px solid #333}
h1{font-size:17px;margin:0 0 4px}.note{color:#bbb;font-size:12px}.ctl{display:flex;flex-wrap:wrap;gap:10px;padding:12px 16px;border-bottom:1px solid #333}
label{display:flex;flex-direction:column;font-size:12px;color:#aaa}select,button{font:inherit;min-height:40px;background:#222;color:#eee;border:1px solid #555;border-radius:6px;padding:0 8px}
button.on{border-color:#e0a030;color:#e0a030}#stage{display:flex;flex-wrap:wrap;gap:12px;padding:12px 16px}figure{margin:0;background:#1d1c24;border:1px solid #333;border-radius:8px;padding:8px}
figcaption{font-size:12px;color:#ccc;margin-bottom:4px}canvas{image-rendering:pixelated;display:block}.strip{display:flex;flex-wrap:wrap;gap:4px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #333;padding:6px 4px;vertical-align:top;font-size:13px}td select{min-height:36px}
section{padding:12px 16px}textarea,input{width:100%;box-sizing:border-box;background:#222;color:#eee;border:1px solid #555;border-radius:6px;font:inherit;padding:6px}
</style></head><body><header><h1>MORWEN-ASSET-74E 実写動画解析モーション 第三者美術QA／Android QA</h1>
<div class="note">候補のみ・本番未反映。74E＝74Dのデザインに実写歩行動画の解析結果を反映。周期は全版共通（推奨0.84秒）。</div></header>
<div class="ctl">
<label>比較<select id="ver"><option value="D8,E8" selected>74D 8f｜74E 8f</option><option value="E8,E12">74E 8f｜74E 12f</option><option value="D8,E8,E12">74D｜74E 8f｜74E 12f</option><option value="E8">74E 8f</option><option value="E12">74E 12f</option></select></label>
<label>表示<select id="mode"><option value="loop" selected>ループ（その場）</option><option value="walk">ループ＋地面スクロール</option><option value="strip">静止コマ一覧</option><option value="seam">継ぎ目（最終→F00→F01）</option></select></label>
<label>周期<select id="cyc"><option value="1680">1.68秒（低速）</option><option value="1000">1.00秒</option><option value="840" selected>0.84秒（推奨）</option><option value="720">0.72秒</option></select></label>
<label>サイズ<select id="size"><option value="96x128">96×128</option><option value="48x64" selected>48×64</option></select></label>
<label>倍率<select id="zoom"><option>1</option><option>2</option><option selected>3</option><option>4</option></select></label>
<label>背景<select id="bg"><option value="moss" selected>苔の森</option><option value="meadow">明るい草原（単色）</option><option value="cave">暗い洞窟（単色）</option><option value="night">夜のフィールド（単色）</option><option value="light">明るい</option><option value="dark">暗い</option></select></label>
<label>再生<button id="play" class="on">一時停止</button></label></div>
<div id="stage"></div>
<section><h2 style="font-size:15px">QA記録（端末に保存・JSONで書き出し）</h2>
<p class="note">判定：PASS／FAIL／BLOCKED／NOT_RUN。未確認はNOT_RUNのまま。</p>
<label>確認者<input id="who"></label><label>端末・ブラウザ（例：Pixel 7 / Chrome 130）<input id="dev"></label>
<table><thead><tr><th>ID</th><th>区分</th><th>項目</th><th>判定</th><th>メモ</th></tr></thead><tbody id="items"></tbody></table>
<p><button id="exp">JSONを書き出し（コピー）</button></p><textarea id="out" rows="6" readonly></textarea></section>
<script>
const D=__DATA__,MOSS='__MOSS__',ITEMS=__ITEMS__,KEY='morwen74e-qa';
const $=id=>document.getElementById(id);const IMG={};let moss=new Image();moss.src=MOSS;
for(const k in D)for(const s of ['96x128','48x64'])IMG[k+s]=D[k][s].map(u=>{const i=new Image();i.src=u;return i;});
let playing=true,t0=performance.now(),cv=[];
function bgFill(c,x,scroll,sc){const g=c.getContext('2d');const b=$('bg').value;
 if(b==='moss'&&moss.complete&&moss.naturalWidth){const p=g.createPattern(moss,'repeat');g.save();g.translate(scroll*sc,0);g.fillStyle=p;g.fillRect(-scroll*sc-2000,0,c.width+4000,c.height);g.restore();}
 else{g.fillStyle={light:'#ece8dc',dark:'#282434',meadow:'#86b45a',cave:'#221e22',night:'#0f1a24'}[b]||'#4a5a3a';g.fillRect(0,0,c.width,c.height);}
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
$('exp').onclick=()=>{const o={task:'MORWEN-ASSET-74E third-party art / Android QA',candidate:'MORWEN-ASSET-74E (feature/morwen-asset-74a-left-walk)',date:new Date().toISOString(),reviewer:rec._who||'',device:rec._dev||'',viewport:innerWidth+'x'+innerHeight,
 items:ITEMS.map(([id,cat,txt])=>({id,cat,item:txt,result:(rec[id]||{}).r||'NOT_RUN',note:(rec[id]||{}).m||''}))};const s=JSON.stringify(o,null,1);$('out').value=s;try{navigator.clipboard.writeText(s)}catch(e){}};
build();requestAnimationFrame(frame);
</script></body></html>'''
html = HTML.replace('__DATA__', json.dumps(DATA)).replace('__MOSS__', MOSS).replace('__ITEMS__', json.dumps(ITEMS, ensure_ascii=False))
a.out.write_text(html, encoding='utf-8')
print(a.out, len(html))
