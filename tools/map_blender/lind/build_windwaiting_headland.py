"""Rebuild the principal headland as a six-section closed rock mass."""
import argparse
import hashlib
import json
from math import sin
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "assets/candidates/lind/windwaiting-cliff-playable"
SOURCE = BASE / "hero-cliff-v1/hero-cliff_UNAPPROVED.blend"
CARRIER = "Cliff C8 B | joinable coastal segment"
REFERENCE = ROOT / "assets/approved/game/cliff/sunset_background.png"
# Traced on the 836x471 half-size preview. Foot points end at foreground occlusion.
TRACE = {
    "main_exposed_rock": [(310,311),(365,297),(447,292),(460,303),(477,367),(454,378),(407,364),(358,352),(325,348)],
    "central_exposed_rock": [(451,277),(506,268),(528,273),(538,297),(550,342),(565,385),(540,391),(478,371)],
    "outer_shoulders": [(540,299),(582,307),(592,322),(619,320),(629,340),(646,345),(632,365),(601,358),(568,365),(551,340)],
    "foreground_occluder": [(204,340),(325,357),(431,373),(530,392),(624,416),(724,449),(836,471)],
}
# x, seaward foot y, y at lower ledge, y at upper ledge, crown y, crown z.
# S1 is the landward tie-in. S2/S3 form the broad head, S4/S6 the lower
# shoulders; S5 pulls back in plan and drops below both shoulders.
STATIONS = [
    (-7.2,-4.0,-3.5,-3.1,-2.85,3.70),
    (-4.65,-7.20,-6.78,-6.15,-5.13,7.23),
    (-1.20,-8.70,-8.37,-7.80,-6.56,7.54),
    (1.10,-8.35,-7.87,-7.22,-6.48,4.74),
    (2.40,-5.85,-5.62,-5.25,-4.46,1.62),
    (4.10,-7.50,-7.14,-6.62,-5.87,3.30),
]


def smooth(t):
    t = min(1, max(0, t))
    return t*t*(3-2*t)


