#!/usr/bin/env python3
"""Export an isolated TECHNICAL GLB for engine loading checks; never production art."""
import bpy, json, hashlib, sys
from pathlib import Path
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
out=Path(args[0]).resolve() if args else Path("/tmp/lind-glb-benchmark/technical-scene.glb")
count=int(args[1]) if len(args)>1 else 100
assert count in (100, 1000, 3000), "Technical benchmark count must be 100, 1000 or 3000"
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
for i in range(count):
    bpy.ops.mesh.primitive_cube_add(size=.38,location=((i%50-24.5)*.7,((i//50)%60-29.5)*.5,0))
    bpy.context.object.name=f"BENCH_ONLY_{i:03d}"
    bpy.context.object.rotation_euler[2]=0
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(out),export_format="GLB",export_yup=True,export_apply=False)
raw=out.read_bytes()
assert raw[:4]==b"glTF" and int.from_bytes(raw[4:8],"little")==2 and int.from_bytes(raw[8:12],"little")==len(raw)
manifest={"role":"TECHNICAL_BENCHMARK_ONLY_NOT_PRODUCTION","objects":count,"blender_version":bpy.app.version_string,"output_sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw),"qa":{"G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL","G4":"NOT_RUN"}}
(out.parent/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
print("TECHNICAL_GLB_EXPORT_PASS",manifest["output_sha256"])
