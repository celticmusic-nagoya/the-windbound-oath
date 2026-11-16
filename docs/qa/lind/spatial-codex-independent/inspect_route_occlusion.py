import bpy,json,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
terrain=bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'];bridge=bpy.data.objects['East_bridge_candidate_single_arch']
def tree(o):return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],all_triangles=False)
tt=tree(terrain);bt=tree(bridge);rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('Village_to_'):continue
 samples=[]
 vs=o.data.vertices
 for i in range(0,len(vs),2):
  for label,pt in [('left',vs[i].co),('center',(vs[i].co+vs[i+1].co)*.5),('right',vs[i+1].co)]:
   z=[]
   for name,t in [('terrain',tt),('bridge',bt)]:
    hit=t.ray_cast(Vector((pt.x,pt.y,100)),Vector((0,0,-1)),200)[0]
    if hit is not None:z.append((name,hit.z))
   if z:
    support=max(z,key=lambda x:x[1]);samples.append({'station':i//2,'sample':label,'road_z':pt.z,'highest_surface':support[0],'surface_z':support[1],'burial':support[1]-pt.z})
 buried=[x for x in samples if x['burial']>.015]
 rows.append({'route':o.name,'samples':len(samples),'buried_samples':len(buried),'buried_center_samples':len([x for x in buried if x['sample']=='center']),'max_burial':max(x['burial'] for x in samples),'max_gap':max(-x['burial'] for x in samples),'buried_station_range':[min(x['station'] for x in buried),max(x['station'] for x in buried)] if buried else None,'worst_samples':sorted(samples,key=lambda x:x['burial'],reverse=True)[:6]})
Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps(rows,indent=2)+'\n');print('ROUTE_SURFACE_OCCLUSION_INSPECTED')
