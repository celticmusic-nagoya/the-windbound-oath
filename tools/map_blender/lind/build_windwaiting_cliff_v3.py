"""V3: a plan-first stacked headland with separately authored rock shoulders."""
import argparse
import json
import struct
from hashlib import sha256
from math import cos, sin
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_windwaiting_cliff_blueprint as blueprint
from build_windwaiting_headland import digest, navigation_rays, terrain_bvh

BASE = blueprint.previous.BASE
SOURCE = BASE / "cliff-v2/cliff-blueprint_UNAPPROVED.blend"
REFERENCE = blueprint.previous.REFERENCE
CARRIER = blueprint.previous.CARRIER
RESULT = "V3 | protected ground and reconstructed shoreline"
PARTS = {
    "main": {
        "plan": [(-5.02,-4.38),(-4.20,-3.79),(-2.92,-2.15),(-1.18,-1.59),(-.24,-2.31),
                 (.44,-3.49),(.76,-5.63),(.18,-7.38),(-1.32,-7.76),(-2.20,-8.74),
                 (-3.52,-7.22),(-4.75,-6.06)],
        "pivot":(-2.27,-4.78), "angle":.06,
        # z, x/y expansion, x/y shift. Slip at changes of bedding.
        "levels":[(-.81,1.31,1.24,.53,-.64),(.31,1.36,1.21,.48,-.69),
                  (1.86,1.27,1.14,.26,-.62),(2.28,1.14,1.03,.26,-.53),
                  (3.32,1.09,1.07,.04,-.46),(4.08,1.12,1.12,.05,-.47),
                  (4.48,1.01,.98,-.07,-.24),(5.88,.97,1.02,-.22,-.18),
                  (6.42,.94,.96,-.13,-.13),(7.42,.98,.90,-.12,.07),
                  (8.05,.89,.86,0,.12)],
        "crest_relief":[-.92,-.64,-.22,.00,.08,-.22,-.51,-.27,-.65,-.48,-.82,-.71],
    },
    "shoulder-a": {
        "plan":[(-.64,-8.36),(1.04,-7.63),(2.68,-8.23),(3.53,-10.32),
                (4.21,-13.93),(3.66,-17.31),(2.18,-18.94),(.74,-17.64),
                (-.22,-14.18),(-.34,-10.66)],
        "pivot":(1.93,-11.84),"angle":-.09,
        "levels":[(-.76,1.19,1.21,.28,-.39),(.34,1.22,1.21,.36,-.45),
                  (1.23,1.20,1.12,.24,-.41),(1.63,1.08,1.04,.17,-.26),
                  (2.51,1.02,1.04,.09,-.27),(3.04,1.07,1.05,.08,-.26),
                  (3.46,.94,.94,.07,-.09),(4.45,.97,.92,-.19,-.16),(5.66,.89,.90,-.18,-.32)],
        "crest_relief":[.45,.38,.12,.05,-.22,-.45,-.70,-.48,-.20,.22],
    },
    "shoulder-b": {
        "plan":[(2.83,-15.24),(4.53,-14.83),(5.43,-15.56),(6.33,-16.11),(8.39,-19.44),
                (9.56,-23.84),(8.82,-26.15),(7.24,-27.34),(6.40,-25.01),
                (4.81,-24.83),(4.31,-22.58),(3.52,-19.22)],
        "pivot":(6.25,-19.08),"angle":.07,
        "levels":[(-.72,1.15,1.18,.12,-.26),(.29,1.22,1.20,.21,-.33),
                  (.92,1.11,1.12,.17,-.18),(1.40,.99,1.03,.07,-.12),
                  (2.28,1.03,1.01,.09,-.18),(2.67,.90,.91,.02,-.03),
                  (3.27,.92,.89,-.27,-.27),(4.18,.83,.84,-.40,-.72)],
        "crest_relief":[.19,.37,.44,.41,.13,-.10,-.22,-.50,-.58,-.51,-.45,-.33],
    },
}
# This buried root keeps the two shoulders geologically joined under low tide
# without bridging the visible gully. It is never a walkable surface.
ROOT_PLAN=[(.18,-9.3),(2.68,-9.0),(5.6,-15.7),(7.8,-20.5),
           (6.3,-22.2),(3.7,-17.1),(1.3,-14.4),(-.47,-12.9)]
TIE_PLAN=[(-6.55,-1.48),(-5.05,.05),(-3.50,.45),(-1.65,-.35),
          (-.86,-2.37),(-1.87,-4.48),(-3.36,-4.80),(-5.18,-3.45)]
