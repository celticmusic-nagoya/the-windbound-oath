"""Corner-anchored local quad study. Actual mesh, NOT completed facial retopology.

Explicitly authored upper/lower stations, not polar sampling, automatic face fitting,
Grab deformation, or a new variation of the rejected coarse hair control nets.
The source face and hair are deliberately retained for registration/integration QA.
Run from repository root with Blender --background --python this_file.
"""
import bpy
import bmesh
import hashlib
import json
from pathlib import Path

SOURCE = Path('assets/candidates/morwen-sculpt02/morwen_sculpt02_v02_UNAPPROVED.blend')
EXPECTED = '90eaf546a4737cd249a59709271b06053d375fe2edf66b7204e944af072c6b0b'
OUT = Path('qa_output/morwen-sculpt03')
TARGET = Path('assets/candidates/morwen-sculpt03/morwen_sculpt03_v01_UNAPPROVED.blend')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

assert sha(SOURCE) == EXPECTED
bpy.ops.wm.open_mainfile(filepath=str(SOURCE.resolve()), use_scripts=False, load_ui=False)
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
OUT.mkdir(parents=True, exist_ok=True)
TARGET.parent.mkdir(parents=True, exist_ok=True)
manifest = json.loads(Path('docs/qa/morwen-sculpt02/canonical_manifest.json').read_text())
packed = {hashlib.sha256(im.packed_file.data).hexdigest() for im in bpy.data.images if im.packed_file}
assert all(f['sha256'] in packed for f in manifest['files'])

