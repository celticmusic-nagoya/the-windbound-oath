#!/usr/bin/env python3
"""MORWEN-PIXEL-69: third-party art QA preview (self-contained HTML, PC + Android).
  python3 make_qa_preview69.py --c67 <67 dir> --c68 <68 dir> --ground <dir with ground_moss.png, ground_mossdirt.png> --out qa_preview_69.html
"""
import argparse, base64, io, json
from pathlib import Path
from PIL import Image

ITEMS = [
    ('ID-1', '顔・キャラクター同一性', '髪型・顔・眼鏡・帽子・花飾り・紋章・衣装配色が公式正本と一致する'),
    ('LB-1', '下半身', 'ストッキングが太腿丈（ニーソックスではない）で、口ゴム・ガーター金具が正本どおり'),
    ('LB-2', '下半身', 'スカート裾〜口ゴム間の肌の帯の幅が6コマで不自然に変化しない'),
    ('LB-3', '下半身', '太腿から膝へのラインが自然（段差・直線的な切断がない）'),
    ('LB-4', '下半身', '立脚・遊脚の陰影が破綻しない（奥脚が手前脚より暗い）'),
    ('LB-5', '下半身', 'ブーツの形状・編み上げ・バックルが各コマで一貫している'),
    ('UB-1', '上半身', 'リボン・ケープ・マントが体の上下動から自然に遅れて動く'),
    ('UB-2', '上半身', '画素が不自然に伸びない（布の引き伸ばしが目立たない）'),
    ('UB-3', '上半身', '動きが過剰でない'),
    ('UB-4', '上半身', 'ポーション瓶が鞄に食い込まない'),
    ('UB-5', '上半身', '固定点（首元・肩・留め具）が不自然に移動しない'),
    ('PX-1', 'ドット品質', 'ボケ・半透明画素・不要な色数増加がない'),
    ('PX-2', 'ドット品質', '上半身と下半身の描画密度が馴染む'),
    ('PX-3', 'ドット品質', '48×64でチェック柄と金装飾が判別できる'),
    ('PX-4', 'ドット品質', '暗背景・明背景・ゲーム背景で美しく見える'),
    ('LP-1', 'ループ', 'F05→F00の継ぎ目に跳び・急な位置変化がない'),
    ('LP-2', 'ループ', '連続再生で脚が滑らず、体が分離して見えない'),
]


def b64(p: Path) -> str:
    return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()


