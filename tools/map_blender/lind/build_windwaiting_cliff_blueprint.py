"""Build and measure an opt-in rock mass arranged around the fixed sunset sightline."""
import argparse
import json
from math import acos, degrees
from pathlib import Path
import sys

import bmesh
import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_windwaiting_headland as previous

sys.path.insert(0, str(previous.ROOT / "tools/production_qa"))
from junction_contact_faces import triangle_crossing

SOURCE = previous.BASE / "headland-v1/headland_UNAPPROVED.blend"
HEADLAND = "Rebuilt headland | promontory, rock shoulders, gully"
# World X, toe Y, lower shelf Y, upper shelf Y, crest Y, crest Z.
# The cliff span and the shoulder separation run diagonally across the sunset frame.
STATIONS = [
    (-7.2, -4.0, -3.5, -3.1, -2.85, 3.7),
    (-4.4, -8.0, -7.59, -6.95, -4.25, 8.48),
    (-.95, -9.25, -8.80, -7.70, -3.23, 8.94),
    (1.25, -10.75, -10.30, -9.17, -7.20, 5.75),
    (2.85, -5.85, -5.49, -5.09, -4.16, 1.25),
    (5.05, -9.10, -8.70, -7.40, -5.94, 3.55),
]


def section(station):
    x, toe, lower, upper, cap, height = station
    # Medium and upper rock tiers use a stepped rear return. A buried toe
    # penetrates the carrier, while the exposed rear wall stays off the route.
    rear = -2.72 + previous.smooth((x + 3.4) / 1.45) * (1 - previous.smooth((x + .1) / 1.15)) * 1.6
    return [
        (x, toe, -.70), (x, toe-.06, .28), (x, lower-.33, height*.27),
        (x, lower, height*.32), (x, lower+.58, height*.33),
        (x, upper-.18, height*.68), (x, upper+.44, height*.70),
        (x, cap-.49, height*.95), (x, cap, height),
        (x, cap+.52, height*.96),
        (x, max(cap+.69,rear-.95), height*.78),
        (x, max(cap+.85,rear-.69), height*.64),
        (x, max(cap+1.07,rear-.63), height*.62),
        (x, max(cap+1.22,rear-.28), height*.39),
        (x, max(cap+1.4,rear), -.70),
    ]


def bvh(obj):
    return previous.terrain_bvh(obj.data)[0]


def visible_samples(scene, rock, blockers):
    camera = bpy.data.objects["Sunset study"]
    origin = camera.matrix_world.translation
    own_tree = bvh(rock)
    rows = []
    rock.data.calc_loop_triangles()
    for tri in rock.data.loop_triangles:
        if rock.data.polygons[tri.polygon_index].material_index != 0:
            continue
        points = [rock.data.vertices[i].co for i in tri.vertices]
        for bary in [(1/3,1/3,1/3),(.60,.20,.20),(.20,.60,.20),(.20,.20,.60)]:
            p = sum((v*w for v,w in zip(points,bary)),Vector())
            direction = p-origin
            uv = world_to_camera_view(scene,camera,p)
            if tri.normal.dot(direction)>=0 or not (0<uv.x<1 and 0<uv.y<1 and uv.z>0):
                continue
            max_distance = direction.length-.008
            unit = direction.normalized()
            own = own_tree.ray_cast(origin,unit,max_distance)
            hit = [(tree.ray_cast(origin,unit,max_distance),name) for name,tree in blockers]
            hit = [(result[3],name,result[0]) for result,name in hit if result[0] is not None]
            if own[0] is not None:
                hit.append((own[3],"self",own[0]))
            nearest=min(hit,key=lambda result:result[0]) if hit else None
            rows.append({"uv":[uv.x,uv.y],"point":list(p),"triangle_polygon":tri.polygon_index,
                         "occluded_by":nearest[1] if nearest else None,
                         "occluder_point":list(nearest[2]) if nearest else None})
    return rows


def expected_ground(objects, probes):
    trees = [bvh(obj) for obj in objects]
    down = Vector((0,0,-1))
    heights = []
    for ray in probes:
        hits = [tree.ray_cast(ray,down)[0] for tree in trees]
        heights.append(max((hit.z for hit in hits if hit is not None),default=-100.0))
    return heights


