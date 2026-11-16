"""09K read-only diagnosis of why 09J renders transparent.

Reports geometry/camera clip interval and collection visibility. Does not render,
modify or save model. Uses actual 09G candidate Blender file.
"""
import argparse,json,hashlib
from pathlib import Path
import bpy
from mathutils import Vector

def main():
    p=argparse.ArgumentParser()
    for key in ("strips","out"):p.add_argument("--"+key,required=True,type=Path)
    a=p.parse_args()
    if a.out.exists():raise ValueError("Refuse overwrite")
    bpy.ops.wm.open_mainfile(filepath=str(a.strips.resolve()))
    lash=bpy.data.objects["M09_L_LASH_CANDIDATE_00"]
    coords=[lash.matrix_world@v.co for v in lash.data.vertices]
    center=sum(coords,Vector())/len(coords)
    extent=max((v-center).length for v in coords)*2
    camera_data=bpy.data.cameras.new("M09K_CAMERA_DATA")
    camera=bpy.data.objects.new("M09K_CAMERA",camera_data)
    camera.data.type="ORTHO"
    target=(coords[0]+coords[1]+coords[2])/3
    direction=Vector((0,-1,0.2)).normalized()
    camera.location=target+direction*max(extent,0.015)*3
    camera.rotation_euler=(target-camera.location).to_track_quat("-Z","Y").to_euler()
    depths=[-(camera.matrix_world.inverted()@v).z for v in coords]
    clip_start=camera.data.clip_start
    clip_end=camera.data.clip_end
    report={"status":"READ_ONLY_CAMERA_DIAGNOSIS",
      "strips_sha256":hashlib.sha256(a.strips.read_bytes()).hexdigest(),
      "mesh_vertices":len(coords),"mesh_polygons":len(lash.data.polygons),
      "mesh_world_extent_m":extent,
      "camera_default_clip_start_m":clip_start,"camera_default_clip_end_m":clip_end,
      "camera_distance_to_target_m":(camera.location-target).length,
      "mesh_camera_depth_min_m":min(depths),"mesh_camera_depth_max_m":max(depths),
      "vertices_inside_default_clip_range":sum(clip_start<=d<=clip_end for d in depths),
      "collection_names":[c.name for c in lash.users_collection],
      "collection_hide_render":[{"name":c.name,"hidden":c.hide_render} for c in lash.users_collection],
      "object_hide_render":lash.hide_render,
      "G1":"BLOCKED","G2":"NOT_RUN","G3":"DIAGNOSIS_ONLY","G4":"NOT_RUN"}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+"\n")
    print("M09_CAMERA_DIAGNOSIS_09K="+json.dumps(report,sort_keys=True),flush=True)
if __name__=="__main__":main()
