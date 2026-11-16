"""Candidate D: actual-surface BVH envelope fitting, preserving A/B/C inputs."""
import bpy,math,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[2];out=root/'assets/candidates/lind-spatial-codex-01/world/candidate-d';out.mkdir(exist_ok=False)
s=bpy.context.scene;deps=bpy.context.evaluated_depsgraph_get()
supports=[('terrain',BVHTree.FromObject(bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'],deps)),('bridge',BVHTree.FromObject(bpy.data.objects['East_bridge_candidate_single_arch'],deps))]
def surface(x,y):
 hits=[]
 for name,tree in supports:
  location,normal,index,distance=tree.ray_cast(Vector((x,y,1000)),Vector((0,0,-1)),2000)
  if location is not None:hits.append((location.z,name))
 if not hits:raise RuntimeError('No support surface at '+str((x,y)))
 return max(hits)
measure=[]
for name in ['Village_to_harbor_access','Village_to_coastal_promontory','Village_to_east_bridge','Village_to_north_farmland']:
 obj=bpy.data.objects[name];v=obj.data.vertices;count=len(v)//2;centers=[(v[2*i].co+v[2*i+1].co)*.5 for i in range(count)];old=[p.z for p in centers];floors=[]
 for i,c in enumerate(centers):
  samples=[v[2*i].co,c,v[2*i+1].co];floors.append(max(old[i],max(surface(p.x,p.y)[0] for p in samples)+.05))
 z=floors[:];steps=[math.hypot(centers[i+1].x-centers[i].x,centers[i+1].y-centers[i].y) for i in range(count-1)];bound=math.tan(math.radians(24.5))
 # Least slope-bounded upper envelope. Raising only preserves every support clearance.
 for i in range(1,count):z[i]=max(z[i],z[i-1]-bound*steps[i-1])
 for i in range(count-2,-1,-1):z[i]=max(z[i],z[i+1]-bound*steps[i])
 for i in range(count):v[2*i].co.z=z[i];v[2*i+1].co.z=z[i]
 obj.data.update();bury=[];gap=[]
 for i in range(count):
  for p in [v[2*i].co,(v[2*i].co+v[2*i+1].co)*.5,v[2*i+1].co]:
   support,kind=surface(p.x,p.y);bury.append(support-p.z);gap.append(p.z-support)
 grade=max(math.degrees(math.atan(abs(z[i+1]-z[i])/steps[i])) for i in range(count-1))
 assert max(bury)<0 and grade<=25
 measure.append({'route':name,'stations':count,'samples':count*3,'buried_samples':sum(b>1e-5 for b in bury),'max_penetration':max(0,max(bury)),'min_clearance':min(gap),'max_gap':max(gap),'max_lift':max(z[i]-old[i] for i in range(count)),'max_grade_degrees':grade,'grade_limit_provisional':25,'surface_occlusion_check':'PASS_ONLY_AT_SAMPLED_STATIONS'})
s['route_method']='actual_support_BVH_clearance_and_slope_bounded_envelope';s.camera=bpy.data.objects['overview'];bpy.ops.wm.save_as_mainfile(filepath=str(out/'world.blend'));s.render.filepath=str(out/'overview.png');bpy.ops.render.render(write_still=True)
report={'status':'CANDIDATE_NOT_FINAL_ART','blender_version':bpy.app.version_string,'source_sha256':s['source_sha256'],'method_family':'actual_support_BVH_clearance_and_slope_bounded_envelope','meters_per_unit':None,'routes':measure,'G1':'BLOCKED_METRIC_EVENT_REVIEW','G2':'FAIL_FINAL_ART','G3':'PARTIAL_SAMPLED_SURFACE_CLEARANCE_ONLY','G4':'NOT_RUN','limits':['raising road envelope does not prove engineered support or collision/navmesh continuity','center+edges sampled at vertices; unsampled triangle interiors not verified','geological art remains B failure and was not regenerated','no metric/camera/dimension approval'],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ['.png','.blend']}}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('CANDIDATE_D_COMPLETE',json.dumps(report))
