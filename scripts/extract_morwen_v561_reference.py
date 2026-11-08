#!/usr/bin/env python3
"""Extract reference-only crops from director-selected Morwen sheet.
Not a sprite converter. Requires Pillow. Fails closed on source mismatch.
"""
from pathlib import Path
from PIL import Image
import hashlib, json, sys
EXPECTED='47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638'
REGIONS={'down':(358,107,452,287),'right':(448,107,545,287),'up':(544,107,638,287),'left':(635,107,728,287)}
def extract(source,destination):
    source=Path(source);destination=Path(destination)
    digest=hashlib.sha256(source.read_bytes()).hexdigest()
    if digest!=EXPECTED:raise ValueError('Source is not director-approved canonical v5.61 image')
    with Image.open(source) as img:
        if img.size!=(1536,1024) or img.format!='JPEG':raise ValueError('Unexpected image format or dimensions')
        destination.mkdir(parents=True,exist_ok=True)
        files=[]
        for direction,rect in REGIONS.items():
            out=destination/(direction+'_REFERENCE_RGB.png')
            img.crop(rect).convert('RGB').save(out)
            files.append({'direction':direction,'file':out.name,'sha256':hashlib.sha256(out.read_bytes()).hexdigest()})
    (destination/'MANIFEST.json').write_text(json.dumps({'source_sha256':digest,'reference_only':True,'files':files},indent=2)+'\\n',encoding='utf-8')
if __name__=='__main__':
    if len(sys.argv)!=3:raise SystemExit('Usage: python extract_morwen_v561_reference.py <canonical.jpg> <output-dir>')
    extract(sys.argv[1],sys.argv[2])
