"""Shared procedural PBR material factory and Geometry Nodes scatter (no external textures, no downloads).

Material: one reusable shader node group TWO_PBR_Factory (base color, roughness, variation, bump) so every
asset gets identical node topology; per-asset values live on the group node inputs.
Scatter: TWO_GN_Scatter reads another object's evaluated geometry (Object Info) and instances small cones on
its faces, so source-object metrics are never changed by scatter. Calibration use only until an asset owner
qualifies it on a native asset.
"""
import bpy

GROUP = "TWO_PBR_Factory"
SCATTER = "TWO_GN_Scatter"


def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def factory_group():
    ng = bpy.data.node_groups.get(GROUP)
    if ng:
        return ng
    ng = bpy.data.node_groups.new(GROUP, "ShaderNodeTree")
    it = ng.interface
    it.new_socket("Base Color", in_out="INPUT", socket_type="NodeSocketColor")
    it.new_socket("Roughness", in_out="INPUT", socket_type="NodeSocketFloat")
    it.new_socket("Variation", in_out="INPUT", socket_type="NodeSocketFloat")
    it.new_socket("Bump Strength", in_out="INPUT", socket_type="NodeSocketFloat")
    it.new_socket("BSDF", in_out="OUTPUT", socket_type="NodeSocketShader")
    n, l = ng.nodes, ng.links
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    tex = n.new("ShaderNodeTexNoise")
    tex.inputs["Scale"].default_value = 40.0
    tex.inputs["Detail"].default_value = 6.0
    mix = n.new("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    # variation centred on 1.0 so mean colour stays close to the base colour
    rng = n.new("ShaderNodeMapRange")
    rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = 0.85, 1.15
    comb = n.new("ShaderNodeCombineColor")
    l.new(tex.outputs["Fac"], rng.inputs["Value"])
    for k in ("Red", "Green", "Blue"):
        l.new(rng.outputs["Result"], comb.inputs[k])
    l.new(gi.outputs["Variation"], mix.inputs["Factor"])
    l.new(gi.outputs["Base Color"], mix.inputs["A"])
    l.new(comb.outputs["Color"], mix.inputs["B"])
    bump = n.new("ShaderNodeBump")
    l.new(gi.outputs["Bump Strength"], bump.inputs["Strength"])
    l.new(tex.outputs["Fac"], bump.inputs["Height"])
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    l.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    l.new(gi.outputs["Roughness"], bsdf.inputs["Roughness"])
    l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    l.new(bsdf.outputs["BSDF"], go.inputs["BSDF"])
    return ng


def build_material(name, srgb8):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = nt.nodes.new("ShaderNodeGroup")
    g.node_tree = factory_group()
    g.name = "PBR"
    g.inputs["Base Color"].default_value = [srgb_to_linear(c) for c in srgb8] + [1.0]
    g.inputs["Roughness"].default_value = 0.45
    g.inputs["Variation"].default_value = 0.35
    g.inputs["Bump Strength"].default_value = 0.08
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(g.outputs["BSDF"], out.inputs["Surface"])
    return mat


def get_base_color(mat):
    return tuple(mat.node_tree.nodes["PBR"].inputs["Base Color"].default_value)[:3]


def correct_base_color(mat, measured_srgb8, target_srgb8):
    s = mat.node_tree.nodes["PBR"].inputs["Base Color"]
    cur = list(s.default_value)
    for i in range(3):
        m = max(srgb_to_linear(measured_srgb8[i]), 1e-5)
        cur[i] = min(1.0, max(0.0, cur[i] * srgb_to_linear(target_srgb8[i]) / m))
    s.default_value = cur


def set_modifier_input(mod, identifier, value):
    """Blender 5.3 exposes GN modifier inputs as mod.properties.inputs.<id>.value; older builds use id-props."""
    props = getattr(mod, "properties", None)
    if props is not None and hasattr(props, "inputs"):
        getattr(props.inputs, identifier).value = value
    else:
        mod[identifier] = value


def add_scatter(source):
    ng = bpy.data.node_groups.get(SCATTER)
    if ng is None:
        ng = bpy.data.node_groups.new(SCATTER, "GeometryNodeTree")
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Source", in_out="INPUT", socket_type="NodeSocketObject")
        ng.interface.new_socket("Density", in_out="INPUT", socket_type="NodeSocketFloat")
        ng.interface.new_socket("Seed", in_out="INPUT", socket_type="NodeSocketInt")
        ng.interface.new_socket("Material", in_out="INPUT", socket_type="NodeSocketMaterial")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        n, l = ng.nodes, ng.links
        gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
        info = n.new("GeometryNodeObjectInfo")
        info.transform_space = "RELATIVE"
        dist = n.new("GeometryNodeDistributePointsOnFaces")
        cone = n.new("GeometryNodeMeshCone")
        cone.inputs["Vertices"].default_value = 6
        cone.inputs["Radius Bottom"].default_value = 0.012
        cone.inputs["Depth"].default_value = 0.05
        inst = n.new("GeometryNodeInstanceOnPoints")
        real = n.new("GeometryNodeRealizeInstances")
        l.new(gi.outputs["Source"], info.inputs["Object"])
        l.new(info.outputs["Geometry"], dist.inputs["Mesh"])
        l.new(gi.outputs["Density"], dist.inputs["Density"])
        l.new(gi.outputs["Seed"], dist.inputs["Seed"])
        l.new(dist.outputs["Points"], inst.inputs["Points"])
        l.new(dist.outputs["Rotation"], inst.inputs["Rotation"])
        l.new(cone.outputs["Mesh"], inst.inputs["Instance"])
        setm = n.new("GeometryNodeSetMaterial")
        l.new(inst.outputs["Instances"], real.inputs["Geometry"])
        l.new(real.outputs["Geometry"], setm.inputs["Geometry"])
        l.new(gi.outputs["Material"], setm.inputs["Material"])
        l.new(setm.outputs["Geometry"], go.inputs["Geometry"])
    me = bpy.data.meshes.new("CAL-hair_scatter")
    ob = bpy.data.objects.new("CAL-hair_scatter", me)
    bpy.context.collection.objects.link(ob)
    mod = ob.modifiers.new("Scatter", "NODES")
    mod.node_group = ng
    ids = {s.name: s.identifier for s in ng.interface.items_tree if getattr(s, "in_out", None) == "INPUT"}
    for key, value in (("Source", source), ("Density", 60.0), ("Seed", 7), ("Material", source.data.materials[0])):
        set_modifier_input(mod, ids[key], value)
    bpy.context.view_layer.update()
    return ob


def scatter_stats(source):
    ob = bpy.data.objects["CAL-hair_scatter"]
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    stats = {"vertices": len(me.vertices), "faces": len(me.polygons), "instances_est": len(me.polygons) // 8}
    ev.to_mesh_clear()
    if stats["faces"] == 0:
        raise RuntimeError("GN_SCATTER_EMPTY")
    return stats
