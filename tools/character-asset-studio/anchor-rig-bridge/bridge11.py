#!/usr/bin/env python3
"""Extract authored SVG anchor markers; no image-generation or guessed anatomy."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
STUDIO = BASE.parent
sys.path.insert(0, str(BASE/'qa/vendor'))
from bridge08 import JOINTS, VIEWS
from bridge10 import run as audit_real
from contact_audit import audit
_spec = importlib.util.spec_from_file_location('rig08_bridge11', STUDIO/'rig-integration/import_rig.py')
rig08 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rig08)
NS = {'s': 'http://www.w3.org/2000/svg'}
LABELS = {'headTop': 'crown', 'headCenter': 'head_center', 'neckBase': 'neck_base', 'pelvis': 'pelvis_center'}
LABELS.update({base+side: base+'_'+side for base in ('shoulder','elbow','wrist','hip','knee','ankle') for side in ('L','R')})


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')


def markers(path, view):
    root = ET.parse(path).getroot()
    if root.get('width') != '384' or root.get('height') != '1024':
        raise ValueError('unexpected SVG canvas')
    # Reject scripts/external content. Only the authored translation(0,0) is
    # present in these per-view originals; do not silently ignore a reflection.
    for node in root.iter():
        if node.tag.split('}')[-1] in ('script','foreignObject','image','use'):
            raise ValueError('external/executable SVG content')
        if 'transform' in node.attrib and node.get('transform') != 'translate(0,0)':
            raise ValueError('unhandled SVG transform')
    group = root.find(".//s:g[@id='guides-"+view+"']/s:g[@id='joints']", NS)
    if group is None:
        raise ValueError('labelled marker group missing')
    out = {}
    for circle in group.findall('s:circle', NS):
        title = circle.find('s:title', NS)
        if title is None or title.text in out:
            raise ValueError('missing/duplicate joint label')
        out[title.text] = [float(circle.get('cx')), float(circle.get('cy'))]
    return out


def measure(inputs):
    template = json.loads((inputs/'anchor_template.json').read_text())
    if template['sheet']['order'] != list(VIEWS):
        raise ValueError('unexpected sheet order')
    sheet = ET.parse(inputs/'anchor_template_sheet.svg').getroot()
    if sheet.get('width') != '1536' or sheet.get('height') != '1024':
        raise ValueError('unexpected sheet canvas')
    results = {}
    for view in VIEWS:
        path = inputs/f'anchor_template_{view}.svg'
        points = markers(path, view)
        sheet_view = sheet.find("s:g[@id='view-"+view+"']", NS)
        offset = template['sheet']['view_offset_x'][view]
        if sheet_view is None or sheet_view.get('transform') != f'translate({offset},0)':
            raise ValueError('sheet view transform disagrees')
        sheet_points = {c.find('s:title',NS).text: [float(c.get('cx')),float(c.get('cy'))]
            for c in sheet_view.findall(".//s:g[@id='joints']/s:circle",NS)}
        if sheet_points != points:
            raise ValueError('sheet/local SVG markers disagree')
        if points.get('ground_center') != [192,984]:
            raise ValueError('declared ground mismatch')
        for label, xy in points.items():
            if xy != template['joints'][view].get(label):
                raise ValueError('SVG/JSON disagree: '+view+'/'+label)
        rows = {}
        for jid in JOINTS:
            if jid in LABELS:
                label = LABELS[jid]
                rows[jid] = {'xy': points[label], 'status': 'MEASURED',
                    'basis': 'Authored labelled SVG circle centre, not a pixel/anatomy inference',
                    'source': path.relative_to(BASE).as_posix(), 'sourceSha256': sha(path),
                    'element': 'guides-'+view+'/joints/circle/title='+label}
            elif jid in ('chin', 'waist'):
                xy = [points['head_center'][0], template['y_anchors']['chin']] if jid == 'chin' else [template['center_x'], template['y_anchors']['waist']]
                rows[jid] = {'xy': xy, 'status': 'DERIVED', 'source': 'measurements/inputs/anchor_template.json',
                    'sourceSha256': sha(inputs/'anchor_template.json'),
                    'basis': 'generic head-centre x intersect chin guide y (not observed mandible)' if jid == 'chin' else 'declared centre-line x intersect waist guide y'}
            else:
                rows[jid] = {'xy': None, 'status': 'UNRESOLVED',
                    'reason': 'No labelled SVG joint or explicit unambiguous anatomical construction rule; silhouette/occlusion is insufficient'}
        results[view] = rows
    return {'schema': 'cas/anchor-bridge/measurements-11', 'space': 'per-view-local-px',
            'subject': 'generic mannequin draft; not Morwen measurements',
            'sourceKind': 'authored SVG', 'views': results, 'adoptionReady': False}


def mappings(measurements, rig, template, rig_path):
    # Explicit two-anchor registration: source crown+ground to existing rig
    # headTop+ground. This is a DERIVED candidate, never measured character fit.
    output = {}
    for view in VIEWS:
        crown = measurements['views'][view]['headTop']['xy']
        target = rig['views'][view]['joints']['headTop']
        ground = rig['worldAnchors']['ground']['px']
        scale = (ground[1]-target[1])/(984-crown[1])
        if not math.isfinite(scale) or scale <= 0:
            raise ValueError('nonpositive/nonfinite registration scale')
        tx, ty = ground[0]-192*scale, ground[1]-984*scale
        crop = [template['sheet']['view_offset_x'][view], 0, 384, 1024]
        matrix = [scale, 0, 0, scale, tx, ty]
        transformed = {jid: {'xy': rig08.affine(p['xy'], matrix) if p['xy'] is not None else None,
            'status': 'DERIVED' if p['xy'] is not None else 'UNRESOLVED', 'sourceStatus': p['status']}
            for jid, p in measurements['views'][view].items()}
        residuals = {jid: math.dist(v['xy'], rig['views'][view]['joints'][jid])
            for jid,v in transformed.items() if v['xy'] is not None}
        output[view] = {'crop': crop, 'sourceSpace': 'sheetPx (subtract crop origin first)',
            'targetSpace': 'rigPx', 'matrix': matrix, 'classification': 'DERIVED_CANDIDATE',
            'basis': 'uniform two-anchor registration (crown and ground); no measured body retarget fit',
            'scale': scale, 'sourceGround': [192,984], 'targetGround': ground,
            'sourceCrown': crown, 'targetCrown': target, 'registrationQA': 'PASS',
            'characterFitStatus': 'BLOCKED', 'rigSourceSha256': sha(rig_path),
            'joints': transformed, 'referenceRigResidualPx': residuals}
    return {'schema': 'cas/anchor-bridge/mappings-11', 'sourceSize': [1536,1024], 'targetSize': [1200,1600],
            'status': 'BLOCKED', 'reason': 'Registration geometry is derived; generic-to-Morwen anatomy fit and adoption are not established',
            'views': output, 'adoptionReady': False}


def fk(rest, tree, angles):
    posed, cumulative = {}, {}
    def solve(jid):
        if jid in posed:
            return
        parent = tree[jid]
        if parent is None:
            posed[jid], cumulative[jid] = rest[jid][:], angles.get(jid, 0)
        else:
            solve(parent)
            a = math.radians(cumulative[parent])
            x, y = rest[jid][0]-rest[parent][0], rest[jid][1]-rest[parent][1]
            posed[jid] = [posed[parent][0]+math.cos(a)*x-math.sin(a)*y,
                          posed[parent][1]+math.sin(a)*x+math.cos(a)*y]
            cumulative[jid] = cumulative[parent]+angles.get(jid, 0)
    for jid in tree:
        solve(jid)
    return posed


def synthetic(rig):
    tree = {**rig['kinematicTree'], 'pelvis': None}
    if set(tree) != set(JOINTS):
        raise ValueError('31-joint hierarchy mismatch')
    tracks = {}
    errors = []
    arm_leg_movement = {}
    for view in VIEWS:
        rest = {j: rig['views'][view]['joints'][j] for j in JOINTS}
        frames, planted = [], {}
        for i, angle in enumerate((-15,-8,0,15,8,0)):
            posed = fk(rest, tree, {'hipL': angle, 'hipR': -angle, 'shoulderL': -angle, 'shoulderR': angle})
            side = 'L' if i < 3 else 'R'
            heel = posed['heel'+side]
            planted.setdefault(side, rest['heel'+side])
            actor = {'translationPx': [planted[side][0]-heel[0], planted[side][1]-heel[1]], 'scale': 1, 'rotationDeg': 0}
            for jid,parent in tree.items():
                if parent and not math.isclose(math.dist(posed[jid],posed[parent]),math.dist(rest[jid],rest[parent]),abs_tol=1e-8):
                    errors.append(view+'/'+str(i)+': length changed '+jid)
            frames.append({'id': 'SYNTHETIC_'+view+'_'+str(i), 'timeMs': i*100,
                'source': 'synthetic-FK-from-designed-candidate-rig', 'joints': posed,
                'actorTransform': actor, 'contacts': {side: {'part': 'heel','stanceId': side+'0'}}})
        tracks[view] = frames
        arm_leg_movement[view] = {jid: any(f['joints'][jid] != rest[jid] for f in frames) for jid in ('wristL','wristR','ankleL','ankleR')}
    data = {'schema': 'cas/anchor-contact-tracks/07', 'synthetic': True, 'status': 'SYNTHETIC_ONLY',
            'basis': 'Authored ±15/8/0 degree synthetic FK, root translation computed to plant a heel. Not image measurements or an actual walking asset.', 'tracks': tracks}
    report = audit(data,2)
    report.update({'synthetic': True, 'hierarchyErrors': errors, 'armLegMovement': arm_leg_movement, 'realAssetVerified': False})
    return data, report


def run():
    inputs = BASE/'measurements/inputs'
    rig_path = STUDIO/'layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json'
    rig = json.loads(rig_path.read_text())
    template = json.loads((inputs/'anchor_template.json').read_text())
    m = measure(inputs)
    write(BASE/'measurements/joints.json', m)
    mapping = mappings(m,rig,template,rig_path)
    write(BASE/'mappings/sheet_to_rig.json',mapping)
    legacy = {'schema':'cas/anchor-bridge/measurement-02','views':{v:{j:p['xy'] if p['status']=='MEASURED' else None for j,p in rows.items()} for v,rows in m['views'].items()}}
    write(BASE/'measurements/bridge10_input.json',legacy)
    real, _ = audit_real(BASE/'measurements/bridge10_input.json',inputs/'REAL_FRAMES_EMPTY_TEMPLATE.json')
    write(BASE/'qa/real_contact.json',real)
    data,report = synthetic(rig)
    write(BASE/'qa/synthetic_frames.json',data)
    write(BASE/'qa/synthetic_contact.json',report)
    # Standalone labelled technical diagrams, not alterations of the originals.
    tree = {**rig['kinematicTree'],'pelvis':None}
    for view in ('left','right'):
        lines=[]
        for i,f in enumerate(data['tracks'][view]):
            body=[]
            for jid,parent in tree.items():
                if parent:
                    a=rig08.source05.world_point(f['joints'][jid], f['actorTransform'])
                    b=rig08.source05.world_point(f['joints'][parent], f['actorTransform'])
                    body.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="#146b80" stroke-width="6"/>')
            lines.append(f'<g transform="translate({i*300},35) scale(0.25)">'+''.join(body)+'</g>')
        (BASE/'previews'/('SYNTHETIC_'+view+'.svg')).write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="440"><text x="10" y="20" fill="#168cac">SYNTHETIC FK ONLY - not measured animation / no production adoption</text>'+''.join(lines)+'</svg>')
    counts={status:sum(p['status']==status for rows in m['views'].values() for p in rows.values()) for status in ('MEASURED','DERIVED','UNRESOLVED')}
    summary={'status':'BLOCKED','jointClassifications':counts,'mappingGeometry':'PASS','mappingCharacterFit':'BLOCKED',
             'syntheticContact':report['status'],'realContact':real['status'],'adoptionReady':False}
    write(BASE/'qa/summary.json',summary)
    print(json.dumps(summary))
    return 2


if __name__=='__main__':
    raise SystemExit(run())
