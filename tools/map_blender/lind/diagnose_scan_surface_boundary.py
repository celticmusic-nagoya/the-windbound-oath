"""Measure and visualize open scan-surface termination before authored terrain joins.
Read-only source mesh analysis; saves QA-only annotated render, no geometry edits.
"""
import argparse,bpy,sys,collections,json,hashlib,math
from pathlib import Path
from mathutils import Vector

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument("--source-blend",required=True);p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 source=Path(a.source_blend).resolve()
 bpy.ops.wm.open_mainfile(filepath=str(source))
 obj=bpy.data.objects.get("SCAN_LED_OPEN_SURFACE_NOT_PRODUCTION")
 assert obj is not None
 mesh=obj.data
 edges=collections.defaultdict(list)
 for poly in mesh.polygons:
  vs=list(poly.vertices)
  for x,y in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((x,y)))].append(poly.index)
 boundary=[edge for edge,owners in edges.items() if len(owners)==1]
 assert boundary
 neighbors=collections.defaultdict(set)
 for x,y in boundary:neighbors[x].add(y);neighbors[y].add(x)
 endpoints=[v for v,ns in neighbors.items() if len(ns)==1]
 junctions=[v for v,ns in neighbors.items() if len(ns)>2]
 unseen=set(neighbors);components=[]
 while unseen:
  seed=min(unseen);stack=[seed];unseen.remove(seed);vertices=[]
  while stack:
   v=stack.pop();vertices.append(v)
   for w in neighbors[v]:
    if w in unseen:unseen.remove(w);stack.append(w)
  components.append(vertices)
 lengths=[]
 for comp in components:
  members=set(comp);length=0.
  for x,y in boundary:
   if x in members and y in members:
    length+=(mesh.vertices[x].co-mesh.vertices[y].co).length
  lengths.append(length)
 coords=[mesh.vertices[i].co for i in neighbors]
 zs=[v.z for v in coords];low=min(zs);high=max(zs);cut=low+.20*(high-low)
 lower=[i for i in neighbors if mesh.vertices[i].co.z<=cut]
 # No source-mesh modification: diagnostic edges are a separate curve object.
 curve=bpy.data.curves.new("BOUNDARY_DIAGNOSTIC_ONLY","CURVE");curve.dimensions="3D";curve.bevel_depth=.008;curve.bevel_resolution=2
 for x,y in boundary:
  spline=curve.splines.new("POLY");spline.points.add(1)
  for point,vi in zip(spline.points,(x,y)):
   v=mesh.vertices[vi].co;point.co=(v.x,v.y,v.z,1)
 guide=bpy.data.objects.new("QA_OPEN_BOUNDARY_RED_NOT_ASSET",curve)
 bpy.context.collection.objects.link(guide)
 mat=bpy.data.materials.new("QA_BOUNDARY_RED");mat.diffuse_color=(1,.09,.04,1);curve.materials.append(mat)
 obj.hide_render=False
 scene=bpy.context.scene
 scene.render.engine="BLENDER_WORKBENCH"
 scene.display.shading.color_type="MATERIAL"
 scene.display.shading.light="STUDIO"
 scene.display.shading.show_cavity=True
 scene.render.resolution_x=1100;scene.render.resolution_y=760
 scene.render.resolution_percentage=100;scene.render.image_settings.file_format="PNG"
 scene.render.filepath=str(out/"scan_boundary_diagnostic.png")
 bpy.ops.render.render(write_still=True)
 metrics={"source_blend_sha256":sha(source),"boundary_edges":len(boundary),"boundary_components":len(components),"boundary_component_lengths":sorted([round(x,5) for x in lengths],reverse=True),"endpoints":len(endpoints),"junctions":len(junctions),"lower_20pct_boundary_vertices":len(lower),"boundary_vertices":len(neighbors),"lower_cut_z":cut,"source_mesh_modified":False,"diagnostic_only":True,"render_sha256":sha(scene.render.filepath),"G1":"BLOCKED","G2":"NOT_RUN","G3":"BOUNDARY_DIAGNOSTICS_PASS","G4":"NOT_RUN"}
 (out/"scan_boundary_metrics.json").write_text(json.dumps(metrics,indent=2)+"\n")
 print("BOUNDARY_DIAGNOSTICS_PASS",json.dumps({k:metrics[k] for k in ("boundary_edges","boundary_components","endpoints","junctions")}),flush=True)
if __name__=="__main__":main()
