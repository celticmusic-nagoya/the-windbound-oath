"""Aidan roof geometry module — candidate, not a completed building.
Blender 5.x: bpy; creates physically coherent slate roof shell, varied slate rows,
ridge caps and timber fascia. Does not touch existing collections or assets.
"""
import bpy, math, random, json, os
from mathutils import Vector
SEED=1311
rng=random.Random(SEED)
COLLECTION="AIDAN_ROOF_CANDIDATE_01"
def collection():
    c=bpy.data.collections.new(COLLECTION)
    bpy.context.scene.collection.children.link(c)
    return c
def mesh_obj(c,name,verts,faces,mat):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    c.objects.link(obj)
    if mat: obj.data.materials.append(mat)
    return obj
def material(name,color,roughness=.86):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=roughness
    return m
def roof_point(x,y,side,width,halfspan,eave_z,ridge_z):
    # y is positive horizontal distance from ridge toward eave
    return (x,side*y,eave_z+(ridge_z-eave_z)*(1-y/halfspan))
def quad(c,name,points,mat):
    return mesh_obj(c,name,points,[(0,1,2,3)],mat)
def build():
    if bpy.data.collections.get(COLLECTION):
        raise RuntimeError("Candidate collection already exists: no overwrite")
    c=collection()
    slate=material("AIDAN_CANDIDATE_bluegray_slate",(0.30,0.36,0.40))
    slate2=material("AIDAN_CANDIDATE_weathered_slate",(0.25,0.31,0.36))
    wood=material("AIDAN_CANDIDATE_dark_weathered_timber",(0.22,0.16,0.11))
    length=8.4
    halfspan=3.55
    eave_z=3.05
    ridge_z=6.60
    # Continuous surface: no repetitive block-built roof.
    for side in (-1,1):
        shell=[roof_point(x,y,side,length,halfspan,eave_z,ridge_z)
               for x,y in [(-length/2,0),(length/2,0),(length/2,halfspan),(-length/2,halfspan)]]
        quad(c,"RoofShell_"+str(side),shell,slate)
        # Continuous slate strips, staggered joints. Variation in strip length and height,
        # with individual pieces only along eaves/verges and ridge.
        rows=15
        for row in range(rows):
            y0=halfspan*row/rows
            y1=halfspan*(row+1)/rows+.035
            y1=min(halfspan+.06,y1)
            stagger=.19 if row%2 else 0
            segments=14
            step=length/segments
            for j in range(segments):
                # Real geometry for the silhouette-facing courses; other rows use
                # a narrow course strip to avoid excessive polygon counts.
                if row not in (0,1,rows-2,rows-1) and j>0:
                    continue
                if row in (0,1,rows-2,rows-1):
                    xa=-length/2+j*step+stagger
                    xb=min(length/2,xa+step*(.96+rng.uniform(-.03,.03)))
                else:
                    xa=-length/2
                    xb=length/2
                xa=max(-length/2,xa)
                if xb<=xa: continue
                d=rng.uniform(-.018,.018)
                pts=[roof_point(x,y,side,length,halfspan,eave_z,ridge_z) for x,y in
                     [(xa,y0),(xb,y0),(xb,y1),(xa,y1)]]
                pts=[(x,yy,z+d+.012) for x,yy,z in pts]
                quad(c,f"Slate_{side}_{row:02}_{j:02}",pts,slate2 if rng.random()<.26 else slate)
        # Timber eave board: coherent structural fascia.
        y=halfspan+.07
        pts=[roof_point(x,y,side,length,halfspan,eave_z,ridge_z) for x in (-length/2-.10,length/2+.10)]
        mesh_obj(c,"Fascia_"+str(side),
                 [(pts[0][0],pts[0][1],pts[0][2]-.12),
                  (pts[1][0],pts[1][1],pts[1][2]-.12),
                  (pts[1][0],pts[1][1],pts[1][2]+.03),
                  (pts[0][0],pts[0][1],pts[0][2]+.03)],[(0,1,2,3)],wood)
    # Continuous, irregular ridge stone caps with varied lengths.
    x=-length/2
    i=0
    while x<length/2:
        w=min(length/2-x,rng.uniform(.38,.62))
        quad(c,f"RidgeCap_{i:02}",[(x,-.13,ridge_z+.08),(x+w,-.13,ridge_z+.08),
             (x+w,.13,ridge_z+.08),(x,.13,ridge_z+.08)],slate2)
        x+=w
        i+=1
    return {"seed":SEED,"collection":COLLECTION,"roof_angle_degrees":45.0,
            "slate_system":"shell+rows+edge detail","objects":len(c.objects),
            "status":"GEOMETRY_CANDIDATE_NO_PBR_OR_ART_APPROVAL"}
if __name__=="__main__":
    print("AIDAN_ROOF_RESULT="+json.dumps(build(),sort_keys=True))