def digest(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def area(poly):
    return abs(sum(a*d-b*c for (a,b),(c,d) in zip(poly, poly[1:]+poly[:1])))/2


def terrain_bvh(mesh):
    mesh.calc_loop_triangles()
    point_ids = [tuple(tri.vertices) for tri in mesh.loop_triangles]
    return BVHTree.FromPolygons([v.co for v in mesh.vertices],point_ids,all_triangles=True),point_ids


def navigation_rays():
    nav=json.loads((BASE/"navigation.json").read_text())
    return [Vector((nav["origin"][0]+(i%nav["width"])*nav["stride"],
                    -(nav["origin"][1]+(i//nav["width"])*nav["stride"]),18))
            for i,h in enumerate(nav["levels"]) if h is not None]


def cut_shoulder(obj, rays):
    mesh=obj.data
    before, triangles=terrain_bvh(mesh)
    down=Vector((0,0,-1))
    hits=[before.ray_cast(ray,down) for ray in rays]
    pins={i for hit in hits for i in triangles[hit[2]]}
    corridor=KDTree(len(rays)+len(pins))
    for i,ray in enumerate(rays):
        corridor.insert((ray.x,ray.y,0),i)
    for j,i in enumerate(sorted(pins),len(rays)):
        p=mesh.vertices[i].co
        corridor.insert((p.x,p.y,0),j)
    corridor.balance()
    coords=[v.co.copy() for v in mesh.vertices]
    for vertex in mesh.vertices:
        x,y,z=vertex.co
        # All heights in a column share the same horizontal map. Its
        # derivative stays positive with the wide blend into the corridor.
        distance=corridor.find((x,y,0))[2]
        wing=smooth((x+9.9)/2.3)*smooth((-3.0-x)/2.4)*smooth((distance-.95)/2.3)
        retreat=.8*wing*smooth((.75-y)/4.15)
        vertex.co.y=y+retreat
        vertex.co.z=z-.29*wing*max(0,z-2.0)
    mesh.update()
    after, _=terrain_bvh(mesh)
    tri_sets=[set(ids) for ids in triangles]

    def clashes(tree):
        return {(a,b) for a,b in tree.overlap(tree) if a<b and not tri_sets[a]&tri_sets[b]}

    new=clashes(after)-clashes(before)
    assert not new, len(new)
    delta=max(abs(a[0].z-after.ray_cast(ray,down)[0].z) for a,ray in zip(hits,rays))
    assert delta<1e-5, delta
    retreat=max(v.co.y-a.y for a,v in zip(coords,mesh.vertices))
    assert retreat>.25
    return hits, retreat, delta, sum((a-v.co).length>.00001 for a,v in zip(coords,mesh.vertices)), {
        "final_new_carrier_crossings":len(new)
    }


def material(name, color, image=None):
    mat=bpy.data.materials.new(name)
    mat.diffuse_color=(*color,1)
    mat.use_nodes=True
    nodes=mat.node_tree.nodes
    bsdf=next(n for n in nodes if n.type=="BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value=(*color,1)
    bsdf.inputs["Roughness"].default_value=.86
    if image:
        tex=nodes.new("ShaderNodeTexImage")
        tex.image=image
        mat.node_tree.links.new(tex.outputs["Color"],bsdf.inputs["Base Color"])
    return mat


def cross_section(record):
    x,toe,lower,upper,crown,h=record
    # Each ring has its toe, riser and shelf breaks, capped at the inland tie.
    return [(x,toe,-.52),(x,toe-.02,.24),(x,lower-.36,h*.29),
            (x,lower,h*.33),(x,lower+.62,h*.34),
            (x,upper-.10,h*.68),(x,upper+.38,h*.70),
            (x,crown-.27,h*.96),(x,crown,h),
            (x,crown+1.22,h*.90),(x,max(crown+2.55,-2.15),h*.67),
            (x,max(crown+2.7,-1.60),-.52)]


def build_rock(image, stations=STATIONS, section=cross_section):
    rings=[]
    for j,(a,b) in enumerate(zip(stations,stations[1:])):
        rings.append(section(a))
        for k in range(1,7):
            t=k/7
            profile=section([u+(v-u)*t for u,v in zip(a,b)])
            rings.append([(x,y+.13*sin(4.1*x+r*.7)*sin(t*3.14159),
                           z+(.115*sin(5.7*x+r*.82)*sin(t*3.14159) if 1<=r<=9 else 0))
                          for r,(x,y,z) in enumerate(profile)])
    rings.append(section(stations[-1]))
    width=len(rings[0])
    faces=[]
    slots=[]
    for j in range(len(rings)-1):
        for k in range(width):
            a=j*width+k
            b=j*width+(k+1)%width
            faces.extend([(a,b,a+width),(b,b+width,a+width)])
            slots.extend([int(k==8)]*2)
    faces.extend([tuple(range(width)),tuple(range(len(rings)*width-1,(len(rings)-1)*width-1,-1))])
    slots.extend([0,0])
    mesh=bpy.data.meshes.new("Six section headland loft | closed rock")
    mesh.from_pydata([p for ring in rings for p in ring],[],faces)
    mesh.update()
    obj=bpy.data.objects.new("Rebuilt headland | promontory, rock shoulders, gully",mesh)
    bpy.context.collection.objects.link(obj)
    for mat in (material("Headland rock | weathered slate",(.29,.30,.30),image),
                material("Headland cap | discontinuous turf",(.12,.16,.054))):
        mesh.materials.append(mat)
    for face,slot in zip(mesh.polygons,slots):
        face.material_index=slot
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    uv=mesh.uv_layers.new(name="Rock projection | 1.3 BU repeat")
    for face in mesh.polygons:
        n=face.normal
        axis=max(range(3),key=lambda i:abs(n[i]))
        ij=[i for i in range(3) if i!=axis]
        for l in face.loop_indices:
            p=mesh.vertices[mesh.loops[l].vertex_index].co
            uv.data[l].uv=(p[ij[0]]/1.30,p[ij[1]]/1.30)
    return obj


def main():
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    out=p.parse_args(sys.argv[sys.argv.index("--")+1:]).output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert not (out/"headland_UNAPPROVED.blend").exists()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
    terrain=bpy.data.objects[CARRIER]
    rays=navigation_rays()
    hits,retreat,ground_delta,changed,retreat_qa=cut_shoulder(terrain,rays)
    photo=BASE/"photo-pbr/rock_boulder_dry"
    record=json.loads((photo/"manifest.json").read_text())
    assert record["license"]=="CC0"
    source=photo/record["textures"]["basecolor"]["path"]
    assert digest(source)==record["textures"]["basecolor"]["sha256"]
    rock=build_rock(bpy.data.images.load(str(source),check_existing=True))
    rock_bvh,rock_tris=terrain_bvh(rock.data)
    rock_sets=[set(ids) for ids in rock_tris]
    crossings=[(a,b) for a,b in rock_bvh.overlap(rock_bvh) if a<b and not rock_sets[a]&rock_sets[b]]
    assert not crossings, len(crossings)
    down=Vector((0,0,-1))
    obstruction=0
    for ray,baseline in zip(rays,hits):
        hit,*_=rock_bvh.ray_cast(ray,down)
        obstruction+=bool(hit and hit.z>baseline[0].z+1e-5)
    assert not obstruction, obstruction
    bpy.ops.object.select_all(action="DESELECT")
    for obj in (terrain,rock):
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(out/"headland.glb"),use_selection=True,
                              export_extras=True,export_animations=False)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"headland_UNAPPROVED.blend"),compress=True)
    data={
        "status":"UNAPPROVED","reference_sha256":digest(REFERENCE),"source_sha256":digest(SOURCE),
        "cg_trace_image_px":[836,471],"cg_trace":TRACE,
        "trace_visible_areas_px2":{k:area(v) for k,v in TRACE.items() if k!="foreground_occluder"},
        "cg_depth_order":["foreground turf","main/central rock faces","seaward shoulders","offshore hills"],
        "trace_uncertainty":"Hand traced from single CG: occluded toe and physical depth unmeasured. Stations are provisional, not reconstructed depths.",
        "section_columns":["X","toe_Y","lower_shelf_Y","upper_shelf_Y","crown_Y","crown_Z"],
        "records":STATIONS,"section_vertices_BU":[cross_section(s) for s in STATIONS],
        "terrain_retreat_BU":retreat,"retreat_validation":retreat_qa,"changed_carrier_vertices":changed,
        "navigation_rays":len(rays),"max_height_delta_BU":ground_delta,"new_rock_over_playable_surface":obstruction,
        "new_rock_nonadjacent_self_contacts":len(crossings),"new_rock_triangles":len(rock_tris),
        "material_source":record,
    }
    (out/"geometry-qa.json").write_text(json.dumps(data,indent=2)+"\n")


if __name__=="__main__":
    main()
