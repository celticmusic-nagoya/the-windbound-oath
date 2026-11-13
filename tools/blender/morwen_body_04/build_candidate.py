"""MORWEN-BODY-04 candidate silhouette mesh; NOT a canonical character model.
Blender -b -noaudio --python tools/blender/morwen_body_04/build_candidate.py
"""
import bpy, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-body-04"
OUT.mkdir(parents=True,exist_ok=True)
marks=json.loads((ROOT/"docs/design/MORWEN_LAYER0_LANDMARKS_CANDIDATE.json").read_text())["front_view"]
z=lambda y:(marks["sole_y_approx"]-y)*1.63/(marks["sole_y_approx"]-marks["head_top_y"])
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
# A connected torso silhouette surface with editable longitudinal rings.
# Widths/depths are hypotheses, NOT measured from canonical four-view sheet.
rings=[(z(marks["hip_y_approx"])-.10,.120,.080),
       (z(marks["hip_y_approx"]),.155,.092),
       (z(marks["elbow_y_approx"]),.125,.075),
       (z(marks["shoulder_y_approx"])-.07,.165,.091),
       (z(marks["shoulder_y_approx"]),.145,.083),
       (z(marks["chin_y_approx"])-.03,.050,.048)]
verts=[];faces=[];N=16
for h,rx,ry in rings:
    for j in range(N):
        t=2*math.pi*j/N
        verts.append((rx*math.cos(t),ry*math.sin(t),h))
for i in range(len(rings)-1):
    for j in range(N):
        a=i*N+j;bb=i*N+(j+1)%N
        faces.append((a,bb,bb+N,a+N))
faces.append(tuple(reversed(range(N))))
faces.append(tuple((len(rings)-1)*N+j for j in range(N)))
mesh=bpy.data.meshes.new("morwen_candidate_torso_mesh")
mesh.from_pydata(verts,[],faces);mesh.update()
body=bpy.data.objects.new("MORWEN_LAYER0_TORSO_CANDIDATE",mesh)
bpy.context.collection.objects.link(body)
for polygon in mesh.polygons:polygon.use_smooth=True
mod=body.modifiers.new("candidate_subdivision","SUBSURF");mod.levels=2
# All pieces are explicitly named candidate placeholders.
def limb(name,a,b,r1,r2):
    a,b=__import__("mathutils").Vector(a),__import__("mathutils").Vector(b)
    d=b-a
    bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=r2,radius2=r1,depth=d.length,location=(a+b)/2)
    o=bpy.context.object;o.name=name;o.rotation_euler=d.to_track_quat("Z","Y").to_euler()
    for p in o.data.polygons:p.use_smooth=True
hip=z(marks["hip_y_approx"]);knee=z(marks["knee_y_approx"]);ankle=z(marks["ankle_y_approx"])
shoulder=z(marks["shoulder_y_approx"]);elbow=z(marks["elbow_y_approx"]);wrist=z(marks["wrist_y_approx"])
for sign,side in ((1,"L"),(-1,"R")):
    limb("CANDIDATE_THIGH_"+side,(sign*.09,0,hip),(sign*.09,0,knee),.064,.043)
    limb("CANDIDATE_SHIN_"+side,(sign*.09,0,knee),(sign*.09,0,ankle),.042,.026)
    limb("CANDIDATE_UPPER_ARM_"+side,(sign*.17,0,shoulder),(sign*.205,0,elbow),.045,.032)
    limb("CANDIDATE_FOREARM_"+side,(sign*.205,0,elbow),(sign*.21,0,wrist),.032,.022)
bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=(0,0,(1.63+z(marks["chin_y_approx"]))/2))
head=bpy.context.object;head.name="CANDIDATE_HEAD";head.scale=(.135,.105,(1.63-z(marks["chin_y_approx"]))/2)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_body_04_candidate.blend"))
report={"status":"PARAMETRIC_CANDIDATE_ONLY","source":"MORWEN_LAYER0_LANDMARKS_CANDIDATE.json","art_qa":"NOT_RUN","full_body_topology":"INCOMPLETE","reference_four_view_fit":"NOT_VERIFIED","canonical_modified":False}
(OUT/"report.json").write_text(json.dumps(report,indent=2)+"\n")
print("MORWEN_BODY_04_CANDIDATE_CREATED")
