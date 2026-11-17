"""Read already-generated normalized OBJ and save .blend; no procedural geometry.
Technical display only; not a production cliff asset.
"""
import argparse, bpy, json, hashlib, sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--obj",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    source=Path(a.obj);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    assert source.exists() and source.stat().st_size>1000
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    print("OBJ_IMPORT_START",flush=True)
    bpy.ops.wm.obj_import(filepath=str(source.resolve()))
    meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
    assert len(meshes)==1,len(meshes)
    obj=meshes[0];obj.name="LIND_MACRO_CLIFF_OBJ_DIAGNOSTIC_NOT_CANON"
    print("OBJ_IMPORTED",len(obj.data.vertices),len(obj.data.polygons),flush=True)
    assert len(obj.data.vertices)>1000 and len(obj.data.polygons)>1000
    bpy.ops.wm.save_as_mainfile(filepath=str((out/"lind_macro_import_diagnostic.blend").resolve()))
    print("BLEND_SAVED",flush=True)
    blend=out/"lind_macro_import_diagnostic.blend"
    manifest={"production_ready":False,"rendered":False,"source_obj_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"blend_sha256":hashlib.sha256(blend.read_bytes()).hexdigest(),"vertices":len(obj.data.vertices),"polygons":len(obj.data.polygons)}
    (out/"import_metrics.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("IMPORT_SAVE_PASS",flush=True)
if __name__=="__main__":main()
