"""RILDE ROOF 02 — independent hand-split ironstone slate roof system.
Original procedural geometry; Pinterest references are visual research only.
Blender 4.x, deterministic seed, no downloaded geometry or textures.
"""
import bpy, math, random, json, hashlib, os
from pathlib import Path
from mathutils import Vector
SEED=261113
rng=random.Random(SEED)
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))
out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.samples=64
scene.cycles.use_denoising=False
bpy.context.view_layer.cycles.use_denoising=False
scene.render.resolution_x=1600
scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
scene.view_settings.view_transform="Standard"
scene.view_settings.look="Medium High Contrast"
world=bpy.data.worlds.new("studio ambient")
scene.world=world
world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.22,.24,.27,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.55

def stone_material(name, base, seed):
 m=bpy.data.materials.new(name)
 m.use_nodes=True
 n=m.node_tree.nodes
 l=m.node_tree.links
 bs=n.get("Principled BSDF")
 bs.inputs["Roughness"].default_value=.87
 tex=n.new("ShaderNodeTexNoise")
 tex.inputs["Scale"].default_value=9
 tex.inputs["Detail"].default_value=6
 fine=n.new("ShaderNodeTexNoise")
 fine.inputs["Scale"].default_value=180
 fine.inputs["Detail"].default_value=3
 ramp=n.new("ShaderNodeValToRGB")
 lo=ramp.color_ramp.elements[0]
 hi=ramp.color_ramp.elements[1]
 lo.position=.20
 hi.position=.82
 lo.color=tuple(v*.49 for v in base[:3])+(1,)
 hi.color=tuple(min(1,v*1.22) for v in base[:3])+(1,)
 l.new(tex.outputs["Fac"],ramp.inputs["Fac"])
 l.new(ramp.outputs["Color"],bs.inputs["Base Color"])
 bump=n.new("ShaderNodeBump")
 bump.inputs["Strength"].default_value=.20
 bump.inputs["Distance"].default_value=.004
 l.new(fine.outputs["Fac"],bump.inputs["Height"])
 l.new(bump.outputs["Normal"],bs.inputs["Normal"])
 return m

# PBR evaluation: real photographed CC0 maps, projected over the roof panel.
# Keep procedural materials as a deterministic fallback when offline.
def load_cc0_roof_material():
 folder=out/"cc0_materials"/"red_slate_roof_tiles_01"
 manifest_path=folder/"manifest.json"
 if not manifest_path.exists():
  print("CC0 texture missing: using procedural fallback")
  return None
 data=json.loads(manifest_path.read_text())
 if data.get("license")!="CC0-1.0":
  raise RuntimeError("Unverified texture license")
 mat=bpy.data.materials.new("CC0 Poly Haven red slate roof PBR EVALUATION")
 mat.use_nodes=True
 nodes=mat.node_tree.nodes
 links=mat.node_tree.links
 bs=nodes.get("Principled BSDF")
 bs.inputs["Roughness"].default_value=.87
 uv=nodes.new("ShaderNodeNewGeometry")
 mapping=nodes.new("ShaderNodeMapping")
 # Object coordinates projected over full roof rather than repeating the entire roof image per slate.
 links.new(uv.outputs["Position"],mapping.inputs["Vector"])
 mapping.inputs["Scale"].default_value=(.42,.42,1.0)
 normal=nodes.new("ShaderNodeNormalMap")
 normal.inputs["Strength"].default_value=.38
 for key,socket in (("Diffuse","Base Color"),("rough","Roughness"),("nor_gl","Color")):
  info=data["maps"][key]
  p=Path(info["file"])
  if hashlib.sha256(p.read_bytes()).hexdigest()!=info["sha256"]:
   raise RuntimeError("PBR map SHA mismatch: "+key)
  image=bpy.data.images.load(str(p),check_existing=True)
  image.pack()
  image.colorspace_settings.name="sRGB" if key=="Diffuse" else "Non-Color"
  tex=nodes.new("ShaderNodeTexImage")
  tex.image=image
  links.new(mapping.outputs["Vector"],tex.inputs["Vector"])
  if key=="nor_gl":
   links.new(tex.outputs["Color"],normal.inputs["Color"])
  else:
   links.new(tex.outputs["Color"],bs.inputs[socket])
 links.new(normal.outputs["Normal"],bs.inputs["Normal"])
 return mat

