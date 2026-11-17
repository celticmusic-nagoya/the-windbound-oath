"""Material-lit preview of unmodified, SHA-verified glTF rock candidates."""
import bpy,sys,argparse,json,hashlib,math
from pathlib import Path
from mathutils import Vector
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument("--source",required=True);parser.add_argument("--out",required=True)
 a=parser.parse_args(sys.argv[sys.argv.index("--")+1:]);source=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((source/"source_provenance.json").read_text());results=[]
 for item in manifest["assets"]:
  assert item["status"]=="DOWNLOADED_UNREVIEWED"
  model=source/item["file"];assert sha(model)==item["sha256"]
  for dep in item["dependencies"]:assert sha(source/dep["file"])==dep["sha256"]
  bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
  bpy.ops.import_scene.gltf(filepath=str(model))
  meshes=[o for o in bpy.context.scene.objects if o.type=="MESH"];assert meshes
  used={m for o in meshes for m in o.data.materials if m}
  textures={img for mat in used if mat.use_nodes for node in mat.node_tree.nodes if node.type=="TEX_IMAGE" and node.image for img in [node.image]}
  # Different pipeline from importer auto-resolution: bind verified dependency files explicitly.
  gltf=json.loads(model.read_text())
  source_images=[x for x in gltf.get("images",[]) if "uri" in x]
  assert len(source_images)>=3,"Source glTF has fewer than three image declarations"
  dependency_by_uri={d["uri"]:source/d["file"] for d in item["dependencies"]}
  material_images=sorted(textures,key=lambda x:x.name)
  assert len(material_images)==len(source_images),"Cannot map imported images one-to-one; stop rather than guess"
  image_report=[]
  for img in material_images:
   matches=[d for d in source_images if img.name.lower().split(".")[0] in (Path(d["uri"]).stem.lower(),d.get("name","").lower()) or Path(d["uri"]).stem.lower() in img.name.lower()]
   assert len(matches)==1,"Ambiguous source image match: "+img.name
   decl=matches[0];uri=decl["uri"];disk=dependency_by_uri.get(uri)
   assert disk and disk.is_file(),"Unverified source image: "+uri
   # Name-based mapping is mandatory; ordering alone cannot justify changing a normal map into diffuse.
   assert img.name.lower().split(".")[0] in (Path(uri).stem.lower(),decl.get("name","").lower()) or Path(uri).stem.lower() in img.name.lower(),"Image binding mismatch: "+img.name+" / "+uri
   assert sha(disk)==next(d["sha256"] for d in item["dependencies"] if d["uri"]==uri)
   # Standalone bpy.data.images.load was independently proven to decode all six JPEGs.
   # Replace only the image datablock reference, preserving every existing shader link.
   fresh=bpy.data.images.load(str(disk),check_existing=False)
   # Blender lazily decodes FILE images: evaluate pixels before checking has_data.
   # Independent diagnostic #44092016791 did pixels[:4] before has_data.
   decoded_pixels=list(fresh.pixels[:4])
   ok=bool(len(decoded_pixels)==4 and fresh.has_data and fresh.size[0]>0 and fresh.size[1]>0)
   assert ok,"Verified image cannot be decoded independently: "+uri
   nodes=[node for mat in used if mat.use_nodes for node in mat.node_tree.nodes if node.type=="TEX_IMAGE" and node.image==img]
   assert nodes,"Imported image has no material node: "+img.name
   for node in nodes:
    fresh.colorspace_settings.name=img.colorspace_settings.name
    node.image=fresh
    assert node.image==fresh
   image_report.append({"name":img.name,"replacement":fresh.name,"node_count":len(nodes),"source_uri":uri,"sha256":sha(disk),"width":int(fresh.size[0]),"height":int(fresh.size[1]),"loaded":ok})
  print("PBR_IMAGE_DIAGNOSTIC",item["id"],json.dumps({"materials":[m.name for m in used],"images":image_report}),flush=True)
  assert len(image_report)>=3 and all(x["loaded"] for x in image_report),"PBR textures missing or invalid"
  allpts=[o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
  lo=Vector([min(v[k] for v in allpts) for k in range(3)]);hi=Vector([max(v[k] for v in allpts) for k in range(3)])
  center=(lo+hi)*.5;span=max(hi-lo);assert span>0
  camd=bpy.data.cameras.new("QA_CAMERA");cam=bpy.data.objects.new("QA_CAMERA",camd);bpy.context.collection.objects.link(cam)
  cam.location=center+Vector((span*1.5,-span*1.75,span*1.2));cam.rotation_euler=(center-cam.location).to_track_quat("-Z","Y").to_euler()
  camd.type="ORTHO";camd.ortho_scale=span*2.2
  scene=bpy.context.scene;scene.camera=cam
  world=bpy.data.worlds.new("QA_WORLD");scene.world=world;world.use_nodes=True
  bg=world.node_tree.nodes.get("Background");bg.inputs["Color"].default_value=(0.38,0.43,0.49,1);bg.inputs["Strength"].default_value=0.7
  for name,pos,power,size in [("KEY",(1.6,-2,3),1100,4),("FILL",(-2,1,2),650,5)]:
   data=bpy.data.lights.new(name,"AREA");data.energy=power;data.shape="DISK";data.size=size
   obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
   obj.location=center+Vector(pos)*span;obj.rotation_euler=(center-obj.location).to_track_quat("-Z","Y").to_euler()
  scene.render.engine="CYCLES";scene.cycles.samples=24
  scene.render.resolution_x=1100;scene.render.resolution_y=760;scene.render.resolution_percentage=100
  scene.render.image_settings.file_format="PNG";scene.render.film_transparent=False
  scene.render.filepath=str(out/(item["id"]+"_PBR_lit_preview.png"))
  bpy.ops.render.render(write_still=True)
  results.append({"id":item["id"],"meshes":len(meshes),"materials":len(used),"texture_images":image_report,"preview":Path(scene.render.filepath).name,"preview_sha256":sha(scene.render.filepath),"source_sha256":item["sha256"],"PBR_texture_loading":"PASS","PBR_visual_art_review":"NOT_RUN","production_G2":"NOT_RUN"})
 (out/"candidate_pbr_report.json").write_text(json.dumps({"candidates":results,"G1":"BLOCKED","G2":"NOT_RUN","G3":"PBR_TEXTURE_LOADING_AND_RENDER_PASS","G4":"NOT_RUN"},indent=2)+"\n")
 print("LIND_PBR_RENDER_PASS",json.dumps(results),flush=True)
if __name__=="__main__":main()
