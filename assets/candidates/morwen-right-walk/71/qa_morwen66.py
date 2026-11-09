#!/usr/bin/env python3
"""MORWEN-PIXEL-66 QA + preview builder.
  python3 qa_morwen66.py --source <65B dir> --out <66 dir>
Writes QA_REPORT.json, morwen_right_walk_66.gif, android_motion_qa.html into --out.
"""
import argparse, json, hashlib, base64, io
from pathlib import Path
import numpy as np
from PIL import Image
import build_morwen66 as B


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def components(mask):
    from collections import deque
    seen = np.zeros_like(mask); sizes = []
    for y0, x0 in zip(*np.where(mask)):
        if seen[y0, x0]: continue
        q = deque([(y0, x0)]); seen[y0, x0] = True; n = 0
        while q:
            y, x = q.popleft(); n += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True; q.append((yy, xx))
        sizes.append(n)
    return sorted(sizes, reverse=True)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--source', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    frames, smalls, uf, ub, meta = B.build(a.source, a.out)
    ref, _ = B.load_reference(a.source / 'morwen_right_walk_00_96x128.png')
    ref48 = np.array(Image.open(a.source / 'morwen_right_walk_00_48x64.png').convert('RGBA'))
    res = {'task': 'MORWEN-PIXEL-66', 'source_frame_reference': 'MORWEN-PIXEL-65B frame 00',
           'source_sha256': sha(a.source / 'morwen_right_walk_00_96x128.png'), 'frames': []}
    fails = []
    prot = uf[:, :, 3] > 0
    prot48 = uf[1::2, 1::2, 3] > 0
    ground_rows = {}
    for f in range(6):
        e = {'frame': f}
        for size, img, path in (('96x128', frames[f], a.out / f'morwen_right_walk_{f:02d}_96x128.png'),
                                ('48x64', smalls[f], a.out / f'morwen_right_walk_{f:02d}_48x64.png')):
            im = Image.open(path)
            arr = np.array(im)
            ok_fmt = im.mode == 'RGBA' and im.size == ((96, 128) if size == '96x128' else (48, 64))
            tr = arr[:, :, 3] == 0
            rgb0 = bool(np.all(arr[tr, :3] == 0))
            binary_alpha = bool(np.isin(arr[:, :, 3], (0, 255)).all())
            comps = components(arr[:, :, 3] > 0)
            e[size] = {'rgba_size_ok': ok_fmt, 'transparent_rgb_zero': rgb0, 'alpha_binary': binary_alpha,
                       'largest_component': comps[0], 'stray_components': [c for c in comps[1:]], 'sha256': sha(path)}
            if not (ok_fmt and rgb0 and binary_alpha): fails.append(f'{f} {size} format')
        bob = B.BOB[f]
        # protected pixels: every U_front pixel must be identical (RGB+A) to reference shifted by bob
        exp = B.shift(uf, 0, bob); got = frames[f]
        pm = exp[:, :, 3] > 0
        mism = int(np.any(exp[pm] != got[pm], axis=1).sum())
        exp48 = exp[1::2, 1::2]; pm48 = exp48[:, :, 3] > 0
        mism48 = int(np.any(exp48[pm48] != smalls[f][pm48], axis=1).sum())
        # same pixels vs. the delivered 65B 48px NEAREST (RGB only; 65B alpha was 250..253)
        if bob % 2 == 0:
            r48 = np.roll(ref48, bob // 2, 0)
            m = pm48 & (r48[:, :, 3] >= 128)
            rgb48 = int(np.any(r48[m, :3] != smalls[f][m, :3], axis=1).sum())
        else:
            rgb48 = None
        e['protected'] = {'pixels_96': int(pm.sum()), 'mismatch_96': mism, 'pixels_48': int(pm48.sum()), 'mismatch_48': mism48,
                          'rgb_mismatch_vs_65B_48_nearest': rgb48}
        if mism or mism48: fails.append(f'{f} protected')
        # ground contact from the solved legs
        legs = meta['legs'][f]
        for side, ph in (('near', f), ('far', (f + 3) % 6)):
            lab, _ = B.rasterise_leg({k: tuple(v) if isinstance(v, list) else v for k, v in legs[side].items() if k in ('hip', 'knee', 'ankle', 'pitch')})
            ys, xs = np.where(lab > 0)
            low = int(ys.max())
            exp_low = B.GROUND - B.GAIT[ph]['lift']
            ground_rows.setdefault(side, []).append({'frame': f, 'phase': ph, 'lowest_row': low, 'expected': exp_low,
                                                     'ankle_x': legs[side]['ankle'][0],
                                                     'contact_x_range': [int(xs[ys == low].min()), int(xs[ys == low].max())]})
            lab48, _ = B.rasterise_leg({k: tuple(v) if isinstance(v, list) else v for k, v in legs[side].items() if k in ('hip', 'knee', 'ankle', 'pitch')}, 0.5)
            low48 = int(np.where(lab48 > 0)[0].max())
            ground_rows[side][-1]['lowest_row_48'] = low48
            if abs(low - exp_low) > 0: fails.append(f'{f} {side} ground {low}!={exp_low}')
            if B.GAIT[ph]['lift'] == 0 and low48 != 61: fails.append(f'{f} {side} ground48 {low48}!=61')
        res['frames'].append(e)
    # stance sliding speed: ankle x progression during stance (phases 0..3) must be uniform (+-1px)
    speed = {}
    for side in ('near', 'far'):
        rows = sorted(ground_rows[side], key=lambda r: r['phase'])
        xs = [r['ankle_x'] for r in rows if r['phase'] in (0, 1, 2, 3)]
        d = [round(xs[i] - xs[i + 1], 2) for i in range(3)]
        speed[side] = d
        if max(d) - min(d) > 1.01: fails.append(f'{side} stance speed uneven {d}')
    # loop: frame 05 -> 00 phase continuity is guaranteed by the table; measure pixel change of legs region
    def legdiff(i, j):
        A, Bb = frames[i][92:], frames[j][92:]
        return int(np.any(A != Bb, axis=2).sum())
    res['ground_contact'] = ground_rows
    res['stance_speed_px_per_frame'] = speed
    res['leg_region_changed_px'] = {f'{i:02d}->{(i + 1) % 6:02d}': legdiff(i, (i + 1) % 6) for i in range(6)}
    res['meta'] = {k: meta[k] for k in ('halo_pixels_removed_from_reference', 'old_lower_body_pixels_discarded', 'bob', 'cape_sway')}
    res['fails'] = fails
    res['format_and_structure'] = 'PASS' if not fails else 'FAIL'
    res['art_qa'] = 'SELF_CHECK_DONE / INDEPENDENT_ART_QA_REQUIRED'
    res['android'] = 'NOT_RUN'
    res['production'] = 'NOT_APPLIED (candidate only)'
    (a.out / 'QA_REPORT.json').write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')

    # GIF (3x, 96x128) on a neutral background, 125 ms/frame
    gif = []
    for img in frames:
        bg = Image.new('RGBA', (96, 128), (164, 184, 150, 255)); bg.alpha_composite(Image.fromarray(img))
        gif.append(bg.convert('RGB').resize((288, 384), Image.NEAREST).convert('P', palette=Image.ADAPTIVE, colors=255))
    gif[0].save(a.out / 'morwen_right_walk_66.gif', save_all=True, append_images=gif[1:], duration=125, loop=0, disposal=2)

    def b64(p):
        return 'data:image/png;base64,' + base64.b64encode(p.read_bytes()).decode()
    f96 = [b64(a.out / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)]
    f48 = [b64(a.out / f'morwen_right_walk_{f:02d}_48x64.png') for f in range(6)]
    old = [b64(a.source / f'morwen_right_walk_{f:02d}_96x128.png') for f in range(6)]
    html = HTML.replace('__F96__', json.dumps(f96)).replace('__F48__', json.dumps(f48)).replace('__OLD__', json.dumps(old))
    (a.out / 'android_motion_qa.html').write_text(html, encoding='utf-8')
    print(json.dumps({'format_and_structure': res['format_and_structure'], 'fails': fails, 'speed': speed,
                      'protected': [fr['protected'] for fr in res['frames']]}, indent=1))


HTML = r'''<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MORWEN-PIXEL-66 右向き歩行QA</title>
<style>
body{margin:0;font:14px/1.5 system-ui,sans-serif;background:#1d1b22;color:#eee}
header{padding:10px 14px;background:#2a2633}h1{font-size:16px;margin:0}
.wrap{display:flex;flex-wrap:wrap;gap:14px;padding:14px}
.card{background:#2a2633;border-radius:8px;padding:10px}
.stage{position:relative;overflow:hidden;border-radius:6px}
canvas{image-rendering:pixelated;display:block}
.ctrl{display:flex;flex-wrap:wrap;gap:6px;padding:0 14px 14px}
button,select{background:#3b3546;color:#eee;border:1px solid #5a5068;border-radius:6px;padding:8px 10px;font-size:14px}
.strip img{image-rendering:pixelated;width:96px;height:128px;background:var(--bg)}
small{color:#bbb}
</style></head><body>
<header><h1>MORWEN-PIXEL-66 右向き歩行 6コマ（候補・本番未適用）</h1>
<small>新版: 脚・ブーツを歩行周期から再構築。旧版: 65B。Android実機確認は未実施（NOT_RUN）。</small></header>
<div class="ctrl">
<button id="play">一時停止</button><button id="step">1コマ進む</button>
<select id="fps"><option value="5">5fps</option><option value="8" selected>8fps</option><option value="10">10fps</option><option value="12">12fps</option></select>
<select id="bg"><option value="#a4b896">草地</option><option value="#6b5a45">土</option><option value="#ffffff">白</option><option value="#000000">黒</option><option value="check">市松</option></select>
<select id="scroll"><option value="0">その場</option><option value="1" selected>地面スクロール</option></select>
<span id="fi" style="align-self:center"></span></div>
<div class="wrap">
<div class="card"><div>新版 96×128（×3）</div><div class="stage"><canvas id="c96" width="288" height="408"></canvas></div></div>
<div class="card"><div>新版 48×64（×2 / 等倍）</div><div class="stage"><canvas id="c48" width="96" height="140"></canvas></div><div class="stage" style="margin-top:8px"><canvas id="c48x1" width="48" height="70"></canvas></div></div>
<div class="card"><div>旧版 65B 96×128（×3・比較）</div><div class="stage"><canvas id="cold" width="288" height="408"></canvas></div></div>
</div>
<div class="ctrl strip" id="strip"></div>
<script>
const F96=__F96__,F48=__F48__,OLD=__OLD__;
function load(a){return a.map(s=>{const i=new Image();i.src=s;return i;});}
const I96=load(F96),I48=load(F48),IOLD=load(OLD);
let f=0,playing=true,last=0,scrollX=0;const SPEED=6; // stance foot speed: 6 px/frame at 96x128
const $=id=>document.getElementById(id);
function bg(ctx,w,h,scale,ground){const v=$('bg').value;
 if(v==='check'){for(let y=0;y<h;y+=8)for(let x=0;x<w;x+=8){ctx.fillStyle=((x+y)/8)%2?'#ccc':'#999';ctx.fillRect(x,y,8,8);}}
 else{ctx.fillStyle=v;ctx.fillRect(0,0,w,h);}
 if($('scroll').value==='1'){ctx.fillStyle='rgba(0,0,0,.25)';const step=24*scale;for(let x=-((scrollX*scale)%step);x<w;x+=step)ctx.fillRect(x,ground*scale,step/2,2);}
 ctx.fillStyle='rgba(0,0,0,.35)';ctx.fillRect(0,ground*scale,w,1);}
function draw(id,img,scale,ground){const c=$(id),x=c.getContext('2d');x.imageSmoothingEnabled=false;bg(x,c.width,c.height,scale,ground);x.drawImage(img,0,0,img.width*scale,img.height*scale);}
function render(){draw('c96',I96[f],3,125);draw('c48',I48[f],2,62.5);draw('c48x1',I48[f],1,62.5);draw('cold',IOLD[f],3,125);$('fi').textContent='Frame '+String(f).padStart(2,'0');}
function tick(t){const dt=1000/+$('fps').value;if(playing&&t-last>=dt){last=t;f=(f+1)%6;scrollX+=SPEED;render();}requestAnimationFrame(tick);}
$('play').onclick=()=>{playing=!playing;$('play').textContent=playing?'一時停止':'再生';};
$('step').onclick=()=>{playing=false;$('play').textContent='再生';f=(f+1)%6;scrollX+=SPEED;render();};
['bg','scroll','fps'].forEach(k=>$(k).onchange=render);
const s=$('strip');F96.forEach((src,i)=>{const im=new Image();im.src=src;im.title='Frame '+i;s.appendChild(im);});
document.documentElement.style.setProperty('--bg','#a4b896');
Promise.all(I96.concat(I48,IOLD).map(i=>i.decode())).then(()=>{render();requestAnimationFrame(tick);});
</script></body></html>'''

if __name__ == '__main__':
    main()
