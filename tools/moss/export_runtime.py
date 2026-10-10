#!/usr/bin/env python3
"""Design JSON (schema v2) -> runtime JSON.
 - every blocker becomes shape 'rects' (ellipse/polygon -> 8px stripes), the only form FieldCollision accepts
 - collision.presets: asset -> relative rects (feet-anchor), applied to props and scatter entities
 - scatter[].render: 'layer' (baked into chunk canvases, no DOM node) or 'node' (culled DOM entity)
usage: export_runtime.py <design.json> <out.json>"""
import json,sys,os,re
sys.path.insert(0,os.path.dirname(__file__))
import mf_lib as L
LAYER=re.compile(r'^(gnd_|veg_grass|veg_flower|veg_fern|veg_reeds|veg_mush|deco_|litter_|fx_)')
def main(src,dst):
    m=json.load(open(src,encoding='utf-8'))
    c=m['collision']
    c['blockers']=[{**{k:v for k,v in b.items() if k in('id','tag','enabledWhen')},'shape':'rects','rects':L.shape_rects(b)} for b in c['blockers']]
    c['edgeBlockers']=[{'shape':'rect',**{k:s[k] for k in('x','y','w','h')}} if s['shape']=='rect' else {'shape':'rects','rects':L.shape_rects(s)} for s in c['edgeBlockers']]
    assets={p['asset'] for p in m['props']}|{a for s in m['scatter'] for a in s['pool']}
    c['presets']={re.sub(r'_\d+$','',a):L.preset(a) for a in sorted(assets) if L.preset(a)}
    for s in m['scatter']:
        s['render']='layer' if all(LAYER.match(a) for a in s['pool']) else 'node'
    json.dump(m,open(dst,'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
    print('wrote',dst,'presets',len(c['presets']),'layer rules',sum(s['render']=='layer' for s in m['scatter']),'of',len(m['scatter']))
if __name__=='__main__': main(*sys.argv[1:3])
