"""Alternative to rejected Decimate: voxel surface rebuild + high-poly normal bake.

Unadopted technical candidate only. Preserve source, use separate new mesh,
rebuild topology by voxel remeshing, then bake tangent-space normals from scan.
"""
import bpy,sys,json,hashlib,time
from pathlib import Path
from mathutils import Vector

def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for x in iter(lambda:f.read(1024*1024),b""):h.update(x)
 return h.hexdigest()

def tris(o):return sum(len(p.vertices)-2 for p in o.data.polygons)

def main():
 import argparse
 ap=argparse.ArgumentParser()
 ap.add_argument("--out",required=True)
 a=ap.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(a.out).resolve()
 source_file=out/"sources/coastal_cliff_04/coastal_cliff_04_1k.gltf"
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 bpy.ops.import_scene.gltf(filepath=str(source_file))
 meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"]
 if len(meshes)!=1:raise RuntimeError("Unexpected source geometry")
 source=meshes[0];source.name="PUBLISHER_SCAN_UNMODIFIED"
 source_tri=tris(source)
 assert source_tri>1000000
 # Keep original glTF and mesh intact; create a separate rebuilt topology.
 target=source.copy();target.data=source.data.copy()
 bpy.context.collection.objects.link(target)
 target.name="VOXEL_RETOPO_CANDIDATE"
 bpy.ops.object.select_all(action="DESELECT")
 target.select_set(True);bpy.context.view_layer.objects.active=target
 # Voxel remeshing is not the failed face-collapse Decimate method.
 rem=target.modifiers.new("VOXEL_TOPOLOGY_REBUILD","REMESH")
 rem.mode="VOXEL";rem.voxel_size=.22;rem.use_smooth_shade=True
 bpy.ops.object.modifier_apply(modifier=rem.name)
 rebuilt_tri=tris(target)
 if rebuilt_tri<1000 or rebuilt_tri>=source_tri:raise RuntimeError("Voxel remesh invalid/budget exceeded: "+str(rebuilt_tri))
 # Transfer high-poly surface shape, without changing topology.
 sw=target.modifiers.new("SURFACE_FIT_TO_ORIGINAL","SHRINKWRAP")
 sw.target=source;sw.wrap_method="NEAREST_SURFACEPOINT";sw.offset=.002
 bpy.ops.object.modifier_apply(modifier=sw.name)
 # Fresh, independent UV unwrap: no inherited distorted UV islands.
 bpy.ops.object.mode_set(mode="EDIT")
 bpy.ops.mesh.select_all(action="SELECT")
 bpy.ops.uv.smart_project(island_margin=.02)
 bpy.ops.object.mode_set(mode="OBJECT")
 assert len(target.data.uv_layers)>=1
 for mat in list(target.data.materials):target.data.materials.clear()
 mat=bpy.data.materials.new("BAKED_NORMAL_QA")
 mat.use_nodes=True
 nodes=mat.node_tree.nodes
 principled=nodes.get("Principled BSDF")
 principled.inputs["Base Color"].default_value=(.4,.42,.42,1)
 principled.inputs["Roughness"].default_value=.9
 tex=nodes.new("ShaderNodeTexImage")
 tex.name="BAKE_TARGET_NORMAL"
 img=bpy.data.images.new("BAKED_TANGENT_NORMAL",width=1024,height=1024,alpha=False,float_buffer=False)
 img.file_format="PNG"
 img.colorspace_settings.name="Non-Color"
 tex.image=img
 nodes.active=tex
 target.data.materials.append(mat)
 scene=bpy.context.scene
 scene.render.engine="CYCLES"
 scene.cycles.samples=8
 scene.render.bake.use_selected_to_active=True
 scene.render.bake.use_cage=False
 scene.render.bake.cage_extrusion=.08
 scene.render.bake.max_ray_distance=.18
 scene.render.bake.margin=8
 bpy.ops.object.select_all(action="DESELECT")
 source.select_set(True);target.select_set(True)
 bpy.context.view_layer.objects.active=target
 bpy.ops.object.bake(type="NORMAL",normal_space="TANGENT")
 normal_file=out/"voxel_retopo_baked_normal.png"
 img.filepath_raw=str(normal_file);img.file_format="PNG";img.save()
 assert normal_file.read_bytes()[:8]==bytes([137,80,78,71,13,10,26,10])
 nmap=nodes.new("ShaderNodeNormalMap")
 nmap.space="TANGENT"
 mat.node_tree.links.new(tex.outputs["Color"],nmap.inputs["Color"])
 mat.node_tree.links.new(nmap.outputs["Normal"],principled.inputs["Normal"])
 source.hide_render=True
 scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
 scene.render.resolution_x=1200;scene.render.resolution_y=800
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 world=bpy.data.worlds.new("QA_WORLD");world.use_nodes=True;scene.world=world
 world.node_tree.nodes["Background"].inputs["Color"].default_value=(.65,.69,.73,1)
 world.node_tree.nodes["Background"].inputs["Strength"].default_value=.8
 bounds=[target.matrix_world@Vector(c) for c in target.bound_box]
 center=sum(bounds,Vector())/8
 span=max(max(p[i] for p in bounds)-min(p[i] for p in bounds) for i in range(3))
 cam_data=bpy.data.cameras.new("QA_CAMERA");cam_data.type="ORTHO";cam_data.ortho_scale=span*1.6
 cam=bpy.data.objects.new("QA_CAMERA",cam_data);bpy.context.collection.objects.link(cam)
 cam.location=center+Vector((span*.55,-span*1.8,span*.5))
 cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
 scene.camera=cam
 ld=bpy.data.lights.new("QA_AREA","AREA");lo=bpy.data.objects.new("QA_AREA",ld)
 bpy.context.collection.objects.link(lo)
 lo.location=center+Vector((-span*.3,-span*.4,span*.7))
 lo.rotation_euler=(center-lo.location).to_track_quat("-Z","Y").to_euler()
 ld.energy=5000;ld.size=span*.25
 scene.render.filepath=str(out/"voxel_retopo_baked_render.png")
 bpy.ops.render.render(write_still=True)
 bpy.ops.file.pack_all()
 blend=out/"voxel_retopo_bake_study.blend"
 bpy.ops.wm.save_as_mainfile(filepath=str(blend))
 result={"method":"VOXEL_REMESH_SHRINKWRAP_SMART_UV_NORMAL_BAKE",
 "source_sha256":sha(source_file),"source_triangles":source_tri,
 "rebuilt_triangles":rebuilt_tri,"uv_layers":len(target.data.uv_layers),
 "voxel_size_source_units":.22,"normal_resolution":1024,
 "source_status":"UNMODIFIED","candidate_status":"TECHNICAL_EVAL_ONLY",
 "outputs":{p.name:sha(p) for p in [normal_file,out/"voxel_retopo_baked_render.png",blend]},
 "G1":"BLOCKED","G2":"NOT_RUN_INDEPENDENT","G3":"TECHNICAL_PENDING","G4":"NOT_RUN"}
 (out/"retopo_bake_qa.json").write_text(json.dumps(result,indent=2)+"\n")
 print("VOXEL_RETOPO_BAKE_DONE",source_tri,rebuilt_tri)
if __name__=="__main__":main()
