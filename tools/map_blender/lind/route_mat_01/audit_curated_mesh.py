"""Independent intake QA for curated/hand-sculpted bridge masonry. Never modifies sources.
Usage: blender -b --factory-startup --python-exit-code 1 --python audit_curated_mesh.py -- --input PATH --manifest PATH --report PATH
The model and rights evidence must exist before the audit can PASS.
"""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy
import bmesh

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",required=True,type=Path)
    p.add_argument("--manifest",required=True,type=Path)
    p.add_argument("--report",required=True,type=Path)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    failures=[]
    report={"status":"BLOCKED","G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN","failures":failures}
    if not a.input.is_file(): failures.append("mesh file absent")
    if not a.manifest.is_file(): failures.append("source rights manifest absent")
    if failures:
        a.report.parent.mkdir(parents=True,exist_ok=True)
        a.report.write_text(json.dumps(report,indent=2))
        print(json.dumps(report));return
    meta=json.loads(a.manifest.read_text())
    required=("source_url","author","license","license_evidence_url","source_sha256","asset_status")
    for field in required:
        if not isinstance(meta.get(field),str) or not meta[field].strip(): failures.append("missing "+field)
    digest=hashlib.sha256(a.input.read_bytes()).hexdigest()
    if meta.get("source_sha256")!=digest: failures.append("source hash mismatch")
    if meta.get("asset_status")!="candidate":failures.append("must remain candidate")
    if not failures:
        bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
        suffix=a.input.suffix.lower()
        if suffix==".blend":bpy.ops.wm.open_mainfile(filepath=str(a.input))
        elif suffix==".glb":bpy.ops.import_scene.gltf(filepath=str(a.input))
        elif suffix==".obj":bpy.ops.wm.obj_import(filepath=str(a.input))
        else:failures.append("unsupported model type")
    details=[]
    if not failures:
        for obj in bpy.data.objects:
            if obj.type!="MESH":continue
            bm=bmesh.new();bm.from_mesh(obj.data)
            boundary=sum(1 for e in bm.edges if e.is_boundary)
            nonmanifold=sum(1 for e in bm.edges if not e.is_manifold)
            details.append({"name":obj.name,"vertices":len(bm.verts),"faces":len(bm.faces),
                            "boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
                            "dimensions":list(obj.dimensions)})
            bm.free()
        if not details:failures.append("no mesh geometry")
        if any(x["boundary_edges"] or x["nonmanifold_edges"] for x in details):
            failures.append("open or nonmanifold mesh present; review before use")
    report.update({"status":"FAIL" if failures else "TECHNICAL_INTAKE_PASS_NOT_ART_APPROVED",
                   "G1":"FAIL" if failures else "PARTIAL",
                   "G3":"FAIL" if failures else "PARTIAL",
                   "source_sha256_actual":digest,"meshes":details})
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
    if failures:sys.exit(2)

if __name__=="__main__":main()
