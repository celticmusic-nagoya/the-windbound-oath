"""Read-only replay of captured real-model topology; never imports bpy or deforms.

Farthest-pair anchors and world-Z labels are proposals only. Adoption requires
source-bound eye-local calibration and reviewed medial/lateral vertex IDs.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from split_lid_loop_07 import split_loop


def propose(component):
    ids = component['ordered_vertex_ids']
    xyz = component['world_xyz_m']
    pairs = sorted(itertools.combinations(ids, 2), key=lambda ab: (-math.dist(xyz[str(ab[0])], xyz[str(ab[1])]), sorted(ab)))
    anchors = list(pairs[0])
    # Direction is explicitly provisional, not anatomical identification.
    anchors.sort(key=lambda v: (abs(xyz[str(v)][0]), v))
    result = split_loop(component, anchors)
    a, b = result['chain_A'], result['chain_B']
    mean_z = lambda chain: sum(xyz[str(v)][2] for v in chain[1:-1]) / (len(chain)-2)
    delta = mean_z(a)-mean_z(b)
    if abs(delta) < 1e-8:
        raise ValueError('Ambiguous superior direction; calibrated eye frame required')
    upper, lower = ('A', 'B') if delta > 0 else ('B', 'A')
    # Project into the candidate canthus/superior plane. Any projected contact
    # between nonadjacent ring edges blocks this proposal (conservative).
    p, q = (xyz[str(v)] for v in anchors)
    axis = [q[k]-p[k] for k in range(3)]
    norm = math.hypot(axis[0], axis[1])
    if norm <= 1e-10:
        raise ValueError('Candidate canthus axis parallel to superior axis')
    uv = {v: ((xyz[str(v)][0]-p[0])*axis[0]/norm + (xyz[str(v)][1]-p[1])*axis[1]/norm,
              xyz[str(v)][2]-p[2]) for v in ids}
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    intersections = []
    for e, f in itertools.combinations(component['edge_ids'], 2):
        if set(e) & set(f):
            continue
        a,b,c,d = [uv[v] for v in (*e,*f)]
        if all(max(min(a[k],b[k]),min(c[k],d[k])) <= min(max(a[k],b[k]),max(c[k],d[k]))+1e-12 for k in (0,1)):
            if cross(a,b,c)*cross(a,b,d) <= 0 and cross(c,d,a)*cross(c,d,b) <= 0:
                intersections.append([e,f])
    lengths = [math.dist(xyz[str(a)],xyz[str(b)]) for a,b in component['edge_ids']]
    middle = sorted(lengths)[len(lengths)//2]
    anomalies = [e for e,length in zip(component['edge_ids'],lengths) if length > 5*middle or length < middle/5]
    result.update(status='BLOCKED_GEOMETRY' if intersections or anomalies else 'DIAGNOSTIC_PROPOSAL_REQUIRES_ANCHOR_REVIEW',
                  candidate_medial_lateral_ids=anchors, candidate_upper_chain=upper,
                  candidate_lower_chain=lower, projected_intersections=intersections,
                  anomalous_edges=anomalies, edge_length_m={'min':min(lengths),'max':max(lengths),'median':middle},
                  anomaly_policy='diagnostic only: outside [median/5, median*5]; not a production tolerance',
                  anchor_method='maximum 3D separation; tentative world-X medial/world-Z superior; NOT calibrated',
                  runner_up_distance_ratio=math.dist(xyz[str(pairs[1][0])],xyz[str(pairs[1][1])])/math.dist(p,q),
                  deformation_authorized=False)
    return result


def source_anchor_ids(component, recorded):
    """Match rounded source-authoring coordinates, never nearest at any cost.

    Baseline report records metres at six decimals: Euclidean rounding error
    is bounded by sqrt(3)*0.5e-6. Require exactly one vertex inside that bound.
    """
    result=[]
    for role in ('inner', 'outer'):
        point=recorded[role]
        candidates=[int(v) for v, xyz in component['world_xyz_m'].items()
                    if math.dist(point,xyz) <= math.sqrt(3)*0.5e-6 + 1e-9]
        if len(candidates) != 1:
            raise ValueError('Missing or ambiguous source anchor: '+role)
        result.append(candidates[0])
    if result[0] == result[1]:
        raise ValueError('Source anchors coincide')
    return result


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--baseline', type=Path)
    args=parser.parse_args()
    raw=args.input.read_bytes()
    report=json.loads(raw)
    result={'status':'DIAGNOSTIC_NOT_CANON','source_map_sha256':hashlib.sha256(raw).hexdigest(),
            'input_blend_sha256':report['input_sha256'],'sides':{}}
    for side, info in report['sides'].items():
        if len(info['components']) != 1:
            raise ValueError('Expected one component; missing/disconnected boundary')
        component=info['components'][0]
        proposal=propose(component)
        if args.baseline:
            baseline=json.loads(args.baseline.read_bytes())
            anchors=source_anchor_ids(component,baseline['build']['lid_'+side]['canthus_vertex_world'])
            if anchors != proposal['anchor_ids']:
                raise ValueError('Source anchors disagree with geometric proposal; review required')
            proposal['anchor_method']='unique match to EYELID-05 authored inner/outer world coordinates (six-decimal rounding bound)'
            proposal['anchor_review']='SOURCE_AUTHORING_CONFIRMED; FORMAL_DESIGN_APPROVAL_PENDING'
            result['baseline_report_sha256']=hashlib.sha256(args.baseline.read_bytes()).hexdigest()
        result['sides'][side]=proposal
    with args.output.open('x') as f:
        json.dump(result,f,indent=2); f.write('\n')

if __name__ == '__main__':
    main()
