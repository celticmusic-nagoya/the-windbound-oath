"""Render calibrated Morwen-09 core with 14 original limb/head segments.
Exclude all original guide geometry and source rigs from render.
"""
import json
from pathlib import Path
import bpy,bmesh
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-10"
VIEWS={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}

def main():
    scene=bpy.context.scene
    rig=bpy.data.objects["Morwen_unified_17_candidate"]
    original=bpy.data.objects["Morwen_unified_neutral_3d_candidate"]
    core=bpy.data.objects["Morwen_09_landmark_core_candidate"]
    assert len(rig.data.bones)==17
    derived=original.copy()
    derived.data=original.data.copy()
    derived.name="Morwen_10_limb_head_segments_candidate"
    scene.collection.objects.link(derived)
    names={g.index:g.name for g in original.vertex_groups}
    keep=set()
    for p in original.data.polygons:
        group_names={names[g.group] for vid in p.vertices
                     for g in original.data.vertices[vid].groups}
        if group_names.isdisjoint({"pelvis","spine"}):keep.add(p.index)
    bm=bmesh.new();bm.from_mesh(derived.data)
    bm.faces.ensure_lookup_table()
    doomed=[face for face in bm.faces if face.index not in keep]
    bmesh.ops.delete(bm,geom=doomed,context="FACES")
    bm.to_mesh(derived.data);bm.free()
    # Hide everything except the calibrated core and derived limbs/head.
    for obj in scene.objects:
        obj.hide_render=obj not in (core,derived)
    core.hide_render=False
    derived.hide_render=False
    deps=bpy.context.evaluated_depsgraph_get();deps.update()
    points=[]
    for obj in (core,derived):
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
        try:points.extend(obj.matrix_world @ v.co for v in mesh.vertices)
        finally:ev.to_mesh_clear()
    assert points
    mins=Vector((min(p.x for p in points),min(p.y for p in points),min(p.z for p in points)))
    maxs=Vector((max(p.x for p in points),max(p.y for p in points),max(p.z for p in points)))
    center=(mins+maxs)/2
    span=maxs-mins
    ortho=max(span.z/0.76,max(span.x,span.y)/(384/1024)/0.76)
    assert ortho>0
    camera_data=bpy.data.cameras.new("MORWEN_10_ORTHO")
    camera=bpy.data.objects.new(camera_data.name,camera_data)
    scene.collection.objects.link(camera)
    scene.camera=camera
    camera_data.type="ORTHO"
    camera_data.ortho_scale=ortho
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
    report={"task":"MORWEN-BLENDER-10","status":"RENDERED_NOT_ART_APPROVED",
            "bones":len(rig.data.bones),"core_faces":len(core.data.polygons),
            "derived_faces":len(derived.data.polygons),"camera_scale":ortho,
            "bounds_min":list(mins),"bounds_max":list(maxs),
            "source_guide_objects_hidden":True,"art_approval":"NOT_RUN",
            "production_use":False}
    (OUT/"render_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_10_FOUR_VIEW_RENDER_PASS")

if __name__=="__main__":main()
