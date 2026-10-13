#!/usr/bin/env python3
"""Read-only validation of 18 prepared RGBA Aidan frames; artwork semantics still need human review."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
from PIL import Image,ImageChops,ImageDraw,ImageOps

GROUPS={'side_right':4,'front_left':6,'back_left':6,'idle_front_left':1,'idle_back_left':1}


def template():
    frames=[]
    for group,n in GROUPS.items():
        for i in range(1,n+1):frames.append({'file':f'aidan_{group}_{i:02d}.png','group':group,'index':i})
    return {'stage':'prepared','canvas':[2048,1280],'anchor':[1024,1230],'alpha_threshold':235,'feet_y_tolerance':8,'feet_x_tolerance':32,
            'body_height_relative_tolerance':.04,'minimum_transparent_fraction':.005,'frames':frames,
            'notes':'Filenames are intake aliases, not runtime frame IDs. Add mirror_file to check mechanically mirrored counterparts.'}


def local_file(directory,name):
    p=(directory/name).resolve()
    if not p.is_relative_to(directory.resolve()):raise ValueError('file escapes asset directory: '+name)
    return p


def measure(path,threshold):
    with Image.open(path)as im:
        rgba=im.convert('RGBA');alpha=rgba.getchannel('A');mask=alpha.point(lambda v:255 if v>=threshold else 0)
        box=mask.getbbox();hist=alpha.histogram();total=im.width*im.height
        if not box:raise ValueError('no opaque character pixels')
        x0,y0,x1,y1=box;band_y=max(y0,y1-max(1,round((y1-y0)*.06)))
        feet=mask.crop((0,band_y,im.width,y1)).getbbox()
        return {'format':im.format,'mode':im.mode,'size':list(im.size),'bounds':list(box),'opaque_bottom':y1,
                'feet_center_x':(feet[0]+feet[2])/2,'body_height':y1-y0,'transparent_fraction':hist[0]/total,
                'corner_alphas':[alpha.getpixel(p)for p in [(0,0),(im.width-1,0),(0,im.height-1),(im.width-1,im.height-1)]],
                'edge_clipped':x0==0 or y0==0 or x1==im.width or y1==im.height,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def inspect(directory,spec):
    errors=[];rows=[];frames=spec['frames']
    counts={g:sum(f.get('group')==g for f in frames)for g in GROUPS}
    if len(frames)!=18 or counts!=GROUPS:errors.append('manifest must have exact group counts '+str(GROUPS))
    source=[f['file']for f in frames]
    if len(set(source))!=len(source):errors.append('duplicate source filenames')
    for group,n in GROUPS.items():
        if sorted(f.get('index')for f in frames if f.get('group')==group)!=list(range(1,n+1)):errors.append('missing/duplicate index in '+group)
    expected=set(source)|{f['mirror_file']for f in frames if f.get('mirror_file')}
    extras=[str(p.relative_to(directory))for p in directory.rglob('*.png')if str(p.relative_to(directory))not in expected]
    if extras:errors.append('unmapped PNGs: '+str(extras))
    for frame in frames:
        row={'file':frame['file'],'group':frame.get('group'),'errors':[],'review':['Sword on back, face/costume/pose/boot contact require visual acceptance.']}
        try:
            path=local_file(directory,frame['file']);metric=measure(path,spec.get('alpha_threshold',235));row['metrics']=metric
            if metric['format']!='PNG' or metric['mode']!='RGBA':row['errors'].append('PNG RGBA required')
            if metric['size']!=spec['canvas']:row['errors'].append('canvas size mismatch')
            if metric['transparent_fraction']<spec.get('minimum_transparent_fraction',.005):row['errors'].append('no sufficient real alpha transparency')
            if any(metric['corner_alphas']):row['errors'].append('opaque/semitransparent canvas corner')
            if metric['edge_clipped']:row['errors'].append('character touches canvas edge')
            anchor=frame.get('anchor',spec['anchor'])
            row['feet_dy']=metric['opaque_bottom']-anchor[1];row['feet_dx']=metric['feet_center_x']-anchor[0]
            if abs(row['feet_dy'])>spec['feet_y_tolerance']:row['errors'].append('feet baseline drift')
            if abs(row['feet_dx'])>spec['feet_x_tolerance']:row['errors'].append('feet horizontal registration drift')
            mirror=frame.get('mirror_file')
            if mirror:
                mirror_path=local_file(directory,mirror)
                with Image.open(path)as im,Image.open(mirror_path)as other:
                    if im.size!=other.size:row['errors'].append('mirror canvas mismatch')
                    else:
                        difference=ImageChops.difference(ImageOps.mirror(im.convert('RGBA')),other.convert('RGBA'))
                        if any(b.getbbox()for b in difference.split()):row['errors'].append('counterpart is not the promised exact RGBA mirror')
                mm=measure(mirror_path,spec.get('alpha_threshold',235));row['mirror_metrics']=mm
                if abs(mm['feet_center_x']-(spec['canvas'][0]-metric['feet_center_x']))>spec['feet_x_tolerance']:row['errors'].append('mirror feet symmetry mismatch')
                if abs(mm['opaque_bottom']-metric['opaque_bottom'])>spec['feet_y_tolerance']:row['errors'].append('mirror baseline mismatch')
            else:row['review'].append('Opposite-facing image not supplied: actual left/right mirror check unperformed.')
        except (OSError,ValueError,KeyError)as exc:row['errors'].append(str(exc))
        row['technical_status']='FAIL'if row['errors']else'PASS';rows.append(row)
    heights=[r['metrics']['body_height']for r in rows if 'metrics'in r]
    if heights:
        import statistics
        median=statistics.median(heights)
        for row in rows:
            if 'metrics'in row and abs(row['metrics']['body_height']/median-1)>spec['body_height_relative_tolerance']:
                row['errors'].append('character height differs from shared median');row['technical_status']='FAIL'
    return {'source_frames':len(frames),'group_counts':counts,'global_errors':errors,'rows':rows,
            'technical_pass':not errors and all(r['technical_status']=='PASS'for r in rows),
            'artwork_acceptance':'REVIEW_REQUIRED','limitations':'Opaque bottom/feet-band centre are registration proxies; cannot identify anatomical feet, shadows, sword presence or pose authenticity.'}


def self_test():
    with tempfile.TemporaryDirectory(prefix='aidan-intake-check-')as t:
        directory=Path(t);spec=template();spec.update(canvas=[256,384],anchor=[128,360],feet_y_tolerance=3,feet_x_tolerance=5)
        for f in spec['frames']:
            im=Image.new('RGBA',(256,384));d=ImageDraw.Draw(im);d.rectangle((108,60,147,319),fill=(60,100,70,255));d.rectangle((111,320,124,359),fill=(90,70,40,255));d.rectangle((132,320,144,359),fill=(90,70,40,255))
            im.save(directory/f['file']);f['mirror_file']='mirror/'+f['file'];(directory/'mirror').mkdir(exist_ok=True);ImageOps.mirror(im).save(directory/f['mirror_file'])
        positive=inspect(directory,spec);assert positive['technical_pass']
        cases={}
        target=directory/spec['frames'][0]['file'];original=target.read_bytes()
        for label,mutate in [('size',lambda im:im.resize((128,384))),('alpha',lambda im:im.convert('RGB')),('baseline',lambda im:ImageChops.offset(im,0,-15)),('horizontal',lambda im:ImageChops.offset(im,20,0))]:
            with Image.open(target)as im:new=mutate(im);new.save(target)
            report=inspect(directory,spec);assert not report['technical_pass'];cases[label]=report['rows'][0]['errors'];target.write_bytes(original)
        missing=directory/spec['frames'][1]['file'];saved=missing.read_bytes();missing.unlink();assert not inspect(directory,spec)['technical_pass'];missing.write_bytes(saved);cases['missing']='detected'
        wrong=directory/spec['frames'][0]['mirror_file'];saved=wrong.read_bytes();wrong.write_bytes(original);assert not inspect(directory,spec)['technical_pass'];wrong.write_bytes(saved);cases['mirror']='detected'
        short={**spec,'frames':spec['frames'][:-1]};assert not inspect(directory,short)['technical_pass'];cases['count']='detected'
        print(json.dumps({'dummy_18_pass':True,'dummy_rows':[{'file':r['file'],'technical_status':r['technical_status'],'feet_dx':r['feet_dx'],'feet_dy':r['feet_dy']}for r in positive['rows']],'negative_cases':cases,'real_assets':'not received/unchecked'},ensure_ascii=False,indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path);parser.add_argument('--manifest',type=Path);parser.add_argument('--json',action='store_true');parser.add_argument('--template',action='store_true');parser.add_argument('--self-test',action='store_true');args=parser.parse_args()
    if args.template:print(json.dumps(template(),ensure_ascii=False,indent=2));return
    if args.self_test:self_test();return
    if not args.directory:parser.error('directory required')
    spec=json.loads(args.manifest.read_text())if args.manifest else template();result=inspect(args.directory,spec)
    if args.json:print(json.dumps(result,ensure_ascii=False,indent=2))
    else:
        print('file | technical | feet dx/dy | issues')
        for row in result['rows']:print(f"{row['file']} | {row['technical_status']} | {row.get('feet_dx','—')}/{row.get('feet_dy','—')} | {'; '.join(row['errors'])}")
        for error in result['global_errors']:print('FAIL '+error)
        print('ARTWORK: REVIEW_REQUIRED')
    raise SystemExit(0 if result['technical_pass'] else 1)

if __name__=='__main__':main()
