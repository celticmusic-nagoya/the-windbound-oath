"""MORWEN-BODY-03: calibrated Layer 0 reference guides, no canonical edits.
Blender: blender -b --python tools/blender/morwen_body_03/setup.py
Optional: TWO_MORWEN_LAYER0_PNG=/absolute/path/to/reference.png
"""
import bpy, json, os, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-body-03"
REG=ROOT/"docs/design/MORWEN_LAYER0_REFERENCE_REGISTRY.json"
POINTS=ROOT/"docs/design/MORWEN_LAYER0_LANDMARKS_CANDIDATE.json"
OUT.mkdir(parents=True,exist_ok=True)
registry=json.loads(REG.read_text())
marks=json.loads(POINTS.read_text())
assert registry["schema"]=="TWO_MORWEN_LAYER0_REFERENCE_V1"
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
# 1.63 m is a visual reference only: sheet explicitly includes footwear.
HEIGHT=1.63
pixel_top=marks["front_view"]["head_top_y"]
pixel_sole=marks["front_view"]["sole_y_approx"]
scale=HEIGHT/(pixel_sole-pixel_top)
landmarks={}
for key,y in marks["front_view"].items():
    if key.endswith("_y") or key.endswith("_approx"):
        if isinstance(y,(int,float)) and key!="axis_x_approx":
            landmarks[key]=round((pixel_sole-y)*scale,5)
def mat(name,rgba):
    m=bpy.data.materials.new(name);m.diffuse_color=rgba;return m
guide=mat("guide_only_blue",(.10,.35,.75,1))
def marker(name,xyz,r=.012):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=r,location=xyz)
    ob=bpy.context.object;ob.name=name;ob.data.materials.append(guide)
def segment(name,a,c,r=.004):
    mid=(Vector(a)+Vector(c))/2
    delta=Vector(c)-Vector(a)
    bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=r,depth=delta.length,location=mid)
    ob=bpy.context.object;ob.name=name;ob.rotation_euler=delta.to_track_quat("Z","Y").to_euler()
    ob.data.materials.append(guide)
# Landmark positions are approximate guides, not a finished body mesh.
heights=[("sole",0),("ankle",landmarks["ankle_y_approx"]),("knee",landmarks["knee_y_approx"]),
         ("hip",landmarks["hip_y_approx"]),("shoulder",landmarks["shoulder_y_approx"]),
         ("chin",landmarks["chin_y_approx"]),("head_top",HEIGHT)]
for name,z in heights:marker("LANDMARK_"+name,(0,0,z))
for (a,az),(c,cz) in zip(heights,heights[1:]):
    segment("GUIDE_"+a+"_"+c,(0,0,az),(0,0,cz))
# Optional sheet is shown as an unmodified image in a separate reference plane.
ref=os.environ.get("TWO_MORWEN_LAYER0_PNG","")
reference_status="MISSING"
if ref:
    path=Path(ref)
    assert path.is_file(),ref
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert digest==registry["source_sha256"],"Layer 0 reference SHA mismatch"
    img=bpy.data.images.load(str(path),check_existing=True)
    assert tuple(img.size)==(1536,1024)
    # Reference composition is a four-view *sheet*, not four separate orthographic photos.
    # Keep it intact; do not treat panel crops as orthographically calibrated.
    bpy.ops.mesh.primitive_plane_add(size=2,location=(0,.4,.9))
    plane=bpy.context.object;plane.name="LAYER0_SHEET_REFERENCE_UNMODIFIED"
    plane.scale=(1.5,1.0,1.0)
    plane.rotation_euler=(1.57079632679,0,0)
    m=bpy.data.materials.new("LAYER0_SHEET_DISPLAY")
    m.use_nodes=True
    tex=m.node_tree.nodes.new("ShaderNodeTexImage");tex.image=img
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    m.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
    plane.data.materials.append(m)
    reference_status="HASH_VERIFIED"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_body_reference_guides.blend"))
report={"task":"MORWEN-BODY-03","stage":"REFERENCE_GUIDES_ONLY",
"source_sha256":registry["source_sha256"],"reference_status":reference_status,
"guide_height_m":HEIGHT,"estimated_landmark_heights_m":landmarks,
"body_mesh":"NOT_BUILT","art_qa":"NOT_RUN","canonical_modified":False}
(OUT/"report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
print("MORWEN_BODY_03_GUIDES_PASS")
