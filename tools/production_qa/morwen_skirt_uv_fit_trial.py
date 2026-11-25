"""2D UV fit trial; observed coarse projection only, NOT final garment mapping."""
import hashlib, json, pathlib, sys
import numpy as np
from PIL import Image
EXPECTED=['7b5558f4d6a548cd15e7803161532c8fbad5e98b25ffc49e094ae646a882ae83','7287b8aa970aed092a87d6fc89aa09a2419edbf5d37316afae9424c32fc66db3','22b6e4634d7f0e9f600d52a9180b2ba25fadab43c31979b4674634c7f4251ca4']
def sha(b):return hashlib.sha256(b).hexdigest()
def compose(paths,out):
    images=[]
    for p,h,sz in zip(paths,EXPECTED,[(1024,512),(1024,512),(1024,128)]):
        p=pathlib.Path(p);assert sha(p.read_bytes())==h
        with Image.open(p) as im:
            assert im.mode=='RGBA' and im.size==sz
            images.append(np.array(im))
    dark,plaid,trim=images; assert np.all(dark[:,:,3]==255) and np.all(plaid[:,:,3]==255)
    # Fit a complete authored plaid repeat rather than crop away its vertical stripes.
    tile=np.array(Image.fromarray(plaid[:,:512]).resize((96,96),Image.Resampling.LANCZOS))
    result=dark.copy();result[:,464:560]=tile[np.arange(512)%96]
    # Front-centered panel is a hypothesis; trim centered approximately y480,495.
    # Neutral dark rear is a test substrate only, not a canonical design assignment.
    y=np.arange(448,512); t=trim[(y-12)%128]; a=t[:,:,3,None].astype(np.int32)
    old=result[448:,:,:3].astype(np.int32)
    result[448:,:,:3]=((t[:,:,:3].astype(np.int32)*a+old*(255-a)+127)//255).astype(np.uint8)
    assert np.array_equal(result[:,:,3],dark[:,:,3]);assert np.array_equal(result[:448,:464],dark[:448,:464]);assert np.array_equal(result[:448,560:],dark[:448,560:])
    out=pathlib.Path(out);out.mkdir(exist_ok=True); target=out/'skirt-uv-fit-trial.png';assert not target.exists();Image.fromarray(result).save(target)
    assert np.array_equal(np.array(Image.open(target)),result)
    rec={'scope':'VOLATILE_UV_FIT_TRIAL_ONLY','source_artifact':15023063410,'source_grid_pixel_sha256':'b7e62a61c9f58611e0abe455d43ab442f4fcf5a342ec026879887556038c3f26','sources':EXPECTED,'panel_x_px_half_open':[464,560],'trial_plaid_repeat_px':[96,96],'trim_centers_y_px':[480,495],'uncertainty':'coarse 128px grid; exact hem/panel boundaries and rear design unresolved','alpha_exact':True,'reopen_exact':True,'wrap_mean_abs_rgb':float(np.abs(result[:,0,:3].astype(float)-result[:,-1,:3]).mean()),'png_sha256':sha(target.read_bytes()),'pixel_sha256':sha(result.tobytes()),'native_import':'NOT_RUN','formal_adoption':False};(out/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps(rec,indent=2))
if __name__=='__main__':compose(sys.argv[1:4],sys.argv[4])
