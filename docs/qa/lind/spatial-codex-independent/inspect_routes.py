import bpy,math,json,sys
from pathlib import Path
rows=[]
for o in bpy.data.objects:
 if o.type!='MESH' or not o.name.startswith('Village_to_'):continue
 vs=o.data.vertices;pts=[(vs[i].co+vs[i+1].co)*.5 for i in range(0,len(vs),2)];grades=[]
 for a,b in zip(pts,pts[1:]):
  d=b-a;grades.append(abs(d.z)/max(1e-9,math.hypot(d.x,d.y)))
 rows.append({'name':o.name,'start':list(pts[0]),'end':list(pts[-1]),'max_grade':max(grades),'max_angle_degrees':math.degrees(math.atan(max(grades)))})
Path(sys.argv[sys.argv.index('--')+1]).write_text(json.dumps(rows,indent=2)+'\n');print('ROUTE_GEOMETRY_INSPECTED')
