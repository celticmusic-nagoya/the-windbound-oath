"""Fiona Blender candidate armature scaffold. Run inside Blender 4.x.
NO mesh, costume or canonical design is inferred; joints are placeholders.
"""
import bpy
from mathutils import Vector

NAME = "FIONA_CANDIDATE_RIG"
# Relative, noncanonical guide positions in Blender meters.
JOINTS = {
 "root": ((0,0,0),(0,0,0.12),None),
 "pelvis": ((0,0,0.90),(0,0,1.05),"root"),
 "spine": ((0,0,1.05),(0,0,1.35),"pelvis"),
 "chest": ((0,0,1.35),(0,0,1.55),"spine"),
 "neck": ((0,0,1.55),(0,0,1.67),"chest"),
 "head": ((0,0,1.67),(0,0,1.92),"neck"),
}
for side,sign in (("L",1),("R",-1)):
 JOINTS.update({
  f"clavicle.{side}": ((0,0,1.51),(.19*sign,0,1.49),"chest"),
  f"upper_arm.{side}": ((.19*sign,0,1.49),(.48*sign,0,1.30),f"clavicle.{side}"),
  f"forearm.{side}": ((.48*sign,0,1.30),(.68*sign,0,1.13),f"upper_arm.{side}"),
  f"hand.{side}": ((.68*sign,0,1.13),(.76*sign,0,1.06),f"forearm.{side}"),
  f"thigh.{side}": ((.12*sign,0,.91),(.12*sign,0,.49),"pelvis"),
  f"shin.{side}": ((.12*sign,0,.49),(.12*sign,0,.10),f"thigh.{side}"),
  f"foot.{side}": ((.12*sign,0,.10),(.12*sign,-.19,.06),f"shin.{side}"),
 })
if NAME in bpy.data.objects:
 raise RuntimeError("Candidate rig already exists; refusing to overwrite")
arm=bpy.data.armatures.new(NAME)
obj=bpy.data.objects.new(NAME,arm)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active=obj
obj.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
for name,(head,tail,parent) in JOINTS.items():
 bone=arm.edit_bones.new(name)
 bone.head=Vector(head);bone.tail=Vector(tail)
 if parent:bone.parent=arm.edit_bones[parent]
bpy.ops.object.mode_set(mode="OBJECT")
obj["status"]="CANDIDATE_NOT_CANONICAL"
obj["reference"]="FIONA_SOURCE_MANIFEST.json"
print("Fiona placeholder rig created:",len(JOINTS),"bones")
