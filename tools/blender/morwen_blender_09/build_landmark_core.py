"""Build anatomically bounded continuous torso core from pinned 4-view landmarks.
Candidate only. Never overwrites the 07 blend or official references.
"""
import json, math
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
SOURCE=ROOT/"assets/candidates/morwen-blender-07/morwen_continuous_core_candidate.blend"
ANCHORS=ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json"
OUT=ROOT/"assets/candidates/morwen-blender-09"

def main():
    data=json.loads(ANCHORS.read_text())
    f=data["facings"]["front"]["rig_points_pixels"]
    side=data["facings"]["right"]
    s=float(data["common_pixel_scale"])
    shoulder_span=abs(f["shoulder.L"][0]-f["shoulder.R"][0])*s
    hip_span=abs(f["hip.L"][0]-f["hip.R"][0])*s
    body_height=abs(f["head_top"][1]-f["toe.L"][1])*s
    torso_height=abs(f["chest"][1]-f["pelvis"][1])*s
    assert 0.1<shoulder_span/body_height<0.30
    assert 0.08<hip_span/body_height<0.24
    assert 0.14<torso_height/body_height<0.32
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    rig=bpy.data.objects["Morwen_unified_17_candidate"]
    oldcore=bpy.data.objects["Morwen_07_continuous_core_candidate"]
    oldcore.hide_render=True
    center_x=((f["hip.L"][0]+f["hip.R"][0])/2-data["facings"]["front"]["origin_x"])*s
    # Convert pixel Y to the same world Z coordinate as 03.
    ground=data["facings"]["front"]["measured_ground_y"]
    def z(px):return (ground-px)*s
    z0=z(f["pelvis"][1])
    z1=z(f["chest"][1])
    assert z1>z0
    # Profile depth is an explicit *candidate* inferred from side-view anchors,
    # not from costume silhouette. Radius is capped by shoulder span.
    inferred_depth=float(side.get("inferred_half_depth_px",48))*s
    depth=min(inferred_depth,shoulder_span*0.40)
    # Lower to upper torso. Radii are based on measured shoulder/hip span.
    levels=((0.00,0.42,0.70),(0.12,0.50,0.78),(0.30,0.47,0.85),
            (0.53,0.44,0.83),(0.74,0.47,0.86),(0.91,0.52,0.92),
            (1.00,0.48,0.85))
    verts=[];faces=[];segments=24
    for t,width_factor,depth_factor in levels:
        rx=(hip_span*(1-t)+shoulder_span*t)*width_factor
        ry=depth*depth_factor
        for j in range(segments):
            angle=2*math.pi*j/segments
            verts.append((center_x+rx*math.cos(angle),ry*math.sin(angle),
                          z0+(z1-z0)*t))
    for k in range(len(levels)-1):
        for j in range(segments):
            a=k*segments+j;b=k*segments+(j+1)%segments
            faces.append((a,b,b+segments,a+segments))
    faces.append(tuple(reversed(tuple(range(segments)))))
    faces.append(tuple((len(levels)-1)*segments+j for j in range(segments)))
    mesh=bpy.data.meshes.new("Morwen_09_landmark_core_mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    core=bpy.data.objects.new("Morwen_09_landmark_core_candidate",mesh)
    bpy.context.scene.collection.objects.link(core)
    gp=core.vertex_groups.new(name="pelvis")
    gs=core.vertex_groups.new(name="spine")
    for k,(t,_,_) in enumerate(levels):
        ids=list(range(k*segments,(k+1)*segments))
        w=max(0.0,min(1.0,(t-0.20)/0.65))
        if w<1:gp.add(ids,1-w,"REPLACE")
        if w>0:gs.add(ids,w,"REPLACE")
    for poly in mesh.polygons:poly.use_smooth=True
    arm=core.modifiers.new("Armature_17_candidate","ARMATURE");arm.object=rig
    core["status"]="CANDIDATE_NOT_CANON"
    xs=[v.co.x for v in mesh.vertices];zs=[v.co.z for v in mesh.vertices]
    width=max(xs)-min(xs)
    height=max(zs)-min(zs)
    assert 0.07<width/body_height<0.30, (width,body_height)
    assert 0.14<height/body_height<0.32, (height,body_height)
    assert len(rig.data.bones)==17
    OUT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_landmark_core_candidate.blend"))
    report={"task":"MORWEN-BLENDER-09","status":"TECHNICAL_CANDIDATE",
        "body_height":body_height,"shoulder_span":shoulder_span,
        "hip_span":hip_span,"core_width":width,"core_height":height,
        "core_width_to_body_height":width/body_height,
        "core_height_to_body_height":height/body_height,
        "vertices":len(mesh.vertices),"faces":len(mesh.polygons),
        "bones":len(rig.data.bones),"art_approval":"NOT_RUN",
        "full_body_continuous":False,"production_use":False}
    (OUT/"build_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_09_LANDMARK_CORE_PASS")

if __name__=="__main__":main()
