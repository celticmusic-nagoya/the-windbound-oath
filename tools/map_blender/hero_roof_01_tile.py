"""RILDE-HERO-ROOF-01: original sculpted tile master, close-up QA only.
Blender 4.x compatible; no third-party source geometry.
"""
import bpy, math, random, json, hashlib, os
from pathlib import Path
from mathutils import Vector
random.seed(130113)
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"));out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="CYCLES";scene.cycles.samples=64
scene.cycles.use_denoising=False
bpy.context.view_layer.cycles.use_denoising=False
scene.render.resolution_x=1600;scene.render.resolution_y=1200
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
world=bpy.data.worlds.new("neutral studio world");scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.38,.41,.45,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.35
mat=bpy.data.materials.new("Rilde kiln fired iron-rich weathered terracotta")
mat.diffuse_color=(.20,.065,.035,1);mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links
bsdf=nodes.get("Principled BSDF")
bsdf.inputs["Roughness"].default_value=.91
coord=nodes.new("ShaderNodeTexCoord")
macro=nodes.new("ShaderNodeTexNoise");macro.inputs["Scale"].default_value=4.5
macro.inputs["Detail"].default_value=5.0
micro=nodes.new("ShaderNodeTexNoise");micro.inputs["Scale"].default_value=115.0
micro.inputs["Detail"].default_value=3.0
links.new(coord.outputs["Generated"],macro.inputs["Vector"])
links.new(coord.outputs["Generated"],micro.inputs["Vector"])
ramp=nodes.new("ShaderNodeValToRGB")
ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i,(pos,color) in enumerate([
 (.0,(.075,.026,.019,1)),(.30,(.16,.050,.031,1)),
 (.52,(.28,.095,.048,1)),(.72,(.38,.16,.077,1)),
 (1.0,(.46,.25,.13,1))]):
 element=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos)
 element.position=pos;element.color=color
links.new(macro.outputs["Fac"],ramp.inputs["Fac"])
links.new(ramp.outputs["Color"],bsdf.inputs["Base Color"])
bump=nodes.new("ShaderNodeBump")
bump.inputs["Strength"].default_value=.30
bump.inputs["Distance"].default_value=.012
links.new(micro.outputs["Fac"],bump.inputs["Height"])
links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])

r=34;c=26
# Sculpted curved slate, irregular edge, nonzero thickness and edge bevel.
v=[];faces=[]
for layer in (0,1):
 for iy in range(r+1):
  y=-.78+1.56*iy/r
  for ix in range(c+1):
   x=-.54+1.08*ix/c
   edge=1 if ix in (0,c) or iy in (0,r) else 0
   wav=.012*math.sin(ix*.9+iy*.37)+.008*math.sin(ix*1.9-iy*.71)
   z=.075*math.sin(math.pi*ix/c)+.035*math.sin(math.pi*iy/r)+wav
   z+=.016*math.sin(iy*.21+ix*.5)
   z-=layer*(.047+.007*math.sin(ix*.2+iy*.4))
   if edge: z+=.003*math.sin(iy*1.7+ix*1.1)
   v.append((x,y,z))
stride=c+1;offset=(r+1)*stride
for iy in range(r):
 for ix in range(c):
  a=iy*stride+ix
  faces.append((a,a+1,a+1+stride,a+stride))
  b=offset+a
  faces.append((b+stride,b+1+stride,b+1,b))
for ix in range(c):
 faces.extend([(ix,offset+ix,offset+ix+1,ix+1),
               (r*stride+ix,r*stride+ix+1,offset+r*stride+ix+1,offset+r*stride+ix)])
for iy in range(r):
 a=iy*stride;z=iy*stride+c
 faces.extend([(a,a+stride,offset+a+stride,offset+a),
               (z,offset+z,offset+z+stride,z+stride)])
mesh=bpy.data.meshes.new("hand sculpted tile master");mesh.from_pydata(v,[],faces);mesh.update()
obj=bpy.data.objects.new("ROOF_TILE_MASTER_high",mesh);bpy.context.collection.objects.link(obj)
mesh.materials.append(mat)
bevel=obj.modifiers.new("real bevel at chipped edges","BEVEL");bevel.width=.008;bevel.segments=3
# Keep native mesh normals: Blender 4.0 runner lacks the legacy Auto Smooth prerequisite.
# Tiny chipped corners via deterministic boundary vertex perturbation, not a duplicated model.
for vertex in mesh.vertices:
 x,y,z=vertex.co
 if abs(x)>.51 and y<-.65:
  vertex.co.x-=math.copysign(.022*(1+math.sin(y*30)),x)
# Camera for a single component, not an assembled cottage.
bpy.ops.object.camera_add(location=(2.1,-2.4,2.2));cam=bpy.context.object
cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
cam.data.type="ORTHO";cam.data.ortho_scale=2.4;scene.camera=cam
for loc,power,size in [((-2,-1,4),420,3),((2,2,3),250,2.5)]:
 bpy.ops.object.light_add(type="AREA",location=loc);light=bpy.context.object
 light.data.energy=power;light.data.shape="DISK";light.data.size=size
 light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat("-Z","Y").to_euler()
scene.render.filepath=str(out/"roof_tile_hero_closeup.png");bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/"roof_tile_hero.blend"))
files=["roof_tile_hero_closeup.png","roof_tile_hero.blend"]
report={"task":"RILDE-HERO-ROOF-01","source":"original procedural sculpt","master_status":"CANDIDATE_NOT_CANON","render_qa":"NOT_RUN","tile_size_m":[1.08,1.56],"tile_thickness_m":.047,"seed":130113,"files":{p:hashlib.sha256((out/p).read_bytes()).hexdigest() for p in files}}
(out/"roof_tile_hero_manifest.json").write_text(json.dumps(report,indent=2))
print("RILDE-HERO-ROOF-01 tile candidate generated")
