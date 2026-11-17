"""Scan-led irregular footprint: retain original 3D rock triangles and UVs.

This is a non-destructive *surface study*, not a finished cliff, collision
surface, terrain connection, or a repeat of ring erosion / voxel remesh.
"""
import argparse,bpy,sys,math,hashlib,json,collections
from pathlib import Path
from mathutils import Vector

def sha(path):
 h=hashlib.sha256()
 with open(path,"rb") as f:
  for block in iter(lambda:f.read(1<<20),b""):h.update(block)
 return h.hexdigest()

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--scan-blend",required=True)
 p.add_argument("--out",required=True)
 a=p.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
 src=Path(a.scan_blend).resolve()
 bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
 with bpy.data.libraries.load(str(src),link=False) as (source,target):
  assert "LOCAL_PATCH_UNOPTIMIZED_SOURCE_GEOMETRY" in source.objects
  target.objects=["LOCAL_PATCH_UNOPTIMIZED_SOURCE_GEOMETRY"]
 original=target.objects[0];bpy.context.collection.objects.link(original)
 original.hide_render=True
 mesh=original.data
 assert len(mesh.polygons)>30000 and mesh.uv_layers.active
 # Choose the dominant exposed rock surface, not a rectangle. Radial cutoff
 # varies by irregular, hand-specified directional lobes, no ring erosion.
 xy=[(v.co.x,v.co.y) for v in mesh.vertices]
 minx,maxx=min(x for x,y in xy),max(x for x,y in xy)
 miny,maxy=min(y for x,y in xy),max(y for x,y in xy)
 cx=(minx+maxx)/2;cy=(miny+maxy)/2
 rx=(maxx-minx)*.44;ry=(maxy-miny)*.44
 assert rx>0 and ry>0
 controls=[(.83,.92,.76,.95,.87,.79,.96,.82,.90,.75,.94,.84,.88)]
 def threshold(theta):
  pos=(theta%(2*math.pi))/(2*math.pi)*len(controls)
  k=int(pos);t=pos-k;t=t*t*(3-2*t)
  return controls[k]*(1-t)+controls[(k+1)%len(controls)]*t
 selected=set()
 for poly in mesh.polygons:
  c=poly.center
  dx=(c.x-cx)/rx;dy=(c.y-cy)/ry
  radius=math.sqrt(dx*dx+dy*dy)
  if radius<=threshold(math.atan2(dy,dx)):
   selected.add(poly.index)
 assert len(selected)>10000, len(selected)
 # Retain only the largest connected face island; don't bridge holes or
 # pretend this open source surface is a watertight manifold.
 edge_to_faces=collections.defaultdict(list)
 for poly in mesh.polygons:
  if poly.index not in selected:continue
  vs=list(poly.vertices)
  for v,w in zip(vs,vs[1:]+vs[:1]):
   edge_to_faces[tuple(sorted((v,w)))].append(poly.index)
 adj=collections.defaultdict(set)
 for fids in edge_to_faces.values():
  if len(fids)==2:
   a,b=fids;adj[a].add(b);adj[b].add(a)
 seen=set();components=[]
 for seed in sorted(selected):
  if seed in seen:continue
  stack=[seed];seen.add(seed);comp=[]
  while stack:
   f=stack.pop();comp.append(f)
   for n in adj[f]:
    if n not in seen:seen.add(n);stack.append(n)
  components.append(comp)
 largest=set(max(components,key=len))
 assert len(largest)>5000
 vertex_map={};verts=[];faces=[];uvs=[]
 old_uv=mesh.uv_layers.active.data
 for poly in mesh.polygons:
  if poly.index not in largest:continue
  face=[];uv=[]
  for li in poly.loop_indices:
   old=mesh.loops[li].vertex_index
   if old not in vertex_map:
    vertex_map[old]=len(verts)
    verts.append(tuple(mesh.vertices[old].co))
   face.append(vertex_map[old]);uv.append(tuple(old_uv[li].uv))
  faces.append(face);uvs.append(uv)
 new=bpy.data.meshes.new("SCAN_LED_IRREGULAR_FOOTPRINT_ORIGINAL_TRIANGLES")
 new.from_pydata(verts,[],faces);new.update()
 new.uv_layers.new(name="PUBLISHER_UV_UNCHANGED")
 for face,coords in zip(new.polygons,uvs):
  for li,uv in zip(face.loop_indices,coords):
   new.uv_layers.active.data[li].uv=uv
 for mat in mesh.materials:new.materials.append(mat)
 obj=bpy.data.objects.new("SCAN_LED_OPEN_SURFACE_NOT_PRODUCTION",new)
 bpy.context.collection.objects.link(obj)
 counts=collections.Counter()
 for face in faces:
  for v,w in zip(face,face[1:]+face[:1]):
   counts[tuple(sorted((v,w)))]+=1
 boundary=sum(n==1 for n in counts.values())
 assert boundary>0
 points=[Vector(c) for c in obj.bound_box]
 lo=Vector([min(v[i] for v in points) for i in range(3)])
 hi=Vector([max(v[i] for v in points) for i in range(3)])
 center=(lo+hi)*.5;span=max(hi-lo)
 scene=bpy.context.scene
 scene.render.engine="BLENDER_WORKBENCH"
 scene.display.shading.light="STUDIO"
 scene.display.shading.color_type="MATERIAL"
 scene.display.shading.show_cavity=True
 scene.render.resolution_x=1100;scene.render.resolution_y=760
 scene.render.resolution_percentage=100
 scene.render.image_settings.file_format="PNG"
 camera_data=bpy.data.cameras.new("SCAN_LED_QA_CAMERA")
 camera=bpy.data.objects.new("SCAN_LED_QA_CAMERA",camera_data)
 bpy.context.collection.objects.link(camera)
 camera_data.type="ORTHO";camera_data.ortho_scale=span*1.5
 camera.location=center+Vector((span*.7,-span*1.4,span*.55))
 camera.rotation_euler=(center-camera.location).to_track_quat("-Z","Y").to_euler()
 scene.camera=camera
 png=out/"scan_led_irregular_surface.png"
 scene.render.filepath=str(png)
 print("SCAN_LED_RENDER_START",flush=True)
 bpy.ops.render.render(write_still=True)
 print("SCAN_LED_RENDER_DONE",flush=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(out/"scan_led_irregular_surface.blend"))
 metrics={"production_ready":False,"scan_source_blend_sha256":sha(src),"method":"IRREGULAR_FOOTPRINT_ORIGINAL_TRIANGLES_NOT_BLIND_EROSION","selected_faces":len(largest),"discarded_islands":len(components)-1,"original_patch_faces":len(mesh.polygons),"boundary_edges":boundary,"surface_open":True,"uv_preserved":True,"world_alignment":"NOT_DEFINED","render_sha256":sha(png),"G1":"BLOCKED","G2":"NOT_RUN_INDEPENDENT","G3":"OPEN_REFERENCE_SURFACE_ONLY","G4":"NOT_RUN"}
 (out/"scan_led_manifest.json").write_text(json.dumps(metrics,indent=2)+"\n")
 print("SCAN_LED_COMPLETE",json.dumps(metrics),flush=True)
if __name__=="__main__":main()