COLORS={"landward-tie":(.49,.50,.505),"main":(.50,.51,.52),"shoulder-a":(.47,.49,.51),"shoulder-b":(.43,.46,.49),"tidal-root":(.42,.44,.47)}
# CG reference observations at 836×471 (top-left origin). This is a composition
# registration; camera pose and depth are not determined by a single painting.
CG_LANDMARKS={"horizon":[[88,254],[829,254]],"sun":[697,229],
              "main_crest":[522,272],"middle_shelf":[580,309],
              "outer_shelf":[616,322],"last_waterline":[657,362]}


def clay(name):
    mat=bpy.data.materials.new("V3 clay | "+name)
    mat.use_nodes=True
    shader=next(n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    shader.inputs["Base Color"].default_value=(*COLORS[name],1)
    shader.inputs["Roughness"].default_value=.93
    mat.diffuse_color=(*COLORS[name],1)
    return mat


def solid(name,plan,pivot,levels,relief,angle=0):
    """Closed nonuniform plan rings, with shared perimeter edges per bedding level."""
    verts=[]
    count=len(plan)
    for j,(z,sx,sy,dx,dy) in enumerate(levels):
        for i,(px,py) in enumerate(plan):
            x,y=px-pivot[0],py-pivot[1]
            shift=angle*(z+.75)/9
            xx,yy=x*cos(shift)-y*sin(shift),x*sin(shift)+y*cos(shift)
            weight=max(0,(z-.3)/max(1,levels[-1][0]-.3))
            verts.append((pivot[0]+xx*sx+dx,pivot[1]+yy*sy+dy,z+relief[i]*weight))
    faces=[tuple(reversed(range(count)))]
    for j in range(len(levels)-1):
        for i in range(count):
            left=j*count+i
            right=j*count+(i+1)%count
            faces.extend(((left,right,left+count),(right,right+count,left+count)))
    faces.append(tuple(range(len(verts)-count,len(verts))))
    mesh=bpy.data.meshes.new(name+" | bedding topology")
    mesh.from_pydata(verts,[],faces)
    mesh.update()
    mesh.materials.append(clay(name))
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges)
    bm.to_mesh(mesh)
    bm.free()
    mesh.uv_layers.new(name="Coast tile | U periodic")
    obj=bpy.data.objects.new("V3 authored | "+name,mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def union(target,operand):
    bpy.context.view_layer.objects.active=target
    mod=target.modifiers.new("V3 buried join: "+operand.name,"BOOLEAN")
    mod.operation="UNION"
    mod.solver="EXACT"
    mod.material_mode="TRANSFER"
    mod.object=operand
    bpy.ops.object.modifier_apply(modifier=mod.name)


def record_sections(objects):
    result=[]
    for x in (-4.4,-2.7,-.8,1.9,4.3,7.6):
        segments={}
        for key,obj in objects.items():
            obj.data.calc_loop_triangles()
            lines=[]
            for t in obj.data.loop_triangles:
                p=[obj.data.vertices[i].co for i in t.vertices]
                hits=[]
                for a,b in zip(p,p[1:]+p[:1]):
                    if (a.x < x)==(b.x < x):
                        continue
                    h=a.lerp(b,(x-a.x)/(b.x-a.x))
                    hits.append([h.y,h.z])
                if len(hits)==2:
                    lines.append(hits)
            segments[key]=lines
        result.append({"X_BU":x,"YZ_segments":segments})
    return result


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output",type=Path)
    out=parser.parse_args(sys.argv[sys.argv.index("--")+1:]).output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    native=out/"cliff-v3_UNAPPROVED.blend"
    assert not native.exists()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
    scene=bpy.context.scene
    carrier=bpy.data.objects[CARRIER]
    v2=bpy.data.objects["Sunset headland | integrated bedrock and meadow"]
    road=bpy.data.objects["Coastal footpath"]
    probes=navigation_rays()
    foliage=json.loads((BASE/"eco-v2/placement.json").read_text())["instances"]
    probes+= [Vector((*item["xy"],18)) for item in foliage]
    baseline=blueprint.expected_ground([v2],probes)

    parts={}
    for name,p in PARTS.items():
        parts[name]=solid(name,p["plan"],p["pivot"],p["levels"],p["crest_relief"],p["angle"])
    parts["tidal-root"]=solid("tidal-root",ROOT_PLAN,(3.6,-15.4),
                              [(-1.03,1,1,0,0),(-.48,1.02,1.03,0,0),(.18,.91,.94,0,0)],
                              [0]*len(ROOT_PLAN))
    parts["landward-tie"]=solid("landward-tie",TIE_PLAN,(-3.8,-2.18),
                                [(-.83,1.11,1.1,0,0),(.32,1.10,1.09,0,0),
                                 (2.2,1.03,.99,0,.05),(3.12,1.04,.96,.05,.13),
                                 (4.03,.89,.86,.18,.10),(4.84,.73,.73,.22,.03)],
                                [-.12,.07,.22,.02,-.19,-.12,-.15,-.07])
    candidate=carrier.copy()
    candidate.data=carrier.data.copy()
    candidate.name=RESULT
    bpy.context.collection.objects.link(candidate)
    candidate.hide_set(False)
    candidate.hide_render=False
    for obj in parts.values():
        union(candidate,obj)
    for obj in [carrier,v2,*parts.values()]:
        obj.hide_set(True)
        obj.hide_render=True
    after=blueprint.expected_ground([candidate],probes)
    error=max(abs(a-b) for a,b in zip(baseline,after))
    assert error<1e-5, error
    bm=bmesh.new()
    bm.from_mesh(candidate.data)
    topology={"boundary_edges":sum(e.is_boundary for e in bm.edges),
              "nonmanifold_edges":sum(not e.is_manifold for e in bm.edges),
              "winding_conflicts":sum(e.is_manifold and not e.is_contiguous for e in bm.edges)}
    remaining=set(bm.verts)
    components=[]
    while remaining:
        todo=[remaining.pop()]
        count=0
        while todo:
            vertex=todo.pop()
            count+=1
            for edge in vertex.link_edges:
                neighbour=edge.other_vert(vertex)
                if neighbour in remaining:
                    remaining.remove(neighbour)
                    todo.append(neighbour)
        components.append(count)
    bm.free()
    assert not topology["nonmanifold_edges"],topology
    assert len(components)==1,components
    tree,triangles=terrain_bvh(candidate.data)
    ids=[set(t) for t in triangles]
    points=[tuple(v.co) for v in candidate.data.vertices]
    contacts=[]
    for a,b in tree.overlap(tree):
        if a<b and not ids[a]&ids[b]:
            test=blueprint.triangle_crossing([points[i] for i in triangles[a]],[points[i] for i in triangles[b]])
            contacts.append({"pair":[a,b],**test})
    assert not [c for c in contacts if c["kind"]=="CROSSING"],contacts[:10]
    bpy.ops.object.select_all(action="DESELECT")
    candidate.select_set(True)
    bpy.context.view_layer.objects.active=candidate
    bm=bmesh.new()
    bm.from_mesh(candidate.data)
    missing={slot.name for slot in candidate.data.materials if slot and slot.name.startswith("V3 clay")}
    used={candidate.data.materials[f.material_index].name for f in bm.faces if candidate.data.materials[f.material_index]}
    bm.free()
    assert all("V3 clay | "+label in used for label in ("main","shoulder-a","shoulder-b")),(missing,used)
    bpy.ops.export_scene.gltf(filepath=str(out/"cliff-v3.glb"),use_selection=True,export_extras=True,
                              export_tangents=False,export_animations=False)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    camera=bpy.data.objects["Sunset study"]
    sun=bpy.data.objects.get("Low amber key")
    camera_info={"name":camera.name,"world_matrix":[list(row) for row in camera.matrix_world],
                 "lens_mm":camera.data.lens,"lens_shift":[camera.data.shift_x,camera.data.shift_y],
                 "sensor_width_mm":camera.data.sensor_width}
    if sun:
        camera_info["sun_direction"]=list(sun.matrix_world.to_quaternion()@Vector((0,0,-1)))
    out.joinpath("qa.json").write_text(json.dumps({
        "status":"UNAPPROVED CLAY",
        "source_sha256":digest(SOURCE),"cg_sha256":digest(REFERENCE),
        "fixed_camera":camera_info,"cg_reference_image_px":[836,471],"cg_image_landmarks_px":CG_LANDMARKS,
        "registration":{"camera":"canonical 3D pose unverified; fixed scene camera left in place",
                        "depth":"plan dimensions, inferred from CG composition, recorded as provisional",
                        "targets":"main crest, two declining shoulders, continuous shelf and intermediate gully"},
        "target_plan_controls_BU":PARTS,"landward_tie_footprint_BU":TIE_PLAN,
        "measured_sections":record_sections({"previous":v2,"v3":candidate}),
        "joined_structure":{"triangles":len(triangles),"topology":topology,"connected_component_vertices":components,
                            "classified_nonadjacent_contacts":contacts},
        "preservation":{"walkable_rays":len(probes)-len(foliage),"vegetation_rays":len(foliage),
                        "maximum_support_delta_BU":error,
                        "navigation_sha256":digest(BASE/"navigation.json"),
                        "road_coordinates_sha256":sha256(b"".join(struct.pack("<fff",*v.co)
                                                                  for v in road.data.vertices)).hexdigest()},
        "protected_objects_untouched":[road.name,"runtime collision carrier","vegetation instances"],
    },separators=(",",":"))+"\n")


if __name__=="__main__":
    main()