def crop_b64(p: Path, box) -> str:
    im = Image.open(p).convert('RGB').crop(box)
    buf = io.BytesIO(); im.save(buf, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


def main():
    ap = argparse.ArgumentParser()
    for k in ('c67', 'c68', 'c70', 'art', 'c71', 'c72', 'ground'): ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    data = {}
    for v, d in (('67', a.c67), ('68', a.c68), ('70', a.c70), ('70A', a.c70 / 'easing_A'), ('ARTA', a.art / 'ART-70A'), ('ARTB', a.art / 'ART-70B'), ('ARTC', a.art / 'ART-70C'), ('M71', a.c71), ('M72', a.c72), ('PHAT', a.c71 / 'proposals/HAT_GOLD'), ('PFLO', a.c71 / 'proposals/FLOWER'), ('PGLA', a.c71 / 'proposals/GLASSES'), ('PUPG', a.c71 / 'proposals/UPPER_GOLD')):
        for s in ('96x128', '48x64'):
            data[f'{v}_{s}'] = [b64(d / f'morwen_right_walk_{f:02d}_{s}.png') for f in range(6)]
    data['bg_moss'] = crop_b64(a.ground / 'ground_moss.png', (0, 0, 192, 192))
    data['bg_dirt'] = crop_b64(a.ground / 'ground_mossdirt.png', (0, 0, 192, 192))
    html = PAGE.replace('__DATA__', json.dumps(data)).replace('__ITEMS__', json.dumps(ITEMS, ensure_ascii=False))
    a.out.write_text(html, encoding='utf-8')
    print(a.out, len(html))


PAGE = r'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MORWEN-PIXEL-72 美術QAプレビュー（右向き歩行）</title>
<style>
:root{--bg:#17151c;--panel:#24212b;--line:#3a3544;--text:#ece9f1;--muted:#a9a3b5;--acc:#c9a24a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.55 system-ui,-apple-system,"Hiragino Sans","Noto Sans JP",sans-serif;-webkit-user-select:none;user-select:none}
header{padding:12px 16px;border-bottom:1px solid var(--line)}
h1{font-size:16px;margin:0 0 2px}
header p{margin:0;color:var(--muted);font-size:12px}
.bar{display:flex;flex-wrap:wrap;gap:8px;padding:10px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:2}
.bar label{display:flex;flex-direction:column;font-size:11px;color:var(--muted);gap:2px}
select,button{background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:6px;padding:8px 10px;font-size:14px;min-height:40px}
button.on{border-color:var(--acc);color:var(--acc)}
main{padding:14px 16px;display:grid;gap:14px}
.views{display:flex;flex-wrap:wrap;gap:14px;align-items:flex-start}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px}
.card h2{font-size:13px;margin:0 0 8px;color:var(--muted);font-weight:600}
canvas{display:block;image-rendering:pixelated;image-rendering:crisp-edges}
.strip{display:flex;flex-wrap:wrap;gap:8px}
.strip figure{margin:0;text-align:center;font-size:11px;color:var(--muted)}
.qa table{width:100%;border-collapse:collapse;font-size:13px}
.qa th,.qa td{border-bottom:1px solid var(--line);padding:6px 4px;text-align:left;vertical-align:top}
.qa select{min-height:34px;padding:4px 6px}
.qa input[type=text]{width:100%;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:4px;padding:6px;font-size:13px;-webkit-user-select:text;user-select:text}
textarea{width:100%;min-height:120px;background:var(--bg);color:var(--text);border:1px solid var(--line);border-radius:6px;font:12px/1.4 ui-monospace,monospace;-webkit-user-select:text;user-select:text}
.note{color:var(--muted);font-size:12px}
</style></head><body>
<header><h1>MORWEN-PIXEL-72 第三者美術QAプレビュー</h1>
<p>候補のみ・本番未反映。72 = 最終美術候補（71＋眼鏡の金28画素）。71 = 採用候補（ART-70B＋ブーツ研磨）。71案（HAT_GOLD/FLOWER/GLASSES/UPPER_GOLD）は保護領域の変更案で未採用。ART-70B = ディレクター採用の正式候補（ブーツ＋マント金縁・ノイズ整理）、ART-70A = ブーツのみ、ART-70C = 保護領域の改善案（未採用・要承認）。70 = ART前（緩急B：ピーク保持＋ドット仕上げ）、70A = 緩急A（68の動き＋ドット仕上げ）、68 = PR #205、67 = PR #204。緩急Cは表示時間の配分で再現。Android実機の結果は下の記録欄に入力してください。</p></header>
<div class="bar">
<label>版<select id="ver"><option value="M72">72（最終候補）</option><option value="c72" selected>70B｜71｜72 並列</option><option value="M71">71</option><option value="c71">ART-70B｜71 並列</option><option value="p4">71案：HAT_GOLD｜FLOWER｜GLASSES｜UPPER_GOLD（未採用）</option><option value="ARTB">ART-70B</option><option value="ARTA">ART-70A（ブーツのみ）</option><option value="ARTC">ART-70C（保護領域の改善案・未採用）</option><option value="art3">ART-70 A｜B｜C 並列</option><option value="c70b">70｜ART-70B 並列</option><option value="70">70（緩急B・ART前）</option><option value="70A">70A（緩急A）</option><option value="68">68</option><option value="67">67</option><option value="c6870">68｜70 並列</option><option value="c3">67｜68｜70 並列</option></select></label>
<label>表示<select id="mode"><option value="loop" selected>連続ループ</option><option value="strip">静止6コマ</option><option value="seam">継ぎ目 F04→F05→F00→F01</option><option value="onion">F05/F00 重ね</option></select></label>
<label>再生配分<select id="timing"><option value="uniform" selected>均等（A・B）</option><option value="ease">表示時間で保持（C：脚が最大1.5px滑る）</option></select></label>
<label>速度<select id="fps"><option value="2">2fps（低速）</option><option value="4">4fps</option><option value="8" selected>8fps（通常）</option><option value="12">12fps</option></select></label>
<label>背景<select id="bg"><option value="light">明</option><option value="dark">暗</option><option value="moss" selected>ゲーム：苔の地面</option><option value="dirt">ゲーム：土</option><option value="check">市松</option></select></label>
<label>96×128 倍率<select id="z96"><option>1</option><option>2</option><option selected>3</option><option>4</option><option>6</option></select></label>
<label>48×64 倍率<select id="z48"><option selected>1</option><option>2</option><option>3</option><option>4</option><option>6</option></select></label>
<label>&nbsp;<button id="play" class="on">一時停止</button></label>
<label>&nbsp;<button id="step">1コマ</button></label>
<label>コマ<span id="fi" style="min-height:40px;display:flex;align-items:center;font-size:15px">F00</span></label>
</div>
<main>
<div class="views" id="views"></div>
<section class="card qa"><h2>第三者美術QA 記録欄（PASS / FAIL / BLOCKED / NOT_RUN）</h2>
<p class="note">未確認の項目はNOT_RUNのままにしてください。FAILの場合は対象コマ・位置・内容をメモに記入。入力はこの端末のブラウザにのみ一時保存されます。</p>
<div style="display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 10px">
<label>確認者<input type="text" id="who" placeholder="氏名・役割"></label>
<label>端末<input type="text" id="dev" placeholder="例: Pixel 7 / Chrome 130 / PC Chrome"></label>
</div>
<table><thead><tr><th>ID</th><th>区分</th><th>確認項目</th><th>結果</th><th>メモ（FAIL時：コマ・位置・内容）</th></tr></thead><tbody id="rows"></tbody></table>
<p><button id="copy">記録をJSONでコピー</button> <span id="copied" class="note"></span></p>
<textarea id="json" readonly></textarea>
</section>
</main>
<script>
const D=__DATA__, ITEMS=__ITEMS__;
const $=id=>document.getElementById(id);
function imgs(list){return list.map(s=>{const i=new Image();i.src=s;return i;});}
const I={}; for(const k in D){ if(Array.isArray(D[k])) I[k]=imgs(D[k]); }
const BG={moss:new Image(),dirt:new Image()}; BG.moss.src=D.bg_moss; BG.dirt.src=D.bg_dirt;
let f=0,playing=true,last=0;
const dpr=()=>Math.max(1,Math.round(window.devicePixelRatio||1));
function canvas(w,h,z){const c=document.createElement('canvas');const r=dpr();c.width=w*z*r;c.height=h*z*r;c.style.width=(w*z*r/(window.devicePixelRatio||1))+'px';c.style.height=(h*z*r/(window.devicePixelRatio||1))+'px';c._s=z*r;return c;}
function paintBg(ctx,c,scaleWorld){const v=$('bg').value;ctx.imageSmoothingEnabled=false;
 if(v==='light'){ctx.fillStyle='#eeeae2';ctx.fillRect(0,0,c.width,c.height);}
 else if(v==='dark'){ctx.fillStyle='#121016';ctx.fillRect(0,0,c.width,c.height);}
 else if(v==='check'){const s=8*c._s/scaleWorld;for(let y=0;y<c.height;y+=s)for(let x=0;x<c.width;x+=s){ctx.fillStyle=((x/s+y/s)%2)?'#bbb':'#888';ctx.fillRect(x,y,s,s);}}
 else{const im=BG[v];const s=c._s/scaleWorld;for(let y=0;y<c.height;y+=192*s)for(let x=0;x<c.width;x+=192*s)ctx.drawImage(im,x,y,192*s,192*s);}}
function draw(c,im,alpha){const x=c.getContext('2d');x.imageSmoothingEnabled=false;x.globalAlpha=alpha==null?1:alpha;x.drawImage(im,0,0,im.width*c._s,im.height*c._s);x.globalAlpha=1;}
function vers(){const v=$('ver').value;if(v==='c72')return ['ARTB','M71','M72'];if(v==='c71')return ['ARTB','M71'];if(v==='p4')return ['PHAT','PFLO','PGLA','PUPG'];return v==='art3'?['ARTA','ARTB','ARTC']:v==='c70b'?['70','ARTB']:v==='c6870'?['68','70']:v==='c3'?['67','68','70']:[v];}
const SEAM=[4,5,0,1];
function build(){const box=$('views');box.innerHTML='';const mode=$('mode').value;
 for(const v of vers())for(const [s,w,h,zid,world] of [['96x128',96,128,'z96',2],['48x64',48,64,'z48',1]]){
  const z=+$(zid).value;const card=document.createElement('div');card.className='card';
  const t=document.createElement('h2');t.textContent=v+'｜'+s+'｜×'+z;card.appendChild(t);
  if(mode==='strip'){const st=document.createElement('div');st.className='strip';
   for(let i=0;i<6;i++){const fg=document.createElement('figure');const c=canvas(w,h,z);paintBg(c.getContext('2d'),c,world);draw(c,I[v+'_'+s][i]);fg.appendChild(c);const cap=document.createElement('figcaption');cap.textContent='F0'+i;fg.appendChild(cap);st.appendChild(fg);}
   card.appendChild(st);}
  else{const c=canvas(w,h,z);c.dataset.key=v+'_'+s;c.dataset.world=world;card.appendChild(c);}
  box.appendChild(card);}
 render();}
function render(){const mode=$('mode').value;const fr=mode==='seam'?SEAM[f%4]:f;$('fi').textContent=mode==='onion'?'F05＋F00':'F0'+fr;
 document.querySelectorAll('canvas[data-key]').forEach(c=>{const ctx=c.getContext('2d');paintBg(ctx,c,+c.dataset.world);const L=I[c.dataset.key];
  if(mode==='onion'){draw(c,L[5],1);draw(c,L[0],0.5);}else draw(c,L[fr]);});}
function tick(t){const W=$('timing').value==='ease'?[1,1.25,0.75,1,1.25,0.75]:[1,1,1,1,1,1];const dt=(1000/+$('fps').value)*($('mode').value==='seam'?1:W[f%6]);if(playing&&t-last>=dt){last=t;const n=$('mode').value==='seam'?4:6;f=(f+1)%n;render();}requestAnimationFrame(tick);}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'一時停止':'再生';$('play').classList.toggle('on',playing);};
$('step').onclick=()=>{playing=false;$('play').textContent='再生';$('play').classList.remove('on');const n=$('mode').value==='seam'?4:6;f=(f+1)%n;render();};
['ver','mode','bg','z96','z48'].forEach(k=>$(k).onchange=()=>{f=0;build();});$('fps').onchange=()=>{};
window.addEventListener('resize',build);
// QA record
const KEY='morwen72-qa';let saved={};try{saved=JSON.parse(localStorage.getItem(KEY)||'{}');}catch(e){saved={};}
const rows=$('rows');
for(const [id,cat,txt] of ITEMS){const tr=document.createElement('tr');
 tr.innerHTML='<td>'+id+'</td><td>'+cat+'</td><td>'+txt+'</td><td><select data-id="'+id+'"><option>NOT_RUN</option><option>PASS</option><option>FAIL</option><option>BLOCKED</option></select></td><td><input type="text" data-note="'+id+'"></td>';
 rows.appendChild(tr);}
