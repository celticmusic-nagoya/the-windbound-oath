"""Sculpt one graded coastal rock table and its eroded sea shelves in Blender."""
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import struct
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_windwaiting_cliff_v3 as prior
import build_windwaiting_cliff_blueprint as blueprint
from build_windwaiting_headland import digest, navigation_rays, terrain_bvh

SOURCE = prior.BASE / "cliff-v3/cliff-v3_UNAPPROVED.blend"
RESULT = "V3-D | integrated grassy headland and eroded bedrock"
# X, Z at crest, coast Y at toe, Y at lower and middle shelf, Y at crest,
# Y at upper landward slope, Y at buried join, Z at buried join.
# Variable cross-shore dimensions form a single eroded landform.
STATIONS = [
    (-9.7, 3.60,-2.65,-2.22,-1.89,-1.48,-.58,.85,3.0),
    (-7.8, 5.21,-5.81,-5.37,-4.49,-3.95,-2.54,.88,3.5),
    (-6.25,6.15,-7.19,-6.82,-5.91,-5.18,-3.79,.58,4.25),
    (-4.55,7.51,-8.38,-7.88,-6.96,-5.34,-2.78,.83,4.64),
    (-2.7,8.17,-10.45,-9.79,-8.37,-6.45,-3.01,1.03,4.94),
    (-.70,8.34,-12.81,-12.17,-10.72,-7.72,-3.76,.68,4.92),
    (1.12,7.47,-16.72,-16.11,-14.87,-11.20,-7.45,-1.00,4.53),
    (2.78,5.82,-21.02,-20.32,-19.18,-16.75,-12.22,-3.67,3.30),
    (4.16,5.02,-22.04,-21.58,-18.56,-17.14,-11.20,-3.95,3.05),
    (5.17,3.14,-16.54,-16.06,-14.68,-13.23,-9.84,-4.04,2.71),
    (6.33,3.82,-23.96,-23.02,-21.98,-20.81,-16.40,-4.33,2.82),
    (7.86,4.43,-28.20,-27.10,-25.84,-24.05,-19.67,-4.91,2.85),
    (9.46,3.48,-27.76,-27.05,-25.97,-23.66,-17.67,-5.40,2.20),
    (11.20,1.20,-18.61,-18.12,-17.68,-17.03,-11.56,-6.20,1.2),
]
# 8547.jpg is an image-space structural guide; its dimensions are not world data.
GUIDE = {
    "basis": "user-supplied embedded 8547.jpg, manually traced image coordinates",
    "raster_px": [1280,800],
    "landmarks_px": {
        "grass_ridge": [[0,423],[459,310],[656,284],[839,316]],
        "landward_shoulder": [345,416], "incision_head": [411,400],
        "valley_waterline": [580,616], "outer_shoulder": [845,357],
        "lower_shelf": [872,676], "skerry": [1044,615],
    },
    "limits": "Silhouette and relative connections only. Apparent depth is inferred; coordinates are not scale.",
}
COLORS = {"rock":(.49,.51,.52), "turf":(.49,.52,.46), "shelf":(.44,.47,.485),
          "underside":(.43,.45,.48), "skerry":(.47,.49,.515)}


