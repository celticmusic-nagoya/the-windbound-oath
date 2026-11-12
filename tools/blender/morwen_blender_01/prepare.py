"""Verify pinned GitHub inputs and calibrate candidate joints, without image edits."""
import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
OUTPUT = ROOT / 'assets/candidates/morwen-blender-01'
REFERENCES = ROOT / 'assets/references/morwen/reference_20261112'
sys.path.insert(0, str(HERE.parent))
from qa_morwen_anchors import validate as legacy_validate

FACINGS = ('front', 'right', 'back', 'left')
NEAR = {'front': None, 'back': None, 'right': 'R', 'left': 'L'}
FILES = {'front': 'REFERENCE_front.png', 'back': 'REFERENCE_back.png',
         'left': 'REFERENCE_profile_facing_left.png',
         'right': 'REFERENCE_profile_facing_right.png'}


def verify_sources(root=ROOT):
    receipt = json.loads((root/'tools/blender/morwen_blender_01/SOURCE_RECEIPT.json').read_text())
    for entry in receipt['files']:
        actual = hashlib.sha256((root/entry['path']).read_bytes()).hexdigest()
        if actual != entry['sha256']:
            raise ValueError('Source SHA mismatch: '+entry['path'])
    return receipt


def bone_points(points, ground):
    """Map anatomical L/R to the upstream 17-bone contract, in source pixels."""
    result = {'root': ([points['pelvis'][0], ground], [points['pelvis'][0], ground-30]),
              'pelvis': (points['pelvis'], points['waist']),
              'spine': (points['waist'], points['chest']),
              'neck': (points['chest'], points['neck']),
              'head': (points['neck'], points['head_top'])}
    for side in ('L','R'):
        chain = [('upper_arm','shoulder','elbow'), ('forearm','elbow','wrist'),
                 ('hand','wrist','handtip'), ('thigh','hip','knee'),
                 ('shin','knee','ankle'), ('foot','ankle','toe')]
        for bone, head, tail in chain:
            result[bone+'.'+side] = (points[head+'.'+side], points[tail+'.'+side])
    return result


def validate_candidate(doc):
    errors = legacy_validate(doc, require_measured=False)
    if doc.get('status') != 'PIXEL_REFINED_VISUAL_CANDIDATE_UNREVIEWED':
        errors.append('Candidate must not claim measured/approved status')
    if len(set(doc.get('required_anchors', []))) != 12:
        errors.append('Twelve upstream anchor names required')
    if doc.get('common_pixel_scale', 0) <= 0 or not math.isfinite(doc.get('common_pixel_scale', 0)):
        errors.append('Finite positive common scale required')
    for facing, entry in doc.get('facings', {}).items():
        if set(entry['anchors']) != set(doc['required_anchors']):
            errors.append(f'{facing}: incomplete anchor adapter')
        if entry.get('dimensions') != [384,1024]:
            errors.append(f'{facing}: wrong source aspect')
        points = entry['rig_points_pixels']
        for name, point in points.items():
            if len(point) != 2 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in point):
                errors.append(f'{facing}/{name}: invalid pixels')
            elif not (0 <= point[0] < 384 and 0 <= point[1] < 1024):
                errors.append(f'{facing}/{name}: out of image')
        expected = 'L' if facing == 'left' else 'R' if facing == 'right' else None
        if entry.get('near_side') != expected:
            errors.append(f'{facing}: incorrect anatomical depth convention')
        if facing in ('front','back'):
            sign = 1 if facing == 'front' else -1
            if sign*(points['shoulder.L'][0]-points['shoulder.R'][0]) <= 0:
                errors.append(f'{facing}: anatomical L/R swapped')
        for name, anchor in entry['anchors'].items():
            hidden = facing in ('left','right') and name.endswith('.'+('R' if expected=='L' else 'L'))
            if hidden and anchor.get('visibility') != 'OCCLUDED_INFERRED':
                errors.append(f'{facing}/{name}: hidden joint must be inferred')
    return errors


def prepare(output=OUTPUT):
    receipt = verify_sources()
    rough = json.loads((ROOT/'tools/blender/candidates/morwen_rig10_20261112/anchors_visual_estimate.json').read_text())
    template = json.loads((ROOT/'tools/blender/profiles/morwen_anchors_v1.json').read_text())
    manual = json.loads((HERE/'LANDMARK_CANDIDATES.json').read_text())
    result = dict(schema_version=2, task='MORWEN-BLENDER-01',
                  status='PIXEL_REFINED_VISUAL_CANDIDATE_UNREVIEWED',
                  source_status='REFERENCE_ONLY', future_canon='FUTURE_CANON_PENDING_APPROVAL',
                  production_use=False, coordinate_system='normalized_image_xy_top_left_origin',
                  required_anchors=template['required_anchors'],
                  asymmetry_policy={'mirror_between_facings': False, 'sides': 'anatomical_not_screen'},
                  method='Manual pixel-refined visual joint estimates; alpha bbox/ground measured only. Hidden depth and anatomy inferred.',
                  facings={})
    heights=[]
    for facing in FACINGS:
        source = REFERENCES/FILES[facing]
        with Image.open(source) as image:
            assert image.size == (384,1024) and image.mode == 'RGBA'
            mask = image.getchannel('A').point(lambda a: 255 if a >= 128 else 0)
            bbox=mask.getbbox()
            assert bbox
            ground=bbox[3]-1
            heights.append(ground-bbox[1])
            points=deepcopy(manual['views'][facing])
            anchors={}
            for name in template['required_anchors']:
                hidden = facing in ('left','right') and name.endswith('.'+('R' if NEAR[facing]=='L' else 'L'))
                x,y=points[name]
                # Check visible joints are inside/close to the measured silhouette;
                # don't silently snap hidden anatomy onto the visible contour.
                inside=bool(mask.getpixel((int(x),int(y))))
                anchors[name]=dict(x=x/384, y=y/1024,
                    visibility='OCCLUDED_INFERRED' if hidden else 'VISIBLE_VISUAL_ESTIMATE',
                    uncertainty_px=30 if hidden else 12,
                    silhouette_contains_candidate=inside,
                    delta_from_rough_px=[round(x-rough['views'][facing]['anchors'][name]['x']*384,3),
                                         round(y-rough['views'][facing]['anchors'][name]['y']*1024,3)])
            result['facings'][facing]=dict(source=source.relative_to(ROOT).as_posix(),
                source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), dimensions=[384,1024],
                alpha_threshold=128, alpha_bbox=list(bbox), measured_ground_y=ground,
                origin_x=points['pelvis'][0], near_side=NEAR[facing],
                inferred_half_depth_px=48, anchors=anchors, rig_points_pixels=points)
    # Shared scale: never independently resize one view to conceal height differences.
    result['common_pixel_scale']=1/statistics.median(heights)
    result['calibration']=dict(shared_pixel_scale=True, image_resizing=False,
                              per_view_translation_only=True, silhouette_heights_px=heights,
                              height_spread_px=max(heights)-min(heights))
    errors=validate_candidate(result)
    if errors:
        raise ValueError('; '.join(errors))
    output.mkdir(parents=True,exist_ok=True)
    (output/'anchors_candidate.json').write_text(json.dumps(result,indent=2)+'\n')
    report=dict(status='PASS', source_sha_checks=len(receipt['files']), protected_pngs=12,
                calibration=result['calibration'], anatomical_measurements=False,
                hidden_depth='INFERRED_NOT_MEASURED', visual_approval=False)
    (output/'source_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=OUTPUT)
    print(json.dumps(prepare(parser.parse_args().output)['calibration']))
