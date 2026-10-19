"""Build the game-ready derivatives of the 20 moss additional assets from the untouched split masters.
 1. faint-alpha cleanup: pixels with alpha 1..8 whose distance to the nearest visible pixel (alpha>8) exceeds CLEAN_R master-px are set to alpha 0.
    Alpha>=9 pixels are never touched; RGB of every pixel is never touched; the natural soft glow hugging the contour is kept.
 2. tree_log_hollow_A3_01: transparent bottom margin added (object pixels unchanged, no rescale) so the root tip no longer touches the canvas edge.
 3. game derivative: premultiplied-alpha Lanczos downscale to 2x world size (repo convention, see tools/moss/install_delivered_art.py), written to img/field/moss/art/.
 Writes docs/art/delivered/moss_additional_20261019/quality/{report.json, diff_*.png, log_hollow_before_after.jpg}. Masters/originals are not modified."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[2]; D = ROOT / 'docs/art/delivered/moss_additional_20261019'; M = D / 'split_masters'; Q = D / 'quality'; OUT = ROOT / 'img/field/moss/art'
CLEAN_R = 10; LOG_BOTTOM_PAD = 24
# world size: ('w'|'h', world px)  -> game sprite is 2x that
WORLD = {'fern_cluster_01': ('w', 70), 'fern_cluster_02': ('w', 110), 'fern_cluster_03': ('w', 90),
         'bush_forest_01': ('w', 90), 'bush_forest_02': ('w', 140), 'bush_forest_03': ('w', 100),
         'rock_moss_01': ('w', 100), 'rock_moss_02': ('w', 150), 'rock_moss_03': ('w', 130),
         'root_exposed_01': ('w', 150), 'root_exposed_02': ('w', 230),
         'stump_rot_01': ('w', 80), 'stump_rot_02': ('w', 110),
         'mushroom_cluster_01': ('w', 60), 'mushroom_cluster_02': ('w', 60),
         'ruins_stone_01': ('w', 90), 'ruins_stone_02': ('w', 130),
         'tree_ancient_great_01': ('w', 420), 'tree_ancient_sentinel_01': ('h', 300), 'tree_log_hollow_A3_01': ('w', 340)}
def main():
    rep = {}
    for i, v in WORLD.items():
        src = np.array(Image.open(M / (i + '.png')).convert('RGBA')); a = src[..., 3]
        vis = a > 8; faint = (a > 0) & (a <= 8); dist = ndi.distance_transform_edt(~vis)
        kill = faint & (dist > CLEAN_R)
        out = src.copy(); out[..., 3][kill] = 0
        assert (out[..., :3] == src[..., :3]).all() and (out[..., 3][a > 8] == a[a > 8]).all()   # RGB untouched, alpha>=9 untouched
        r = {'master_size': [src.shape[1], src.shape[0]], 'faint_a1_8_total': int(faint.sum()), 'cleaned_px': int(kill.sum()), 'kept_contour_glow_px': int((faint & ~kill).sum()),
             'visible_px_changed': 0, 'rgb_changed': 0}
        if i == 'tree_log_hollow_A3_01':
            h0 = out.shape[0]; out = np.vstack([out, np.zeros((LOG_BOTTOM_PAD, out.shape[1], 4), np.uint8)])
            r['bottom_pad_px'] = LOG_BOTTOM_PAD; r['size_after_pad'] = [out.shape[1], out.shape[0]]
            ys, xs = np.where(out[..., 3] > 8); r['object_bottom_row'] = int(ys.max()); r['anchor_note'] = 'object foot is %d master px above the canvas bottom (= %.1f world px at w=340)' % (out.shape[0] - 1 - ys.max(), (out.shape[0] - 1 - ys.max()) * 340 / out.shape[1])
            assert (out[:h0][..., :3] == src[..., :3]).all() and (out[:h0][..., 3][a > 8] == a[a > 8]).all()
            Image.fromarray(out, 'RGBA').save(Q / 'tree_log_hollow_A3_01_clean_padded_master.png', optimize=True)
        # changed pixel map (for the review)
        dif = np.zeros(src.shape[:2] + (3,), np.uint8); dif[kill] = (255, 0, 0); dif[(a > 8)] = (40, 40, 40)
        small = Image.fromarray(dif); s = 700 / max(small.size); small.resize((int(small.width * s), int(small.height * s)), Image.NEAREST).save(Q / ('diff_%s.png' % i), optimize=True)
        im = Image.fromarray(out, 'RGBA'); w0, h0_ = im.size
        wr = v[1] / w0 if v[0] == 'w' else v[1] / h0_; gw, gh = max(1, round(w0 * wr * 2)), max(1, round(h0_ * wr * 2))
        g = im.convert('RGBa').resize((gw, gh), Image.LANCZOS).convert('RGBA'); g.save(OUT / (i + '.png'), optimize=True)
        r.update({'game_px': [gw, gh], 'world_px': [round(gw / 2, 1), round(gh / 2, 1)], 'manifest_wh': [round(gw / 2, 1), round(gh / 2, 1)]})
        ga = np.array(g)[..., 3]; r['game_edge_alpha_max'] = int(max(ga[0].max(), ga[-1].max(), ga[:, 0].max(), ga[:, -1].max())); r['game_faint_px_a1_8'] = int(((ga > 0) & (ga <= 8)).sum())
        rep[i] = r
    json.dump(rep, open(Q / 'report.json', 'w'), indent=1)
    tot = sum(r['cleaned_px'] for r in rep.values()); print('cleaned px total', tot, 'of', sum(r['faint_a1_8_total'] for r in rep.values()))
main()
