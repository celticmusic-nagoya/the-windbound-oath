"""Inspect glTF material texture nodes against independently decoded verified JPEGs."""
import argparse,bpy,hashlib,json,sys
from pathlib import Path
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source",required=True);p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:]);src=Path(a.source).resolve();out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((src/"source_provenance.json").read_text());report=[]
 for asset in manifest["assets"]:
  assert asset["status"]=="DOWNLOADED_UNREVIEWED"
  model=src/asset["file"];assert digest(model)==asset["sha256"]
  deps={d["uri"]:d for d in asset["dependencies"]}
  gltf=json.loads(model.read_text());images=gltf.get("images",[])
  bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
  bpy.ops.import_scene.gltf(filepath=str(model))
  mats={m for o in bpy.context.scene.objects if o.type=="MESH" for m in o.data.materials if m}
  nodes=[(m,n) for m in mats if m.use_nodes for n in m.node_tree.nodes if n.type=="TEX_IMAGE"]
  entries=[]
  for mat,node in nodes:
   imp=node.image;assert imp is not None
   candidates=[x for x in images if imp.name.lower().split(".")[0] in (Path(x["uri"]).stem.lower(),x.get("name","").lower()) or Path(x["uri"]).stem.lower() in imp.name.lower()]
   assert len(candidates)==1, "ambiguous image match"
   uri=candidates[0]["uri"];dep=deps[uri];disk=src/dep["file"]
   assert digest(disk)==dep["sha256"]
   fresh=bpy.data.images.load(str(disk),check_existing=False)
   fresh_px=list(fresh.pixels[:4])
   assert fresh.has_data and len(fresh_px)==4
   links=[{"from":l.from_socket.name,"to_node":l.to_node.name,"to_socket":l.to_socket.name} for l in mat.node_tree.links if l.from_node==node]
   entries.append({"material":mat.name,"node":node.name,"imported_image":imp.name,"imported_has_data":bool(imp.has_data),"imported_filepath":imp.filepath,"uri":uri,"sha256":dep["sha256"],"fresh_has_data":bool(fresh.has_data),"fresh_size":list(fresh.size),"outgoing_links":links,"link_count":len(links)})
  assert len(entries)>=3 and all(e["fresh_has_data"] and e["link_count"]>0 for e in entries),"source decoding or material linkage missing"
  report.append({"asset":asset["id"],"entries":entries,"node_links":"PASS","fresh_decode":"PASS","production_pbr_render":"NOT_RUN"})
 result={"candidates":report,"G1":"BLOCKED","G2":"NOT_RUN","G3":"GLTF_NODE_LINKS_AND_STANDALONE_DECODE_PASS","G4":"NOT_RUN"}
 (out/"gltf_material_link_diagnostic.json").write_text(json.dumps(result,indent=2)+"\n")
 print("GLTF_MATERIAL_LINK_DIAGNOSTIC_PASS",json.dumps(result),flush=True)
if __name__=="__main__":main()
