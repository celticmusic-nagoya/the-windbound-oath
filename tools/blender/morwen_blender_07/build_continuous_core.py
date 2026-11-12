"""Create a continuous torso+pelvis candidate while preserving the 17-bone rig.
Never modifies source .blend or canonical references.
"""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/"assets/candidates/morwen-blender-03/morwen_unified_neutral_candidate.blend"
OUT=ROOT/"assets/candidates/morwen-blender-07"
RIG="Morwen_unified_17_candidate"
BODY="Morwen_unified_neutral_3d_candidate"

def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    rig=bpy.data.objects[RIG]
    old=bpy.data.objects[BODY]
    assert len(rig.data.bones)==17 and len(old.vertex_groups)==16
    assert "pelvis" in old.vertex_groups and "spine" in old.vertex_groups
    pelvis=rig.data.bones["pelvis"]
    spine=rig.data.bones["spine"]
    z0=min(pelvis.head_local.z,pelvis.tail_local.z)
    z1=max(spine.head_local.z,spine.tail_local.z)
    assert z1-z0>0.1
    center_x=(pelvis.head_local.x+spine.tail_local.x)/2
    center_y=(pelvis.head_local.y+spine.tail_local.y)/2
    # Profile is an intentionally conservative inferred-depth candidate.
    levels=((0.00,0.40,0.30),(0.13,0.55,0.40),(0.32,0.68,0.43),
            (0.52,0.56,0.37),(0.74,0.62,0.36),(0.90,0.70,0.38),
            (1.00,0.49,0.31))
    segments=24
    import math
    verts=[]
    for t,rx,ry in levels:
        for j in range(segments):
            angle=2*math.pi*j/segments
            verts.append((center_x+rx*math.cos(angle),center_y+ry*math.sin(angle),
                          z0+(z1-z0)*t))
    faces=[]
    for k in range(len(levels)-1):
        for j in range(segments):
            a=k*segments+j
            b=k*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    faces.append(tuple(reversed(tuple(range(segments)))))
    faces.append(tuple((len(levels)-1)*segments+j for j in range(segments)))
    mesh=bpy.data.meshes.new("Morwen_07_continuous_core_mesh")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    core=bpy.data.objects.new("Morwen_07_continuous_core_candidate",mesh)
    bpy.context.scene.collection.objects.link(core)
    # Smooth interpolation between pelvis and spine groups, rather than rigid skin.
    pelvis_group=core.vertex_groups.new(name="pelvis")
    spine_group=core.vertex_groups.new(name="spine")
    for k,(t,_,_) in enumerate(levels):
        ids=list(range(k*segments,(k+1)*segments))
        w=min(1.0,max(0.0,(t-0.20)/0.65))
        if w<1: pelvis_group.add(ids,1-w,"REPLACE")
        if w>0: spine_group.add(ids,w,"REPLACE")
    for p in mesh.polygons: p.use_smooth=True
    mod=core.modifiers.new("Armature_17_candidate","ARMATURE")
    mod.object=rig
    core["status"]="CANDIDATE_ONLY_NOT_CANON"
    core["depth"]="INFERRED_NOT_MEASURED"
    # Keep original ellipsoid body in source .blend; hide pelvis/spine surface
    # only in the new candidate scene to avoid two competing torso shells.
    # Other 14 segments remain as separate candidate pieces.
    old.hide_render=True
    old.hide_set(True)
    core.hide_render=False
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/"morwen_continuous_core_candidate.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(target))
    report={"task":"MORWEN-BLENDER-07","status":"CANDIDATE_NOT_APPROVED",
            "source":str(SRC.relative_to(ROOT)),"source_modified":False,
            "bones":len(rig.data.bones),"core_vertices":len(mesh.vertices),
            "core_faces":len(mesh.polygons),"continuous_core":True,
            "full_body_continuous":False,"art_approval":"NOT_RUN",
            "production_use":False}
    (OUT/"build_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_07_CONTINUOUS_CORE_CANDIDATE_PASS")

if __name__=="__main__":main()
