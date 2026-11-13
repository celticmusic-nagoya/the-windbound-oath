"""G0: fast Blender geometry checks before expensive render."""
import bpy,math,statistics,json,sys
from mathutils import Vector
def inspect():
 objs=list(bpy.data.objects)
 errors=[];warnings=[]
 stones=[o for o in objs if o.name.startswith("Hand_set_stone")]
 widths=[max(o.dimensions.x,o.dimensions.y) for o in stones]
 if len(stones)<100:errors.append("stone count below 100")
 if len(widths)>2:
  cv=statistics.pstdev(widths)/statistics.mean(widths)
  if cv<.18:errors.append("stone dimensions too uniform")
 else:cv=0
 foundations=[o for o in objs if o.name=="Foundation"]
 if not foundations:errors.append("foundation absent")
 else:
  bottom=min((o.matrix_world@v.co).z for o in foundations for v in o.data.vertices)
  if bottom>-.20+1e-3:errors.append("foundation skirt does not reach -0.20m")
 for o in objs:
  if o.type!="MESH":continue
  if not o.data.vertices:errors.append("empty mesh: "+o.name)
  if any(not math.isfinite(x) for v in o.data.vertices for x in v.co):errors.append("nonfinite vertices: "+o.name)
 # AABB overlap alone cannot certify closed seams; flag this limitation explicitly.
 warnings.append("Gable-roof seam requires evaluated mesh section/ray tests")
 report={"level":"G0_PARTIAL","passed":not errors,"errors":errors,"warnings":warnings,"stone_cv":cv,"stone_count":len(stones)}
 print("G0_REPORT",json.dumps(report))
 if errors:raise RuntimeError("G0 FAIL: "+"; ".join(errors))
 return report
if __name__=="__main__":inspect()
