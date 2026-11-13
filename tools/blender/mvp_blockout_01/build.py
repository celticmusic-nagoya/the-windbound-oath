"""MVP BLOCKOUT-01: candidate-only primitive Morwen + modular one-screen map.
Run: blender -b --python tools/blender/mvp_blockout_01/build.py
No canonical assets are read or overwritten. ART approval is NOT_RUN.
"""
import json
import math
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "assets/candidates/mvp-blockout-01"
PALETTE = {
    "skin": (0.73, 0.56, 0.46, 1),
    "hair": (0.23, 0.17, 0.15, 1),
    "uniform": (0.22, 0.29, 0.38, 1),
    "socks": (0.18, 0.21, 0.27, 1),
    "boots": (0.12, 0.11, 0.11, 1),
    "ground": (0.27, 0.43, 0.29, 1),
    "stone": (0.43, 0.43, 0.42, 1),
    "wood": (0.35, 0.22, 0.14, 1),
    "leaves": (0.16, 0.32, 0.18, 1),
}
def mat(name):
    m = bpy.data.materials.new(name)
    m.diffuse_color = PALETTE[name]
    return m
def part(name, kind, pos, scale, material):
    if kind == "cube":
        bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    elif kind == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, location=pos)
    else:
        bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.5, depth=1, location=pos)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    return obj
def save_candidate(filename):
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / filename))
def export_glb(filename):
    bpy.ops.export_scene.gltf(filepath=str(OUT / filename), export_format="GLB")
def morwen():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    m = {k: mat(k) for k in ("skin", "hair", "uniform", "socks", "boots")}
    parts = [
        ("torso", "cube", (0,0,1.36), (.54,.30,.72), "uniform"),
        ("pelvis", "cube", (0,0,0.96), (.46,.31,.24), "uniform"),
        ("neck", "cylinder", (0,0,1.81), (.15,.15,.18), "skin"),
        ("head", "sphere", (0,-.015,2.02), (.37,.32,.45), "skin"),
        ("hair_cap", "sphere", (0,.04,2.22), (.39,.34,.21), "hair"),
    ]
    for side, sign in (("L",-1),("R",1)):
        parts += [
            ("arm_"+side,"cylinder",(sign*.40,0,1.38),(.18,.19,.65),"uniform"),
            ("hand_"+side,"sphere",(sign*.40,-.01,1.02),(.16,.15,.17),"skin"),
            ("thigh_"+side,"cylinder",(sign*.145,0,.70),(.20,.23,.54),"uniform"),
            ("sock_"+side,"cylinder",(sign*.145,0,.31),(.18,.19,.36),"socks"),
            ("boot_"+side,"cube",(sign*.145,-.065,.095),(.21,.34,.19),"boots"),
        ]
    for args in parts:
        part(*args[:-1],m[args[-1]])
    assert len(parts) >= 15
    save_candidate("morwen_blockout.blend")
    export_glb("morwen_blockout.glb")
    return len(parts)
def map_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    m={k:mat(k) for k in ("ground","stone","wood","leaves")}
    part("ground_tile_01","cube",(0,0,-.10),(10,8,.2),m["ground"])
    for i in range(5):
        part("wall_"+str(i),"cube",(-4+i*2,3.75,.45),(2,.5,.9),m["stone"])
    for i,(x,y) in enumerate(((-3,-2.5),(3,2.0))):
        part("tree_trunk_"+str(i),"cylinder",(x,y,.75),(.38,.38,1.5),m["wood"])
        part("tree_crown_"+str(i),"sphere",(x,y,1.75),(1.35,1.35,1.35),m["leaves"])
    for i,(x,y) in enumerate(((-2,2),(2,-2))):
        part("rock_"+str(i),"sphere",(x,y,.25),(.85,.75,.5),m["stone"])
    save_candidate("test_map_blockout.blend")
    export_glb("test_map_blockout.glb")
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    count=morwen()
    map_scene()
    report={"task":"MVP-BLOCKOUT-01","candidate_only":True,
      "art_approval":"NOT_RUN","game_integration":"NOT_RUN",
      "morwen_parts":count,"map_modules":["ground","wall","tree","rock"],
      "canonical_assets_modified":False}
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MVP_BLOCKOUT_EXPORT_PASS")
if __name__=="__main__":
    main()
