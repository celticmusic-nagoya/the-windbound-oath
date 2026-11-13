"""Deterministic 26-bone master armature template for Morwen.
This creates a RIG TEMPLATE, not a production model or approved animation.
Coordinates: character faces -Y; anatomical right = +X; floor Z=0.
"""
import bpy, json
from pathlib import Path
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
arm=bpy.data.armatures.new("MORWEN_26_BONE_DATA")
rig=bpy.data.objects.new("MORWEN_MASTER_RIG",arm)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig
rig.select_set(True)
bpy.ops.object.mode_set(mode="EDIT")
def add(name,head,tail,parent=None,connected=False):
    bone=arm.edit_bones.new(name)
    bone.head=head;bone.tail=tail
    if parent:
        bone.parent=arm.edit_bones[parent]
        bone.use_connect=connected
    return bone
add("root",(0,0,.05),(0,0,.15))
add("pelvis",(0,0,.75),(0,0,.90),"root")
add("spine_01",(0,0,.90),(0,0,1.08),"pelvis")
add("chest",(0,0,1.08),(0,0,1.39),"spine_01",True)
add("neck",(0,0,1.39),(0,0,1.49),"chest",True)
add("head",(0,0,1.49),(0,0,1.76),"neck",True)
for side,sign in (("L",-1),("R",1)):
    add("clavicle."+side,(0,0,1.35),(sign*.19,0,1.34),"chest")
    add("upper_arm."+side,(sign*.19,0,1.34),(sign*.25,0,1.10),"clavicle."+side,True)
    add("forearm."+side,(sign*.25,0,1.10),(sign*.27,0,.88),"upper_arm."+side,True)
    add("hand."+side,(sign*.27,0,.88),(sign*.27,0,.76),"forearm."+side,True)
    add("thigh."+side,(sign*.105,0,.78),(sign*.11,0,.47),"pelvis")
    add("shin."+side,(sign*.11,0,.47),(sign*.11,0,.13),"thigh."+side,True)
    add("foot."+side,(sign*.11,0,.13),(sign*.11,-.11,.065),"shin."+side,True)
    add("toe."+side,(sign*.11,-.11,.065),(sign*.11,-.19,.065),"foot."+side,True)
add("hat",(0,0,1.71),(0,0,1.97),"head")
add("cape.L",(-.14,.05,1.34),(-.28,.11,.70),"chest")
add("cape.R",(.14,.05,1.34),(.28,.11,.70),"chest")
# 22 body + 4 accessories: hat, two cape bones, and satchel.
add("satchel",(.10,.05,1.10),(.23,.08,.85),"chest")
bpy.ops.object.mode_set(mode="OBJECT")
assert len(arm.bones)==26,len(arm.bones)
assert set(arm.bones.keys())=={"root","pelvis","spine_01","chest","neck","head",
"clavicle.L","upper_arm.L","forearm.L","hand.L","clavicle.R","upper_arm.R","forearm.R","hand.R",
"thigh.L","shin.L","foot.L","toe.L","thigh.R","shin.R","foot.R","toe.R","hat","cape.L","cape.R","satchel"}
out=Path("render_output/morwen_rig_template");out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str((out/"MORWEN_26_BONE_RIG_TEMPLATE.blend").resolve()))
(out/"QA.json").write_text(json.dumps({"bones":len(arm.bones),"rig_template":True,
"approved_master_model":False,"mesh_bound":False,"G1":"NOT_RUN","G2":"NOT_RUN",
"G3":"RIG_STRUCTURE_PASS","G4":"NOT_RUN",
"coordinate_convention":"character right +X; front screen left"},indent=2)+"\n")
