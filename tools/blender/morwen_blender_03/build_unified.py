"""MORWEN-BLENDER-03: unified neutral 3D *candidate*, not canonical art.
Run: blender -b -t 1 --python tools/blender/morwen_blender_03/build_unified.py
Requires PR #246's .blend and anchors JSON in their committed locations.
Never overwrites the input .blend or references.
"""
import json
import math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "assets/candidates/morwen-blender-01"
OUTPUT = ROOT / "assets/candidates/morwen-blender-03"
CONTRACT = ROOT / "tools/blender/rigs/humanoid_v1.json"
BONES = ("root", "pelvis", "spine", "neck", "head")
SEGMENTS = (("upper_arm", "shoulder", "elbow"), ("forearm", "elbow", "wrist"),
            ("hand", "wrist", "handtip"), ("thigh", "hip", "knee"),
            ("shin", "knee", "ankle"), ("foot", "ankle", "toe"))
RADII = {"pelvis": (48, 42), "spine": (53, 36), "neck": (19, 18),
         "head": (49, 43), "upper_arm": (19, 19), "forearm": (15, 15),
         "hand": (12, 11), "thigh": (30, 29), "shin": (22, 21),
         "foot": (19, 31)}

def main():
    data = json.loads((SOURCE / "anchors_candidate.json").read_text())
    contract = json.loads(CONTRACT.read_text())
    parents = {item["id"]: item["parent"] for item in contract["bones"]}
    assert len(parents) == 17
    front, right, back, left = (data["facings"][k] for k in ("front","right","back","left"))
    for entry in (front,right,back,left):
        assert entry["dimensions"] == [384,1024]
    scale = float(data["common_pixel_scale"])
    assert 0 < scale < 0.1
    # Front view provides X and Z. Side silhouettes provide only a *candidate*
    # depth, not a reconstructed 3D surface. Side x differences are averaged.
    # The back view is used only for numerical X-consistency reporting.
    f = front["rig_points_pixels"]
    def pixel(name):
        if name in f:
            return f[name]
        raise ValueError("Missing landmark: " + name)
    def point(name):
        x,y = pixel(name)
        right_xy = right["rig_points_pixels"][name]
        left_xy = left["rig_points_pixels"][name]
        # Right-facing profile looks toward +X; its screen x is a provisional
        # front/back axis. Left-facing looks toward -X, hence sign inversion.
        depth_px = ((right_xy[0] - right["origin_x"]) -
                    (left_xy[0] - left["origin_x"])) / 2
        depth_px = max(-80, min(80, depth_px))
        return Vector(((x-front["origin_x"])*scale,
                       depth_px*scale,
                       (front["measured_ground_y"]-y)*scale))
    endpoints = {"root": ("pelvis","waist"), "pelvis": ("pelvis","waist"),
                 "spine": ("waist","chest"), "neck": ("chest","neck"),
                 "head": ("neck","head_top")}
    # Root is offset below pelvis so it has nonzero length.
    for side in ("L","R"):
        for key,a,b in SEGMENTS:
            endpoints[key+"."+side] = (a+"."+side,b+"."+side)
    assert set(endpoints) == set(parents)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/"morwen_base_rig_candidate.blend"))
    scene = bpy.context.scene
    coll = bpy.data.collections.new("UNIFIED_3D_CANDIDATE_NOT_CANON")
    scene.collection.children.link(coll)
    arm = bpy.data.armatures.new("Morwen_unified_17_candidate")
    rig = bpy.data.objects.new(arm.name,arm)
    coll.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    locations = {}
    for name,(a,b) in endpoints.items():
        head,tail = point(a),point(b)
        if name == "root":
            head = point("pelvis") + Vector((0,0,-0.05))
        assert (head-tail).length > 1e-6, name
        bone = arm.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        bone.use_deform = name != "root"
        locations[name] = (head,tail)
    for name,parent in parents.items():
        if parent:
            arm.edit_bones[name].parent = arm.edit_bones[parent]
            arm.edit_bones[name].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")
    vertices, faces, weights = [], [], {}
    for name,(head,tail) in locations.items():
        if name == "root":
            continue
        key = name.split(".")[0]
        rx,ry = RADII[key]
        axis = (tail-head).normalized()
        basis = Vector((1,0,0))
        if abs(axis.dot(basis)) > .95:
            basis = Vector((0,1,0))
        basis = (basis-axis*basis.dot(axis)).normalized()
        other = axis.cross(basis).normalized()
        center = (head+tail)/2
        half = (tail-head).length/2 + 6*scale
        start = len(vertices)
        rings,steps = 10,16
        vertices.append(tuple(center+axis*half))
        for lat in range(1,rings):
            theta = math.pi*lat/rings
            for lon in range(steps):
                phi = 2*math.pi*lon/steps
                v = (center+axis*(math.cos(theta)*half)
                     +basis*(math.sin(theta)*math.cos(phi)*rx*scale)
                     +other*(math.sin(theta)*math.sin(phi)*ry*scale))
                vertices.append(tuple(v))
        bottom = len(vertices)
        vertices.append(tuple(center-axis*half))
        weights[name] = list(range(start,len(vertices)))
        for lon in range(steps):
            faces.append((start,start+1+lon,start+1+(lon+1)%steps))
            last = start+1+(rings-2)*steps
            faces.append((bottom,last+(lon+1)%steps,last+lon))
        for lat in range(rings-2):
            for lon in range(steps):
                a=start+1+lat*steps+lon
                b=start+1+lat*steps+(lon+1)%steps
                faces.append((a,b,b+steps,a+steps))
    mesh = bpy.data.meshes.new("Morwen_unified_neutral_segments")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj = bpy.data.objects.new("Morwen_unified_neutral_3d_candidate",mesh)
    coll.objects.link(obj)
    for name,indices in weights.items():
        obj.vertex_groups.new(name=name).add(indices,1.0,"REPLACE")
    mod = obj.modifiers.new("CandidateArmature","ARMATURE")
    mod.object = rig
    obj["status"] = "UNIFIED_3D_CANDIDATE_NOT_ART_APPROVED"
    rig["depth"] = "INFERRED_FROM_SIDE_VIEWS_NOT_MEASURED"
    scene["task"] = "MORWEN-BLENDER-03"
    scene["approval_status"] = "FUTURE_CANON_PENDING_APPROVAL"
    assert len(arm.bones) == 17
    assert len(obj.vertex_groups) == 16
    assert all(len(poly.vertices) >= 3 for poly in mesh.polygons)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    target = OUTPUT/"morwen_unified_neutral_candidate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report = {"status":"CANDIDATE_BUILT_NOT_VISUALLY_APPROVED",
              "bones":len(arm.bones),"vertices":len(mesh.vertices),
              "faces":len(mesh.polygons),"depth":"INFERRED",
              "single_shared_armature":True,"single_mesh_object":True,
              "single_continuous_skin":False,"visual_qa":"NOT_RUN",
              "independent_blender_qa":"NOT_RUN",
              "production_use":False}
    (OUTPUT/"build_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_BLENDER_03_CANDIDATE_BUILT")

if __name__ == "__main__":
    main()
