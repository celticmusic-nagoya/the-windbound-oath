"""One controlled differential diagnosis of PBR hairline artifacts in LOD25.

Source is unchanged. Render PBR and two controlled material/geometry conditions
using identical camera and lights; do not claim cause without independent QA.
"""
import bpy,sys,json,hashlib
from pathlib import Path
from mathutils import Vector

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
    return h.hexdigest()

def main():
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True)
    a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
    out=Path(a.out).resolve()
    source_path=out/"sources/coastal_cliff_04/coastal_cliff_04_1k.gltf"
    bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(source_path))
    objs=[x for x in bpy.context.scene.objects if x.type=="MESH"]
    if len(objs)!=1:raise RuntimeError("Unexpected source scan object count")
    source=objs[0];source.name="SOURCE_SCAN_UNMODIFIED"
    lod=source.copy();lod.data=source.data.copy()
    bpy.context.collection.objects.link(lod)
    lod.name="LOD25_TEST_ONLY"
    bpy.ops.object.select_all(action="DESELECT")
    lod.select_set(True);bpy.context.view_layer.objects.active=lod
    mod=lod.modifiers.new("LOD25","DECIMATE");mod.ratio=.25
    bpy.ops.object.modifier_apply(modifier=mod.name)
    source_tri=sum(len(p.vertices)-2 for p in source.data.polygons)
    lod_tri=sum(len(p.vertices)-2 for p in lod.data.polygons)
    assert source_tri>1000000 and 0<lod_tri<source_tri
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
    scene.render.resolution_x=1200;scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.view_transform="Standard"
    if hasattr(scene,"eevee"):scene.eevee.taa_render_samples=32
    world=bpy.data.worlds.new("QA_WORLD");world.use_nodes=True;scene.world=world
    bg=world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value=(.7,.73,.78,1)
    bg.inputs["Strength"].default_value=.8
    target=Vector((-5,-4,4.4));camera=Vector((-1,-24,11))
    cam_data=bpy.data.cameras.new("DIAG_FIXED_CAM")
    cam_data.type="ORTHO";cam_data.ortho_scale=11
    cam=bpy.data.objects.new("DIAG_FIXED_CAM",cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location=camera
    cam.rotation_euler=(target-camera).to_track_quat("-Z","Y").to_euler()
    scene.camera=cam
    for name,location,energy,size in [
        ("QA_KEY",(-9,-16,22),4500,12),
        ("QA_FILL",(9,-10,15),2500,15)]:
        data=bpy.data.lights.new(name,"AREA");obj=bpy.data.objects.new(name,data)
        bpy.context.collection.objects.link(obj)
        obj.location=Vector(location)
        obj.rotation_euler=(target-obj.location).to_track_quat("-Z","Y").to_euler()
        data.energy=energy;data.size=size
    materials=list(lod.data.materials)
    if not materials:raise RuntimeError("Source has no PBR material")
    result={"source_glTF_sha256":sha(source_path),
      "source_triangles":source_tri,"lod25_triangles":lod_tri,
      "conditions":{},"render_resolution":[1200,800],
      "camera":{"location":list(camera),"target":list(target),"ortho_scale":11},
      "G1":"BLOCKED","G2":"NOT_RUN_INDEPENDENT","G3":"PENDING","G4":"NOT_RUN"}
    def shot(name,which):
        source.hide_render=which!="full"
        lod.hide_render=which=="full"
        scene.render.filepath=str(out/(name+".png"))
        bpy.ops.render.render(write_still=True)
        result["conditions"][name]={"file":name+".png","sha256":sha(out/(name+".png"))}
    # 1. Original PBR baseline; 2. LOD PBR known failure.
    shot("01_full_pbr","full")
    shot("02_lod25_pbr","lod")
    # 3. LOD basecolor + roughness, explicitly disable normal map links on a copy.
    # This preserves original material nodes and makes only test duplicates.
    copies=[]
    for i,m in enumerate(materials):
        cp=m.copy();cp.name="QA_NO_NORMAL_"+str(i)
        if cp.use_nodes:
            nt=cp.node_tree
            for node in nt.nodes:
                if node.type=="BSDF_PRINCIPLED":
                    socket=node.inputs.get("Normal")
                    if socket:
                        for link in list(socket.links):nt.links.remove(link)
        lod.data.materials[i]=cp;copies.append(cp)
    shot("03_lod25_pbr_without_normalmap","lod")
    # 4. Neutral diffuse shading isolates actual geometry and face normals.
    clay=bpy.data.materials.new("QA_NEUTRAL_CLAY")
    clay.diffuse_color=(.48,.48,.48,1)
    clay.use_nodes=True
    bsdf=clay.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value=(.48,.48,.48,1)
    bsdf.inputs["Roughness"].default_value=.9
    for i in range(len(lod.data.materials)):lod.data.materials[i]=clay
    shot("04_lod25_neutral_clay","lod")
    # 5. Full mesh clay baseline; original materials only temporarily assigned.
    original_mats=list(source.data.materials)
    for i in range(len(source.data.materials)):source.data.materials[i]=clay
    shot("05_full_neutral_clay","full")
    for i,m in enumerate(original_mats):source.data.materials[i]=m
    for i,m in enumerate(materials):lod.data.materials[i]=m
    source.hide_render=False;lod.hide_render=True
    bpy.ops.file.pack_all()
    blend=out/"scan_lod_artifact_diagnostic.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    result["blend"]={"file":blend.name,"sha256":sha(blend)}
    result["source_preservation"]="publisher glTF and PBR textures untouched"
    (out/"diagnostic_manifest.json").write_text(json.dumps(result,indent=2)+"\n")
    print("LOD_ARTIFACT_DIAG_RENDERED",len(result["conditions"]),source_tri,lod_tri)
if __name__=="__main__":main()
