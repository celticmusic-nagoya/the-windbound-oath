"""TWO shared deformation rig: -Y forward, +X .L, 22 core bones."""
import bpy
from mathutils import Vector
NAME="TWO_MasterRig_v1"
core=[
("root",None,(0,0,.05),(0,0,.22)),
("pelvis","root",(0,0,.96),(0,0,1.10)),
("spine","pelvis",(0,0,1.10),(0,.025,1.35)),
("chest","spine",(0,.025,1.35),(0,0,1.63)),
("neck","chest",(0,0,1.63),(0,0,1.79)),
("head","neck",(0,0,1.79),(0,0,2.17))]
side=[
("clavicle","chest",(.07,0,1.59),(.27,0,1.58)),
("upper_arm","clavicle",(.27,0,1.58),(.44,-.045,1.28)),
("forearm","upper_arm",(.44,-.045,1.28),(.48,-.01,1.00)),
("hand","forearm",(.48,-.01,1.00),(.48,-.01,.88)),
("thigh","pelvis",(.14,0,.99),(.16,.045,.57)),
("shin","thigh",(.16,.045,.57),(.16,0,.15)),
("foot","shin",(.16,0,.15),(.16,-.20,.08)),
("toe","foot",(.16,-.20,.08),(.16,-.29,.08))]
def create_rig():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    assert NAME not in bpy.data.objects, "rig already exists"
    bpy.ops.object.armature_add()
    rig=bpy.context.object
    rig.name=NAME
    rig.show_in_front=True
    bpy.ops.object.mode_set(mode="EDIT")
    rig.data.edit_bones.remove(rig.data.edit_bones[0])
    def add(n,p,h,t):
        bone=rig.data.edit_bones.new(n)
        bone.head=Vector(h);bone.tail=Vector(t)
        if p: bone.parent=rig.data.edit_bones[p]
        bone.align_roll(Vector((0,1,0)))
    for n,p,h,t in core: add(n,p,h,t)
    for suffix,sign in ((".L",1),(".R",-1)):
        for n,p,h,t in side:
            mirror=lambda v:(v[0]*sign,v[1],v[2])
            add(n+suffix,p+suffix if p in {row[0] for row in side} else p,mirror(h),mirror(t))
    for n,_,h,t in side:
        l=rig.data.edit_bones[n+".L"]; rr=rig.data.edit_bones[n+".R"]
        for a,c in ((l.head,rr.head),(l.tail,rr.tail)):
            assert abs(a.x+c.x)<1e-5 and abs(a.y-c.y)<1e-5 and abs(a.z-c.z)<1e-5
    bpy.ops.object.mode_set(mode="OBJECT")
    assert len(rig.data.bones)==22
    rig["schema"]=NAME
    rig["forward"]="-Y"
    return rig
