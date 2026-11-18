"""Read-only Blender runtime and scene inventory for TWO production gate.
Run: blender -b source.blend --python validate_blender_runtime.py -- --output qa.json
Never saves or mutates the source .blend.
"""
import bpy
import json
import os
import sys
from pathlib import Path

EXPECTED = (5, 2, 4)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(args) != 2 or args[0] != '--output':
    raise SystemExit('Usage: -- --output path.json')
path = Path(args[1])
version = tuple(bpy.app.version)
report = {
    'blender_version': bpy.app.version_string,
    'version_tuple': list(version),
    'required_version': '.'.join(map(str, EXPECTED)),
    'version_pass': version == EXPECTED,
    'source_blend': os.path.basename(bpy.data.filepath) if bpy.data.filepath else None,
    'source_opened': bool(bpy.data.filepath),
    'scene_count': len(bpy.data.scenes),
    'objects': len(bpy.data.objects),
    'meshes': len(bpy.data.meshes),
    'armatures': len(bpy.data.armatures),
    'materials': len(bpy.data.materials),
    'images': len(bpy.data.images),
    'cameras': len(bpy.data.cameras),
    'mesh_inventory': [
        {'name': m.name, 'vertices': len(m.vertices), 'edges': len(m.edges),
         'polygons': len(m.polygons), 'uv_layers': len(m.uv_layers),
         'shape_keys': len(m.shape_keys.key_blocks) if m.shape_keys else 0}
        for m in bpy.data.meshes
    ],
    'armature_inventory': [
        {'name': a.name, 'bones': len(a.bones)} for a in bpy.data.armatures
    ],
    'missing_external_images': [
        im.name for im in bpy.data.images
        if im.source == 'FILE' and not im.packed_file and
        im.filepath and not os.path.exists(bpy.path.abspath(im.filepath))
    ],
}
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('TWO_BLENDER_RUNTIME_QA', json.dumps({k: report[k] for k in ('blender_version','version_pass','source_opened','meshes','armatures','missing_external_images')}))
if not report['version_pass'] or not report['source_opened']:
    raise SystemExit(2)
