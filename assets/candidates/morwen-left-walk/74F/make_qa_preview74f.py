#!/usr/bin/env python3
"""ART-74F Android / third-party art QA page (single self-contained HTML, no network).
  python3 make_qa_preview74f.py --art <74F dir> --e74 <74E dir> --right72 <72 dir> --ground <repo>/img/field/moss/art --out qa_preview_74F.html"""
import argparse, base64, json
from pathlib import Path
ap = argparse.ArgumentParser()
for k in ('art', 'e74', 'ground', 'out'): ap.add_argument('--' + k, type=Path, required=True)
a = ap.parse_args()
b64 = lambda p: 'data:image/png;base64,' + base64.b64encode(Path(p).read_bytes()).decode()
SP = 41.6 / 12
V = {  # key: (label, n, path fn, ground speed px/frame at 96)
    'E': ('ART-74E 12f（基準）', 12, lambda f, s: a.e74 / f'morwen_left_walk_12f_{f:02d}_{s}.png', SP),
    'FB': ('ART-74F-B（位相差のみ）', 12, lambda f, s: a.art / f'morwen_left_walk_74FB_12f_{f:02d}_{s}.png', SP),
    'FC': ('ART-74F-C（総合・推奨）', 12, lambda f, s: a.art / f'morwen_left_walk_74FC_12f_{f:02d}_{s}.png', SP),
}
DATA = {k: {'label': v[0], 'n': v[1], 'speed': v[3], **{s: [b64(v[2](f, s)) for f in range(v[1])] for s in ('96x128', '48x64')}} for k, v in V.items()}
MOSS = b64(a.ground / 'ground_moss.png')
ITEMS = [
    ('D-1', '公式', '公式デザイン・74Dの色・ショートブーツ・ニーソックスが保たれている（追加装飾なし）'),
    ('D-2', '公式', '頭身・体型が74Eと同じ（誇張・性的強調なし）'),
    ('P-1', '腰', '荷重で腰がわずかに沈み、支持中期で中立、蹴り出しで前へ出る（しなやかさ）'),
    ('P-2', '胸郭・肩', '胸郭が腰より少し遅れて追従し、肩（ケープ）がわずかに逆方向に動く'),
    ('P-3', '頭部', '顔・メガネ・帽子が安定し、首が不自然に伸び縮みしない'),
    ('P-4', '腕', '腕と脚が自然に逆相（手首・袖口が前腕より少し遅れる：C）'),
    ('L-1', '脚', '膝・足首の動きが自然、つま先で最後まで押す（C：F08）'),
    ('L-2', '脚', '接地中の足が滑らない（地面スクロール表示）／脚の前後が48pxで読める'),
    ('S-1', '衣装', 'スカート・マント・髪・リボンが部位ごとに少しずつ遅れ、過剰に揺れない'),
    ('S-2', '衣装', '金刺繍・模様がコマごとに消えたり跳んだりしない'),
    ('Q-1', '品質', '輪郭・1pxノイズ・プリーツ・ニーソックスとブーツの境界'),
    ('Q-2', '品質', '48×64原寸での読みやすさ'),
    ('X-1', '表示', '暗い背景（洞窟・夜）での視認性'),
    ('X-2', '表示', '長時間ループ（30秒以上）で疲れない・違和感がない'),
    ('X-3', '表示', 'Android幅で崩れない'),
    ('R-1', '選定', '推奨版（B／C）とその理由'),
]
HTML = r'''<!DOCTYPE html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>MORWEN-ASSET-74F 左向き歩行QA</title><style>
body{margin:0;background:#15141a;color:#eee;font:14px/1.5 system-ui,sans-serif}header{padding:12px 16px;border-bottom:1px solid #333}
h1{font-size:17px;margin:0 0 4px}.note{color:#bbb;font-size:12px}.ctl{display:flex;flex-wrap:wrap;gap:10px;padding:12px 16px;border-bottom:1px solid #333}
label{display:flex;flex-direction:column;font-size:12px;color:#aaa}select,button{font:inherit;min-height:40px;background:#222;color:#eee;border:1px solid #555;border-radius:6px;padding:0 8px}
button.on{border-color:#e0a030;color:#e0a030}#stage{display:flex;flex-wrap:wrap;gap:12px;padding:12px 16px}figure{margin:0;background:#1d1c24;border:1px solid #333;border-radius:8px;padding:8px}
figcaption{font-size:12px;color:#ccc;margin-bottom:4px}canvas{image-rendering:pixelated;display:block}.strip{display:flex;flex-wrap:wrap;gap:4px}
table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #333;padding:6px 4px;vertical-align:top;font-size:13px}td select{min-height:36px}
section{padding:12px 16px}textarea,input{width:100%;box-sizing:border-box;background:#222;color:#eee;border:1px solid #555;border-radius:6px;font:inherit;padding:6px}
</style></head><body><header><h1>MORWEN-ASSET-74F 12コマ歩行ブラッシュアップ 第三者美術QA／Android QA</h1>
<div class="note">候補のみ・本番未反映。74E（基準）／74F-B（腰・胸郭・肩の位相差のみ）／74F-C（B＋脚・衣装の二次動作）を同じ周期（0.84秒）・同じ速度で比較。</div></header>
<div class="ctl">
<label>比較<select id="ver"><option value="E,FB,FC" selected>74E｜74F-B｜74F-C</option><option value="E,FC">74E｜74F-C</option><option value="FB,FC">74F-B｜74F-C</option><option value="FC">74F-C</option><option value="FB">74F-B</option><option value="E">74E</option></select></label>
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
const D=__DATA__,MOSS='__MOSS__',ITEMS=__ITEMS__,KEY='morwen74f-qa';
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
$('exp').onclick=()=>{const o={task:'MORWEN-ASSET-74F third-party art / Android QA',candidate:'MORWEN-ASSET-74F B/C (feature/morwen-asset-74a-left-walk)',date:new Date().toISOString(),reviewer:rec._who||'',device:rec._dev||'',viewport:innerWidth+'x'+innerHeight,
 items:ITEMS.map(([id,cat,txt])=>({id,cat,item:txt,result:(rec[id]||{}).r||'NOT_RUN',note:(rec[id]||{}).m||''}))};const s=JSON.stringify(o,null,1);$('out').value=s;try{navigator.clipboard.writeText(s)}catch(e){}};
build();requestAnimationFrame(frame);
</script></body></html>'''
html = HTML.replace('__DATA__', json.dumps(DATA)).replace('__MOSS__', MOSS).replace('__ITEMS__', json.dumps(ITEMS, ensure_ascii=False))
a.out.write_text(html, encoding='utf-8')
print(a.out, len(html))