# Three distinct contours, each with corresponding semantic stations:
# medial canthus, upper nasal arc, apex, lateral upper arc, lateral canthus,
# lower lateral arc, lower apex, lower nasal arc. Coordinates in metres.
# x/z are local to source right eye centre. y is authored world depth.
# 9 upper stations including BOTH corners, then 7 lower stations backwards.
# Corners are shared topologically: no duplicate vertices or zipper triangulation.
CONTOURS = [
    [(-.021,-.1350,-.001),(-.017,-.1400,.006),(-.012,-.1440,.012),(-.006,-.1460,.015),
     (.001,-.1465,.016),(.008,-.1440,.015),(.014,-.1390,.011),(.019,-.1330,.006),(.023,-.1260,.002),
     (.018,-.1320,-.004),(.012,-.1380,-.009),(.005,-.1410,-.012),(-.002,-.1420,-.013),
     (-.009,-.1410,-.011),(-.015,-.1380,-.007),(-.019,-.1355,-.003)],
    [(-.023,-.1345,-.001),(-.019,-.1400,.008),(-.013,-.1440,.014),(-.006,-.1460,.017),
     (.001,-.1460,.018),(.008,-.1435,.017),(.015,-.1385,.013),(.021,-.1325,.007),(.025,-.1255,.002),
     (.020,-.1320,-.006),(.013,-.1380,-.011),(.005,-.1405,-.014),(-.002,-.1415,-.015),
     (-.010,-.1405,-.013),(-.017,-.1375,-.009),(-.021,-.1350,-.004)],
    [(-.030,-.1290,-.001),(-.025,-.1330,.014),(-.017,-.1355,.023),(-.008,-.1360,.028),
     (.002,-.1350,.029),(.012,-.1320,.027),(.021,-.1260,.021),(.028,-.1180,.012),(.032,-.1100,.002),
     (.027,-.1190,-.012),(.019,-.1270,-.021),(.008,-.1310,-.025),(-.003,-.1320,-.026),
     (-.015,-.1315,-.023),(-.024,-.1300,-.016),(-.028,-.1295,-.007)],
]
coll = bpy.data.collections.new('SCULPT03_LOCAL_EYELID_TOPOLOGY_PROTOTYPE_UNAPPROVED')
bpy.context.scene.collection.children.link(coll)
skin = bpy.data.objects['SCULPT02_FACE_BODY'].data.materials[0]
records = []
for sign, label in [(-1, 'L'), (1, 'R')]:
    vertices = [(sign*(.03021274+x), y, 1.52188194+z) for row in CONTOURS for x,y,z in row]
    faces = []
    for band in range(2):
        for station in range(16):
            nxt = (station+1) % 16
            quad = (band*16+station, band*16+nxt, (band+1)*16+nxt, (band+1)*16+station)
            faces.append(quad if sign == 1 else tuple(reversed(quad)))
    mesh = bpy.data.meshes.new('SCULPT03_'+label+'_corner_quad_flow')
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('SCULPT03_EYELID_'+label+'_LOCAL_PROTOTYPE', mesh)
    coll.objects.link(obj)
    mesh.materials.append(skin)
    # Consistent outward front-facing normals. Open surface: 2 boundary loops expected.
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    if sum(f.normal.y for f in bm.faces) > 0:
        bmesh.ops.reverse_faces(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    uv = mesh.uv_layers.new(name='LOCAL_STATION_UV_NOT_FINAL_FACE_ATLAS')
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vid = mesh.loops[li].vertex_index
            # Planar local patch; continuous across canthi, no angular seam.
            uv.data[li].uv = ((vertices[vid][0]*sign-.00021274)/.1, (vertices[vid][2]-1.48)/.1)
    obj.shape_key_add(name='Basis')
    blink = obj.shape_key_add(name='LOCAL_BLINK_NOT_RIGGED')
    # Fixed medial/lateral canthi; both arcs meet at an explicitly authored seam.
    # Tiny residual opening avoids overlapping faces at the closed sample.
    for i, vert in enumerate(blink.data):
        band, station = divmod(i, 16)
        x, y, z = CONTOURS[band][station]
        u = max(0., min(1., (x+.021)/.044))
        seam_z = -.001 + .003*u
        weight = [1., .85, 0.][band]
        is_upper = station < 9
        target = seam_z + (.00025 if is_upper else -.00025)
        if station in (0,8):
            weight = 0.
        vert.co.z = 1.52188194 + z + weight*(target-z)
    sub = obj.modifiers.new('LOCAL_QUAD_PREVIEW', 'SUBSURF')
    sub.levels = 2; sub.render_levels = 2
    obj['status'] = 'LOCAL_TOPOLOGY_PROTOTYPE_NOT_INTEGRATED_SKIN_NOT_FINAL_ART'
    obj['source_sha256'] = EXPECTED
    obj['method_family'] = 'corner_anchored_semantic_upper_lower_quad_strips'
    obj['canthus_vertex_indices'] = [0,8,16,24,32,40]
    obj['known_limitations'] = 'Open outer socket; no source face replacement; no eyeball clearance or rig acceptance'
    records.append({'object': obj.name, 'control_vertices':len(vertices), 'quad_faces':len(faces),
                    'expected_boundary_edges':32, 'blink_key':blink.name})

scene = bpy.context.scene
scene['sculpt03_status'] = 'LOCAL_EYELID_TOPOLOGY_PROTOTYPE_ONLY_UNAPPROVED'
scene['sculpt03_face_completed'] = False
scene['sculpt03_hair_completed'] = False
scene['sculpt03_source_sha256'] = EXPECTED
readme = bpy.data.texts.new('SCULPT03_README_PARTIAL_NOT_FINAL')
readme.write('UNAPPROVED LOCAL EYELID TOPOLOGY PROTOTYPE. Explicitly authored semantic corner strips, executed through Blender Python, not manual GUI sculpting. Source face/hair unchanged. Open boundaries require skin integration. Blink is a diagnostic shape key, not an accepted rig. Full character G2 remains FAIL; G1 BLOCKED by registration; G3 incomplete; G4 NOT_RUN. No canon replacement.\n')
bpy.ops.object.select_all(action='DESELECT')
for obj in coll.objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = next(iter(coll.objects))
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET.resolve()), compress=True)
assert sha(SOURCE) == EXPECTED
report = {'status':'EXECUTED_LOCAL_TOPOLOGY_PROTOTYPE_NOT_FINISHED_SCULPT',
          'source_sha256':EXPECTED, 'candidate_sha256':sha(TARGET),
          'candidate_path':str(TARGET), 'blender':bpy.app.version_string,
          'references_verified':True, 'source_face_and_hair_edited':False,
          'method_family':'corner_anchored_semantic_upper_lower_quad_strips',
          'causal_difference':'New explicitly authored connectivity with paired semantic stations and shared canthi; no polar UV/zipper or source Grab deformation. No hair generation.',
          'objects':records, 'actual_retopology_completed':False,
          'local_quad_geometry_created':True, 'new_hair_geometry_completed':False,
          'G1':'BLOCKED_REGISTRATION', 'G2':'FAIL_INHERITED_CHARACTER',
          'G3':'NOT_RUN', 'G4':'NOT_RUN'}
(OUT/'build_manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print('SCULPT03_LOCAL_GEOMETRY_SAVED', report['candidate_sha256'])