def material(key):
    mat = bpy.data.materials.new("V3-D clay | "+key)
    mat.use_nodes = True
    mat.diffuse_color = (*COLORS[key],1)
    shader = next(n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value = mat.diffuse_color
    shader.inputs["Roughness"].default_value = .93
    return mat


def profile(station):
    x,z,toe,lower,middle,crest,slope,rear,heel = station
    # Side faces, overhanging bedding ledges, meadow return and buried heel.
    # Keep the closure below the sea datum and stagger the face angles.
    coast_guard=math.exp(-((x+4.65)/2.05)**2)
    slope=slope-0.95*coast_guard
    mix=.70-.52*coast_guard
    rear_mid=z*mix+heel*(1-mix)
    # A seaward-facing side scarp breaks out beneath the grass cap. Keep its
    # upper return inside the old non-walkable envelope by only cutting down.
    inner=(slope+rear)*.5
    cut_weight=math.exp(-((x+.45)/4.9)**2)
    upper_z=z*.92
    notch_y=slope+(inner-slope)*(.18+.07*math.sin(x*1.4))
    notch_cap=upper_z+(rear_mid-upper_z)*((notch_y-slope)/(inner-slope))
    notch_z=max(heel,notch_cap-cut_weight*(.71+.14*math.sin(x*1.7)))
    ledge_y=slope+(inner-slope)*.43
    ledge_z=max(heel,min(notch_z-.035,upper_z+(rear_mid-upper_z)*.43))
    inner_z=max(heel,min(rear_mid,ledge_z-.045))
    return [
        (x,toe+.02,-.83), (x,toe-.08,.20), (x,lower-.44,z*.22),
        (x,lower-.21,z*.28), (x,lower+.32,z*.29),
        (x,middle-.46,z*.53), (x,middle-.19,z*.58), (x,middle+.43,z*.60),
        (x,crest-.55,z*.88), (x,crest,z),
        (x,slope,upper_z), (x,notch_y,notch_z), (x,ledge_y,ledge_z),
        (x,inner,inner_z), (x,rear,heel), (x,rear+.11,-.83),
    ]


def closed_loft():
    rings = []
    for i,(a,b) in enumerate(zip(STATIONS,STATIONS[1:])):
        rings.append(profile(a))
        cells = max(3,round((b[0]-a[0])/.24))
        for step in range(1,cells):
            t = step/cells
            ring = profile(tuple(v+(w-v)*t for v,w in zip(a,b)))
            # Long bedding surfaces break up across asymmetric short strikes.
            # The ring ordering and cross-shore shelf levels remain explicit.
            points=[]
            for row,(x,y,z) in enumerate(ring):
                weight=math.sin(math.pi*t)
                relief=math.sin(x*3.6+i*.53+row*.61)*weight
                offset=0 if row==0 or row>=10 else .11*relief
                depth=0 if row>=10 else relief*(.19 if row<9 else .10)
                points.append((x,y+depth,z+offset))
            rings.append(points)
    rings.append(profile(STATIONS[-1]))
    width = len(rings[0])
    faces,slots=[],[]
    for i in range(len(rings)-1):
        for j in range(width):
            a=i*width+j
            b=i*width+(j+1)%width
            faces.extend([(a,b,a+width),(b,b+width,a+width)])
            turf=(j==9 or (j>=10 and j<width-1 and STATIONS[0][0] < rings[i][0][0] < -5.5))
            slots.extend([1 if turf else 2 if j in (3,6,11) else 3 if j==width-1 else 0]*2)
    faces.extend([tuple(range(width-1,-1,-1)),tuple(range(len(rings)*width-width,len(rings)*width))])
    slots.extend([0,0])
    mesh=bpy.data.meshes.new("Coherent shoreline | graded strata")
    mesh.from_pydata([p for ring in rings for p in ring],[],faces)
    mesh.update()
    for tag in ("rock","turf","shelf","underside"):
        mesh.materials.append(material(tag))
    for face,slot in zip(mesh.polygons,slots):
        face.material_index=slot
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold and e.is_contiguous for e in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    mesh.uv_layers.new(name="Coast tile | U periodic")
    obj=bpy.data.objects.new("V3-D authored | continuous cliffs",mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def skerry(label, rings):
    """Independent waterline rock with a closed tilted base and upper outline."""
    count=len(rings[0])
    points=[point for ring in rings for point in ring]
    faces=[tuple(reversed(range(count)))]
    for i in range(len(rings)-1):
        for j in range(count):
            a=i*count+j
            b=i*count+(j+1)%count
            faces.extend([(a,b,a+count),(b,b+count,a+count)])
    faces.append(tuple(range(len(points)-count,len(points))))
    mesh=bpy.data.meshes.new(label)
    mesh.from_pydata(points,[],faces)
    mesh.update()
    mesh.materials.append(material("skerry"))
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold and e.is_contiguous for e in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    obj=bpy.data.objects.new(label,mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def create_skerries():
    # Unequal sizes and bedding tilt; outside the walkable terrain.
    return [
        skerry("V3-D | detached skerry east",[
            [(9.36,-28.59,-.55),(10.31,-28.12,-.57),(10.89,-29.35,-.62),(10.28,-30.41,-.58),(9.26,-30.02,-.6)],
            [(9.39,-28.81,.49),(10.28,-28.44,.45),(10.74,-29.39,.21),(10.26,-30.14,.28),(9.40,-29.85,.45)],
            [(9.55,-29.02,.95),(10.19,-28.96,1.13),(10.36,-29.44,.87),(10.12,-29.78,.61),(9.54,-29.54,.82)],
        ]),
        skerry("V3-D | detached skerry south",[
            [(8.04,-30.52,-.63),(8.78,-30.44,-.61),(9.03,-31.30,-.57),(8.37,-31.48,-.64)],
            [(8.16,-30.64,.18),(8.70,-30.67,.33),(8.82,-31.26,.22),(8.35,-31.34,.15)],
            [(8.31,-30.72,.48),(8.56,-30.82,.55),(8.68,-31.16,.51),(8.42,-31.19,.44)],
        ]),
    ]


def audit_mesh(obj):
    """Measure connectivity, winding, closed underside and real triangle contacts."""
    mesh=obj.data
    bm=bmesh.new()
    bm.from_mesh(mesh)
    values={"boundary_edges":sum(e.is_boundary for e in bm.edges),
            "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),
            "winding_conflicts":sum(e.is_manifold and not e.is_contiguous for e in bm.edges),
            "signed_volume_BU3":bm.calc_volume(signed=True)}
    remaining=set(bm.verts)
    components=[]
    while remaining:
        stack=[remaining.pop()]
        size=0
        while stack:
            v=stack.pop()
            size+=1
            for e in v.link_edges:
                n=e.other_vert(v)
                if n in remaining:
                    remaining.remove(n)
                    stack.append(n)
        components.append(size)
    bm.free()
    tree,indices=terrain_bvh(mesh)
    sets=[set(t) for t in indices]
    coords=[tuple(v.co) for v in mesh.vertices]
    contacts=[]
    for i,j in tree.overlap(tree):
        if i<j and not sets[i]&sets[j]:
            evidence=blueprint.triangle_crossing([coords[x] for x in indices[i]],[coords[x] for x in indices[j]])
            contacts.append({"triangles":[i,j],**evidence})
    values.update(
        components=sorted(components,reverse=True),triangles=len(indices),contacts=contacts,
        downward_triangles=sum(t.normal.z<-.6 for t in mesh.loop_triangles),
        near_zero_area_triangles=sum(t.area<1e-9 for t in mesh.loop_triangles),
    )
    return values


def main():
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    out=p.parse_args(sys.argv[sys.argv.index("--")+1:]).output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert not (out/"cliff-v3d_UNAPPROVED.blend").exists()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
    old=bpy.data.objects[prior.RESULT]
    carrier=bpy.data.objects[prior.CARRIER]
    road=bpy.data.objects["Coastal footpath"]
    foliage=json.loads((prior.BASE/"eco-v2/placement.json").read_text())["instances"]
    rays=navigation_rays()
    probe_set=rays+[Vector((*item["xy"],18)) for item in foliage]
    baseline=blueprint.expected_ground([old],probe_set)
    old_geometry=audit_mesh(old)
    rock=closed_loft()
    skerries=create_skerries()
    candidate=carrier.copy()
    candidate.data=carrier.data.copy()
    bpy.context.collection.objects.link(candidate)
    candidate.name=RESULT
    candidate.hide_set(False)
    candidate.hide_render=False
    prior.union(candidate,rock)
    for obj in (old,carrier,rock):
        obj.hide_set(True)
        obj.hide_render=True
    new_ground=blueprint.expected_ground([candidate,*skerries],probe_set)
    delta=max(abs(x-y) for x,y in zip(baseline,new_ground))
    assert delta<1e-5, (delta,[(tuple(r),round(a-b,4)) for r,a,b in zip(probe_set,new_ground,baseline) if abs(a-b)>1e-5][:24])
    audits={o.name:audit_mesh(o) for o in (candidate,*skerries)}
    for info in audits.values():
        assert len(info["components"])==1,info["components"]
        assert info["signed_volume_BU3"]>0
        assert not info["nonmanifold_edges"] and not info["winding_conflicts"],info
        assert not [k for k in info["contacts"] if k["kind"]=="CROSSING"],info["contacts"]
    # Compare section intersections and keep the native union editable.
    bpy.ops.object.select_all(action="DESELECT")
    for obj in (candidate,*skerries):
        obj.select_set(True)
    bpy.context.view_layer.objects.active=candidate
    bpy.ops.export_scene.gltf(filepath=str(out/"cliff-v3d.glb"),use_selection=True,
                              export_extras=True,export_animations=False)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"cliff-v3d_UNAPPROVED.blend"),compress=True)
    mesh=blueprint.mesh_record(rock)
    data={
        "candidate":"V3-D CLAY ONLY",
        "source_sha256":digest(SOURCE),"canonical_cg_sha256":digest(prior.REFERENCE),
        "reference_scope":{"official":prior.CG_LANDMARKS,"supplemental":GUIDE,"units":"provisional Blender units"},
        "authored_stations_BU":STATIONS,"authored_profile_vertices_BU":[profile(s) for s in STATIONS],
        "measured_sections":prior.record_sections({"previous":old,"v3d":candidate}),
        "authoring_mesh":mesh,
        "old_structure":old_geometry,"new_structure":audits,
        "protection":{"walkable_points":len(rays),"vegetation_points":len(foliage),
                      "max_surface_delta_BU":delta,"road_coordinates_sha256":sha256(
                       b"".join(struct.pack("<fff",*v.co) for v in road.data.vertices)).hexdigest()},
    }
    (out/"qa.json").write_text(json.dumps(data,separators=(",",":"))+"\n")
    print(f"SUPPORT {delta:.8g}, SEALED {len(audits)} objects",flush=True)


if __name__=="__main__":
    main()
