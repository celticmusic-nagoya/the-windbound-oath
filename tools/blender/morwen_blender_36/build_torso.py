"""BLENDER-24: parametric stylized torso candidate, preserving canonical reference assets.
Run: blender -b -noaudio --python tools/blender/morwen_blender_24/build_torso.py
"""
import json, math
from pathlib import Path
import bpy, bmesh
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"assets/candidates/morwen-blender-36"
ANCHORS=ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json"
NAME="Morwen_24_refined_torso_CANDIDATE"
def smooth(t):
    t=max(0.,min(1.,t))
    return t*t*(3.-2.*t)
def blend(a,b,t):
    return a+(b-a)*smooth(t)
def interpolate(keys,z):
    for i in range(len(keys)-1):
        lo,hi=keys[i],keys[i+1]
        if lo[0]<=z<=hi[0]:
            t=(z-lo[0])/(hi[0]-lo[0])
            return [blend(lo[j],hi[j],t) for j in range(1,len(lo))]
    return list(keys[0 if z<keys[0][0] else -1][1:])
def main():
    a=json.loads(ANCHORS.read_text())
    f=a["facings"]["front"]["rig_points_pixels"]
    s=float(a["common_pixel_scale"]);ox=a["facings"]["front"]["origin_x"];ground=a["facings"]["front"]["measured_ground_y"]
    def x(k):return (f[k][0]-ox)*s
    def z(k):return (ground-f[k][1])*s
    shoulder=abs(x("shoulder.L")-x("shoulder.R"))
    hip=abs(x("hip.L")-x("hip.R"))
    chest,waist,pelvis=z("chest"),z("waist"),z("pelvis")
    assert chest>waist>pelvis
    # BLENDER-36 candidate refinement; canonical source anchors remain immutable.
    # z, lateral half-width, anterior radius, posterior radius, y-center.
    # These are editable modeling *proposals*, NOT measured nude contours.
    # In Blender front is negative Y; back is positive Y.
    keys=[
      (pelvis-.045,hip*.39,.073,.088,.002),
      (pelvis-.025,hip*.46,.079,.093,.003),
      (pelvis+.005,hip*.51,.081,.096,.004),
      (pelvis+.025,hip*.50,.077,.092,.003),
      (waist-.040,hip*.445,.068,.083,-.001),
      (waist-.015,hip*.425,.063,.078,-.003),
      (waist+.010,hip*.425,.063,.077,-.004),
      (waist+.045,hip*.45,.071,.081,-.003),
      (chest-.085,shoulder*.40,.082,.086,-.002),
      (chest-.050,shoulder*.445,.090,.088,-.004),
      (chest-.015,shoulder*.465,.096,.088,-.006),
      (chest+.010,shoulder*.475,.096,.087,-.006),
      (chest+.030,shoulder*.46,.091,.085,-.004),
      (chest+.050,shoulder*.395,.079,.079,-.002),
      (chest+.070,shoulder*.28,.066,.070,.001),
      (chest+.083,shoulder*.19,.056,.060,.002),
    ]
    assert all(keys[i][0]<keys[i+1][0] for i in range(len(keys)-1))
    # Equal subdivisions within anatomical key intervals, smooth tangents.
    levels=[]
    for i in range(len(keys)-1):
        for j in range(4):
            t=j/4
            zz=keys[i][0]+(keys[i+1][0]-keys[i][0])*t
            levels.append((zz,*interpolate(keys,zz)))
    levels.append(keys[-1])
    n=32;vertices=[];faces=[]
    for zz,rx,front,back,offset in levels:
        for j in range(n):
            ang=2*math.pi*j/n
            sy=math.sin(ang)
            depth=front if sy<0 else back
            # Slightly squarer ribcage and pelvis than an ellipse, without corners.
            lateral=math.copysign(abs(math.cos(ang))**.86,math.cos(ang))
            vertices.append((x("chest")+rx*lateral,offset+depth*sy,zz))
    for k in range(len(levels)-1):
        for j in range(n):
            u=k*n+j;v=k*n+(j+1)%n
            faces.append((u,v,v+n,u+n))
    faces.append(tuple(reversed(range(n))))
    faces.append(tuple((len(levels)-1)*n+j for j in range(n)))
    mesh=bpy.data.meshes.new(NAME+"_mesh")
    mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(NAME,mesh)
    bpy.context.scene.collection.objects.link(obj)
    for poly in mesh.polygons:poly.use_smooth=True
    bm=bmesh.new();bm.from_mesh(mesh)
    boundary=sum(e.is_boundary for e in bm.edges)
    nonmanifold=sum(not e.is_manifold for e in bm.edges)
    # Negative volume indicates inverted face winding.
    volume=bm.calc_volume(signed=True)
    bm.free()
    assert boundary==0 and nonmanifold==0 and abs(volume)>1e-6
    assert len(mesh.vertices)==len(levels)*n
    assert all(levels[i][0]<levels[i+1][0] for i in range(len(levels)-1))
    OUT.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"morwen_anatomical_torso_candidate.blend"))
    report={"task":"MORWEN-BLENDER-36","candidate_only":True,
      "art_approval":"NOT_RUN","rings":len(levels),"vertices":len(vertices),
      "faces":len(faces),"signed_volume":volume,"boundary_edges":boundary,
      "nonmanifold_edges":nonmanifold,"shoulder_anchor_width":shoulder,
      "hip_anchor_width":hip,"fit_source":"stylized anatomical design proposal, not direct alpha contour",
      "source_refs_modified":False}
    (OUT/"build_report.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_24_TOPOLOGY_PASS")
if __name__=="__main__":main()
