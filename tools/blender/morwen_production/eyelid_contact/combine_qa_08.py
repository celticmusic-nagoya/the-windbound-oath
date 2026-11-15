"""Combine geometry and delivery/collision checks without promoting partial PASS."""
import argparse
import json
from pathlib import Path


def combine(qa,verification):
    result=dict(qa);result['delivery_verification']=verification
    failures=list(result['failures'])
    for side,checks in verification['cage_eye_intersections'].items():
        if any(checks.values()):failures.append(side+': cage intersects eyeball')
    for side,count in verification['opaque_card_samples_inside_cage'].items():
        if count:failures.append(f'{side}: {count} opaque card samples inside cage')
    if not verification['protected_face_data_unchanged'] or verification['protected_face_key_count']!=58:failures.append('Protected Face mismatch')
    result['failures']=failures;result['G3']='FAIL' if failures else 'PARTIAL_STATIC_CAGE_CHECKS_PASS_FULL_ANIMATION_NOT_RUN'
    result['status']='DISABLED_FAILED_CANDIDATE' if failures else 'DISABLED_CANDIDATE_PENDING_ART_AND_ANIMATION'
    result['continuous_card_collision']='NOT_RUN_FINITE_ALPHA_SAMPLES_ONLY'
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('qa',type=Path);p.add_argument('verification',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    with a.output.open('x') as f:json.dump(combine(json.loads(a.qa.read_text()),json.loads(a.verification.read_text())),f,indent=2);f.write('\n')

if __name__=='__main__':main()
