"""Candidate C: route-driven earthwork grading, separate from surface-draped method."""
import bpy,math,json,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[2];out=root/'assets/candidates/lind-spatial-codex-01/world/candidate-c';out.mkdir(exist_ok=False)
terrain=bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'];original=[v.co.copy() for v in terrain.data.vertices]
def coast(y):return -11+2.5*math.sin(y*.28)+1.25*math.sin(y*.73)+5.8*math.exp(-((y+10)/4.5)**2)
def nearest(x,y):return min(original,key=lambda v:(v.x-x)**2+(v.y-y)**2).z
village=nearest(0,0);xc=8.;left=xc-2.15;right=xc+2.15
routes=[('Village_to_harbor_access',(0,0),(coast(-10)-.6,-10),village,1.7),('Village_to_coastal_promontory',(0,0),(coast(7)+1.4,7),village,nearest(coast(7)+1.4,7)),('Village_to_east_bridge',(0,0),(14,0),village,nearest(14,0))]
def profile(name,t,z0,z1,x):
 if name!='Village_to_east_bridge':return z0+(z1-z0)*t
 if x<left:return z0+(5.85-z0)*x/left
 if x>right:return 5.85+(z1-5.85)*(x-right)/(14-right)
 return 5.85+.3*math.sin(math.pi*(x-left)/(right-left))
for vert in terrain.data.vertices:
 x,y=vert.co.x,vert.co.y
 for name,(ax,ay),(bx,by),za,zb in routes:
  dx=bx-ax;dy=by-ay;raw=((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy);t=max(0,min(1,raw));xx=ax+dx*t;yy=ay+dy*t;dist=math.hypot(x-xx,y-yy)
  if dist>1.4 or raw<-.04 or raw>1.04:continue
  # No earth fill in the navigation span: masonry bridge remains the crossing support.
  if name=='Village_to_east_bridge' and left+.05<x<right-.05:continue
  weight=1 if dist<.45 else .5+.5*math.cos(math.pi*(dist-.45)/.95)
  grade=profile(name,t,za,zb,xx)-.08
  vert.co.z=vert.co.z*(1-weight)+grade*weight
terrain.data.update()
measure=[]
for name,(ax,ay),(bx,by),za,zb in routes:
 old=bpy.data.objects.get(name);material=old.data.materials[0];bpy.data.objects.remove(old,do_unlink=True)
 dx=bx-ax;dy=by-ay;length=math.hypot(dx,dy);sx=-dy/length*.3;sy=dx/length*.3;v=[];levels=[]
 for i in range(141):
  t=i/140;x=ax+dx*t;y=ay+dy*t;z=profile(name,t,za,zb,x);levels.append(z)
  v.extend([(x+sx,y+sy,z),(x-sx,y-sy,z)])
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],[(2*j,2*j+1,2*j+3,2*j+2) for j in range(140)]);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(material)
 maxgrade=max(math.degrees(math.atan(abs(levels[i+1]-levels[i])/(length/140))) for i in range(140))
 measure.append({'id':name,'endpoint_z':levels[-1],'min_z':min(levels),'max_grade_degrees':maxgrade,'candidate_grade_limit_degrees':25,'grade_limit_pass':maxgrade<=25,'bridge_surface_clearance':.05 if name=='Village_to_east_bridge' else None})
s=bpy.context.scene;s['method']='route_driven_cut_fill_with_arched_bridge_grade';s.camera=bpy.data.objects['overview'];bpy.ops.wm.save_as_mainfile(filepath=str(out/'world.blend'))
for name in ['overview','coast','river']:
 s.camera=bpy.data.objects[name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'status':'CANDIDATE_NOT_FINAL_ART','method_family':'route_driven_cut_fill_with_bridge_profile','source_sha256':s['source_sha256'],'blender_version':bpy.app.version_string,'routes':measure,'meters_per_unit':None,'technical_limits':['grade and geometric support only; no navmesh/collision test','harbor landing below cliff graded but dock piles/material art unfinished','regional estuary outside study extent','CG geological detail not final quality'],'G1':'BLOCKED_METRIC_EVENT_REVIEW','G2':'INDEPENDENT_REVIEW_REQUIRED','G3':'PARTIAL_ROUTE_GRADES_AND_RENDER','G4':'NOT_RUN','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ['.png','.blend']}}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('CANDIDATE_C_COMPLETE',json.dumps(report))
