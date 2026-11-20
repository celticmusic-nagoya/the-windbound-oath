"""Render calibrated-in-frame source candidate silhouette masks in Blender 5.3.
These masks are geometry evidence, not proof of design alignment or G2.
Usage: blender -b source.blend --python script.py -- OUTPUT_DIR
"""
import bpy
import json
import sys
from pathlib import Path
from mathutils import Vector

out=Path(sys.argv[sys.argv.index("--")+1]);out.mkdir(parents=True,exist_ok=True)
names=("GEO-head_stylized","GEO-body_female_stylized")
views={"front":(0,-1,0),"right":(1,0,0),"back":(0,1,0),"left":(-1,0,0)}
report={"status":"GEOMETRY_MASK_ONLY_NOT_CANON_ALIGNED","blender":bpy.app.version_string,"render_contract":{"engine":"CYCLES_CPU","resolution":[384,1024],"orthographic":True,"alpha":"TRANSPARENT","color":"WHITE_UNLIT"},"objects":[]}
for name in names:
    ob=bpy.data.objects.get(name)
    if ob is None or ob.type!="MESH":raise RuntimeError("SOURCE_OBJECT_MISSING:"+name)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in list(bpy.data.objects):
        if obj.type=="MESH":obj.hide_render=(obj!=ob)
    # Evaluate world-space bounding box; retain original object geometry and transforms.
    bpy.context.view_layer.update()
    corners=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    center=sum(corners,Vector())/8
    extent=max((max(v[i] for v in corners)-min(v[i] for v in corners)) for i in range(3))
    assert extent>0
    # Uniform camera framing per object across all views. Not canonical alignment.
    cam_data=bpy.data.cameras.new("Blueprint_mask_camera")
    cam=bpy.data.objects.new("Blueprint_mask_camera",cam_data)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam_data.type="ORTHO"
    # Vertical ortho_scale is NOT the horizontal field of view. At 384:1024,
    # frame horizontal span = ortho_scale * 384/1024. Fit both dimensions.
    aspect=384/1024
    fit_width=max(bounds_x for bounds_x in (
        max(c.x for c in corners)-min(c.x for c in corners),
        max(c.y for c in corners)-min(c.y for c in corners)))
    fit_height=max(c.z for c in corners)-min(c.z for c in corners)
    cam_data.ortho_scale=max(fit_height,fit_width/aspect)*1.12
    scene=bpy.context.scene
    scene.render.engine="CYCLES"
    scene.cycles.device="CPU"
    scene.cycles.samples=8
    scene.render.resolution_x=384;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
    scene.render.image_settings.color_depth="8"
    # Blender 5.3 compositor API differs; use an emission override material
    # with film transparency, avoiding legacy Scene.node_tree entirely.
    scene.use_nodes=False
    white_mat=bpy.data.materials.get("MORWEN_MASK_WHITE") or bpy.data.materials.new("MORWEN_MASK_WHITE")
    white_mat.use_nodes=True
    mat_nodes=white_mat.node_tree.nodes
    mat_nodes.clear()
    output_node=mat_nodes.new("ShaderNodeOutputMaterial")
    emission=mat_nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value=(1,1,1,1)
    emission.inputs["Strength"].default_value=1.0
    white_mat.node_tree.links.new(emission.outputs[0],output_node.inputs["Surface"])
    scene.view_layers[0].material_override=white_mat
    slug="head" if "head" in name else "body_female"
    record={"name":name,"bounds_world":[list(map(float,center)),extent],"views":{}}
    for view,direction in views.items():
        d=Vector(direction);cam.location=center+d*max(extent*4,2)
        cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
        # Orthographic scale is vertical extent; aspect ratio makes horizontal
        # frame much narrower. Capture this contract rather than claiming fit.
        scene.render.filepath=str(out/(slug+"_"+view+"_mask.png"))
        bpy.ops.render.render(write_still=True)
        record["views"][view]={"file":Path(scene.render.filepath).name,"camera_matrix_world":[[float(cam.matrix_world[r][c]) for c in range(4)] for r in range(4)],"ortho_scale":cam_data.ortho_scale,"frame_width_world":cam_data.ortho_scale*aspect}
    report["objects"].append(record)
    bpy.data.objects.remove(cam,do_unlink=True)
(out/"geometry_mask_contract.json").write_text(json.dumps(report,indent=2)+"
")
print("MORWEN_SOURCE_MASK_RENDER_PASS")
