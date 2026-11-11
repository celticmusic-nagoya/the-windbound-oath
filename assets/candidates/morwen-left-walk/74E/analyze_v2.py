"""metrics from ann_v2.json (manual keypoints) + v2_series.json (automatic silhouette series)."""
import json, math
import numpy as np
A = json.load(open('ann_v2.json')); S = json.load(open('v2_series.json'))
HS_A, HS_B, HS_A2, TO_A = 134, 187, 240, 204
CYC = HS_A2 - HS_A
GROUND = 325
def ang(p, q):   # angle of p->q from vertical, + = forward (to +x)
    return math.degrees(math.atan2(q[0] - p[0], q[1] - p[1]))
rows = []
Lmid = math.hypot(A['160']['AA'][0] - A['160']['H'][0], A['160']['AA'][1] - A['160']['H'][1])
for f, v in A.items():
    if f.startswith('_'): continue
    f = int(f); H = v['H']
    for leg, hs in (('A', HS_A), ('B', HS_B - CYC)):
        K, An, He, To = v['K' + leg], v['A' + leg], v['He' + leg], v['To' + leg]
        t = ((f - hs) / CYC) % 1.0
        thigh, shin = ang(H, K), ang(K, An)
        rows.append(dict(frame=f, leg=leg, t=round(t, 3), knee_flex_deg=round(thigh - shin, 1),
                         thigh_deg=round(thigh, 1), shin_deg=round(shin, 1),
                         foot_pitch_deg=round(math.degrees(math.atan2(He[1] - To[1], To[0] - He[0])), 1),
                         ankle_rel_hip_L=round((An[0] - H[0]) / Lmid, 3),
                         ankle_height_L=round((GROUND - 10 - An[1]) / Lmid, 3),
                         foot_clearance_px=GROUND - max(He[1], To[1])))
rows.sort(key=lambda r: (r['leg'], r['t']))
tops = [S[i - 1]['top'] for i in range(HS_A, HS_A2 + 1)]
body_h = GROUND - min(tops)
wr = []
for f, v in A.items():
    if f.startswith('_'): continue
    for w in ('WN', 'WF'):
        if w in v: wr.append(dict(frame=int(f), arm='near' if w == 'WN' else 'far', t=round((int(f) - HS_A) / CYC, 3), wrist_rel_hip_L=round((v[w][0] - v['H'][0]) / Lmid, 3)))
rep = {
    'video': 'animation_reference_-_female_standard_walk_-_grid_overlay_360p.mp4 (640x360, 25 fps, 24.72 s, 618 frames; split screen: left = side view, right = front view; every frame is shown twice -> 12.5 unique fps; slow motion)',
    'cycle_frames': CYC, 'cycle_video_seconds': CYC / 25, 'step_frames_median': 53,
    'events': {'heel_strike_far_leg': HS_A, 'heel_strike_near_leg': HS_B, 'toe_off_far_leg': TO_A, 'next_heel_strike_far_leg': HS_A2},
    'stance_share': round((TO_A - HS_A) / CYC, 3), 'swing_share': round(1 - (TO_A - HS_A) / CYC, 3),
    'double_support_share_each': round((TO_A - HS_B) / CYC, 3),
    'head_top_range_px': [min(tops), max(tops)], 'head_bob_share_of_height': round((max(tops) - min(tops)) / body_h, 4),
    'head_low_plateau': 'lowest from heel strike through loading (about 0-0.15 of each step), highest at mid-stance',
    'leg_length_hip_to_ankle_px': round(Lmid, 1), 'body_height_px': body_h,
    'step_length_heel_to_heel_L': round((A['187']['HeB'][0] - A['187']['HeA'][0]) / Lmid, 3),
    'legs': rows, 'wrists': wr,
    'notes': ['subject is camera-followed (planted foot moves backwards in frame); all positions are relative to the hip',
              'side view: far leg = A (leading at f134), near leg = B; near arm forward at the far-leg heel strike (contralateral)',
              'joint positions are manual annotations (+-3 px); head top / pelvis x / foot spread are automatic silhouette measurements']}
json.dump(rep, open('VIDEO_ANALYSIS_74E.json', 'w'), indent=1, ensure_ascii=False)
print({k: v for k, v in rep.items() if k not in ('legs', 'wrists', 'notes')})
for r in rows: print(r)
for w in wr: print(w)
