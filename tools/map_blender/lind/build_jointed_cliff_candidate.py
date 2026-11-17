"""LIND cliff study: authored non-periodic joint-constrained cliff face.

Distinct from stopped smooth-heightfield / horizontal rock-band approach.
Candidate-only local-space cliff segment; no canonical metric scale or placement.
Blender: blender -b --factory-startup --disable-autoexec --python-exit-code 1 --python this.py -- --out /tmp/lind-cliff
"""
import bpy, math, random, hashlib, json, sys
from pathlib import Path
from mathutils import Vector

def args_out():
    if "--" not in sys.argv: return Path("/tmp/lind-cliff")
    a=sys.argv[sys.argv.index("--")+1:]
    if len(a)!=2 or a[0]!="--out": raise ValueError("expected -- --out DIR")
    return Path(a[1]).resolve()

out=args_out()
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
seed=170117
rng=random.Random(seed)
col=bpy.data.collections.new("LIND_TERRAIN_CLIFF_CANDIDATE")
bpy.context.scene.collection.children.link(col)

# Explicit nonuniform geological joint paths, each authored from distinct endpoints
# and irregular kinks; not regular horizontal strata or stacked cuboids.
joint_specs=[
 (-4.9,-2.7,-4.1,3.3),(-2.7,-3.2,-3.0,3.2),(-0.9,-3.1,-0.2,3.3),
 (1.7,-3.3,1.0,3.2),(3.9,-3.1,4.6,3.4)
]
joint_lines=[]
for xa,za,xb,zb in joint_specs:
    kink=rng.uniform(-0.7,0.7)
    joint_lines.append([(xa,za),(xa+kink,0.2),(xb,zb)])
def joint_x(line,z):
    if z<=line[1][1]:
        a,b=line[0],line[1]
    else:
        a,b=line[1],line[2]
    t=(z-a[1])/(b[1]-a[1])
    return a[0]+t*(b[0]-a[0])

nx,nz=90,48
xmin,xmax=-6.0,6.0
zmin,zmax=-3.2,3.2
verts=[]
for iz in range(nz+1):
    z=zmin+(zmax-zmin)*iz/nz
    for ix in range(nx+1):
        x=xmin+(xmax-xmin)*ix/nx
        # cliff face Y: large-scale fractured mass, not repeating material bands
        macro=0.24*math.sin(x*0.51+z*0.38)+0.17*math.cos(x*0.33-z*0.79)
        face=0.09*math.sin(x*2.9+z*1.3)+0.045*math.cos(x*5.2-z*3.7)
        crack=0.0
        for line in joint_lines:
            dx=abs(x-joint_x(line,z))
            if dx<0.14:
                crack-=0.20*(1-dx/0.14)**2
        # irregular weathered ledges controlled by local fracture intersection
        shelf=0.07*math.sin(1.6*x+1.3*z+0.7*math.sin(0.6*x))
        y=macro+face+crack+shelf
        verts.append((x,y,z))
faces=[]
for iz in range(nz):
    for ix in range(nx):
        i=iz*(nx+1)+ix
        # non-axis-aligned triangulation, alternating to prevent directional artifacts
        if (ix*17+iz*11)%3:
            faces.extend([(i,i+1,i+nx+2),(i,i+nx+2,i+nx+1)])
        else:
            faces.extend([(i,i+1,i+nx+1),(i+1,i+nx+2,i+nx+1)])
mesh=bpy.data.meshes.new("jointed_cliff_surface_mesh")
mesh.from_pydata(verts,[],faces)
mesh.update()
obj=bpy.data.objects.new("JointedCliff_Face_CANDIDATE",mesh)
col.objects.link(obj)
for p in mesh.polygons:p.use_smooth=False

# Ground/turf cap: independent sculpt mass, not final seam solution.
capverts=[(-6,-0.2,3.2),(6,-0.2,3.2),(6,3.0,3.5),(-6,3.0,3.5)]
capmesh=bpy.data.meshes.new("turf_cap_study")
capmesh.from_pydata(capverts,[],[(0,1,2,3)])
capmesh.update()
cap=bpy.data.objects.new("TurfCap_CANDIDATE",capmesh)
col.objects.link(cap)
def mat(name,rgb,rough):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*rgb,1)
    bs.inputs["Roughness"].default_value=rough
    return m
obj.data.materials.append(mat("neutral_clay_rock",(0.48,0.46,0.43),0.91))
cap.data.materials.append(mat("neutral_clay_ground",(0.40,0.42,0.37),0.93))
# Three fixed cameras. Geometry remains unplaced in official world.
world=bpy.context.scene.world
world.color=(0.6,0.6,0.6)
def camera(name,loc,target):
    data=bpy.data.cameras.new(name)
    cam=bpy.data.objects.new(name,data)
    col.objects.link(cam)
    cam.location=loc
    direction=Vector(target)-cam.location
    cam.rotation_euler=direction.to_track_quat("-Z","Y").to_euler()
    data.type="ORTHO"
    data.ortho_scale=15
    return cam
cams=[
 camera("clay_front",(0,-17,2),(0,0,0)),
 camera("clay_threequarter",(12,-15,7),(0,0,0)),
 camera("clay_raking",(-11,-8,4),(0,0,0))]
ld=bpy.data.lights.new("softbox","AREA")
lo=bpy.data.objects.new("softbox",ld)
col.objects.link(lo)
lo.location=(-3,-7,11)
ld.energy=1800
ld.shape="DISK"
ld.size=9
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=16
# Ubuntu packaged Blender may be built without OpenImageDenoiser.
# Disable compositor/view-layer denoising to keep CPU clay renders portable.
scene.cycles.use_denoising=False
for layer in scene.view_layers:
    layer.cycles.use_denoising=False
scene.render.resolution_x=960
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.render.film_transparent=False
scene.camera=cams[0]
blend=out/"cliff_candidate.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
for cam in cams:
    scene.camera=cam
    scene.render.filepath=str(out/(cam.name+".png"))
    bpy.ops.render.render(write_still=True)
files=[blend]+[out/(c.name+".png") for c in cams]
report={
 "asset_status":"candidate","method_family":"joint-constrained authored cross-section surface",
 "seed":seed,"blender_version":bpy.app.version_string,
 "geometry":{"vertices":len(mesh.vertices),"triangles":len(mesh.polygons),"note":"open cliff study face, not manifold solid or approved full terrain"},
 "camera_names":[c.name for c in cams],
 "world_transform":None,"bounding_box_m":None,
 "source_image_sha256":"abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620",
 "qa":{"G1":"BLOCKED","G2":"NOT_RUN","G3":"PARTIAL_RENDER_ONLY","G4":"NOT_RUN"},
 "output_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"result":"candidate_rendered_not_art_approved","out":str(out),"files":list(report["output_sha256"])},indent=2))
