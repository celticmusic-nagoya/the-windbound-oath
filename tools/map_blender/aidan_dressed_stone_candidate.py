"""Deterministic hand-dressed limestone block mesh for isolated art evaluation.

Not wired into approved Aidan house or masonry v1. Blender 4.x, metres.
Face perimeter is deliberately irregular; structural bounds remain inside
the supplied rectangular envelope so door/window dimensions are preserved.
"""
import random
import bpy

def create_dressed_stone(name, center, size, material, collection, seed=141127,
                         edge_variation=0.035, bevel=0.012):
    if min(size) <= 0:
        raise ValueError("Stone dimensions must be positive")
    rng=random.Random(seed)
    sx,sy,sz=size
    # Three irregular rings across the depth, with four points on each ring.
    # The front and rear ring corners vary independently, producing non-planar
    # side faces which are triangulated for robust mesh normals.
    vertices=[]
    for zsign in (-1,1):
        for ysign,xsign in ((-1,-1),(-1,1),(1,1),(1,-1)):
            inset_x=rng.uniform(0,edge_variation)*min(sx,sz)
            inset_y=rng.uniform(0,edge_variation)*min(sy,sz)
            inset_z=rng.uniform(0,edge_variation)*min(sx,sy)
            vertices.append((xsign*(sx/2-inset_x),
                             ysign*(sy/2-inset_y),
                             zsign*(sz/2-inset_z)))
    # Front/back caps and four triangulated side strips.
    faces=[(3,2,1,0),(4,5,6,7)]
    for i in range(4):
        j=(i+1)%4
        faces.extend(((i,j,4+j),(i,4+j,4+i)))
    mesh=bpy.data.meshes.new(name+" mesh")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    collection.objects.link(obj)
    obj.location=center
    if material is not None:mesh.materials.append(material)
    modifier=obj.modifiers.new("subtle chipped edges","BEVEL")
    modifier.width=min(bevel,min(size)*.08)
    modifier.segments=2
    obj.modifiers.new("weighted normals","WEIGHTED_NORMAL")
    return obj

if __name__=="__main__":
    import json
    group=bpy.data.collections.new("DRESSED_STONE_STANDALONE_CANDIDATE")
    bpy.context.scene.collection.children.link(group)
    obj=create_dressed_stone("sample dressed limestone",(0,0,0),(.57,.32,.29),None,group)
    assert len(obj.data.vertices)==8
    assert len(obj.data.polygons)==10
    print(json.dumps({"status":"CANDIDATE_NOT_ART_APPROVED","vertices":8,"faces":10}))
