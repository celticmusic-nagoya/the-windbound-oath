"""MORWEN-PRODUCTION-07: create deformation-oriented continuous torso mesh candidate.
Requires production-06 reference kit extracted; does NOT replace approved art.
Run blender -b --python tools/blender/production_mesh_07/build.py -- --root /path/to/kit
"""
import bpy,sys,argparse,json,hashlib,math
from pathlib import Path
from mathutils import Vector
p=argparse.ArgumentParser();p.add_argument("--root",required=True);a=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
root=Path(a.root);manifest=json.loads((root/"reference_manifest.json").read_text())
for e in manifest["references"]:
    f=root/"references"/e["filename"]
    if not f.exists() or hashlib.sha256(f.read_bytes()).hexdigest()!=e["sha256"]:
        raise RuntimeError("CANON_HASH_MISMATCH:"+e["filename"])
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
def mat(name,color,rough=.75):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF");bs.inputs["Base Color"].default_value=(*color,1);bs.inputs["Roughness"].default_value=rough
    return m
skin=mat("SKIN_CANDIDATE",(.78,.57,.53));hair=mat("HAIR_PURPLE_CANDIDATE",(.20,.095,.27))
# Each ring is a 16-vertex cross section, connected by quad strips.
# Unlike independent spheres/cones this produces explicit, editable edge loops.
def loft(name,rings,material,n=16):
    verts=[];faces=[]
    for cx,cy,cz,rx,ry in rings:
        for j in range(n):
            t=2*math.pi*j/n
            verts.append((cx+rx*math.cos(t),cy+ry*math.sin(t),cz))
    for k in range(len(rings)-1):
        for j in range(n):
            a=k*n+j;b=k*n+(j+1)%n
            faces.append((a,b,b+n,a+n))
    faces.append(tuple(reversed(tuple(range(n)))))
    faces.append(tuple((len(rings)-1)*n+j for j in range(n)))
    mesh=bpy.data.meshes.new(name+"_mesh");mesh.from_pydata(verts,[],faces);mesh.update()
    ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob)
    ob.data.materials.append(material)
    for poly in mesh.polygons:poly.use_smooth=True
    return ob
# Height 1.63m is approximate, footwear-inclusive. These are CANDIDATE proportions.
torso=loft("BODY_TORSO_CONTINUOUS_CANDIDATE",[
(0,0,.77,.115,.085),(0,0,.84,.145,.102),(0,0,.91,.13,.085),
(0,0,1.00,.105,.078),(0,0,1.07,.112,.083),
(0,0,1.15,.15,.098),(0,0,1.22,.17,.094),
(0,0,1.29,.15,.083),(0,0,1.34,.095,.075),
(0,0,1.38,.056,.056)],skin)
# Separate manifold limb surfaces are deformable, with multiple loops at joints.
# Shoulder/hip integration and weight painting remain an explicit BLOCKER.
for side in (-1,1):
    tag="L" if side==1 else "R"
    loft("ARM_"+tag+"_DEFORMATION_LOOPS",[
    (side*.17,0,1.285,.067,.067),(side*.20,0,1.22,.064,.061),
    (side*.225,0,1.12,.052,.049),(side*.245,0,1.05,.045,.045),
    (side*.255,0,1.02,.047,.047),(side*.265,0,.99,.044,.043),
    (side*.28,0,.89,.038,.037),(side*.29,0,.83,.031,.031),
    (side*.29,0,.80,.034,.034)],skin)
    loft("LEG_"+tag+"_DEFORMATION_LOOPS",[
    (side*.085,0,.80,.079,.078),(side*.087,0,.73,.085,.083),
    (side*.09,0,.63,.079,.076),(side*.095,0,.53,.065,.064),
    (side*.098,0,.47,.057,.056),(side*.098,0,.44,.057,.057),
    (side*.10,0,.40,.059,.059),(side*.10,0,.30,.057,.056),
    (side*.10,0,.19,.043,.044),(side*.10,0,.105,.035,.036)],skin)
loft("NECK_CANDIDATE",[(0,0,1.35,.052,.049),(0,0,1.42,.052,.048)],skin)
loft("HEAD_CRANIUM_CANDIDATE",[
(0,-.01,1.41,.07,.07),(0,-.01,1.46,.095,.085),
(0,-.005,1.51,.105,.09),(0,0,1.56,.108,.091),
(0,0,1.61,.086,.08),(0,0,1.635,.045,.045)],skin)
# QA cameras: render geometry only, never source art composited into result.
world=bpy.context.scene.world;world.color=(.12,.12,.12)
for name,location in {"front":(0,-3,.82),"right":(-3,0,.82),"back":(0,3,.82),"left":(3,0,.82)}.items():
    data=bpy.data.cameras.new("ORTHO_"+name);ob=bpy.data.objects.new("ORTHO_"+name,data)
    bpy.context.collection.objects.link(ob);ob.location=location
    ob.rotation_euler=(Vector((0,0,.82))-ob.location).to_track_quat("-Z","Y").to_euler()
    data.type="ORTHO";data.ortho_scale=1.9
scene=bpy.context.scene;scene.render.resolution_x=512;scene.render.resolution_y=768
scene.render.resolution_percentage=100;scene.render.film_transparent=True
scene.render.image_settings.file_format="PNG";scene.render.image_settings.color_mode="RGBA"
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
out=root/"output"/"production_07";out.mkdir(parents=True,exist_ok=True)
for view in ("front","right","back","left"):
    scene.camera=bpy.data.objects["ORTHO_"+view]
    scene.render.filepath=str(out/("morwen_topology_candidate_"+view+".png"))
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"MORWEN_PRODUCTION_07_TOPOLOGY_CANDIDATE.blend"))
report={"reference_hashes":"PASS","topology":"MULTI_LOOP_QUAD_CANDIDATE","connected_full_body":"NO","source_art_comparison":"NOT_RUN","face_hair_costume":"NOT_BUILT","art_qa":"NOT_RUN","promotion_eligible":False}
(out/"QA.json").write_text(json.dumps(report,indent=2)+"\n")
print("MORWEN_PRODUCTION_07_TECHNICAL_CANDIDATE")
