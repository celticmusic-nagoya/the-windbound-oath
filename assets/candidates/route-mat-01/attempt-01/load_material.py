"""Load the verified image candidate only. Does not assign, edit, or save geometry.
Blender --background --factory-startup --python this.py -- --root REPO --report /tmp/report.json
Claude owns the new full-thickness masonry sample, UVs and actual integration QA.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy


def create_material(repo_root):
    root = Path(repo_root).resolve()
    sys.path.insert(0, str(root))
    from tools.material_pipeline.validate_material_handoff import validate
    path = root / 'assets/candidates/route-mat-01/attempt-01/manifest.json'
    errors = validate(path, root)
    if errors:
        raise ValueError(errors)
    data = json.loads(path.read_text())
    maps = {m['type']: m for m in data['maps']}
    mat = bpy.data.materials.new('ROUTE_MAT_01_WEATHERED_STONE_CANDIDATE')
    mat.use_nodes = True
    mat['asset_id'] = data['asset_id']
    mat['manifest_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    mat['adoption'] = 'CANDIDATE_NOT_ADOPTED'
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bs = nodes.get('Principled BSDF')
    bs.inputs['Metallic'].default_value = 0
    texcoord = nodes.new('ShaderNodeTexCoord')
    texcoord.location = (-700, 0)
    loaded = {}
    for role in ('base_color', 'roughness'):
        m = maps[role]
        image = bpy.data.images.load(str(root / m['path']), check_existing=False)
        image.colorspace_settings.name = m['color_space']
        if list(image.size) != m['dimensions']:
            raise ValueError('Image dimensions differ from manifest: ' + role)
        node = nodes.new('ShaderNodeTexImage')
        node.name = 'ROUTE_MAT_01_' + role
        node.image = image
        node.extension = 'CLIP'
        node.interpolation = 'Linear'
        node.location = (-450, 150 if role == 'base_color' else -150)
        links.new(texcoord.outputs['UV'], node.inputs['Vector'])
        loaded[role] = {'node': node.name, 'color_space': image.colorspace_settings.name, 'dimensions': list(image.size), 'sha256': m['sha256']}
        if role == 'base_color':
            links.new(node.outputs['Color'], bs.inputs['Base Color'])
        else:
            separate = nodes.new('ShaderNodeSeparateColor')
            separate.mode = 'RGB'
            separate.name = 'Roughness_R_scalar'
            separate.location = (-180, -150)
            links.new(node.outputs['Color'], separate.inputs['Color'])
            links.new(separate.outputs['Red'], bs.inputs['Roughness'])
    return mat, loaded


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
    before = {o.name: (o.type, o.data.name if o.data else None) for o in bpy.data.objects}
    material, maps = create_material(a.root)
    after = {o.name: (o.type, o.data.name if o.data else None) for o in bpy.data.objects}
    assert before == after, 'Loader must not change geometry/objects'
    bs = material.node_tree.nodes.get('Principled BSDF')
    assert bs.inputs['Base Color'].is_linked and bs.inputs['Roughness'].is_linked
    assert not bs.inputs['Normal'].is_linked
    report = {'status': 'PASS_MATERIAL_NODE_LOAD_ONLY', 'blender': bpy.app.version_string, 'maps': maps, 'objects_unchanged': before == after, 'normal_height': 'not provided; geometry normals retained', 'G2_independent_masonry_review': 'NOT_RUN', 'G3_uv_support_saved_masonry': 'NOT_RUN', 'G4': 'NOT_RUN'}
    a.report.parent.mkdir(parents=True, exist_ok=True)
    a.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
