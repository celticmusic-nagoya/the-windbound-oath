"""Measure failed voxel candidate, without generating or replacing any asset.

Open verified saved .blend from prior run; report topology, bounding boxes,
UV occupancy, surface distances, and camera framing. No rendering/rebake.
"""
import bpy,sys,json,math,hashlib,statistics
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

def bounds(o):
 pts=[o.matrix_world@Vector(c) for c in o.bound_box]
 return {"min":[min(p[i] for p in pts) for i in range(3)],"max":[max(p[i] for p in pts) for i in range(3)]}
def triangles(o):return sum(len(p.vertices)-2 for p in o.data.polygons)
def main():
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument("--out",required=True)
 a=ap.parse_args(sys.argv[sys.argv.index("--")+1:])
 out=Path(a.out).resolve()
 src=bpy.data.objects["PUBLISHER_SCAN_UNMODIFIED"]
 dst=bpy.data.objects["VOXEL_RETOPO_CANDIDATE"]
 cam=bpy.data.objects["QA_CAMERA"]
 assert src.type=="MESH" and dst.type=="MESH"
 result={"blender_version":bpy.app.version_string,"source":{"triangles":triangles(src),"vertices":len(src.data.vertices),"bounds":bounds(src)},"candidate":{"triangles":triangles(dst),"vertices":len(dst.data.vertices),"bounds":bounds(dst)},"camera":{"ortho_scale":cam.data.ortho_scale,"position":list(cam.location)}}
 # Mesh normal orientation, triangle area and degenerates.
 from mathutils import geometry
 for name,obj in [("source",src),("candidate",dst)]:
  poly=obj.data.polygons
  result[name]["face_area_total"]=sum(p.area for p in poly)
  result[name]["degenerate_face_count"]=sum(p.area<1e-10 for p in poly)
  result[name]["normal_mean_z"]=sum(p.normal.z for p in poly)/max(1,len(poly))
  result[name]["uv_layers"]=len(obj.data.uv_layers)
 # UV atlas occupancy via coarse raster of actual UV triangles (no image generation).
 mesh=dst.data
 uv=mesh.uv_layers.active
 N=256
 mask=bytearray(N*N)
 uv_area=0.
 for poly in mesh.polygons:
  coords=[Vector(uv.data[li].uv) for li in poly.loop_indices]
  if len(coords)<3:continue
  for j in range(1,len(coords)-1):
   a,b,c=coords[0],coords[j],coords[j+1]
   uv_area+=abs((b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x))/2
   x0=max(0,int(math.floor(min(a.x,b.x,c.x)*N)))
   x1=min(N-1,int(math.ceil(max(a.x,b.x,c.x)*N)))
   y0=max(0,int(math.floor(min(a.y,b.y,c.y)*N)))
   y1=min(N-1,int(math.ceil(max(a.y,b.y,c.y)*N)))
   if x1<x0 or y1<y0:continue
   v0=b-a;v1=c-a
   denom=v0.x*v1.y-v0.y*v1.x
   if abs(denom)<1e-14:continue
   for yy in range(y0,y1+1):
    py=(yy+.5)/N
    for xx in range(x0,x1+1):
     px=(xx+.5)/N
     d=Vector((px-a.x,py-a.y))
     s=(d.x*v1.y-d.y*v1.x)/denom
     t=(v0.x*d.y-v0.y*d.x)/denom
     if s>=-1e-8 and t>=-1e-8 and s+t<=1+1e-8:mask[yy*N+xx]=1
 result["uv"]={"estimated_total_triangle_area":uv_area,"atlas_occupancy_256":sum(mask)/(N*N),"occupied_cells":sum(mask),"atlas_cells":N*N}
 # Source surface nearest distances at a deterministic subsample of target vertices.
 src_bvh=BVHTree.FromObject(src,bpy.context.evaluated_depsgraph_get())
 step=max(1,len(dst.data.vertices)//3000)
 distances=[]
 for vi in range(0,len(dst.data.vertices),step):
  v=dst.data.vertices[vi]
  co=dst.matrix_world@v.co
  hit=src_bvh.find_nearest(src.matrix_world.inverted()@co)
  if hit[0] is not None:
   distances.append((src.matrix_world@hit[0]-co).length)
 distances.sort()
 result["surface_fit"]={"samples":len(distances),"mean_distance":statistics.mean(distances),"p95_distance":distances[int(.95*(len(distances)-1))],"max_distance":max(distances)}
 # Project bounding box to current camera, to check scene composition.
 for name,obj in [("source",src),("candidate",dst)]:
  q=[world_to_camera_view(bpy.context.scene,cam,obj.matrix_world@Vector(c)) for c in obj.bound_box]
  result[name]["camera_projected_bounds"]={"x":[min(p.x for p in q),max(p.x for p in q)],"y":[min(p.y for p in q),max(p.y for p in q)],"depth":[min(p.z for p in q),max(p.z for p in q)]}
 result["scope"]="READ_ONLY_SAVED_BLEND_DIAGNOSTIC_NO_ASSET_CHANGE"
 (out/"voxel_rootcause_metrics.json").write_text(json.dumps(result,indent=2)+"\n")
 print("VOXEL_ROOTCAUSE_METRICS_COMPLETE",json.dumps({"uv":result["uv"],"surface_fit":result["surface_fit"],"camera":result["candidate"]["camera_projected_bounds"]}))
if __name__=="__main__":main()
