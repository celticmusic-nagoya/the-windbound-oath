import hashlib, io, json, pathlib, sys, urllib.parse, urllib.request
import numpy as np
from PIL import Image, ImageDraw
ASSETS=('poly_wool_herringbone','stretch_poplin','cotton_jersey')
LIMIT=12_000_000
UA='TWO-Morwen-MaterialQA/1.0 (Poly Haven source attribution)'
def require(ok,msg):
    if not ok: raise ValueError(msg)
def get(url,host,limit):
    u=urllib.parse.urlsplit(url);require(u.scheme=='https' and u.hostname==host and u.username is None and u.password is None,'invalid source URL')
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':UA}),timeout=35) as r:
        final=urllib.parse.urlsplit(r.geturl());require(final.scheme=='https' and final.hostname==host,'unexpected redirect')
        data=r.read(limit+1)
    require(0<len(data)<=limit,'download bound');return data
def digest(b):return hashlib.sha256(b).hexdigest()
def select(meta,role):
    keys=[k for k in meta if k.lower() in {'diffuse':('diff','diffuse'),'normal':('nor_gl',),'rough':('rough','roughness')}[role]]
    require(len(keys)==1,'missing or ambiguous map '+role)
    files=meta[keys[0]]['1k']; formats=('png','jpg') if role=='normal' else ('jpg','png')
    fmt=next((x for x in formats if x in files),None);require(fmt is not None,'missing 1k raster format')
    return fmt,files[fmt]
def verify(raw,item):
    require(len(raw)==item['size'] and hashlib.md5(raw).hexdigest()==item['md5'].lower(),'provider size/MD5 mismatch')
