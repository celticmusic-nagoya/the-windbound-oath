"""EYELID-09 isolated Blender geometry smoke test.

Creates only a temporary synthetic candidate scene, not Morwen production geometry.
Run: blender -b --factory-startup --python tools/blender/morwen_production/eyelid_lash/blender_smoke_09.py
"""
import json
import pathlib
import sys
import bpy

HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from lash_attachment_09 import evaluated_root
from lash_strip_geometry_09 import build_lash_strip
from lash_blender_adapter_09 import evaluated_anchor,validate_stable_topology

def run():
    mesh=bpy.data.meshes.new("M09_SYNTHETIC_LID_MESH")
    mesh.from_pydata([(0,0,0),(.01,0,0),(0,0,.01)],[],[(0,1,2)])
    mesh.update()
    obj=bpy.data.objects.new("M09_SYNTHETIC_LID",mesh)
    bpy.context.collection.objects.link(obj)
    try:
        topo=validate_stable_topology(obj,3)
        frame=evaluated_anchor(obj,(0,1,2),(.2,.3,.5),offset_m=.0001)
        candidate=build_lash_strip(frame,length_m=.003,width_m=.0004,samples=7)
        lash_mesh=bpy.data.meshes.new("M09_LASH_STRIP_SMOKE_MESH")
        lash_mesh.from_pydata(candidate["vertices"],[],candidate["faces"])
        lash_mesh.update()
        lash_obj=bpy.data.objects.new("M09_LASH_STRIP_SMOKE",lash_mesh)
        bpy.context.collection.objects.link(lash_obj)
        try:
            assert len(lash_mesh.vertices)==14
            assert len(lash_mesh.polygons)==6
            assert all(p.area>1e-14 for p in lash_mesh.polygons)
            result={"status":"PASS_SYNTHETIC_ONLY","vertex_count":14,"face_count":6,
                    "topology":topo,"morwen_geometry":"NOT_RUN",
                    "collision_qa":"NOT_RUN","art_qa":"NOT_RUN"}
            print("EYELID09_SMOKE_JSON="+json.dumps(result,sort_keys=True))
        finally:
            bpy.data.objects.remove(lash_obj,do_unlink=True)
            bpy.data.meshes.remove(lash_mesh)
    finally:
        bpy.data.objects.remove(obj,do_unlink=True)
        bpy.data.meshes.remove(mesh)
if __name__=="__main__":run()
