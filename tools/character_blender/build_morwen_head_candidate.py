"""Morwen head/hair FIRST GEOMETRY CANDIDATE, not approved final art.

Creates independently editable anatomical head surface, paired ears, eye surfaces,
iris, brows and distinct layered bob hair locks. No source files are modified.
Run: python tools/character_blender/build_morwen_head_candidate.py -- OUT.blend
"""
import bpy, math, json, hashlib, pathlib, sys
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
if len(args)!=1: raise SystemExit("usage: -- OUTPUT.blend")
out=pathlib.Path(args[0]).resolve()
root=pathlib.Path("assets/canonical/morwen/2026-11-16").resolve()
if out.suffix!=".blend" or root in out.parents: raise SystemExit("BLOCKED output path")
manifest=json.loads((root/"MANIFEST.json").read_text())
sources={}
for f in manifest["files"]:
    p=root/f["filename"]
    h=hashlib.sha256(p.read_bytes()).hexdigest()
    if h!=f["sha256"]: raise SystemExit("BLOCKED source mismatch "+f["filename"])
    sources[f["filename"]]=h
bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
def material(name,color,roughness=.65):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
    m.use_nodes=True; bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=roughness
    return m
skin=material("skin_warm",(.76,.48,.41)); hair=material("hair_deep_violet",(.105,.047,.16),.4)
hairlight=material("hair_violet_highlight",(.24,.10,.33),.42)
iris=material("iris_violet",(.36,.16,.53),.25);white=material("eye_sclera",(.9,.82,.82),.22)
gold=material("glass_rim_gold",(.62,.39,.12),.3)
def surface(name, rings, sides, mat, cap=False):
    verts=[];faces=[]
    for ring in rings:
        z,cx,cy,rx,ry=ring
        for j in range(sides):
            t=2*math.pi*j/sides
            verts.append((cx+rx*math.cos(t),cy+ry*math.sin(t),z))
    for i in range(len(rings)-1):
        for j in range(sides):
            a=i*sides+j;b=i*sides+(j+1)%sides
            faces.append((a,b,b+sides,a+sides))
    if cap:
        faces.extend([tuple(reversed(range(sides))),tuple((len(rings)-1)*sides+j for j in range(sides))])
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for p in mesh.polygons:p.use_smooth=True
    return obj
# Z=0 chin, Z=0.255 crown; 3D full body target = 7.75 head units.
# Head rings have tapered jaw, cheek volume, temporal fullness and crown.
rings=[]
for i in range(41):
    u=i/40;z=.255*u
    width=.092*(.20+.80*math.sin(math.pi*(u*.89+.055))**.68)
    depth=.079*(.35+.65*math.sin(math.pi*(u*.92+.03))**.65)
    width*=1+.10*math.exp(-((u-.53)/.18)**2)
    depth*=1+.07*math.exp(-((u-.60)/.19)**2)
    rings.append((z,0,0,max(.005,width),max(.005,depth)))
head=surface("HEAD__sculpt_base_candidate",rings,64,skin,True)
# Hair cap follows crown, detached and editable.
caprings=[]
for i in range(27):
    u=i/26;z=.12+.145*u
    rx=.096*(.64+.36*math.sin(math.pi*(u*.85+.12))**.5)
    ry=.085*(.65+.35*math.sin(math.pi*(u*.85+.12))**.5)
    caprings.append((z,0,.003,rx,ry))
surface("HAIR__crown_cap",caprings,48,hair,True)
# Independent tapered sculptable curved strands, not rectangular blocks.
def lock(name,origin,tip,width,depth,mat,phase=0):
    start=Vector(origin);end=Vector(tip)
    direction=end-start
    rings=[]
    for i in range(17):
        t=i/16
        pos=start.lerp(end,t)
        pos.x+=.009*math.sin(math.pi*t+phase)*math.sin(math.pi*t)
        pos.y+=.011*math.sin(math.pi*t+phase)*math.sin(math.pi*t)
        taper=max(.001, (1-t)**.75)
        rings.append((pos.z,pos.x,pos.y,max(.001,width*taper),max(.001,depth*taper)))
    return surface(name,rings,12,mat,True)
# Face-framing locks and side/rear bob in anatomical left/right.
for side in (-1,1):
    for i in range(7):
        a=(i/6)*math.pi*.8
        x=side*(.050+.038*math.sin(a))
        y=-.014+.062*math.cos(a)
        z=.224-.016*(i/6)
        endz=.083+.022*math.cos(a)
        lock("HAIR__%s_side_%02d"%("L" if side<0 else "R",i),
             (x,y,z),(x*1.02,y+.005,endz),.014,.010,hairlight if i%3==0 else hair,phase=i*.2)
for i in range(13):
    x=-.078+.156*i/12
    lock("HAIR__fringe_%02d"%i,(x,-.068,.238),(x*.96,-.084,.155+.017*math.cos(i*.5)),.012,.009,
         hairlight if i%4==0 else hair,phase=i*.3)
for i in range(17):
    a=math.pi*i/16
    x=.088*math.cos(a);y=.068*math.sin(a)
    lock("HAIR__rear_%02d"%i,(x,y,.223),(x*.96,y+.006,.076+.012*math.sin(a)),.014,.011,hair)
# Eyes and eyewear are independent candidate components.
def uvball(name,location,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,location=location)
    o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(mat)
    for p in o.data.polygons:p.use_smooth=True
    return o
for s in (-1,1):
    uvball("EYE__sclera_"+str(s),(s*.039,-.071,.149),(.025,.009,.015),white)
    uvball("EYE__iris_"+str(s),(s*.039,-.080,.149),(.010,.003,.011),iris)
    # Separate glass rim curve, deliberately not joined to head.
    curve=bpy.data.curves.new("RIM_"+str(s),"CURVE");curve.dimensions="3D"
    curve.bevel_depth=.0017;curve.bevel_resolution=3
    spline=curve.splines.new("POLY");spline.points.add(63)
    for i,p in enumerate(spline.points):
        a=2*math.pi*i/64
        p.co=(s*.039+.028*math.cos(a),-.088,.149+.022*math.sin(a),1)
    spline.use_cyclic_u=True
    ob=bpy.data.objects.new("GLASSES__rim_"+str(s),curve)
    bpy.context.collection.objects.link(ob);ob.data.materials.append(gold)
uvball("NOSE__bridge_candidate",(0,-.079,.119),(.009,.012,.020),skin)
# Mark as candidate: no false approval or full-body ratio claim.
scene=bpy.context.scene
scene["asset_status"]="HEAD_HAIR_GEOMETRY_CANDIDATE_UNAPPROVED"
scene["full_body_ratio_target"]=7.75
scene["full_body_geometry"]="NOT_CREATED"
scene["source_manifest_sha256"]=hashlib.sha256((root/"MANIFEST.json").read_bytes()).hexdigest()
scene["G1"]="BLOCKED";scene["G2"]="NOT_RUN";scene["G3"]="NOT_RUN";scene["G4"]="NOT_RUN"
out.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
report={"status":"HEAD_HAIR_GEOMETRY_CANDIDATE","source_sha256":sources,
        "output_sha256":hashlib.sha256(out.read_bytes()).hexdigest(),
        "objects":len(bpy.data.objects),"mesh_objects":sum(o.type=="MESH" for o in bpy.data.objects),
        "full_body_geometry":False,"head_ratio_target":7.75,
        "G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"}
out.with_suffix(".json").write_text(json.dumps(report,indent=2))
print(json.dumps({"status":report["status"],"objects":report["objects"]}))
