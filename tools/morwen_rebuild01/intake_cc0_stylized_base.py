"""Intake an unmodified licensed anatomical source, NOT a fitted Morwen model.

Different source from SCULPT01–03's realistic body. No auto fit, Grab, primitive
assembly, hair generation, rig or final-art claim. Run only after Layer 0 QA.
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'render_output/rebuild01_base_intake'
OUT.mkdir(parents=True, exist_ok=True)
ref_qa = json.loads((ROOT / 'render_output/layer0_reference_setup/REOPEN_QA.json').read_text())
assert ref_qa['G1_body_reference'] == 'PASS'
assert ref_qa['G3_reference_scene'] == 'PASS'
source = ROOT / '_cc0_source/official_source.blend'
official_sha = 'e5e9d30a7e6bb385fed21459dce68d1ad0d06e7bde4f9626696dbfda07cd541a'
recovered = '--source-intake' in sys.argv
if recovered:
    source = Path(sys.argv[sys.argv.index('--source-intake') + 1]).resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == 'cc551e8c666f956534c3632ee65c0ffb0597e8b787c651a5885d2ad64b7f06ab'
else:
    assert hashlib.sha256(source.read_bytes()).hexdigest() == official_sha
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(source), link=False) as (available, requested):
    source_name = 'CC0_STYLIZED_ANATOMY_SOURCE_NOT_FITTED_MORWEN' if recovered else 'GEO-body_female_stylized'
    matches = [n for n in available.objects if n == source_name]
    assert len(matches) == 1, available.objects
    requested.objects = matches
obj = requested.objects[0]
bpy.context.scene.collection.objects.link(obj)
assert obj.type == 'MESH'
metadata = obj.asset_data or obj.data.asset_data
# License of this bundle was independently verified in PR407. Record source
# metadata too when attached to the collection rather than the object.
obj.name = 'CC0_STYLIZED_ANATOMY_SOURCE_NOT_FITTED_MORWEN'
original_coords = [[float(x) for x in v.co] for v in obj.data.vertices]
original_faces = [list(p.vertices) for p in obj.data.polygons]
geometry_sha = hashlib.sha256(json.dumps([original_coords, original_faces], separators=(',', ':')).encode()).hexdigest()
assert geometry_sha == '606a5cbed38aa3318626a48185bde66d3ce9f9c1f39d2fe9b6e66783f9740c4c'
# Scene-space presentation transform only; never edit source coordinates.
bpy.context.view_layer.update()
pts = [obj.matrix_world @ v.co for v in obj.data.vertices]
lo = Vector(tuple(min(p[i] for p in pts) for i in range(3)))
hi = Vector(tuple(max(p[i] for p in pts) for i in range(3)))
height = hi.z - lo.z
assert height > 0
obj.scale /= height
obj.location = (obj.location - Vector(((lo.x + hi.x)/2, (lo.y + hi.y)/2, lo.z)))/height
obj['fit_status'] = 'UNMODIFIED_SOURCE_INTAKE_NOT_MORWEN_ART'
obj['license'] = 'CC0 Human Base Meshes bundle 1.4.1'
scene = bpy.context.scene
scene.unit_settings.system = 'NONE'
scene['height_is_metric'] = False
scene.world = bpy.data.worlds.new('Neutral review world')
scene.world.color = (.18, .18, .18)
mat = bpy.data.materials.new('Neutral anatomical construction clay')
mat.diffuse_color = (.42, .46, .5, 1)
mat.use_nodes = True
mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.32, .36, .4, 1)
obj.data.materials.clear()
obj.data.materials.append(mat)
for name, loc, energy, size in [('KEY', (-2,-3,3), 100, 2), ('FILL', (2,-1,2),40,2), ('RIM',(0,2,2),60,2)]:
    light = bpy.data.lights.new(name, 'AREA')
    light.energy, light.size = energy, size
    ob = bpy.data.objects.new(name, light)
    scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector((0,0,.5))-ob.location).to_track_quat('-Z','Y').to_euler()
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = False
scene.render.resolution_x = 512
scene.render.resolution_y = 768
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
frame_checks = []
for name, pos in {'front':(0,-3,.5),'right':(-3,0,.5),'back':(0,3,.5),'left':(3,0,.5),'three_quarter_left':(2,-3,.5),'three_quarter_right':(-2,-3,.5)}.items():
    data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new('SOURCE_REVIEW_' + name, data)
    scene.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (Vector((0,0,.5))-cam.location).to_track_quat('-Z','Y').to_euler()
    data.type, data.ortho_scale = 'ORTHO', 1.2
    scene.camera = cam
    bpy.context.view_layer.update()
    from bpy_extras.object_utils import world_to_camera_view
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    projected = [world_to_camera_view(scene, cam, evaluated.matrix_world @ v.co) for v in mesh.vertices]
    bounds = [[min(p[i] for p in projected), max(p[i] for p in projected)] for i in range(2)]
    evaluated.to_mesh_clear()
    assert all(.01 < low < high < .99 for low, high in bounds), (name, bounds)
    frame_checks.append({'view': name, 'projected_bounds': bounds, 'full_mesh_in_frame': True})
    scene.render.filepath = str(OUT/(name+'.png'))
    bpy.ops.render.render(write_still=True)
blend = OUT/'CC0_STYLIZED_BASE_INTAKE_NOT_MORWEN.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
assert original_coords == [[float(x) for x in v.co] for v in obj.data.vertices]
report = {'task':'MORWEN-REBUILD-01-BASE-INTAKE', 'stage':'UNMODIFIED_CC0_SOURCE_INTAKE',
          'license':'CC0', 'source_object':'GEO-body_female_stylized',
          'author':'Julien Kaspar (Human Base Meshes metadata previously verified in PR407)',
          'license_listing':'https://www.blender.org/download/demo-files/#assets',
          'source_blend_sha256':official_sha,
          'recovered_from_verified_artifact':recovered,
          'control_geometry_sha256':geometry_sha,
          'vertices':len(obj.data.vertices), 'faces':len(obj.data.polygons),
          'source_coordinates_unchanged':True, 'body_height_normalized':1.0,
          'frame_checks':frame_checks,
          'G1_body_reference':'PASS','G1_character':'BLOCKED','G2':'NOT_RUN',
          'G3':'NOT_RUN','G4':'NOT_RUN','independent_art_qa':'NOT_RUN',
          'morwen_fit_performed':False,'production_approved':False,
          'next':'Reference-registered anatomy target and authored retopology; no face detail or rig before full-body art acceptance',
          'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest()}
(OUT/'QA.json').write_text(json.dumps(report,indent=2)+'\n')
print('CC0_STYLIZED_BASE_SOURCE_INTAKE_ONLY_NOT_FINISHED_MORWEN')
