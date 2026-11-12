"""Render four non-clipped views of Morwen 07 core and existing limbs.
Temporary QA-only scene; source .blend and official PNGs remain untouched.
"""
import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-08"
VIEWS={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}
RIG="Morwen_unified_17_candidate"
OLD="Morwen_unified_neutral_3d_candidate"
CORE="Morwen_07_continuous_core_candidate"

def main():
    scene=bpy.context.scene
    rig=bpy.data.objects[RIG]
    old=bpy.data.objects[OLD]
    core=bpy.data.objects[CORE]
    assert len(rig.data.bones)==17
    # Make a derived limb-only mesh by removing faces belonging to the old
    # rigid pelvis/spine ellipsoids. This never writes to the source blend.
    # The original body has per-segment rigid vertex groups.
    group_names={g.index:g.name for g in old.vertex_groups}
    excluded={"pelvis","spine"}
    keep=[]
    for poly in old.data.polygons:
        names=set()
        for idx in poly.vertices:
            names.update(group_names[w.group] for w in old.data.vertices[idx].groups)
        if names.isdisjoint(excluded):keep.append(poly.index)
    mesh=old.data.copy()
    derived=old.copy()
    derived.data=mesh
    derived.name="Morwen_08_limb_segments_candidate"
    scene.collection.objects.link(derived)
    # Remove polygons from a separate mesh using bmesh; no edit to old mesh.
    import bmesh
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    selected=set(keep)
    doomed=[f for f in bm.faces if f.index not in selected]
    bmesh.ops.delete(bm,geom=doomed,context="FACES")
    bm.to_mesh(mesh)
    bm.free()
    old.hide_render=True
    core.hide_render=False
    derived.hide_render=False
    for obj in scene.objects:
        if obj.type=="MESH" and obj not in (core,derived):
            obj.hide_render=True
    # World-space bbox of both candidate objects, evaluated with modifiers.
    deps=bpy.context.evaluated_depsgraph_get()
    deps.update()
    points=[]
    for obj in (core,derived):
        ev=obj.evaluated_get(deps)
        em=ev.to_mesh()
        try:
            points.extend(obj.matrix_world @ v.co for v in em.vertices)
        finally:ev.to_mesh_clear()
    assert points
    xmin,xmax=min(v.x for v in points),max(v.x for v in points)
    ymin,ymax=min(v.y for v in points),max(v.y for v in points)
    zmin,zmax=min(v.z for v in points),max(v.z for v in points)
    center=Vector(((xmin+xmax)/2,(ymin+ymax)/2,(zmin+zmax)/2))
    height=zmax-zmin
    width=max(xmax-xmin,ymax-ymin)
    # For 384x1024 portrait, camera ortho_scale is vertical span.
    # Guarantee >= 12% padding on both vertical and horizontal extents.
    ortho=max(height/0.76,width/(384/1024)/0.76)
    assert ortho>0
    camdata=bpy.data.cameras.new("MORWEN_08_QA_CAMERA")
    camera=bpy.data.objects.new(camdata.name,camdata)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camdata.type="ORTHO"
    camdata.ortho_scale=ortho
    scene.render.engine="CYCLES"
    scene.cycles.samples=8
    scene.cycles.device="CPU"
    scene.render.resolution_x=384
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=True
    OUT.mkdir(parents=True,exist_ok=True)
    for facing,direction in VIEWS.items():
        camera.location=center+Vector(direction)*10
        camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
        scene.render.filepath=str(OUT/(facing+"_projection.png"))
        bpy.ops.render.render(write_still=True)
    report={"task":"MORWEN-BLENDER-08","status":"CANDIDATE_QA_ONLY",
            "bones":len(rig.data.bones),"core_faces":len(core.data.polygons),
            "limb_faces":len(derived.data.polygons),"camera_ortho_scale":ortho,
            "bounds":[[xmin,xmax],[ymin,ymax],[zmin,zmax]],
            "reference_comparison":"NOT_RUN","art_approval":"NOT_RUN",
            "production_use":False}
    (OUT/"render_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_08_RENDER_PASS")

if __name__=="__main__":main()
