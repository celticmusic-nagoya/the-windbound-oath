"""BLENDER-19: measure the candidate torso rather than blindly adjust ring radii."""
import json, math
from pathlib import Path
import bpy

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/"assets/candidates/morwen-blender-18"
OUT=ROOT/"assets/candidates/morwen-blender-19"
ANCHORS=ROOT/"assets/candidates/morwen-blender-01/anchors_candidate.json"
BLEND=BASE/"morwen_monotonic_torso_candidate.blend"
NAME="Morwen_18_monotonic_torso_candidate"

def main():
    assert BLEND.is_file(), f"missing candidate: {BLEND}"
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    obj=bpy.data.objects.get(NAME)
    assert obj is not None and obj.type=="MESH"
    a=json.loads(ANCHORS.read_text())
    f=a["facings"]["front"]["rig_points_pixels"]
    scale=float(a["common_pixel_scale"])
    ground=float(a["facings"]["front"]["measured_ground_y"])
    def z_of(name): return (ground-f[name][1])*scale
    target={
      "shoulder_width":abs(f["shoulder.L"][0]-f["shoulder.R"][0])*scale,
      "hip_width":abs(f["hip.L"][0]-f["hip.R"][0])*scale,
    }
    vertices=[obj.matrix_world @ v.co for v in obj.data.vertices]
    def slice_at(z):
        # Intersect edges with a horizontal plane; vertex-only nearest rings
        # are inaccurate for interpolated anatomical profiles.
        points=[]
        for edge in obj.data.edges:
            v1,v2=(vertices[i] for i in edge.vertices)
            lo,hi=sorted((v1.z,v2.z))
            if not (lo<=z<=hi):continue
            if abs(v2.z-v1.z)<1e-10:
                points.extend([v1,v2])
            else:
                t=(z-v1.z)/(v2.z-v1.z)
                points.append(v1.lerp(v2,t))
        if not points:return None
        return {"width_x":max(p.x for p in points)-min(p.x for p in points),
                "depth_y":max(p.y for p in points)-min(p.y for p in points),
                "front_y":min(p.y for p in points),
                "back_y":max(p.y for p in points),
                "count":len(points)}
    measured={name:slice_at(z_of(name)) for name in ("chest","waist","pelvis")}
    assert all(measured.values()), "missing landmark intersections"
    widths={k:measured[k]["width_x"] for k in measured}
    assert widths["waist"]<widths["chest"], "waist not narrower than chest"
    # This is a diagnostic only. Rig anchors locate bones, NOT external
    # garment/body silhouette; avoid claiming these are reference contours.
    report={
      "task":"MORWEN-BLENDER-19",
      "status":"MEASUREMENT_ONLY",
      "source_blend":str(BLEND.relative_to(ROOT)),
      "measured_cross_sections":measured,
      "rig_joint_spans_not_silhouette_targets":target,
      "limitations":[
        "Rig anchors are not body-outline landmarks.",
        "Side-view chest/waist anchors do not define front/back contours.",
        "True image silhouette fitting requires traced outer edges from approved reference PNGs.",
        "No geometry was modified or officially approved."
      ],
      "production_use":False,
      "art_approval":"NOT_RUN"
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"profile_measurements.json").write_text(json.dumps(report,indent=2)+"\n")
    print("MORWEN_19_PROFILE_MEASUREMENT_PASS")
if __name__=="__main__":main()
