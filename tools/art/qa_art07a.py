#!/usr/bin/env python3
"""DIRECTIVE-ART-07A runtime QA of the implemented soldier walk (no swaps: the committed manifest/PNGs are loaded as-is).
For both patrol soldiers (fort ramparts w_f2_lookout, castle plaza w_r2_herald) and PC / Android landscape / portrait emulation:
  - every soldier frame request returns HTTP 200 and the walker uses only the v2 frames + the adopted idle
  - frame timing ~7 fps, mirrored (scaleX(-1)) exactly when dir<0, idle while resting, resume continues mid-cycle
  - display box stays 47.6 x 71.4 world with bottom-centre placement
Needs python3 -m http.server 8765. Output: docs/art/qa/art-07a/ (results.json + sheet)."""
import json, pathlib, statistics
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

R = pathlib.Path(__file__).resolve().parents[2]; OUT = R / 'docs/art/qa/art-07a'; TMP = pathlib.Path('/tmp/art07a')
VP = {'pc': (1280, 720), 'land': (915, 412), 'port': (412, 915)}
WALKERS = [('w_r2_herald', 'royal_capital_02_castle_plaza', (2265, 2690)), ('w_f2_lookout', 'fort_dunvall_02_ramparts', (2475, 430))]
F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 13)
LOG = r'''async (id)=>{const out=[];const t0=performance.now();
  for(let i=0;i<260;i++){const w=FieldWalkers.list.find(r=>r.id===id);
    out.push([Math.round(performance.now()-t0),w.state,(w.el.dataset.src||'').split('/').pop(),w.dir,w.el.style.transform,parseFloat(w.el.style.width),parseFloat(w.el.style.height),
              Math.round((parseFloat(w.el.style.left)+parseFloat(w.el.style.width)/2-w.x)*100)/100,Math.round((parseFloat(w.el.style.top)+parseFloat(w.el.style.height)-w.y)*100)/100]);
    await new Promise(r=>setTimeout(r,40));}
  return out;}'''


def analyse(log):
    walk = [r for r in log if r[1] == 'walk']; srcs = {r[2] for r in log}
    changes = [(log[i][0], log[i][2]) for i in range(1, len(log)) if log[i][2] != log[i - 1][2] and log[i][1] == 'walk' and log[i - 1][1] == 'walk']
    gaps = [b[0] - a[0] for a, b in zip(changes, changes[1:])]
    flip_ok = all((r[4] == 'scaleX(-1)') == (r[3] < 0) for r in log)
    idle_ok = all(r[2] == 'npc_soldier_idle_v2.png' for r in log if r[1] == 'idle')
    walk_ok = all(r[2].startswith('npc_soldier_walk_v2_') for r in walk)
    resumes = [log[i][2] for i in range(1, len(log)) if log[i][1] == 'walk' and log[i - 1][1] == 'idle']
    return dict(samples=len(log), walk_samples=len(walk), sources=sorted(srcs), frame_interval_ms_median=statistics.median(gaps) if gaps else None,
                flip_matches_dir=flip_ok, idle_uses_adopted_idle=idle_ok, walk_uses_v2_only=walk_ok, resume_first_frames=resumes,
                box=sorted({(r[5], r[6]) for r in log}), anchor_offset=sorted({(r[7], r[8]) for r in log}))


def main():
    OUT.mkdir(parents=True, exist_ok=True); TMP.mkdir(exist_ok=True); res = {}; cells = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for wid, mid, stand in WALKERS:
            for v, (w, h) in VP.items():
                pg = b.new_page(viewport={'width': w, 'height': h}, is_mobile=v != 'pc', has_touch=v != 'pc')
                resp = {}; errs = []
                pg.on('response', lambda r: resp.__setitem__(r.url.split('/')[-1].split('?')[0], r.status) if 'npc_soldier' in r.url else None)
                pg.on('pageerror', lambda e: errs.append(str(e)))
                pg.goto('http://localhost:8765/index.html?title=0'); pg.wait_for_timeout(1500); pg.evaluate('storyStage=15')
                pg.evaluate("enterWorldMap('fort')"); pg.wait_for_timeout(1200)
                pg.evaluate("(a)=>MossForest.enter({map:a,spawn:null})", mid); pg.wait_for_timeout(1500)
                pg.evaluate("([x,y])=>MossForest.goFeet(x,y)", list(stand)); pg.wait_for_timeout(3000); pg.evaluate('closeDialogue()')
                log = pg.evaluate(LOG, wid); a = analyse(log); a['http'] = resp; a['pageErrors'] = errs
                # capture a walking frame
                for i in range(300):
                    st = pg.evaluate("(id)=>{const w=FieldWalkers.list.find(r=>r.id===id);return [w.state,w.x,w.y,(w.el.dataset.src||'').split('/').pop(),w.dir]}", wid)
                    if st[0] == 'walk': break
                    pg.wait_for_timeout(30)
                off = pg.evaluate("(()=>{const r=document.getElementById('forestWorld').getBoundingClientRect();return [r.left,r.top]})()")
                f = TMP / f'{wid}_{v}.png'; pg.screenshot(path=str(f)); pg.close(); res[f'{wid}_{v}'] = a
                im = Image.open(f).convert('RGB'); cx, cy = st[1] + off[0], st[2] + off[1]
                z = im.crop((int(cx - 60), int(cy - 85), int(cx + 60), int(cy + 10))).resize((360, 285), Image.NEAREST)
                c = Image.new('RGB', (360, 330), (10, 14, 12)); c.paste(z, (0, 44)); d = ImageDraw.Draw(c)
                d.text((6, 4), f'{wid} {"PC" if v == "pc" else ("Android横相当" if v == "land" else "Android縦相当")}', fill=(240, 228, 190), font=F)
                d.text((6, 22), f'{st[3]} {"←" if st[4] < 0 else "→"}・3倍', fill=(190, 200, 190), font=F); cells.append(c)
        b.close()
    S = Image.new('RGB', (3 * 372 + 12, 2 * 342 + 52), (10, 14, 12)); ImageDraw.Draw(S).text((12, 12), 'ART-07A 実装後の巡回兵（コミット済みmanifest/PNG）: 歩行中の1コマ', fill=(240, 228, 190), font=F)
    for i, c in enumerate(cells): S.paste(c, (12 + (i % 3) * 372, 48 + (i // 3) * 342))
    S.save(OUT / 'qa_walkers.png')
    (OUT / 'results.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    for k, a in res.items():
        print(k, 'walk', a['walk_samples'], 'int', a['frame_interval_ms_median'], 'flip', a['flip_matches_dir'], 'idle', a['idle_uses_adopted_idle'], 'v2', a['walk_uses_v2_only'],
              'resume', a['resume_first_frames'], 'box', a['box'], 'anchor', a['anchor_offset'], 'http', sorted(set(a['http'].values())), a['pageErrors'][:1])


if __name__ == '__main__':
    main()
