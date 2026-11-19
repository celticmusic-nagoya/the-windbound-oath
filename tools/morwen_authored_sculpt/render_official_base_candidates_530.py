"""Non-adopted, source-faithful Blender Studio CC0 candidate four-view audit.
Run Blender 5.3 -b source.blend --python script.py -- OUTPUT_DIR.
Never changes canonical Morwen assets or source file.
"""
import bpy, math, sys, json
from pathlib import Path
from mathutils import Vector
out=Path(sys.argv[sys.argv.index("--")+1]);out.mkdir(parents=True,exist_ok=True)
targets=("STYLIZED_Head","STYLIZED_Body_Female.001")
audit={"status":"CANDIDATE_ONLY_NOT_ADOPTED","blender":bpy.app.version_string,"objects":[]}
for name,original in source.items():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Append a specific mesh object from the verified source .blend (not a linked dependency).
    sourcefile=Path(sys.argv[sys.argv.index("--")+2]) if len(sys.argv)>sys.argv.index("--")+2 else None
    if not sourcefile:raise RuntimeError("SOURCE_BLEND_PATH_REQUIRED")
    with bpy.data.libraries.load(str(sourcefile),link=False) as (src,dst):
        if name not in src.objects:raise RuntimeError("OBJECT_NOT_IN_SOURCE:"+name)
        dst.objects=[name]
    ob=dst.objects[0];bpy.context.collection.objects.link(ob)
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    # Preserve source geometry; only normalize display transforms for comparisons.
    corners=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    center=sum(corners,Vector())/8
    span=max(max(v[i] for v in corners)-min(v[i] for v in corners) for i in range(3))
    if span<=0:raise RuntimeError("ZERO_EXTENT")
    ob.location-=center
    scale=2.0/span;ob.scale*=scale
    bpy.context.view_layer.update()
    mesh=ob.data
    audit["objects"].append({"source_name":name,"vertices":len(mesh.vertices),"faces":len(mesh.polygons),"scale_for_preview_only":scale})
    mat=bpy.data.materials.new("Neutral_clay_for_visual_audit");mat.diffuse_color=(0.56,0.49,0.44,1);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get("Principled BSDF");bsdf.inputs["Base Color"].default_value=(0.56,0.49,0.44,1)
    ob.data.materials.clear();ob.data.materials.append(mat)
    world=bpy.data.worlds.new("Audit_world");bpy.context.scene.world=world;world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.16,0.16,0.16,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.65
    for pos,power,size in [((3,-4,5),850,5),((-3,1,3),600,4)]:
        data=bpy.data.lights.new("Softbox","AREA");data.energy=power;data.shape="DISK";data.size=size
        lamp=bpy.data.objects.new("Softbox",data);bpy.context.collection.objects.link(lamp);lamp.location=pos
        lamp.rotation_euler=(Vector((0,0,0))-lamp.location).to_track_quat("-Z","Y").to_euler()
    camdata=bpy.data.cameras.new("Ortho_camera");cam=bpy.data.objects.new("Ortho_camera",camdata)
    bpy.context.collection.objects.link(cam);bpy.context.scene.camera=cam;camdata.type="ORTHO";camdata.ortho_scale=3.1
    sc=bpy.context.scene;sc.render.engine="CYCLES";sc.cycles.samples=20
    sc.render.resolution_x=512;sc.render.resolution_y=640;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format="PNG"
    slug="head" if name=="STYLIZED_Head" else "body_female"
    bpy.ops.wm.save_as_mainfile(filepath=str(out/(slug+"_source_candidate.blend")))
    for view,pos in [("front",(0,-5,0)),("right",(5,0,0)),("back",(0,5,0)),("three_quarter",(3,-4,0))]:
        cam.location=pos;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
        sc.render.filepath=str(out/(slug+"_"+view+".png"));bpy.ops.render.render(write_still=True)
(out/"source_candidate_qa.json").write_text(json.dumps(audit,indent=2))
print("MORWEN_SOURCE_CANDIDATE_RENDER_PASS")
