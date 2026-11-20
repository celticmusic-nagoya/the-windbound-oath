"""Read-only QA for preserved face material islands in isolated Blender candidate."""
import bpy, json, os, sys, hashlib
from collections import Counter

outdir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(outdir, exist_ok=True)
original = bpy.data.objects.get("Face")
isolated = bpy.data.objects.get("MORWEN_LegacyFaceParts_316_CANDIDATE")
assert original and isolated and original.data is not isolated.data
names = ("FaceEyelash", "FaceEyeline", "FaceBrow")
def q(vec):
    return tuple(round(float(v), 7) for v in vec)
def inspect(obj, token):
    mesh = obj.data
    indexes = {i for i, m in enumerate(mesh.materials) if m and token in m.name}
    assert len(indexes) == 1, (obj.name, token)
    faces = [p for p in mesh.polygons if p.material_index in indexes]
    ids = {v for p in faces for v in p.vertices}
    keys = mesh.shape_keys.key_blocks
    assert len(keys) == 58
    key_coords = {k.name: Counter(q(k.data[i].co) for i in ids) for k in keys}
    topology = Counter(tuple(sorted(q(mesh.vertices[i].co) for i in p.vertices)) for p in faces)
    uvs = Counter(tuple(sorted(q(mesh.uv_layers.active.data[li].uv) for li in p.loop_indices)) for p in faces)
    weights = Counter((q(mesh.vertices[i].co), tuple(sorted((obj.vertex_groups[g.group].name,round(g.weight,7)) for g in mesh.vertices[i].groups))) for i in ids)
    return {"faces":len(faces), "verts":len(ids), "keys":key_coords, "topology":topology, "uvs":uvs, "weights":weights}
report = {"source":bpy.data.filepath,"regions":{},"status":"PASS"}
for token in names:
    a,b=inspect(original,token),inspect(isolated,token)
    checks={"face_count":a["faces"]==b["faces"],"vertex_count":a["verts"]==b["verts"],"topology":a["topology"]==b["topology"],"uvs":a["uvs"]==b["uvs"],"weights":a["weights"]==b["weights"],"shape_keys":all(a["keys"][k]==b["keys"].get(k) for k in a["keys"])}
    report["regions"][token]={"source_faces":a["faces"],"isolated_faces":b["faces"],"checks":checks}
    if not all(checks.values()):report["status"]="FAIL"
with open(os.path.join(outdir,"deformation_integrity_qa.json"),"w") as f:json.dump(report,f,indent=2)
print("FACE_PARTS_INTEGRITY",report["status"],json.dumps(report["regions"]))
assert report["status"]=="PASS",report["regions"]
