"""Produce review-only Lou field candidates outside adopted assets."""
import argparse,json,subprocess
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('/tmp/lou-field-proposal'));p.add_argument('--height',type=int,default=120);a=p.parse_args()
    if a.height<52: p.error('height must be >= 52px')
    out=a.output.resolve()
    if out==ROOT/'img' or ROOT/'img' in out.parents:p.error('adopted img tree is forbidden')
    out.mkdir(parents=True,exist_ok=True)
    js="global.window=global;require('./js/assets.js');process.stdout.write(JSON.stringify(BATTLE_IDLE_ASSETS.lou))"
    spec=json.loads(subprocess.check_output(['node','-e',js],cwd=ROOT));rows=[]
    for f in spec['frames']:
        src=ROOT/f['path'];im=Image.open(src).convert('RGBA');scale=a.height/im.height;size=(round(im.width*scale),a.height)
        small=im.resize(size,Image.Resampling.LANCZOS);png=out/src.name;webp=out/(src.stem+'.webp');small.save(png,optimize=True);small.save(webp,lossless=True,method=6)
        rows.append(dict(source=f['path'],source_size=list(im.size),source_bytes=src.stat().st_size,png=png.name,png_bytes=png.stat().st_size,webp=webp.name,webp_bytes=webp.stat().st_size,size=list(size),battle_anchor=f['anchor'],anchor=[f['anchor'][0]*size[0]/im.width,f['anchor'][1]*size[1]/im.height],alpha_bbox=small.getbbox()))
    report=dict(proposal_only=True,height=a.height,display_height=52,frames=rows,totals={k:sum(r[k] for r in rows) for k in ['source_bytes','png_bytes','webp_bytes']})
    (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report['totals']));return report
if __name__=='__main__':main()
