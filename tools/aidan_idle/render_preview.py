#!/usr/bin/env python3
"""Render the Aidan idle v1 candidate (reference renderer) to frames / MP4 / GIF.
usage: render_preview.py MASTER.png OVERLAY_DIR OUT_DIR [--scale 0.5] [--fps 25] [--seconds 8] [--bg R,G,B] [--blinks 2.0,5.4]
"""
import sys, os, json, argparse, subprocess, numpy as np, cv2
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from idle_motion import Idle, warp, P
BLINK_SEQ = [(1, 30), (2, 30), (3, 35), (4, 70), (3, 35), (2, 30), (1, 30)]   # (stage, ms) as the Fiona v3 blink: ~260 ms

def blink_state(t, starts):
    for s in starts:
        ms = (t - s) * 1000
        if ms < 0: continue
        for st, d in BLINK_SEQ:
            if ms < d: return st
            ms -= d
    return 0

def composite_eyes(master, ov, boxes, state):
    """eye overlay replaces RGB only where the overlay alpha is set; the MASTER's own alpha channel is kept (no alpha change anywhere)"""
    if state == 0: return master
    out = master.copy()
    for e in ('L', 'R'):
        o = np.array(Image.open(f'{ov}/overlay_{e}_s{state}.png')); x, y = boxes[e][:2]; h, w = o.shape[:2]
        m = o[..., 3] > 0
        sub = out[y:y + h, x:x + w, :3]; sub[m] = o[..., :3][m]
    return out

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('master'); ap.add_argument('ov'); ap.add_argument('out')
    ap.add_argument('--scale', type=float, default=0.5); ap.add_argument('--fps', type=int, default=25); ap.add_argument('--seconds', type=float, default=P)
    ap.add_argument('--bg', default='38,62,52'); ap.add_argument('--blinks', default='2.0,5.4'); ap.add_argument('--frames', action='store_true')
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    master = np.array(Image.open(a.master).convert('RGBA')); boxes = json.load(open(f'{a.ov}/boxes.json'))
    idle = Idle(master[..., 3]); starts = [float(x) for x in a.blinks.split(',') if x]
    bg = np.array([int(x) for x in a.bg.split(',')], np.float32)
    n = int(round(a.seconds * a.fps)); frames = []
    for i in range(n):
        t = i / a.fps
        base = composite_eyes(master, a.ov, boxes, blink_state(t, starts))
        dx, dy = idle.field(t); f = warp(base, dx, dy)
        al = f[..., 3:4].astype(np.float32) / 255
        rgb = f[..., :3].astype(np.float32) * al + bg * (1 - al)
        small = cv2.resize(rgb, (int(f.shape[1] * a.scale), int(f.shape[0] * a.scale)), interpolation=cv2.INTER_AREA)
        frames.append(np.clip(small, 0, 255).astype(np.uint8))
        if a.frames: Image.fromarray(frames[-1]).save(f'{a.out}/f_{i:03d}.png')
    h, w = frames[0].shape[:2]; h -= h % 2; w -= w % 2; frames = [f[:h, :w] for f in frames]
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(a.fps), '-i', '-',
                          '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', f'{a.out}/aidan_idle_v1_preview.mp4'], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(f.tobytes())
    p.stdin.close(); p.wait()
    np.save(f'{a.out}/frames.npy', np.stack(frames)) if a.frames else None
    print('frames', n, 'size', w, h)

if __name__ == '__main__':
    main()
