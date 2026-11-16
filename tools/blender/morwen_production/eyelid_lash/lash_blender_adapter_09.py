"""Blender-only adapter for EYELID-09 lash anchors; non-destructive by default.

Usage in Blender Python:
    from lash_blender_adapter_09 import evaluated_anchor
    result = evaluated_anchor(lid_object, (0,1,2), (.2,.3,.5))
The triangle IDs refer to stable mesh vertex indices, not evaluated loop-triangle indices.
"""
from lash_attachment_09 import offset_root

def evaluated_anchor(lid_object, vertex_ids, weights, offset_m=0.0001, depsgraph=None):
    import bpy
    if depsgraph is None: depsgraph=bpy.context.evaluated_depsgraph_get()
    if lid_object.type!="MESH": raise TypeError("lid_object must be a mesh")
    evaluated=lid_object.evaluated_get(depsgraph)
    mesh=evaluated.to_mesh(preserve_all_data_layers=False,depsgraph=depsgraph)
    try:
        if mesh is None: raise RuntimeError("evaluated mesh unavailable")
        if any(i<0 or i>=len(mesh.vertices) for i in vertex_ids): raise ValueError("vertex ID missing in evaluated mesh")
        world=evaluated.matrix_world
        positions=[tuple(world@mesh.vertices[i].co) for i in vertex_ids]
        return offset_root(positions,(0,1,2),weights,offset_m)
    finally:
        evaluated.to_mesh_clear()

def validate_stable_topology(lid_object, expected_count, depsgraph=None):
    import bpy
    if depsgraph is None: depsgraph=bpy.context.evaluated_depsgraph_get()
    obj=lid_object.evaluated_get(depsgraph)
    mesh=obj.to_mesh()
    try:
        actual=len(mesh.vertices)
        if actual!=expected_count:
            raise ValueError(f"evaluated topology changed: {actual} != {expected_count}")
        return {"vertex_count":actual,"topology_count_matches":True,
                "warning":"matching count alone does not prove stable vertex ordering"}
    finally:
        obj.to_mesh_clear()
