"""Read-only PNG, scalar-channel, statistical registration and edge QA."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    folder = Path(__file__).resolve().parent
    arrays, rows = {}, {}
    for role, name in [('base_color','stone_basecolor.png'),('roughness','stone_roughness.png')]:
        path = folder / name
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            a = np.array(image)
            assert image.format == 'PNG' and image.mode == 'RGB'
            assert min(image.size) >= 1024
            assert a.std() > 3, 'flat placeholder'
            rows[role] = {'file':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'dimensions':list(image.size),'mode':image.mode,'std_8bit':float(a.std()),'lr_edge_mean_abs_delta_8bit':float(np.abs(a[:,0].astype(float)-a[:,-1].astype(float)).mean()),'tb_edge_mean_abs_delta_8bit':float(np.abs(a[0].astype(float)-a[-1].astype(float)).mean())}
            arrays[role] = a
    a, r = arrays['base_color'], arrays['roughness']
    assert a.shape == r.shape
    ag = (a * [.2126,.7152,.0722]).sum(2)/255
    rg = r[:,:,0].astype(float)/255  # actual scalar used by Blender
    fa, fr = np.fft.rfft2(ag-ag.mean()), np.fft.rfft2(rg-rg.mean())
    cross = fa*np.conj(fr)
    cross /= np.maximum(np.abs(cross),1e-9)
    cc = np.fft.irfft2(cross,s=ag.shape)
    pos = np.unravel_index(cc.argmax(),cc.shape)
    shift = [int(v if v <= size//2 else v-size) for v,size in zip(pos,ag.shape)]
    y = np.fft.fftfreq(ag.shape[0])[:,None]
    x = np.fft.rfftfreq(ag.shape[1])[None,:]
    gaussian = np.exp(-2*np.pi**2*4*(x*x+y*y))
    low_a = np.fft.irfft2(np.fft.rfft2(ag)*gaussian,s=ag.shape)
    low_r = np.fft.irfft2(np.fft.rfft2(rg)*gaussian,s=rg.shape)
    assert shift == [0,0], 'nonzero global registration shift'
    report = {'status':'PASS_IMAGE_HANDOFF_SUBSET','maps':rows,'roughness_R_quantiles':dict(zip(['min','p01','p05','median','p95','p99','max'],np.quantile(r[:,:,0]/255,[0,.01,.05,.5,.95,.99,1]).tolist())),'roughness_RGB_max_channel_difference_8bit':int((r.max(2).astype(int)-r.min(2).astype(int)).max()),'roughness_scalar_policy':'Use R only, Non-Color; channels are not numerically identical','registration':{'global_phase_shift_yx_pixels':shift,'phase_peak':float(cc.max()),'raw_luminance_correlation':float(np.corrcoef(ag.ravel(),rg.ravel())[0,1]),'sigma2_lowfrequency_correlation':float(np.corrcoef(low_a.ravel(),low_r.ravel())[0,1]),'limit':'Global alignment check only; semantic micro-feature correspondence is inferred, not measured geometry'},'tiling':'NOT_VALIDATED_SEAMLESS; use CLIP and UV islands inside image; no whole-wall stamped repeat','normal_height_mortar_mask':'NOT_DELIVERED: author from actual geometry/mortar ownership in Claude phase, not grayscale albedo','G2_independent_final_material':'NOT_RUN','G3_masonry_UV_support':'NOT_RUN','G4':'NOT_RUN'}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'dimensions':rows['base_color']['dimensions'],'global_shift':shift}))


if __name__ == '__main__':
    main()
