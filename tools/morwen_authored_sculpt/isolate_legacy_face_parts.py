"""Non-destructive extraction QA of PR #316 legacy face material islands.

Run: blender -b source.blend --python this_file -- OUTPUT_DIR
Never overwrites source; no official design adoption.
"""
import bpy, json, os, sys, hashlib

outdir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(outdir, exist_ok=True)
source = bpy.data.filepath
assert source and os.path.exists(source)
source_hash = hashlib.sha256(open(source, "rb").read()).hexdigest()
assert source_hash == "6c5a9919fd6733a0a1ec8d261fb647e5825cb3dfbc4092ed12c0e7baab26de5c"
face = bpy.data.objects.get("Face")
assert face and face.type == "MESH"
regions = ("FaceEyelash", "FaceEyeline", "FaceBrow")
mesh = face.data
selected = {i for i, mat in enumerate(mesh.materials) if mat and any(t in mat.name for t in regions)}
assert len(selected) == 3, [(i, m.name if m else "") for i,m in enumerate(mesh.materials)]
assert mesh.shape_keys and len(mesh.shape_keys.key_blocks) == 58
original_face_count = len(mesh.polygons)
result = {"source_sha256":source_hash, "source_faces":original_face_count, "regions":{}}
# bpy.ops.object.duplicate preserves UVs, materials, groups, modifiers and all shape keys.
bpy.ops.object.select_all(action="DESELECT")
face.select_set(True)
bpy.context.view_layer.objects.active = face
bpy.ops.object.duplicate()
copy = bpy.context.object
copy.name = "MORWEN_LegacyFaceParts_316_CANDIDATE"
# Enter edit mode and remove all faces outside target material slots.
bpy.ops.object.mode_set(mode="OBJECT")
for poly in copy.data.polygons:
    poly.select = poly.material_index not in selected
bpy.ops.object.mode_set(mode="EDIT")
bpy.ops.mesh.select_mode(type="FACE")
bpy.ops.mesh.delete(type="FACE")
bpy.ops.object.mode_set(mode="OBJECT")
assert copy.data.polygons and len(copy.data.polygons) < original_face_count
assert len(copy.data.shape_keys.key_blocks) == 58
assert len(copy.data.uv_layers) == len(mesh.uv_layers)
assert len(copy.vertex_groups) == len(face.vertex_groups)
assert len(copy.modifiers) == len(face.modifiers)
for i in selected:
    mat = mesh.materials[i].name
    expected = sum(p.material_index == i for p in mesh.polygons)
    actual = sum(p.material_index == i for p in copy.data.polygons)
    assert actual == expected, (mat, expected, actual)
    result["regions"][mat] = {"source_faces":expected, "copy_faces":actual}
# Hide originals in exported candidate, without changing their source .blend.
for obj in bpy.data.objects:
    if obj != copy:
        obj.hide_render = True
        obj.hide_set(True)
copy.hide_render = False
copy.hide_set(False)
target = os.path.join(outdir, "MORWEN_FACE_PARTS_316_ISOLATED_CANDIDATE.blend")
bpy.ops.wm.save_as_mainfile(filepath=target)
assert os.path.exists(target)
result.update(output_sha256=hashlib.sha256(open(target,"rb").read()).hexdigest(),
              output_faces=len(copy.data.polygons), shape_keys=len(copy.data.shape_keys.key_blocks),
              uv_layers=len(copy.data.uv_layers), vertex_groups=len(copy.vertex_groups),
              modifiers=len(copy.modifiers))
with open(os.path.join(outdir,"isolation_qa.json"),"w") as f:
    json.dump(result,f,indent=2)
print("MORWEN_FACE_PARTS_ISOLATION",json.dumps(result))