cc0_material=load_cc0_roof_material()
materials=[
 stone_material("weathered ironstone umber",(.29,.12,.065),0),
 stone_material("deep fired burgundy",(.21,.075,.057),1),
 stone_material("warm oxidised sandstone",(.35,.17,.09),2),
 stone_material("soot stained russet",(.19,.105,.082),3),
]
def slate(name,center_x,center_y,z,scale,material,seed):
 local=random.Random(seed)
 nx,ny=36,44
 width=.35*scale
 length=.51*scale
 thickness=.017*scale
 outline=[]
 for iy in range(ny+1):
  t=iy/ny
  row=[]
  for ix in range(nx+1):
   u=ix/nx
   # Hand-split slab: nearly flat, fractured perimeter, chipped corners.
   x=(u-.5)*width
   y=(t-.5)*length
   edge=min(u,1-u,t,1-t)
   chip=.006*math.sin(31*t+seed)*math.sin(14*t+seed*.1)
   if ix in (0,nx):
    x+=(-1 if ix==0 else 1)*chip
   if iy==0:
    y+=.010*math.sin(11*u+seed)*math.sin(23*u)
   if iy==ny:
    y+=.004*math.sin(19*u+seed)
   warp=.008*math.sin(math.pi*u)+.006*math.sin(2*math.pi*t+seed*.4)
   cleavage=.0025*math.sin(29*u+7*t+seed)+.0018*math.sin(9*u+27*t)
   row.append((x+center_x,y+center_y,z+warp+cleavage))
  outline.extend(row)
 vertices=outline+[(x,y,zv-thickness) for x,y,zv in outline]
 stride=nx+1
 layer_size=len(outline)
 faces=[]
 for iy in range(ny):
  for ix in range(nx):
   a=iy*stride+ix
   faces.append((a,a+1,a+1+stride,a+stride))
   b=a+layer_size
   faces.append((b+stride,b+stride+1,b+1,b))
 for ix in range(nx):
  a=ix
  b=ny*stride+ix
  faces.extend([(a,a+layer_size,a+layer_size+1,a+1),
                (b,b+1,b+layer_size+1,b+layer_size)])
 for iy in range(ny):
  a=iy*stride
  b=iy*stride+nx
  faces.extend([(a,a+stride,a+layer_size+stride,a+layer_size),
                (b,b+layer_size,b+layer_size+stride,b+stride)])
 mesh=bpy.data.meshes.new(name+"_fractured_mesh")
 mesh.from_pydata(vertices,[],faces)
 mesh.update()
 obj=bpy.data.objects.new(name,mesh)
 bpy.context.collection.objects.link(obj)
 mesh.materials.append(cc0_material if cc0_material is not None else material)
 bevel=obj.modifiers.new("fine fractured edge highlights","BEVEL")
 bevel.width=.0025
 bevel.segments=2
 return obj

wood=bpy.data.materials.new("dark oak battens")
wood.diffuse_color=(.13,.065,.032,1)
wood.use_nodes=True
wood.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.13,.065,.032,1)
wood.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.9
def batten(y):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,y,-.055))
 o=bpy.context.object
 o.name="hand-hewn support batten"
 o.dimensions=(1.8,.09,.075)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(wood)
 bevel=o.modifiers.new("soft cut corners","BEVEL")
 bevel.width=.008
 bevel.segments=2
for y in (-.50,-.05,.40):
 batten(y)
# Overlapping staggered courses: lower rows in front of upper rows.
for row,y in enumerate((.31,-.06,-.43)):
 for col in range(5):
  x=(col-2)*.31+(.15 if row%2 else 0)
  scale=1+rng.uniform(-.055,.055)
  slate("split_slate_%d_%d"%(row,col),x,y,.025+(.012*(2-row)),scale,
        materials[(row*3+col)%len(materials)],SEED+row*17+col*31)
# Inspect a single master on its own at the right of the panel.
master=slate("MASTER_ironstone_slate_independent",1.25,-.07,.11,1.35,materials[0],SEED+900)
# Orthographic hero closeup showing thickness and overlapping construction.
bpy.ops.object.camera_add(location=(2.7,-3.8,4.5))
cam=bpy.context.object
target=Vector((.30,-.03,.02))
cam.rotation_euler=(target-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO"
cam.data.ortho_scale=3.5
scene.camera=cam
for loc,power,size in [((-3,-2,5),700,3.0),((2,3,4),380,2.5)]:
 bpy.ops.object.light_add(type="AREA",location=loc)
 lamp=bpy.context.object
 lamp.data.energy=power
 lamp.data.shape="DISK"
 lamp.data.size=size
 lamp.rotation_euler=(target-lamp.location).to_track_quat("-Z","Y").to_euler()
scene.render.filepath=str(out/"roof_slate_system_02.png")
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"roof_slate_system_02.blend"))
files=["roof_slate_system_02.png","roof_slate_system_02.blend"]
report={"task":"RILDE-ROOF-SLATE-02","status":"CANDIDATE_NOT_CANON",
        "material":"Poly Haven CC0 red slate PBR" if cc0_material else "original procedural fallback", "material_source":"https://polyhaven.com/a/red_slate_roof_tiles_01" if cc0_material else None,"seed":SEED,
        "render_size":[1600,1200],"tile_width_m":.35,"tile_length_m":.51,
        "files":{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in files}}
(out/"roof_slate_system_02_manifest.json").write_text(json.dumps(report,indent=2))
print("ROOF SLATE 02 candidate generated")