def mesh_record(obj):
    mesh=obj.data
    mesh.calc_loop_triangles()
    edges=bmesh.new()
    edges.from_mesh(mesh)
    qa={"boundary_edges":sum(e.is_boundary for e in edges.edges),
        "nonmanifold_edges":sum(not e.is_manifold for e in edges.edges),
        "winding_conflicts":sum(e.is_manifold and not e.is_contiguous for e in edges.edges)}
    edges.free()
    uv=mesh.uv_layers.active
    headland_uv=mesh.uv_layers.get("Rock projection | 1.3 BU repeat")

    def face_uv(face):
        material=mesh.materials[face.material_index] if mesh.materials else None
        layer=headland_uv if headland_uv is not None and material and material.name.startswith("Headland") else uv
        return [list(layer.data[i].uv) for i in face.loop_indices] if layer else []
    return {
        "name":obj.name,"vertices":[list(obj.matrix_world@v.co) for v in mesh.vertices],
        "edges":[list(e.vertices) for e in mesh.edges],
        "materials":[{"id":i,"name":mat.name if mat else None} for i,mat in enumerate(mesh.materials)],
        "faces":[{"vertices":list(f.vertices),"material_id":f.material_index,"normal":list(f.normal),
                  "slope_degrees":degrees(acos(min(1,abs(f.normal.z)))),
                  "area":f.area,"uv":face_uv(f)}
                 for f in mesh.polygons],
        "triangles":[{"vertices":list(t.vertices),"face":t.polygon_index} for t in mesh.loop_triangles],
        "topology":qa,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output",type=Path)
    out=parser.parse_args(sys.argv[sys.argv.index("--")+1:]).output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    native=out/"cliff-blueprint_UNAPPROVED.blend"
    assert not native.exists()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE),load_ui=False)
    scene=bpy.context.scene
    carrier=bpy.data.objects[previous.CARRIER]
    old=bpy.data.objects[HEADLAND]
    road=bpy.data.objects["Coastal footpath"]
    image=next(n.image for n in old.data.materials[0].node_tree.nodes if n.type=="TEX_IMAGE")
    new=previous.build_rock(image,STATIONS,section)
    material_source=json.loads((previous.BASE/"photo-pbr/rock_boulder_dry/manifest.json").read_text())
    rock_nodes=new.data.materials[0].node_tree
    shader=next(n for n in rock_nodes.nodes if n.type=="BSDF_PRINCIPLED")
    for channel in ("normal","roughness"):
        record=material_source["textures"][channel]
        path=previous.BASE/"photo-pbr/rock_boulder_dry"/record["path"]
        assert previous.digest(path)==record["sha256"]
        tid=rock_nodes.nodes.new("ShaderNodeTexImage")
        tid.image=bpy.data.images.load(str(path),check_existing=True)
        tid.image.colorspace_settings.name="Non-Color"
        if channel=="normal":
            mapping=rock_nodes.nodes.new("ShaderNodeNormalMap")
            rock_nodes.links.new(tid.outputs["Color"],mapping.inputs["Color"])
            rock_nodes.links.new(mapping.outputs["Normal"],shader.inputs["Normal"])
        else:
            rock_nodes.links.new(tid.outputs["Color"],shader.inputs["Roughness"])
    uv_node=rock_nodes.nodes.new("ShaderNodeUVMap")
    uv_node.uv_map=new.data.uv_layers.active.name
    for node in rock_nodes.nodes:
        if node.type=="TEX_IMAGE":
            rock_nodes.links.new(uv_node.outputs["UV"],node.inputs["Vector"])
        if node.type=="NORMAL_MAP":
            node.uv_map=uv_node.uv_map
    blockers=[(carrier.name,bvh(carrier))]
    for item in scene.objects:
        if item.type=="MESH" and (item.name.startswith("C10 large rock") or item.name.startswith("eco_tree")) and not item.hide_render:
            blockers.append((item.name,BVHTree.FromObject(item,bpy.context.evaluated_depsgraph_get())))
    visibility={"baseline":visible_samples(scene,old,blockers),"candidate":visible_samples(scene,new,blockers)}
    rays=previous.navigation_rays()
    foliage=json.loads((previous.BASE/"eco-v2/placement.json").read_text())["instances"]
    foliage_rays=[Vector((*item["xy"],18)) for item in foliage]
    before=expected_ground([carrier,old],rays+foliage_rays)
    unjoined=expected_ground([carrier,new],rays+foliage_rays)
    assert max(abs(a-b) for a,b in zip(before,unjoined)) < 1e-5, [(tuple(ray),round(b-a,4)) for ray,a,b in zip(rays+foliage_rays,before,unjoined) if abs(a-b)>1e-5][:20]
    # Keep both editable operands in the native file; only the welded result renders.
    joined=carrier.copy()
    joined.data=carrier.data.copy()
    joined.name="Sunset headland | integrated bedrock and meadow"
    bpy.context.collection.objects.link(joined)
    bpy.context.view_layer.objects.active=joined
    mod=joined.modifiers.new("Weld buried inland join","BOOLEAN")
    mod.operation="UNION"
    mod.solver="EXACT"
    mod.material_mode="TRANSFER"
    mod.object=new
    bpy.ops.object.modifier_apply(modifier=mod.name)
    after=expected_ground([joined],rays+foliage_rays)
    delta=max(abs(a-b) for a,b in zip(before,after))
    assert delta<1e-5, delta
    # Boolean may retain basic mesh attributes. Validate watertightness and
    # ensure no non-neighbour face crossings in the joined output.
    assert any(mat and mat.name.startswith("Headland rock") for mat in joined.data.materials)
    assert any(joined.data.materials[f.material_index] and
               joined.data.materials[f.material_index].name.startswith("Headland rock")
               for f in joined.data.polygons)
    # Exporter tangents are generated on UV0. Preserve the carrier UV0 while
    # putting the authored coordinates in UV0 only for transferred loft faces.
    primary=joined.data.uv_layers.active
    authored=joined.data.uv_layers[uv_node.uv_map]
    for face in joined.data.polygons:
        mat=joined.data.materials[face.material_index]
        if mat and mat.name.startswith("Headland"):
            for loop in face.loop_indices:
                primary.data[loop].uv=authored.data[loop].uv
    shader_uv=joined.data.materials[next(f.material_index for f in joined.data.polygons
                                        if joined.data.materials[f.material_index] and
                                        joined.data.materials[f.material_index].name.startswith("Headland rock"))].node_tree
    for node in shader_uv.nodes:
        if node.type in ("UVMAP","NORMAL_MAP"):
            node.uv_map=primary.name
    # The editable loft shares the material datablock; give it matching UV0.
    new.data.uv_layers.active.name=primary.name
    tree,triangles=previous.terrain_bvh(joined.data)
    sets=[set(t) for t in triangles]
    xyz=[tuple(v.co) for v in joined.data.vertices]
    contacts=[{"triangles":[a,b],**triangle_crossing([xyz[i] for i in triangles[a]],
                                                     [xyz[i] for i in triangles[b]])}
              for a,b in tree.overlap(tree) if a<b and not sets[a]&sets[b]]
    bm=bmesh.new()
    bm.from_mesh(joined.data)
    open_edges=sum(not e.is_manifold for e in bm.edges)
    bm.free()
    for item in (carrier,old,new):
        item.hide_set(True)
        item.hide_render=True
    bpy.ops.object.select_all(action="DESELECT")
    joined.select_set(True)
    triangulate=joined.modifiers.new("Stable runtime triangulation","TRIANGULATE")
    triangulate.quad_method="FIXED"
    triangulate.keep_custom_normals=True
    bpy.ops.export_scene.gltf(filepath=str(out/"cliff-blueprint.glb"),use_selection=True,export_apply=True,
                              export_extras=True,export_tangents=True,export_animations=False)
    joined.modifiers.remove(triangulate)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(native),compress=True)
    uv_layers={key:list(obj.data.uv_layers.keys()) for key,obj in
               [("carrier",carrier),("loft",new),("joined",joined),("road",road)]}
    result={
        "schema":1,"units":"provisional Blender units (X,Y,Z; sea is -Y)",
        "source_blend_sha256":previous.digest(SOURCE),
        "official_cg_sha256":previous.digest(previous.REFERENCE),
        "measurement":{"carrier":mesh_record(carrier),"loft":mesh_record(new),"joined":mesh_record(joined),
                       "road":mesh_record(road)},
        "pbr_source":material_source,"uv_layer_names":uv_layers,
        "candidate_stations_BU":STATIONS,"candidate_section_profiles_BU":[section(s) for s in STATIONS],
        "cg_image_measurement":{"raster_px":[836,471],"polygons":previous.TRACE,
              "projected_faces_px2":{k:previous.area(v) for k,v in previous.TRACE.items() if k!="foreground_occluder"}},
        "inference":{"cg_depth":"not recoverable from one perspective image",
                     "world_dimensions_and_position":"provisional; authored, not measured from CG",
                     "visibility":"ray sampled on outward rock faces, not pixel area"},
        "gameplay":{"walkable_samples":len(rays),"vegetation_samples":len(foliage_rays),"max_height_delta_BU":delta},
        "joined_qa":{"nonmanifold_edges":open_edges,"nonadjacent_overlap_candidates":len(contacts),"classified_contacts":contacts,
                     "triangles":len(triangles)},
        "visibility":visibility,
    }
    (out/"structure.json").write_text(json.dumps(result,separators=(",",":"))+"\n")
    for name,rows in visibility.items():
        print(name,len(rows),sum(r["occluded_by"] is None for r in rows),flush=True)
    print("JOIN",result["joined_qa"],flush=True)


if __name__=="__main__":
    main()
