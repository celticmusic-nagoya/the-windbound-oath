"""Isolated high-detail limestone candidate v2: subdivided closed surface.

Does not replace v1 or approved architectural assets. Deterministic per seed.
Blender 4.x compatible. Local X length, Y depth, Z height, metres.
"""
import random
import bpy
import bmesh
from mathutils import Vector

def make_limestone_material(name="Aidan v2 warm limestone"):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(.48,.41,.31,1)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    bsdf=nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value=.93
    noise=nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value=52
    noise.inputs["Detail"].default_value=4
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position=.24
    ramp.color_ramp.elements[0].color=(.27,.24,.20,1)
    ramp.color_ramp.elements[1].position=.77
    ramp.color_ramp.elements[1].color=(.59,.51,.39,1)
    bump=nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value=.26
    bump.inputs["Distance"].default_value=.018
    links=mat.node_tree.links
    links.new(noise.outputs["Fac"],ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"],bsdf.inputs["Base Color"])
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])
    return mat

def create_dressed_stone_v2(name, center, size, material, collection,
                            seed=141127, cuts=5, chip=.065, relief=.035):
    if min(size)<=0 or not 2<=cuts<=12:
        raise ValueError("Invalid dimensions or subdivision count")
    rng=random.Random(seed)
    sx,sy,sz=size
    bm=bmesh.new()
    bmesh.ops.create_cube(bm,size=1)
    bmesh.ops.scale(bm,vec=Vector(size),verts=bm.verts)
    bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=cuts,
                              use_grid_fill=True)
    bm.verts.ensure_lookup_table()
    # Perturb only inward from bounding envelope. Front surface is Y-.
    # Edge recession creates irregular chipped silhouette and small planar
    # facets; front face displacement adds genuine geometric depth relief.
    for v in bm.verts:
        x,y,z=v.co
        edge_count=sum((abs(x)>=sx/2-1e-6,
                        abs(y)>=sy/2-1e-6,
                        abs(z)>=sz/2-1e-6))
        if edge_count>=2:
            for axis,dim in enumerate(size):
                coord=v.co[axis]
                if abs(coord)>=dim/2-1e-6:
                    v.co[axis]-=(1 if coord>0 else -1)*rng.uniform(0,chip)*min(size)
        elif y<0:
            v.co.y+=rng.uniform(0,relief)*min(size)
        elif y>0:
            v.co.y-=rng.uniform(0,relief*.4)*min(size)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    mesh=bpy.data.meshes.new(name+" detailed mesh")
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj.location=center
    if material:mesh.materials.append(material)
    return obj

if __name__=="__main__":
    import json
    col=bpy.data.collections.new("AIDAN_DRESSED_V2_ISOLATED")
    bpy.context.scene.collection.children.link(col)
    obj=create_dressed_stone_v2("v2 test",(0,0,0),(.57,.32,.29),
                                make_limestone_material(),col)
    print(json.dumps({"status":"CANDIDATE_NOT_ART_APPROVED",
                      "vertices":len(obj.data.vertices),
                      "faces":len(obj.data.polygons)}))
