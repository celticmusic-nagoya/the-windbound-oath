"""Render isolated flat-vs-smooth stylized hair clump comparison.

Blender 5.3 bpy runtime; synthetic mesh only. Output is QA evidence, not art approval.
"""
import argparse
import hashlib
import json
from pathlib import Path
import bpy

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",default="render_output/morwen_hair_shading_09")
    args=p.parse_args()
    out=Path(args.out)
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Asymmetric 3D clump with bent centerline and noncoplanar facets.
    vertices=[(-.4,-.13,0),(.4,-.13,0),(-.35,.15,.35),(.35,.15,.35),
              (-.24,-.04,.7),(.22,.04,.7),(-.12,.12,1),(.1,.12,1)]
    faces=[(0,1,3,2),(2,3,5,4),(4,5,7,6),(0,2,4,6),(1,7,5,3)]
    mesh=bpy.data.meshes.new("SYNTHETIC_CLUMP_SOURCE")
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    source_fingerprint=hashlib.sha256(json.dumps({"vertices":vertices,"faces":faces},sort_keys=True).encode()).hexdigest()
    objects=[]
    for name,x,smooth in (("FLAT",-0.65,False),("SMOOTH",0.65,True)):
        obj=bpy.data.objects.new("HAIR09_"+name,mesh.copy())
        bpy.context.collection.objects.link(obj)
        obj.location.x=x
        if smooth:
            group=bpy.data.node_groups.new("HAIR09_SHADE_SMOOTH","GeometryNodeTree")
            group.interface.new_socket(name="Geometry",in_out="INPUT",socket_type="NodeSocketGeometry")
            group.interface.new_socket(name="Geometry",in_out="OUTPUT",socket_type="NodeSocketGeometry")
            inp=group.nodes.new("NodeGroupInput")
            out_node=group.nodes.new("NodeGroupOutput")
            node=group.nodes.new("GeometryNodeSetShadeSmooth")
            geometry=next((s for s in node.inputs if s.identifier=="Geometry" and s.enabled),None)
            shade=next((s for s in node.inputs if s.name=="Shade Smooth" and s.enabled),None)
            assert geometry is not None and shade is not None
            shade.default_value=True
            group.links.new(inp.outputs["Geometry"],geometry)
            group.links.new(node.outputs["Geometry"],out_node.inputs["Geometry"])
            obj.modifiers.new("HAIR09_SMOOTH","NODES").node_group=group
        objects.append(obj)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_WORKBENCH"
    scene.render.resolution_x=960
    scene.render.resolution_y=600
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.render.film_transparent=False
    scene.display.shading.light="STUDIO"
    scene.display.shading.color_type="MATERIAL"
    camera_data=bpy.data.cameras.new("HAIR09_QA_CAMERA")
    camera=bpy.data.objects.new("HAIR09_QA_CAMERA",camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location=(2.8,-4.8,2.6)
    direction=(__import__("mathutils").Vector((0,0,.48))-camera.location)
    camera.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    camera_data.type="ORTHO"
    camera_data.ortho_scale=3.2
    scene.camera=camera
    before=[(len(o.data.vertices),len(o.data.polygons)) for o in objects]
    assert before==[(8,5),(8,5)]
    evaluated=objects[1].evaluated_get(bpy.context.evaluated_depsgraph_get())
    emesh=evaluated.to_mesh()
    try:
        assert len(emesh.vertices)==8 and len(emesh.polygons)==5
        assert all(face.use_smooth for face in emesh.polygons)
    finally:
        evaluated.to_mesh_clear()
    image_path=out/"HAIR09_FLAT_VS_SMOOTH.png"
    scene.render.filepath=str(image_path.resolve())
    bpy.ops.render.render(write_still=True)
    assert image_path.is_file() and image_path.stat().st_size>1000
    report={"status":"PASS_TECHNICAL_RENDER_ONLY","source_sha256":source_fingerprint,
            "blender":bpy.app.version_string,"output":image_path.name,
            "png_sha256":hashlib.sha256(image_path.read_bytes()).hexdigest(),
            "flat_mesh":before[0],"smooth_mesh":before[1],
            "visual_quality":"NOT_RUN","official_morwen":"NOT_RUN","game_qa":"NOT_RUN"}
    (out/"HAIR09_RENDER_QA.json").write_text(json.dumps(report,indent=2)+"\n")
    print("HAIR09_RENDER_QA="+json.dumps(report,sort_keys=True),flush=True)

if __name__=="__main__":
    main()
