"""Pack and independently reopen the legacy Layer 0 setup; no body generation."""
import hashlib
import json
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'render_output/layer0_reference_setup'
SCENE_FILE = OUT / 'MORWEN_LAYER0_REFERENCES.blend'
manifest = json.loads((ROOT / 'tools/blender/production_mesh_08/layer0_reference_manifest.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(SCENE_FILE), load_ui=False, use_scripts=False)
scene = bpy.context.scene
scene.unit_settings.system = 'NONE'
scene['scale_status'] = 'NORMALIZED_REFERENCE_CANVAS_NOT_METRIC_BODY_HEIGHT'
scene['reference_scope'] = 'BODY_STRUCTURE_ONLY; NOT_COSTUME_OR_FINAL_FACE_AUTHORITY'
scene['is_character_model'] = False
positions = {'front': (0, -4, 1), 'right': (-4, 0, 1),
             'back': (0, 4, 1), 'left': (4, 0, 1)}
for r in manifest['images']:
    ob = bpy.data.objects['CANON_LAYER0_' + r['view'].upper()]
    ob.data.pack()
    ob.data.filepath = '//packed_references/' + r['filename']
    ob['usage'] = 'BODY_PROPORTION_REFERENCE_ONLY'
    cam_data = bpy.data.cameras.new('ORTHO_' + r['view'])
    cam = bpy.data.objects.new('QA_CAM_' + r['view'].upper(), cam_data)
    scene.collection.objects.link(cam)
    cam.location = positions[r['view']]
    cam.rotation_euler = (ob.location - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 2.0
scene.camera = bpy.data.objects['QA_CAM_FRONT']
scene.render.resolution_x = 384
scene.render.resolution_y = 1024
scene.render.resolution_percentage = 100
scene.render.pixel_aspect_x = scene.render.pixel_aspect_y = 1
bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_FILE))
# Reopen with script execution disabled, verify actual packed bytes and projection.
bpy.ops.wm.open_mainfile(filepath=str(SCENE_FILE), load_ui=False, use_scripts=False)
scene = bpy.context.scene
bpy.context.view_layer.update()
checks = []
for r in manifest['images']:
    ob = bpy.data.objects['CANON_LAYER0_' + r['view'].upper()]
    cam = bpy.data.objects['QA_CAM_' + r['view'].upper()]
    digest = hashlib.sha256(bytes(ob.data.packed_file.data)).hexdigest()
    assert digest == r['sha256']
    assert tuple(ob.data.size) == (384, 1024)
    assert ob.hide_select and ob.hide_render
    assert all(ob.lock_location) and all(ob.lock_rotation) and all(ob.lock_scale)
    # IMAGE empty size is its maximum dimension: local canvas width .75, height 2.
    corners = []
    for x, y in ((-.375, -1), (.375, -1), (.375, 1), (-.375, 1)):
        p = world_to_camera_view(scene, cam, ob.matrix_world @ Vector((x, y, 0)))
        corners.append([float(p.x), float(p.y)])
    expected = ((0, 0), (1, 0), (1, 1), (0, 1))
    error = max(abs(a - b) for p, q in zip(corners, expected) for a, b in zip(p, q))
    assert error < 1e-5, (r['view'], corners)
    # Exercise individual reference visibility; restore before final save.
    ob.hide_set(True)
    assert ob.hide_get()
    ob.hide_set(False)
    assert not ob.hide_get()
    checks.append({'view': r['view'], 'sha256': digest, 'packed': True,
                   'image_size': list(ob.data.size), 'projected_corners': corners,
                   'max_corner_error': error, 'unmirrored_upright': True,
                   'transform_locks': True, 'visibility_toggle': 'PASS'})
assert not any(o.type == 'MESH' for o in scene.objects)
bpy.ops.wm.save_as_mainfile(filepath=str(SCENE_FILE))
report = {'task': 'MORWEN-REBUILD-01-LAYER0', 'blender': bpy.app.version_string,
          'reference_source_commit': '8cc6687ce4498b6f0ea5bd59f0ebe2d7017629f1',
          'G1_body_reference': 'PASS', 'G1_final_design': 'BLOCKED',
          'G2': 'NOT_RUN', 'G3_reference_scene': 'PASS', 'G3_character': 'NOT_RUN',
          'G4': 'NOT_RUN', 'scope': 'Reference scene only; zero character meshes',
          'canvas_height': 2.0, 'canvas_is_metric_body_height': False,
          'ground_and_landmark_registration': 'NOT_RUN',
          'checks': checks, 'reopened_with_scripts_disabled': True,
          'blend_sha256': hashlib.sha256(SCENE_FILE.read_bytes()).hexdigest()}
(OUT / 'REOPEN_QA.json').write_text(json.dumps(report, indent=2) + '\n')
print('REFERENCE_SCENE_REOPEN_PACKED_PROJECTION_PASS')
