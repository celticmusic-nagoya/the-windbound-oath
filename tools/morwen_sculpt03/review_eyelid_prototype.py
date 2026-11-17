"""Read-only candidate review: matching 6+6 context, local wire/shape-key evidence.
Context images show retained SCULPT02 + unintegrated eyelid study, NOT final art.
"""
import bpy
import bmesh
import hashlib
import json
import math
from pathlib import Path
from mathutils import Vector

SOURCE = Path('assets/candidates/morwen-sculpt02/morwen_sculpt02_v02_UNAPPROVED.blend')
TARGET = Path('assets/candidates/morwen-sculpt03/morwen_sculpt03_v01_UNAPPROVED.blend')
OUT = Path('qa_output/morwen-sculpt03/review')
OUT.mkdir(parents=True, exist_ok=True)
source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
candidate_sha = hashlib.sha256(TARGET.read_bytes()).hexdigest()
assert source_sha == '90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b'
bpy.ops.wm.open_mainfile(filepath=str(TARGET.resolve()), use_scripts=False, load_ui=False)
assert bpy.context.scene['sculpt03_status'] == 'LOCAL_EYELID_TOPOLOGY_PROTOTYPE_ONLY_UNAPPROVED'
sc = bpy.context.scene
prototypes = sorted([ob for ob in bpy.data.objects if ob.name.startswith('SCULPT03_EYELID_')], key=lambda ob:ob.name)
assert len(prototypes) == 2
report = {'candidate_sha256':candidate_sha, 'source_sha256':source_sha,
          'status':'LOCAL_PROTOTYPE_SCREEN_NOT_FULL_G3', 'blender':bpy.app.version_string,
          'G1':'BLOCKED_REGISTRATION', 'G2':'PENDING_INDEPENDENT_REVIEW',
          'G3':'INCOMPLETE_LOCAL_SCREEN_ONLY', 'G4':'NOT_RUN',
          'source_face_hair_retained':True, 'meshes':[], 'renders':[]}
for ob in prototypes:
    bm = bmesh.new(); bm.from_mesh(ob.data)
    boundary = [e for e in bm.edges if e.is_boundary]
    report['meshes'].append({'name':ob.name, 'vertices':len(bm.verts), 'quads':sum(len(f.verts)==4 for f in bm.faces),
                            'faces':len(bm.faces), 'boundary_edges':len(boundary),
                            'non_boundary_nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges),
                            'loose_vertices':sum(not v.link_edges for v in bm.verts),
                            'control_min_face_area':min(f.calc_area() for f in bm.faces),
                            'boundary_policy':'32 expected: open lid and open socket; not a watertight character',
                            'uv_status':'LOCAL_PLANAR_STUDY_NOT_FINAL_ATLAS', 'blink':[]})
    bm.free()
    for value in [0., .5, 1.]:
        ob.data.shape_keys.key_blocks['LOCAL_BLINK_NOT_RIGGED'].value = value
        bpy.context.view_layer.update()
        evaluated = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
        me = evaluated.to_mesh(); bm = bmesh.new(); bm.from_mesh(me)
        evidence = {'value':value, 'finite':all(math.isfinite(c) for v in bm.verts for c in v.co),
                    'evaluated_vertices':len(bm.verts), 'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),
                    'minimum_face_area':min(f.calc_area() for f in bm.faces),
                    'front_normal_faces':sum(f.normal.y<0 for f in bm.faces),
                    'back_normal_faces':sum(f.normal.y>=0 for f in bm.faces),
                    'collision_and_self_intersection':'NOT_CERTIFIED_BY_AREA_SCREEN'}
        report['meshes'][-1]['blink'].append(evidence)
        bm.free(); evaluated.to_mesh_clear()
    ob.data.shape_keys.key_blocks['LOCAL_BLINK_NOT_RIGGED'].value = 0

sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 16
sc.cycles.seed = 0; sc.cycles.use_denoising = False
sc.render.film_transparent = True
sc.render.resolution_x = 768; sc.render.resolution_y = 768; sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGBA'
sc.view_settings.view_transform = 'AgX'; sc.view_settings.look = 'AgX - Medium High Contrast'
sc.view_settings.exposure = -.3; sc.view_settings.gamma = 1
clay = bpy.data.materials.new('SCULPT03_REVIEW_CLAY'); clay.use_nodes = True
clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.35,.35,.35,1)
clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .75

def render(name):
    sc.render.filepath = str((OUT/(name+'.png')).resolve())
    bpy.ops.render.render(write_still=True)
    report['renders'].append({'file':name+'.png', 'camera':sc.camera.name,
                             'ortho_scale':sc.camera.data.ortho_scale,
                             'camera_location':list(sc.camera.location),
                             'camera_rotation':list(sc.camera.rotation_euler)})

for mode in ['color','clay']:
    sc.view_layers[0].material_override = clay if mode == 'clay' else None
    for view in ['front','character_left','character_right','back','three_quarter','three_quarter_other']:
        sc.camera = bpy.data.objects['SCULPT02_'+view]
        render(mode+'_'+view)

# Diagnostic isolation: retain lights/cameras/references, hide ALL other meshes,
# including historical collection objects. This is an isolated open skin patch.
for ob in bpy.data.objects:
    if ob.type == 'MESH' and ob not in prototypes:
        ob.hide_render = True
sc.view_layers[0].material_override = clay
cd = bpy.data.cameras.new('SCULPT03_LOCAL_REVIEW_CAMERA')
cam = bpy.data.objects.new(cd.name, cd); sc.collection.objects.link(cam)
cd.type = 'ORTHO'; cd.ortho_scale = .19
cam.location = (0,-.65,1.522)
cam.rotation_euler = (Vector((0,-.13,1.522))-cam.location).to_track_quat('-Z','Y').to_euler()
sc.camera = cam
for value, label in [(0.,'open'),(.5,'half'),(1.,'closed')]:
    for ob in prototypes:
        ob.data.shape_keys.key_blocks['LOCAL_BLINK_NOT_RIGGED'].value = value
    render('isolated_blink_'+label)
for ob in prototypes:
    ob.data.shape_keys.key_blocks['LOCAL_BLINK_NOT_RIGGED'].value = 0
    # Show the original explicit quad cage, not a triangulated evaluated mesh.
    ob.modifiers['LOCAL_QUAD_PREVIEW'].show_render = False
    wire = ob.modifiers.new('REVIEW_ONLY_CONTROL_WIRE', 'WIREFRAME'); wire.thickness = .00018
    wire.use_replace = True
render('isolated_control_wire_front')
cam.location = (.16,-.55,1.56)
cam.rotation_euler = (Vector((0,-.13,1.522))-cam.location).to_track_quat('-Z','Y').to_euler()
render('isolated_control_wire_three_quarter')
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha
assert hashlib.sha256(TARGET.read_bytes()).hexdigest() == candidate_sha
# Reopen verifies that render-only overrides were never saved into the master.
bpy.ops.wm.open_mainfile(filepath=str(TARGET.resolve()), use_scripts=False, load_ui=False)
assert bpy.data.objects['SCULPT03_EYELID_L_LOCAL_PROTOTYPE'].data.shape_keys.key_blocks['LOCAL_BLINK_NOT_RIGGED'].value == 0
report['reopen_pass'] = True; report['candidate_unchanged'] = True; report['source_unchanged'] = True
(OUT/'technical_screen.json').write_text(json.dumps(report, indent=2)+'\n')
print('SCULPT03_PARTIAL_REVIEW_COMPLETE', len(report['renders']))
