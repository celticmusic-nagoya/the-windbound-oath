# MORWEN_RENDER_16_TRIGGER: existing PR workflow includes this path; diagnostic outputs remain candidate-only.
"""MVP BLOCKOUT-01: candidate-only primitive Morwen character.
Run: blender -b --python tools/blender/mvp_blockout_01/build.py
No canonical assets are read or overwritten. ART approval is NOT_RUN.
"""
import json
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
    for side, sign in (("L",1),("R",-1)):
        parts += [
            ("arm_"+side,"cylinder",(sign*.40,0,1.38),(.18,.19,.65),"uniform"),
            ("hand_"+side,"sphere",(sign*.40,-.01,1.02),(.16,.15,.17),"skin"),
            ("thigh_"+side,"cylinder",(sign*.145,0,.70),(.20,.23,.54),"uniform"),
            ("sock_"+side,"cylinder",(sign*.145,0,.31),(.18,.19,.36),"socks"),
            ("boot_"+side,"cube",(sign*.145,-.065,.095),(.21,.34,.19),"boots"),
        ]
    for args in parts:
        part(*args[:-1],m[args[-1]])
    assert len(parts) == 15
    save_candidate("morwen_blockout.blend")
    export_glb("morwen_blockout.glb")
    return len(parts)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    count=morwen()
    report={"task":"MVP-BLOCKOUT-01","candidate_only":True,
      "art_approval":"NOT_RUN","game_integration":"NOT_RUN",
      "morwen_parts":count,
      "canonical_assets_modified":False}
    (OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MVP_BLOCKOUT_EXPORT_PASS")
if __name__=="__main__":
    main()
