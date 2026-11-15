"""Aidan material study: deterministic weathering and directional timber grain.

Independent candidate only. No modification of canonical house or v3 meshes.
"""
import random
import bpy

SEED=141127

def _principled(name, base, roughness):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*base,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Roughness"].default_value=roughness
    return m,bs

def stone_material(stone_id, low_course=False, exposure=0.5):
    """Per-stone seeded palette with physically motivated dampness bias."""
    rng=random.Random(SEED+stone_id*1009)
    warm=rng.uniform(-.035,.035)
    damp=(.10 if low_course else 0)+.045*max(0,min(1,exposure))
    base=(.47+warm-damp,.42+warm*.8-damp,.33+warm*.6-damp*.85)
    m,bs=_principled("Aidan weathered limestone %04d"%stone_id,base,.91)
    nodes=m.node_tree.nodes;links=m.node_tree.links
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=26+rng.uniform(-4,4)
    noise.inputs["Detail"].default_value=3.0
    ramp=nodes.new("ShaderNodeValToRGB")
    dark=tuple(max(.02,c*.76) for c in base)
    light=tuple(min(1,c*1.13) for c in base)
    ramp.color_ramp.elements[0].position=.24
    ramp.color_ramp.elements[0].color=(*dark,1)
    ramp.color_ramp.elements[1].position=.76
    ramp.color_ramp.elements[1].color=(*light,1)
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.18
    bump.inputs["Distance"].default_value=.008
    links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],bs.inputs["Base Color"])
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    return m

def timber_material(beam_id, aged=True):
    """Wood grain runs along local X axis (beam length)."""
    rng=random.Random(SEED+beam_id*2089)
    base=(.30+rng.uniform(-.025,.025),.17,.085)
    if aged:base=tuple(c*.83 for c in base)
    m,bs=_principled("Aidan directional timber %04d"%beam_id,base,.82)
    nodes=m.node_tree.nodes;links=m.node_tree.links
    tex=nodes.new("ShaderNodeTexCoord")
    vec=nodes.new("ShaderNodeVectorMath");vec.operation="MULTIPLY"
    vec.inputs[1].default_value=(1.3,21.0,18.0)
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=2.6
    noise.inputs["Detail"].default_value=3.2
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(.14,.068,.028,1)
    ramp.color_ramp.elements[1].color=(*base,1)
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.12
    bump.inputs["Distance"].default_value=.004
    links.new(tex.outputs["Generated"],vec.inputs[0])
    links.new(vec.outputs["Vector"],noise.inputs["Vector"])
    links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],bs.inputs["Base Color"])
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    return m
