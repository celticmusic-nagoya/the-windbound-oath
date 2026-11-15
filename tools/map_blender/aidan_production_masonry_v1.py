"""Aidan House production masonry module v1. Blender 4.x, metres, Z up.

Non-destructive standalone layer. Does not modify v3, canon, or scene unless
build_masonry() is explicitly called. Diagnostic candidate, not art-approved.
"""
from dataclasses import dataclass
import math
import random
import bpy

SEED = 141127

@dataclass(frozen=True)
class MasonrySpec:
    length: float = 8.4
    width: float = 7.1
    eaves: float = 3.05
    wall_thickness: float = 0.32
    course_height: float = 0.29
    stone_length: float = 0.57
    mortar_gap: float = 0.018
    depth_relief: float = 0.028
    seed: int = SEED

def _mat(name, color, roughness):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value = (*color, 1)
    bs.inputs["Roughness"].default_value = roughness
    return m

def _stone(name, center, size, material, collection, bevel=0.024):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for c in tuple(o.users_collection):
        c.objects.unlink(o)
    collection.objects.link(o)
    o.data.materials.append(material)
    b = o.modifiers.new("hand dressed edges", "BEVEL")
    b.width = min(bevel, min(size) * .20)
    b.segments = 2
    o.modifiers.new("weighted normals", "WEIGHTED_NORMAL")
    return o

def _intervals(total, nominal, course, rng):
    # Bonded courses: alternate half-stone offsets. Never leave sliver stones.
    offset = nominal * .5 if course % 2 else 0
    edges = [0.0]
    x = -offset
    while x < total:
        if 0 < x < total:
            edges.append(x)
        x += nominal * rng.uniform(.91, 1.09)
    edges.append(total)
    edges.sort()
    # Absorb tiny end stones into the neighbouring block rather than leaving
    # unsupported chips at wall ends. Preserve total span and deterministic seed.
    min_end = min(nominal * .35, total * .25)
    if len(edges) > 2 and edges[1] - edges[0] < min_end:
        edges.pop(1)
    if len(edges) > 2 and edges[-1] - edges[-2] < min_end:
        edges.pop(-2)
    return [(a,b) for a,b in zip(edges, edges[1:]) if b-a > 1e-5]

def _subtract(open_intervals, holes):
    result = open_intervals
    for h0,h1 in holes:
        new=[]
        for a,b in result:
            if h1 <= a or h0 >= b:
                new.append((a,b))
            else:
                if a < h0:new.append((a,h0))
                if h1 < b:new.append((h1,b))
        result=new
    return result

def build_masonry(spec=MasonrySpec(), parent=None):
    """Build stone courses with structural openings, corners and depth relief.

    Door on south (-Y), window on east (+X). The roof/gables and actual
    approved reference design must be validated separately.
    """
    if min(spec.length, spec.width, spec.eaves, spec.course_height) <= 0:
        raise ValueError("Masonry dimensions must be positive")
    rng = random.Random(spec.seed)
    parent = parent or bpy.context.scene.collection
    group = bpy.data.collections.new("AIDAN_PRODUCTION_MASONRY_CANDIDATE")
    parent.children.link(group)
    limestone = [
        _mat("masonry limestone %d" % i, c, .91)
        for i,c in enumerate(((.43,.41,.36),(.47,.45,.39),(.38,.37,.33),(.51,.48,.41)))
    ]
    mortar = _mat("masonry recessed dark mortar", (.25,.24,.22), .96)
    L=spec.length/2;W=spec.width/2
    t=spec.wall_thickness;g=spec.mortar_gap
    # Recessed wall backing keeps real openings empty.
    segments = (
        ("south", spec.length, (-L,-W), (1,0), (0,-1), [(-.785,.785,0,2.20)]),
        ("north", spec.length, (-L,W), (1,0), (0,1), []),
        ("west", spec.width-t, (-L,-W+t/2), (0,1), (-1,0), []),
        ("east", spec.width-t, (L,-W+t/2), (0,1), (1,0), [(.45-.945,.45+.945,1.12,2.47)]),
    )
    total=0
    course_count=math.ceil(spec.eaves/spec.course_height)
    for side, span, start, axis, outward, openings in segments:
        for row in range(course_count):
            z0=row*spec.course_height
            z1=min(spec.eaves,(row+1)*spec.course_height)
            if z1-z0 <= g*2:continue
            active_openings=[(a-start[0] if axis[0] else a+W-t/2,
                              b-start[0] if axis[0] else b+W-t/2,h0,h1)
                             for a,b,h0,h1 in openings if z0 < h1 and z1 > h0]
            # Preserve exact opening heights: split intersecting courses vertically.
            z_edges=sorted(set([z0,z1]+[max(z0,min(z1,z)) for _,_,h0,h1 in active_openings for z in (h0,h1)]))
            # Intersecting opening boundaries are split explicitly per stone.
            for a,b in _intervals(span,spec.stone_length,row,rng):
                for low,high in zip(z_edges,z_edges[1:]):
                    if high-low <= g*1.1:continue
                    holes=[(ha,hb) for ha,hb,h0,h1 in active_openings
                           if low < h1 and high > h0]
                    for aa,bb in _subtract([(a,b)],holes):
                        if bb-aa <= g:continue
                        relief=rng.uniform(-spec.depth_relief,spec.depth_relief)
                        cx=start[0]+axis[0]*(aa+bb)/2+outward[0]*relief
                        cy=start[1]+axis[1]*(aa+bb)/2+outward[1]*relief
                        sx=(bb-aa-g) if axis[0] else t
                        sy=(bb-aa-g) if axis[1] else t
                        if sx <= 0 or sy <= 0:continue
                        _stone("%s course %02d ashlar %04d"%(side,row,total),
                               (cx,cy,(low+high)/2),
                               (sx,sy,high-low-g),
                               rng.choice(limestone),group)
                        total+=1
    return {"status":"CANDIDATE_NOT_ART_APPROVED","seed":spec.seed,
            "stone_count":total,"course_count":course_count,
            "collection":group.name,"openings":"DOOR_SOUTH_WINDOW_EAST",
            "requires":"G1_G2_G3_G4_REVIEW"}

if __name__ == "__main__":
    import json
    print(json.dumps(build_masonry(),sort_keys=True))
