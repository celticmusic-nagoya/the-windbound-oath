"""Topology-first Morwen anatomical blockout: voxel-union source geometry.
Candidate-only; original 17-bone rig, references and 09 core untouched.
"""
import json,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-11"
RIG="Morwen_unified_17_candidate"
OLD="Morwen_unified_neutral_3d_candidate"
CORE="Morwen_09_landmark_core_candidate"

def bridge_mesh(name,a,b,radius,collection):
    direction=b-a
    if direction.length<1e-5:return None
    mid=(a+b)/2
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=radius,depth=direction.length+radius*2,location=mid)
    obj=bpy.context.object
    obj.name=name
    obj.rotation_euler=direction.to_track_quat("Z","Y").to_euler()
    return obj

def count_components(mesh):
    bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
    seen=set();components=0
    for v in bm.verts:
        if v.index in seen:continue
        components+=1;stack=[v];seen.add(v.index)
        while stack:
            cur=stack.pop()
            for edge in cur.link_edges:
                other=edge.other_vert(cur)
                if other.index not in seen:seen.add(other.index);stack.append(other)
    bm.free()
    return components

def main():
    scene=bpy.context.scene
    rig=bpy.data.objects[RIG]
    old=bpy.data.objects[OLD]
    core=bpy.data.objects[CORE]
    assert len(rig.data.bones)==17
    # Remove old pelvis/spine ellipsoids in a DERIVED mesh only.
    derived=old.copy();derived.data=old.data.copy()
    derived.name="Morwen_11_source_limbs_head_candidate"
    scene.collection.objects.link(derived)
    names={g.index:g.name for g in old.vertex_groups}
    keep=set()
    for p in old.data.polygons:
        memberships={names[w.group] for i in p.vertices for w in old.data.vertices[i].groups}
        if memberships.isdisjoint({"pelvis","spine"}):keep.add(p.index)
    bm=bmesh.new();bm.from_mesh(derived.data);bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in keep],context="FACES")
    bm.to_mesh(derived.data);bm.free()
    # All joints are bridged with overlapping anatomical capsules so voxel
    # union can form one surface instead of 14 disconnected shells.
    bones=rig.data.bones
    def head(n):return rig.matrix_world @ bones[n].head_local
    def tail(n):return rig.matrix_world @ bones[n].tail_local
    bridges=[]
    for side in ("L","R"):
        for a,b,r in (
            ("spine","upper_arm."+side,.033),
            ("upper_arm."+side,"forearm."+side,.020),
            ("forearm."+side,"hand."+side,.016),
            ("pelvis","thigh."+side,.043),
            ("thigh."+side,"shin."+side,.030),
            ("shin."+side,"foot."+side,.022)):
            start=tail(a) if a in ("spine","pelvis") else tail(a)
            end=head(b)
            obj=bridge_mesh("MORWEN_11_BRIDGE_"+a+"_"+b,start,end,r,scene.collection)
            if obj:bridges.append(obj)
    for a,b,r in (("spine","neck",.038),("neck","head",.034)):
        obj=bridge_mesh("MORWEN_11_BRIDGE_"+a+"_"+b,tail(a),head(b),r,scene.collection)
        if obj:bridges.append(obj)
    # Convert copied limb mesh and torso to unskinned mesh coordinates;
    # all source objects are independent and never edited.
    parts=[derived,core]+bridges
    bpy.ops.object.select_all(action="DESELECT")
    for obj in parts:
        for mod in list(obj.modifiers):
            if mod.type=="ARMATURE":obj.modifiers.remove(mod)
        obj.select_set(True)
    bpy.context.view_layer.objects.active=derived
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    joined=bpy.context.object
    joined.name="Morwen_11_voxel_union_candidate"
    # Voxel remesh union of overlapping shells; test connectivity afterward.
    joined.data.remesh_voxel_size=.012
    bpy.ops.object.voxel_remesh()
    assert len(joined.data.vertices)>100
    components=count_components(joined.data)
    # Nearest segment distance -> smooth two-bone blending for deformation.
    # Vertex group names must match existing 17-bone contract.
    for g in list(joined.vertex_groups):joined.vertex_groups.remove(g)
    deform=[b for b in bones if b.use_deform]
    groups={b.name:joined.vertex_groups.new(name=b.name) for b in deform}
    for v in joined.data.vertices:
        pos=joined.matrix_world @ v.co
        distances=[]
        for bone in deform:
            a=head(bone.name);b=tail(bone.name);ab=b-a
            t=max(0,min(1,(pos-a).dot(ab)/max(ab.length_squared,1e-10)))
            d=(pos-(a+ab*t)).length
            distances.append((d,bone.name))
        distances.sort()
        nearest=distances[:2]
        inv=[1/max(d,.005)**2 for d,_ in nearest]
        total=sum(inv)
        for (d,name),w in zip(nearest,inv):
            groups[name].add([v.index],w/total,"REPLACE")
    mod=joined.modifiers.new("Morwen_11_armature","ARMATURE");mod.object=rig
    for obj in scene.objects:
        if obj.type in {"MESH","CURVE","FONT","SURFACE"} and obj!=joined:obj.hide_render=True
    joined.hide_render=False
    OUT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_connected_candidate.blend"))
    report={"task":"MORWEN-BLENDER-11","bones":len(bones),
        "vertices":len(joined.data.vertices),"faces":len(joined.data.polygons),
        "connected_components":components,"bridge_count":len(bridges),
        "single_mesh_object":True,"full_body_continuous":components==1,
        "art_approval":"NOT_RUN","deformation_qa":"NOT_RUN","production_use":False}
    (OUT/"build_report.json").write_text(json.dumps(report,indent=2)+"\n")
    assert components==1, "Non-continuous voxel mesh: inspect bridge alignment; do not approve"
    print("MORWEN_11_CONNECTED_BODY_PASS")

if __name__=="__main__":main()
