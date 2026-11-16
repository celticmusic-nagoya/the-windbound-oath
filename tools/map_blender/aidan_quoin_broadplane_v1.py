"""Candidate-only broad-plane dressed quoin study. Blender 4.x headless.
Run: blender -b -t 2 --python tools/map_blender/aidan_quoin_broadplane_v1.py
No downloads or changes to canonical assets. Output directory is controlled by env.
"""
import bpy, bmesh, json, hashlib, os, random
from pathlib import Path
from mathutils import Vector
SEED=20261116
OUT=Path(os.environ.get("AIDAN_QUOIN_BROADPLANE_OUT","/tmp/aidan-quoin-broadplane-v1"))
OUT.mkdir(parents=True,exist_ok=True)
rng=random.Random(SEED)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def mat(name,rgba):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgba,1);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*rgba,1)
    bs.inputs["Roughness"].default_value=.94
    return m
stone=mat("PROCEDURAL PLACEHOLDER NOT PBR",(0.49,.47,.40))
mortar=mat("mortar",(0.52,.50,.46))

def stone_mesh(name, origin=(0,0,0),scale=1):
    """Closed irregular L-plan with broad outer-face relief; protected inner seating."""
    # Polygon CCW, 0.40 x 0.46m corner; inner step remains stable.
    plan=[(-.40,-.20),(.00,-.20),(.00,.26),(-.24,.26),(-.24,.04),(-.40,.04)]
    # Asymmetric mid-height rings: 4 slices; perimeter vertices vary coherently,
    # with larger offsets only on exposed front and right outer edges.
    levels=[0,.045,.155,.245,.265]
    rings=[]
    for k,z in enumerate(levels):
        pts=[]
        for i,(x,y) in enumerate(plan):
            # Outer front and return faces get a few broad irregular planes.
            # Inner bond surfaces (x=-.24,y=.04) are left unchanged.
            if i in (0,1,2):
                face_shift=[.007,-.010,.018,-.013,.006][k]
                x+= (face_shift*.55 if i==2 else 0)
                y+=face_shift if i in (0,1) else 0
            if i==3: x+= [.003,0,-.007,.002,.001][k]
            pts.append((x*scale+origin[0],y*scale+origin[1],z*scale+origin[2]))
        rings.append(pts)
    n=len(plan);verts=[v for ring in rings for v in ring]
    faces=[tuple(reversed(range(n))),tuple((len(levels)-1)*n+i for i in range(n))]
    for j in range(len(levels)-1):
        for i in range(n):
            a=j*n+i;b=j*n+(i+1)%n
            faces.append((a,b,b+n,a+n))
    mesh=bpy.data.meshes.new(name+"_mesh");mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(stone)
    return obj

objects=[stone_mesh("QUOIN_BROAD_PLANE_CANDIDATE")]
# Second course shifted for visibility; this is a comparison fixture, not a house dimension.
objects.append(stone_mesh("QUOIN_COURSE_2_CANDIDATE",(.06,.0,.283)))
bpy.ops.mesh.primitive_cube_add(size=1,location=(-.7,-.075,.265))
back=bpy.context.object;back.name="MORTAR_BACKING_FIXTURE"
back.dimensions=(.65,.18,.52);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
back.data.materials.append(mortar)

qa=[]
for obj in objects:
    bm=bmesh.new()
    try:
        bm.from_mesh(obj.data)
        boundary=sum(e.is_boundary for e in bm.edges)
        nonmanifold=sum(not e.is_manifold for e in bm.edges)
        volume=bm.calc_volume(signed=True)
        # All vertices connected, including mid-height rings.
        unseen=set(bm.verts);components=0
        while unseen:
            components+=1;stack=[unseen.pop()]
            while stack:
                v=stack.pop()
                for e in v.link_edges:
                    other=e.other_vert(v)
                    if other in unseen:unseen.remove(other);stack.append(other)
        qa.append(dict(name=obj.name,vertices=len(bm.verts),faces=len(bm.faces),
                       boundary_edges=boundary,nonmanifold_edges=nonmanifold,
                       components=components,signed_volume=round(volume,8)))
    finally:bm.free()
passed=all(x["boundary_edges"]==0 and x["nonmanifold_edges"]==0 and
           x["components"]==1 and x["signed_volume"]>0 for x in qa)
world=bpy.context.scene.world or bpy.data.worlds.new("neutral")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.7
for xyz,energy in [((-3,-4,5),750),((4,2,3),500)]:
    bpy.ops.object.light_add(type="AREA",location=xyz)
    bpy.context.object.data.energy=energy;bpy.context.object.data.size=3
bpy.ops.object.camera_add(location=(1.5,-2.5,1.5))
cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=1.8
cam.rotation_euler=(Vector((-.3,0,.25))-cam.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=960;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
png=OUT/"quoin_broadplane_v1.png";scene.render.filepath=str(png)
bpy.ops.render.render(write_still=True)
manifest={"status":"CANDIDATE_ONLY_NOT_ART_APPROVED","seed":SEED,
          "blender":bpy.app.version_string,"material":"PROCEDURAL_PLACEHOLDER_NOT_PBR",
          "image":png.name,"image_sha256":hashlib.sha256(png.read_bytes()).hexdigest(),
          "geometry_qa":qa,"topology_pass":passed,
          "g1":"BLOCKED","g2":"NOT_RUN","g3":"PARTIAL_PASS" if passed else "FAIL",
          "g4":"NOT_RUN","limitations":["no licensed PBR texture","no overlap or clearance QA",
          "no evaluated self-intersection test","not compared to official dimensions",
          "no game-size render"]}
(OUT/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print("AIDAN_QUOIN_BROADPLANE_QA="+json.dumps(manifest))
assert passed,"candidate geometry topology check failed"
