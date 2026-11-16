"""Aidan masonry candidate v2: individually faceted stones, no canonical asset edits.
Headless Blender 4.x. Deliberately separate from broad-plane ring generator.
"""
import bpy, bmesh, json, hashlib, os, random
from mathutils import Vector
from pathlib import Path

SEED=20261116
OUT=Path(os.environ.get("AIDAN_FACET_OUT","/tmp/aidan-facet-v2"))
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def material(name, color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    p=m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value=(*color,1)
    p.inputs["Roughness"].default_value=.94
    return m

colors=[(0.48,.45,.39),(.53,.50,.43),(.43,.42,.38)]
mats=[material("stone_procedural_placeholder_%d"%i,c) for i,c in enumerate(colors)]

def create_stone(name, center, size, seed, material_index):
    """Convex irregular polyhedron from independent corner and face-point vertices.
    Every visible face has its own large triangular planes, not horizontal bands.
    """
    r=random.Random(seed)
    sx,sy,sz=size
    # Eight independently disturbed corners, with top/bottom variation.
    corners=[]
    for z in (-1,1):
        for y in (-1,1):
            for x in (-1,1):
                corners.append((x*sx*.5+r.uniform(-.045,.045)*sx,
                                y*sy*.5+r.uniform(-.06,.06)*sy,
                                z*sz*.5+r.uniform(-.065,.065)*sz))
    # Cube face loops with outward normals.
    faces=[[0,2,3,1],[4,5,7,6],[0,1,5,4],
           [2,6,7,3],[0,4,6,2],[1,3,7,5]]
    vertices=list(corners)
    tris=[]
    for face_id,quad in enumerate(faces):
        # A different off-center recessed/protruding point per face creates
        # several broad triangular facets rather than ring stripes.
        weights=[r.uniform(.15,.35) for _ in quad]
        total=sum(weights)
        weights=[w/total for w in weights]
        centerpt=Vector((0,0,0))
        for idx,w in zip(quad,weights):centerpt+=Vector(vertices[idx])*w
        normal=(Vector(vertices[quad[1]])-Vector(vertices[quad[0]])).cross(
            Vector(vertices[quad[2]])-Vector(vertices[quad[0]])).normalized()
        # Use inward indentation, avoiding spikes and large self-intersections.
        depth=(.013+.022*r.random())*min(sx,sy,sz)
        centerpt-=normal*depth
        mid=len(vertices);vertices.append(tuple(centerpt))
        for k in range(4):tris.append((quad[k],quad[(k+1)%4],mid))
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata([tuple(Vector(v)+Vector(center)) for v in vertices],[],tris)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mats[material_index%len(mats)])
    # Recalculate normals consistently, not depending on initial face winding.
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces)
    bm.to_mesh(mesh);bm.free()
    return obj

# Independent stones, deliberately non-identical proportions, staggered bond.
# Spacing is a comparison fixture, NOT a canonical building dimension.
stones=[]
courses=[
    [(-.36,-.06,.14),(.04,-.04,.14),(.39,-.03,.14)],
    [(-.46,-.04,.43),(-.10,-.03,.43),(.29,-.05,.43)]
]
for course,positions in enumerate(courses):
    for index,pos in enumerate(positions):
        width=[.34,.29,.38,.27,.39,.31][course*3+index]
        height=[.235,.24,.22,.23,.245,.225][course*3+index]
        obj=create_stone("FACET_STONE_%02d"%(course*3+index),
                         pos,(width,.24,height),SEED+course*101+index*17,
                         course*3+index)
        stones.append(obj)

qa=[]
for obj in stones:
    bm=bmesh.new()
    try:
        bm.from_mesh(obj.data)
        boundary=sum(e.is_boundary for e in bm.edges)
        nonmanifold=sum(not e.is_manifold for e in bm.edges)
        vol=bm.calc_volume(signed=True)
        qa.append(dict(name=obj.name,vertices=len(bm.verts),faces=len(bm.faces),
                       boundary=boundary,nonmanifold=nonmanifold,
                       signed_volume=round(vol,8)))
    finally:bm.free()
passed=all(q["boundary"]==0 and q["nonmanifold"]==0 and
           abs(q["signed_volume"])>0 for q in qa)
world=bpy.context.scene.world or bpy.data.worlds.new("world")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7
for loc,energy in [((-3,-4,5),800),((3,2,4),450)]:
    bpy.ops.object.light_add(type="AREA",location=loc)
    bpy.context.object.data.energy=energy
    bpy.context.object.data.size=3
bpy.ops.object.camera_add(location=(1.3,-2.4,1.4))
cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=1.8
cam.rotation_euler=(Vector((0,0,.28))-cam.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
png=OUT/"aidan_facet_v2.png";scene.render.filepath=str(png)
bpy.ops.render.render(write_still=True)
manifest={"candidate":"FACET_V2_UNAPPROVED","seed":SEED,"blender":bpy.app.version_string,
          "image":png.name,"image_sha256":hashlib.sha256(png.read_bytes()).hexdigest(),
          "qa":qa,"topology_pass":passed,"g1":"BLOCKED","g2":"NOT_RUN",
          "g3":"PARTIAL_PASS" if passed else "FAIL","g4":"NOT_RUN",
          "limitations":["PBR not acquired","stone clearances unverified",
          "mesh self-intersection unverified","not a canonical house wall",
          "game-size art QA pending"]}
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
print("AIDAN_FACET_V2_QA="+json.dumps(manifest))
assert passed
