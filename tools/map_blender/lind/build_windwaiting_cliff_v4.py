"""Plan-first V4: cross-shore sections, opposed profiles and a buried support heel."""
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
import build_windwaiting_cliff_blueprint as atlas
import build_windwaiting_cliff_v3 as v3
import build_windwaiting_cliff_v3d as v3d
from build_windwaiting_headland import digest, navigation_rays

BASE=v3.BASE
SOURCE=BASE/"cliff-v3d/cliff-v3d_UNAPPROVED.blend"
TARGETS=BASE/"cliff-v4/design-targets.json"
RESULT="V4 | sea-axis headland and meadow return"
MATERIALS=[
    ("bedrock",(.53,.54,.55)),("cap",(.53,.55,.49)),
    ("shelf",(.43,.46,.49)),("heel",(.37,.39,.42)),
]


def material(name,color):
    mat=bpy.data.materials.new("V4 gray | "+name)
    mat.use_nodes=True
    node=next(n for n in mat.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    node.inputs["Base Color"].default_value=(*color,1)
    node.inputs["Roughness"].default_value=.93
    mat.diffuse_color=(*color,1)
    return mat


def section(row):
    y,west,east,h,wb,eb,twist=row
    breadth=east-west
    cx=(west+east)*.5+twist*.2
    wx=west+breadth*wb
    ex=east-breadth*eb
    def p(x,z,lean=0):
        return x,y+lean,z
    # West cap shoulder, central ridge and eastern shelf are asymmetric;
    # the floor is kept under the Z=0 test datum throughout.
    return [
        p(west+.27,-.87),p(west,.21),p(west+.13,h*.19),p(west+.38,h*.32,-.09),
        p(west+.90,h*.34,-.12),p(wx-.53,h*.56),p(wx-.72,h*.69,.09),
        p(wx-.28,h*.73,.08),p(wx,h*.88,.12),p(wx+.5,h*.95,.06),
        p(cx,h),p(ex-.32,h*.93,-.07),p(ex,h*.85),p(ex+.21,h*.69,-.08),
        p(ex+.25,h*.54,-.08),p(east-.50,h*.40),p(east-.39,h*.27),
        p(east,h*.16),p(east-.1,-.87)
    ]


def generate(rows,refined):
    rings=[]
    for i,(a,b) in enumerate(zip(rows,rows[1:])):
        rings.append(section(a))
        cells=max(3,math.ceil(abs(b[0]-a[0])/(.28 if refined and a[0] < -3.7 else .78)))
        for j in range(1,cells):
            t=j/cells
            p=section([u+(v-u)*t for u,v in zip(a,b)])
            modified=[]
            for band,(x,y,z) in enumerate(p):
                # Constructed relief is applied only to the offshore rock,
                # preserving the authored cap and the key surveyed sections.
                offshore=min(1,max(0,(-y-3.7)/4.3))
                wall=band in (1,2,3,4,5,6,7,8,12,13,14,15,16,17)
                strength=offshore*math.sin(math.pi*t) if refined and wall else 0
                cut=max(0.0,math.sin(y*2.17+band*.39+i*.52))**3
                bedding=math.sin(y*1.49+band*.48+i*.17)
                offset=1 if band<10 else -1
                modified.append((x+offset*strength*(.22*cut-.12*bedding),y,
                                 z+strength*(.105*bedding+.075*cut)))
            rings.append(modified)
    rings.append(section(rows[-1]))
    width=len(rings[0])
    faces=[tuple(range(width-1,-1,-1))]
    slots=[0]
    for i in range(len(rings)-1):
        for j in range(width):
            a=i*width+j
            b=i*width+(j+1)%width
            if (i+j)%2:
                faces.extend([(a,b,b+width),(a,b+width,a+width)])
            else:
                faces.extend([(a,b,a+width),(b,b+width,a+width)])
            slots.extend([1 if j in (9,10,11) else 2 if j in (3,6,15) else 3 if j==width-1 else 0]*2)
    faces.append(tuple(range(len(rings)*width-width,len(rings)*width)))
    slots.append(0)
    mesh=bpy.data.meshes.new("V4 | surveyed section ring surfaces")
    mesh.from_pydata([p for ring in rings for p in ring],[],faces)
    mesh.update()
    for key,color in MATERIALS:
        mesh.materials.append(material(key,color))
    for face,slot in zip(mesh.polygons,slots):
        face.material_index=slot
    bm=bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    mesh.uv_layers.new(name="Coast tile | U periodic")
    body=bpy.data.objects.new("V4 authored | cross-shore bedrock",mesh)
    bpy.context.collection.objects.link(body)
    return body


def measure_sections(objects):
    vertex_sets = {}
    for key, obj in objects.items():
        mesh = obj.data
        mesh.calc_loop_triangles()
        points = [obj.matrix_world @ vertex.co for vertex in mesh.vertices]
        vertex_sets[key] = (points, [tuple(tri.vertices) for tri in mesh.loop_triangles])
    cuts = []
    for axis, stations in ((0, (-4.4, -2.7, -.8, 1.9, 4.3, 7.6)),
                           (1, (0, -5.7, -10.8, -15.9, -18.6, -23.8))):
        for station in stations:
            segments = {}
            for key, (points, triangles) in vertex_sets.items():
                lines = []
                for triangle in triangles:
                    corners = [points[index] for index in triangle]
                    hits = []
                    for a, b in zip(corners, corners[1:] + corners[:1]):
                        if (a[axis] < station) != (b[axis] < station):
                            hit = a.lerp(b, (station - a[axis]) / (b[axis] - a[axis]))
                            hits.append([round(hit[1-axis], 5), round(hit.z, 5)])
                    if len(hits) == 2 and hits[0] != hits[1]:
                        lines.append(hits)
                segments[key] = lines
            cuts.append({"plane": "XY"[axis], "station_BU": station,
                         "coordinates": "YX"[axis] + "Z", "segments": segments})
    return cuts


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("A","B"))
    parser.add_argument("output",type=Path)
    parser.add_argument("--refined",action="store_true")
    args=parser.parse_args(sys.argv[sys.argv.index("--")+1:])
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert not (out/"cliff-v4_UNAPPROVED.blend").exists()
    design=json.loads(TARGETS.read_text())
    rows=design["authored_provisional"][args.mode]["sections"]
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
    old=bpy.data.objects[v3d.RESULT]
    carrier=bpy.data.objects[v3.CARRIER]
    road=bpy.data.objects["Coastal footpath"]
    skerries=[obj for obj in bpy.context.scene.objects if obj.name.startswith("V3-D | detached skerry")]
    probes=navigation_rays()
    vegetation=json.loads((BASE/"eco-v2/placement.json").read_text())["instances"]
    probes += [Vector((*entry["xy"],18)) for entry in vegetation]
    before=atlas.expected_ground([old],probes)
    body=generate(rows,args.refined)
    cliff=carrier.copy()
    cliff.data=carrier.data.copy()
    cliff.name=RESULT
    bpy.context.collection.objects.link(cliff)
    cliff.hide_set(False)
    cliff.hide_render=False
    v3.union(cliff,body)
    for obj in (old,carrier,body):
        obj.hide_set(True)
        obj.hide_render=True
    current=atlas.expected_ground([cliff,*skerries],probes)
    error=max(abs(a-b) for a,b in zip(before,current))
    assert error<design["interface_qa"]["support_error_tolerance_BU"],(
        error,[(list(p),round(b-a,5)) for p,a,b in zip(probes,before,current) if abs(b-a)>1e-5][:14])
    inspection=v3d.audit_mesh(cliff)
    assert len(inspection["components"])==1,inspection["components"]
    assert not inspection["boundary_edges"] and not inspection["winding_conflicts"],inspection
    assert not [item for item in inspection["contacts"] if item["kind"]=="CROSSING"],inspection
    road_sha=sha256(b"".join(struct.pack("<fff",*v.co) for v in road.data.vertices)).hexdigest()
    assert road_sha==design["interface_qa"]["road_coordinates_sha256"]
    bpy.ops.object.select_all(action="DESELECT")
    for obj in (cliff,*skerries):
        obj.select_set(True)
    bpy.context.view_layer.objects.active=cliff
    if args.refined:
        bpy.ops.export_scene.gltf(filepath=str(out/"cliff-v4.glb"),use_selection=True,
                                  export_extras=True,export_animations=False)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"cliff-v4_UNAPPROVED.blend"),compress=True)
    qa={
        "mode":args.mode,"refined":args.refined,"status":"UNAPPROVED CLAY",
        "source_sha256":digest(SOURCE),"blueprint_sha256":digest(TARGETS),"official_cg_sha256":digest(v3.REFERENCE),
        "main_structure":inspection,"support_max_delta_BU":error,
        "walkable_samples":len(probes)-len(vegetation),"vegetation_samples":len(vegetation),
        "road_coordinates_sha256":road_sha,
        "authored_key_sections_xyz_BU":[section(row) for row in rows],
    }
    if args.refined:
        qa["transverse_and_longitudinal_reference_sections"]=measure_sections({"v3d":old,"v4":cliff})
        qa["authoring_mesh"]=atlas.mesh_record(body)
    (out/"qa.json").write_text(json.dumps(qa,separators=(",",":"))+"\n")
    print(f"V4 {args.mode}: {inspection['triangles']} triangles; max support delta {error}",flush=True)


if __name__=="__main__":
    main()
