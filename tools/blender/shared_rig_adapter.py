"""Shared topology -> Blender armature adapter (candidate only).

Run: blender -b --python tools/blender/shared_rig_adapter.py -- <topology.json> <measured.json>
Measured schema: {"schema":"cas/blender-measured/01","characterId":"fiona",
 "sourceSha256":"<64 hex>","rigSize":[1200,1600],
 "joints":{"pelvis":[x,y],... all topology joint IDs ...}}
Coordinates are 2D rig pixels (top-left, y down); z=0 plane.
Do not use until actual adopted full-body measurements exist.
"""
import json
import re
import sys
from pathlib import Path

def validate(topology, measured):
    joints = topology["joints"]
    if topology["schema"] != "cas/shared-topology/01":
        raise ValueError("unsupported topology")
    if measured.get("schema") != "cas/blender-measured/01":
        raise ValueError("missing measured schema")
    if not re.fullmatch(r"[0-9a-f]{64}", measured.get("sourceSha256", "")):
        raise ValueError("source image SHA256 required")
    size = measured.get("rigSize")
    if not isinstance(size,list) or len(size)!=2 or any(not isinstance(v,int) or v<=0 for v in size):
        raise ValueError("invalid rigSize")
    pts=measured.get("joints",{})
    if set(pts)!=set(joints):
        raise ValueError("all joint IDs must be explicitly measured")
    import math
    for name,p in pts.items():
        if not isinstance(p,list) or len(p)!=2 or any(not isinstance(v,(int,float)) or isinstance(v,bool) or not math.isfinite(v) for v in p):
            raise ValueError("invalid joint: "+name)
        if not (0<=p[0]<=size[0] and 0<=p[1]<=size[1]):
            raise ValueError("joint outside canvas: "+name)
    for name,info in joints.items():
        parent=info["parent"]
        if parent is not None and parent not in joints:
            raise ValueError("unknown parent: "+name)
    return pts,size

def build(topology,measured):
    pts,size=validate(topology,measured)
    import bpy
    name="SHARED_RIG_"+measured["characterId"].upper()+"_CANDIDATE"
    if name in bpy.data.objects:
        raise RuntimeError("refusing to overwrite "+name)
    arm=bpy.data.armatures.new(name)
    obj=bpy.data.objects.new(name,arm)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    scale=1.0/max(size)
    for jid,info in topology["joints"].items():
        p=pts[jid]
        bone=arm.edit_bones.new(jid)
        bone.head=((p[0]-size[0]/2)*scale,0,(size[1]-p[1])*scale)
        # End is deliberately short; these are measured landmark markers,
        # not invented deform-bone lengths.
        bone.tail=(bone.head.x,0,bone.head.z+0.002)
    for jid,info in topology["joints"].items():
        if info["parent"] is not None:
            arm.edit_bones[jid].parent=arm.edit_bones[info["parent"]]
    bpy.ops.object.mode_set(mode="OBJECT")
    obj["approval"]="CANDIDATE_ONLY"
    obj["sourceSha256"]=measured["sourceSha256"]
    return obj

if __name__=="__main__":
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    if len(args)!=2:
        raise SystemExit("usage: blender -b --python shared_rig_adapter.py -- topology.json measured.json")
    t=json.loads(Path(args[0]).read_text(encoding="utf-8"))
    m=json.loads(Path(args[1]).read_text(encoding="utf-8"))
    build(t,m)