function collect(){const r={task:'MORWEN-PIXEL-70/71 third-party art QA',candidate:'MORWEN-PIXEL-72 (feature/morwen-pixel-72-final-candidate)',reviewer:$('who').value,device:$('dev').value,date:new Date().toISOString().slice(0,10),items:{}};
 document.querySelectorAll('select[data-id]').forEach(s=>{r.items[s.dataset.id]={result:s.value,note:document.querySelector('input[data-note="'+s.dataset.id+'"]').value};});
 const vals=Object.values(r.items).map(x=>x.result);r.overall=vals.includes('FAIL')?'FAIL':vals.every(v=>v==='PASS')?'PASS':'INCOMPLETE';return r;}
function sync(){const r=collect();$('json').value=JSON.stringify(r,null,1);try{localStorage.setItem(KEY,JSON.stringify(r));}catch(e){}}
if(saved.items){for(const id in saved.items){const s=document.querySelector('select[data-id="'+id+'"]');if(s){s.value=saved.items[id].result;document.querySelector('input[data-note="'+id+'"]').value=saved.items[id].note||'';}}$('who').value=saved.reviewer||'';$('dev').value=saved.device||'';}
document.querySelector('.qa').addEventListener('input',sync);document.querySelector('.qa').addEventListener('change',sync);sync();
$('copy').onclick=()=>{try{navigator.clipboard.writeText($('json').value).then(()=>{$('copied').textContent='コピーしました';},()=>{$('copied').textContent='コピーできません。下の欄を長押しして選択してください';});}catch(e){$('copied').textContent='コピーできません。下の欄を選択してください';}};
Promise.all(Object.values(I).flat().concat([BG.moss,BG.dirt]).map(i=>i.decode().catch(()=>{}))).then(()=>{build();requestAnimationFrame(tick);});
</script></body></html>'''

if __name__ == '__main__':
    main()
