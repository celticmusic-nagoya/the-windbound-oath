"""Build deliberate 24-vertex anatomical torso rings; no voxel union."""
import json,math
from pathlib import Path
import bpy,bmesh
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[3]
ANCHORS=ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json"
OUT=ROOT/"assets/candidates/morwen-blender-15"
NAME="Morwen_15_anatomical_torso_candidate"

def main():
    a=json.loads(ANCHORS.read_text())
    f=a["facings"]["front"]["rig_points_pixels"]
    scale=float(a["common_pixel_scale"])
    origin=a["facings"]["front"]["origin_x"]
    ground=a["facings"]["front"]["measured_ground_y"]
    def xyz(name):
        x,y=f[name]
        return Vector(((x-origin)*scale,0,(ground-y)*scale))
    shoulder_width=abs(xyz("shoulder.L").x-xyz("shoulder.R").x)
    hip_width=abs(xyz("hip.L").x-xyz("hip.R").x)
    chest=xyz("chest");waist=xyz("waist");pelvis=xyz("pelvis")
    assert chest.z>waist.z>pelvis.z
    # Neck-to-hip rings: waist and shoulder transitions are deliberate loops,
    # not a remeshed union of primitive ellipsoids.
    levels=[
      (pelvis.z-.025,hip_width*.42,.060,"pelvis"),
      (pelvis.z+.025,hip_width*.52,.070,"pelvis"),
      (waist.z-.025,hip_width*.46,.062,"waist"),
      (waist.z+.025,hip_width*.43,.060,"waist"),
      (chest.z-.055,shoulder_width*.42,.080,"chest"),
      (chest.z-.010,shoulder_width*.48,.087,"chest"),
      (chest.z+.035,shoulder_width*.44,.075,"shoulder"),
      (chest.z+.065,shoulder_width*.30,.060,"neck_base")]
    n=24;verts=[];faces=[]
    for z,rx,ry,name in levels:
        for j in range(n):
            angle=2*math.pi*j/n
            verts.append((chest.x+rx*math.cos(angle),ry*math.sin(angle),z))
    for k in range(len(levels)-1):
        for j in range(n):
            q=k*n+j;r=k*n+(j+1)%n
            faces.append((q,r,r+n,q+n))
    faces.append(tuple(reversed(tuple(range(n)))))
    faces.append(tuple((len(levels)-1)*n+j for j in range(n)))
    mesh=bpy.data.meshes.new(NAME+"_mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(NAME,mesh)
    bpy.context.scene.collection.objects.link(obj)
    for p in mesh.polygons:p.use_smooth=True
    groups={name:obj.vertex_groups.new(name=name) for name in ("pelvis","spine","neck")}
    for k,(_,_,_,label) in enumerate(levels):
        ids=list(range(k*n,(k+1)*n))
        t=k/(len(levels)-1)
        if t<.30: weights={"pelvis":1-t/.30,"spine":t/.30}
        elif t<.78: weights={"spine":1.0}
        else: weights={"spine":(1-t)/.22,"neck":1-(1-t)/.22}
        for name,w in weights.items():
            if w>1e-6:groups[name].add(ids,max(0,min(1,w)),"REPLACE")
    bm=bmesh.new();bm.from_mesh(mesh)
    components=0;seen=set()
    for v in bm.verts:
        if v in seen:continue
        components+=1;stack=[v];seen.add(v)
        while stack:
            for edge in stack.pop().link_edges:
                other=edge.other_vert(edge.verts[0]) if False else None
                for other in edge.verts:
                    if other not in seen:seen.add(other);stack.append(other)
    boundary=sum(e.is_boundary for e in bm.edges)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    assert components==1 and boundary==0 and nonmanifold==0
    assert len(mesh.vertices)==len(levels)*n
    assert len(mesh.polygons)==(len(levels)-1)*n+2
    OUT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_anatomical_torso_candidate.blend"))
    report={"task":"MORWEN-BLENDER-15","stage":"TORSO_ONLY",
       "vertices":len(mesh.vertices),"faces":len(mesh.polygons),
       "rings":len(levels),"ring_vertices":n,"components":components,
       "boundary_edges":boundary,"nonmanifold_edges":nonmanifold,
       "shoulder_width":shoulder_width,"hip_width":hip_width,
       "full_body":False,"art_approval":"NOT_RUN","production_use":False}
    (OUT/"build_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_15_TORSO_TOPOLOGY_PASS")

if __name__=="__main__":main()