def process(raw,role):
    with Image.open(io.BytesIO(raw)) as im:
        w,h=im.size
        # 1K is a provider resolution tier, not a promise of a square 1024 atlas.
        require(im.format in ('JPEG','PNG') and 128<=min(w,h)<=max(w,h)<=4096 and w*h<=8_388_608, f'bad format or dimensions: {im.format} {w}x{h} {im.mode}')
        if role=='rough':
            if im.mode in ('I;16','I;16B','I;16L','I'):
                v=np.asarray(im).astype(np.int64); require(v.min()>=0 and v.max()<=65535,'scalar range invalid')
                a=((v*255+32767)//65535).astype(np.uint8)
            else:
                require(im.mode in ('L','RGB'),'rough map mode unsupported');a=np.asarray(im.convert('L')).copy()
        else:
            require(im.mode=='RGB','expected RGB map');a=np.asarray(im).copy()
        # Original source bytes retained independently; analysis uses decoded 8-bit samples.
    return a
def compare(rgb):
    f=rgb.astype(float)/255;lin=np.where(f<=.04045,f/12.92,((f+.055)/1.055)**2.4);lum=lin@np.array([.2126,.7152,.0722]);med=float(np.median(lum));require(med>1e-5,'dark source');detail=np.clip(lum/med,.72,1.28)
    base=np.array([52,38,60])/255;base=np.where(base<=.04045,base/12.92,((base+.055)/1.055)**2.4);v=np.clip(base*detail[:,:,None],0,1);return np.rint(255*np.where(v<=.0031308,12.92*v,1.055*v**(1/2.4)-.055)).astype(np.uint8)
def save(out,name,a):
    p=out/name;Image.fromarray(a).save(p);require(np.array_equal(np.asarray(Image.open(p)),a),'PNG reopen mismatch');return {'file':name,'sha256':digest(p.read_bytes()),'pixel_sha256':digest(a.tobytes()),'shape':list(a.shape)}
def preflight():
    b=io.BytesIO();Image.new('RGB',(1024,512),(120,100,80)).save(b,format='PNG');raw=b.getvalue();item={'size':len(raw),'md5':hashlib.md5(raw).hexdigest(),'url':'https://dl.polyhaven.org/example.png'};meta={'Diffuse':{'1k':{'png':item}},'nor_gl':{'1k':{'png':item}},'Rough':{'1k':{'png':item}}}
    assert select(meta,'diffuse')[1]==item;verify(raw,item);a=process(raw,'diffuse');assert np.all(compare(a)==[52,38,60]);assert process(raw,'rough').shape==(512,1024)
    for fn in (lambda:verify(raw+b'x',item),lambda:select({},'normal'),lambda:compare(np.zeros_like(a)),lambda:process(b'not png','normal')):
        try:fn()
        except (ValueError,OSError):continue
        raise AssertionError('negative fixture accepted')
    for size in ((2048,1024),(768,1536)):
        f=io.BytesIO();Image.new('RGB',size,(120,100,80)).save(f,format='JPEG');assert process(f.getvalue(),'diffuse').shape==(size[1],size[0],3)
    f=io.BytesIO();Image.fromarray(np.full((128,256),32768,dtype=np.uint16)).save(f,format='PNG');assert np.all(process(f.getvalue(),'rough')==128)
    f=io.BytesIO();Image.new('RGB',(4097,128)).save(f,format='PNG')
    try:process(f.getvalue(),'diffuse')
    except ValueError:pass
    else:raise AssertionError('oversize accepted')
    print('FIXTURE_PASS 12 checks')
def main(out):
    out.mkdir(exist_ok=False);rec={'scope':'ISOLATED_MATERIAL_COMPARISON_NOT_ADOPTED','provider':'Poly Haven','license':'CC0','license_url':'https://polyhaven.com/license','api_terms':'https://polyhaven.com/our-api','assets':{}}
    sheet=Image.new('RGB',(900,660),(24,24,30));draw=ImageDraw.Draw(sheet)
    for j,asset in enumerate(ASSETS):
        folder=out/asset;folder.mkdir();meta_raw=get('https://api.polyhaven.com/files/'+asset,'api.polyhaven.com',1_000_000);meta=json.loads(meta_raw);(folder/'api-files.json').write_bytes(meta_raw);r={'source':'https://polyhaven.com/a/'+asset,'api_metadata_sha256':digest(meta_raw),'maps':{}};arrays={}
        for role in ('diffuse','normal','rough'):
            fmt,item=select(meta,role);require(0<item['size']<=LIMIT,'map exceeds budget');raw=get(item['url'],'dl.polyhaven.org',LIMIT);verify(raw,item);(folder/(role+'.'+fmt)).write_bytes(raw);
            with Image.open(io.BytesIO(raw)) as header: print(asset,role,header.format,header.size,header.mode,flush=True)
            a=process(raw,role);arrays[role]=a;r['maps'][role]={'url':item['url'],'format':fmt,'sha256':digest(raw),'md5':item['md5'],'size':len(raw),'decoded_shape':list(a.shape),'pixel_sha256':digest(a.tobytes())}
        require(arrays['diffuse'].shape[:2]==arrays['normal'].shape[:2]==arrays['rough'].shape,'map dimensions mismatch')
        color=compare(arrays['diffuse']);r['trial_color']=save(folder,'common-violet.png',color);r['roughness_mean']=float(arrays['rough'].mean()/255);r['roughness_std']=float(arrays['rough'].std()/255);r['normal_xy_std']=float(arrays['normal'][:,:,:2].std()/255);r['wrap_mean_abs_rgb']=[float(np.abs(color[:,0].astype(float)-color[:,-1]).mean()),float(np.abs(color[0].astype(float)-color[-1]).mean())];rec['assets'][asset]=r
        draw.text((12,j*220+8),asset,fill='white')
        for k,im in enumerate((arrays['diffuse'],color,arrays['normal'],arrays['rough'])):
            panel=Image.fromarray(im).convert('RGB');panel.thumbnail((210,180));sheet.paste(panel,(12+220*k,j*220+30));draw.text((12+220*k,j*220+207),('source','common violet','normal GL','roughness')[k],fill='white')
        (out/'receipt.json').write_text(json.dumps(rec,indent=2)+'\n')
    sheet.save(out/'comparison.png');print('ACQUIRED 3 assets / 9 maps; candidate only')
if __name__=='__main__':
    preflight()
    if len(sys.argv)==2 and sys.argv[1]!='--self-test':main(pathlib.Path(sys.argv[1]))
