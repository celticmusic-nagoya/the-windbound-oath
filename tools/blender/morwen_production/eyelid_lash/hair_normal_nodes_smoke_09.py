"""Isolated Blender Geometry Nodes normal-control feasibility smoke test.

Uses only synthetic meshes. No canonical model, external addons, or materials.
"""
import json
import bpy
from mathutils import Vector

def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mesh=bpy.data.meshes.new("M09_SYNTHETIC_HAIR_STRIP")
    mesh.from_pydata([(-.01,0,0),(.01,0,0),(-.01,.005,.02),(.01,.005,.02)],[],[(0,1,3,2)])
    mesh.update()
    obj=bpy.data.objects.new("M09_SYNTHETIC_HAIR",mesh)
    bpy.context.collection.objects.link(obj)
    before=[tuple(v.normal) for v in mesh.vertices]
    group=bpy.data.node_groups.new("M09_HAIR_NORMAL_CONTROL_TEST","GeometryNodeTree")
    group.interface.new_socket(name="Geometry",in_out="INPUT",socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry",in_out="OUTPUT",socket_type="NodeSocketGeometry")
    inp=group.nodes.new("NodeGroupInput")
    out=group.nodes.new("NodeGroupOutput")
    set_normal=group.nodes.new("GeometryNodeSetMeshNormal")
    normal=group.nodes.new("ShaderNodeCombineXYZ")
    normal.inputs["Z"].default_value=1.0
    group.links.new(inp.outputs["Geometry"],set_normal.inputs["Mesh"])
    available=[{"name":s.name,"identifier":s.identifier,"enabled":s.enabled} for s in set_normal.inputs]
    print("M09_SET_MESH_NORMAL_INPUTS="+json.dumps(available,sort_keys=True))
    normal_socket=next((s for s in set_normal.inputs if s.name=="Normal" and s.enabled),None)
    if normal_socket is None:
        raise RuntimeError("GeometryNodeSetMeshNormal has no enabled Normal socket; inspect reported interface")
    group.links.new(normal.outputs["Vector"],normal_socket)
    group.links.new(set_normal.outputs["Mesh"],out.inputs["Geometry"])
    mod=obj.modifiers.new("M09_TEST_NORMALS","NODES")
    mod.node_group=group
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    eval_mesh=evaluated.to_mesh()
    try:
        assert len(eval_mesh.vertices)==4
        assert len(eval_mesh.polygons)==1
        normals=[tuple(v.normal) for v in eval_mesh.vertices]
        assert all(Vector(n).dot(Vector((0,0,1)))>.99 for n in normals),normals
        result={"status":"PASS_SYNTHETIC_ONLY","blender_version":bpy.app.version_string,
            "vertices":len(eval_mesh.vertices),"faces":len(eval_mesh.polygons),
            "normals_before":before,"normals_after":normals,
            "official_morwen":"NOT_RUN","render_art_qa":"NOT_RUN","game_qa":"NOT_RUN"}
        print("M09_HAIR_NORMAL_TEST="+json.dumps(result,sort_keys=True))
    finally:evaluated.to_mesh_clear()

if __name__=="__main__":main()
