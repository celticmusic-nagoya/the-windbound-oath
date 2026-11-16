"""Verify reopened source-review bytes and semantic-only scene, never art acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy

EXPECTED = 'abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620'
COLLECTIONS = {'LIND_TERRAIN','LIND_WATER','LIND_ROADS','LIND_HERO_HOME',
               'LIND_BUILDINGS','LIND_ECOLOGY','LIND_STORY_MARKERS'}

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--graph', type=Path, default=Path(__file__).resolve().parents[2] / 'docs/production/lind-new-world-topology.v1.json')
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    graph = json.loads(args.graph.read_text())
    scene = bpy.context.scene
    assert scene['approved_source_sha256'] == EXPECTED
    assert scene['metric_approval'] == 'BLOCKED'
    actual_collections = {c.name for c in scene.collection.children if c.name.startswith('LIND_')}
    assert actual_collections == COLLECTIONS
    markers = [o for o in bpy.data.objects if o.name.startswith('SEMANTIC_')]
    assert len(markers) == len(graph['nodes']) == 11
    assert {o['node_id'] for o in markers} == {n['id'] for n in graph['nodes']}
    assert all(o['position_status'] == 'UNPLACED' and not o['world_transform_approved'] for o in markers)
    assert not any(o.type == 'MESH' for o in bpy.data.objects)
    refs = [i for i in bpy.data.images if i.get('role') == 'APPROVED_VISUAL_REFERENCE_NOT_METRIC']
    assert len(refs) == 1 and refs[0].packed_file is not None
    packed_sha = hashlib.sha256(bytes(refs[0].packed_file.data)).hexdigest()
    assert packed_sha == EXPECTED
    report = {'status':'TECHNICAL_SOURCE_REVIEW_PASS','blender_version':bpy.app.version_string,
              'packed_source_sha256':packed_sha,'semantic_nodes':len(markers),
              'collections':sorted(actual_collections),'mesh_count':0,
              'metric_approval':'BLOCKED','art_qa':'NOT_RUN','game_qa':'NOT_RUN'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
