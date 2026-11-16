"""Isolated Blender 5.3 Geometry Nodes shading smoke.

Structural switch after two failures of Set Mesh Normal custom-normal socket.
This tests shade-smooth capability only; it is NOT a custom-normal-transfer QA.
"""
import bpy
import json

def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    mesh=bpy.data.meshes.new("M09_SYNTHETIC_HAIR_STRIP")
    mesh.from_pydata([(-.01,0,0),(.01,0,0),(-.01,.005,.02),(.01,.005,.02)],[],[(0,1,3,2)])
    mesh.update()
    obj=bpy.data.objects.new("M09_SYNTHETIC_HAIR",mesh)
    bpy.context.collection.objects.link(obj)
    group=bpy.data.node_groups.new("M09_HAIR_SMOOTH_TEST","GeometryNodeTree")
    group.interface.new_socket(name="Geometry",in_out="INPUT",socket_type="NodeSocketGeometry")
    group.interface.new_socket(name="Geometry",in_out="OUTPUT",socket_type="NodeSocketGeometry")
    inp=group.nodes.new("NodeGroupInput")
    out=group.nodes.new("NodeGroupOutput")
    shade=group.nodes.new("GeometryNodeSetShadeSmooth")
    sockets=[{"name":s.name,"identifier":s.identifier,"enabled":s.enabled} for s in shade.inputs]
    print("M09_SHADE_SMOOTH_INPUTS="+json.dumps(sockets,sort_keys=True),flush=True)
    geometry=next((s for s in shade.inputs if s.name=="Geometry" and s.enabled),None)
    smooth=next((s for s in shade.inputs if s.name=="Shade Smooth" and s.enabled),None)
    if geometry is None or smooth is None:
        raise RuntimeError("Set Shade Smooth API unsupported: inspect reported inputs")
    smooth.default_value=True
    group.links.new(inp.outputs["Geometry"],geometry)
    group.links.new(shade.outputs["Geometry"],out.inputs["Geometry"])
    mod=obj.modifiers.new("M09_TEST_SMOOTH","NODES")
    mod.node_group=group
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    result_mesh=evaluated.to_mesh()
    try:
        assert len(result_mesh.vertices)==4 and len(result_mesh.polygons)==1
        assert result_mesh.polygons[0].use_smooth, "Smooth shading not applied"
        result={"status":"PASS_SYNTHETIC_SHADE_SMOOTH_ONLY",
                "blender_version":bpy.app.version_string,
                "vertices":len(result_mesh.vertices),"faces":len(result_mesh.polygons),
                "shade_smooth":result_mesh.polygons[0].use_smooth,
                "custom_normal_transfer":"NOT_RUN",
                "official_morwen":"NOT_RUN","render_art_qa":"NOT_RUN","game_qa":"NOT_RUN"}
        print("M09_HAIR_SHADING_TEST="+json.dumps(result,sort_keys=True),flush=True)
    finally:
        evaluated.to_mesh_clear()

if __name__=="__main__":
    main()
