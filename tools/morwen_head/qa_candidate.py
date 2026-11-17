"""Screen render visibility, frame margins and mesh integrity; never approve art."""
import argparse
import hashlib
import json
import pathlib
import sys
from PIL import Image, ImageDraw
import numpy as np


def main():
    ap=argparse.ArgumentParser();ap.add_argument('output');a=ap.parse_args()
    root=pathlib.Path(a.output);e=json.loads((root/'build_evidence.json').read_text())
    rows=[]
    for v in e['views']:
        path=root/v['file'];im=Image.open(path);p=np.asarray(im.convert('RGBA'));mask=p[:,:,3]>16
        ys,xs=np.where(mask);n=int(mask.sum())
        opaque=p[:,:,:3][mask]
        clipped=float(np.mean(np.all(opaque>=250,axis=1))) if n else 1
        shadow=float(np.mean(np.all(opaque<=5,axis=1))) if n else 1
        bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if n else None
        margin=v.get('head_geometry_in_frame',bool(n and xs.min()>3 and ys.min()>3 and xs.max()<im.width-4 and ys.max()<im.height-4))
        row={'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'mode':im.mode,'size':im.size,'nonzero_alpha_pixels':n,'coverage':n/(im.width*im.height),'bbox':bbox,'margin_pass':margin,'crop_policy':v.get('crop_policy','full body alpha margins'),'white_clip_fraction':clipped,'black_crush_fraction':shadow}
        row['pass']=im.mode=='RGBA' and n>500 and margin and clipped<.01 and shadow<.05
        rows.append(row)
    bad=[r for r in e['mesh_stats'] if r['nonmanifold_edges'] or r['degenerate_faces']]
    ratio=e['landmarks']['head_count']
    checks={'source_unchanged':e['source_unchanged'],'reopen':e['reopen_pass'],'mesh_nonempty':all(r['vertices']>0 and r['faces']>0 for r in e['mesh_stats']),'closed_nondegenerate_base_meshes':not bad,'five_or_more_views':len(rows)>=5,'anatomical_ratio_self_review':7.5<=ratio<=8,'rgba_frame_visibility':all(r['pass'] for r in rows)}
    report={'status':'PASS_TECHNICAL_SCREEN' if all(checks.values()) else 'FAIL_TECHNICAL_SCREEN','checks':checks,'head_count':ratio,'mesh_defects':bad,'renders':rows,'scope_limitations':['Self-reviewed anatomical vertices; independent confirmation pending','Normals recalculated; manifold screen is not a self-intersection or rigging test','Eyeball/socket, glasses/skin and hair intersections require visual review','No independent art acceptance or game/Android test'],'gates':{'G1':'BLOCKED: source SHA PASS, candidate fidelity not accepted','G2':'NOT_RUN: independent art QA; self visual findings in report','G3':'PASS_TECHNICAL_SCREEN' if all(checks.values()) else 'FAIL','G4':'NOT_RUN'}}
    (root/'technical_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    thumbs=[]
    for v in e['views'][:6]:
        im=Image.open(root/v['file']).convert('RGBA');bg=Image.new('RGBA',im.size,(42,43,49,255));bg.alpha_composite(im);bg=bg.convert('RGB');bg.thumbnail((384,384))
        tile=Image.new('RGB',(384,416),(42,43,49));tile.paste(bg,((384-bg.width)//2,24));ImageDraw.Draw(tile).text((12,8),v['name'],fill='white');thumbs.append(tile)
    sheet=Image.new('RGB',(1152,832))
    for i,im in enumerate(thumbs):sheet.paste(im,((i%3)*384,(i//3)*416))
    sheet.save(root/'head_contact_sheet.png')
    # The manifest includes every deliverable except itself; no circular hashes.
    files=[p for p in root.rglob('*') if p.is_file() and p.name not in {'SHA256SUMS','artifact_manifest.json'} and not p.name.endswith('.blend1')]
    (root/'SHA256SUMS').write_text(''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+str(p.relative_to(root))+'\n' for p in sorted(files)))
    print(json.dumps({'status':report['status'],'checks':checks}))
    return 0 if all(checks.values()) else 2

if __name__=='__main__':sys.exit(main())
