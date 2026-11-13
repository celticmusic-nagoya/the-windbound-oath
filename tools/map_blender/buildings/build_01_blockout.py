"""MAP-BUILDING-01: isolated modular cottage blockout, not official art.
blender -b --python tools/map_blender/buildings/build_01_blockout.py
"""
import bpy,json,os,hashlib,math
from pathlib import Path
from mathutils import Vector
HERE=Path(__file__).resolve().parent
spec=json.loads((HERE/"aidan_home_candidate.json").read_text(encoding="utf-8"))
out=Path(os.environ.get("MAP_OUTPUT","/tmp/map-preview"))/"building_01";out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action="SELECT");bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene;scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version >= (4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
collections={}
for layer in spec["layers"]:
 c=bpy.data.collections.new(layer["collection"]);scene.collection.children.link(c);collections[layer["id"]]=c
def material(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(*c,1);m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.87;return m
wood=material("provisional timber",(.30,.20,.13));plaster=material("provisional plaster",(.70,.62,.49))
roof=material("weathered red-brown roof",(.44,.20,.12));roof_light=material("aged clay roof tile",(.57,.29,.17));roof_dark=material("mossy roof tile",(.31,.16,.12));wood_light=material("aged light timber",(.45,.31,.20));glass=material("blue-green glass",(.21,.36,.38));grass=material("soft meadow grass",(.30,.43,.23));floor=material("provisional floor",(.48,.35,.23));stone=material("provisional stone",(.43,.44,.41))
def block(n,loc,dims,mat,layer):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.dimensions=dims
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mat)
 for c in list(o.users_collection):c.objects.unlink(o)
 collections[layer].objects.link(o);return o
w=spec["dimensions"]["width"];d=spec["dimensions"]["depth"];h=spec["dimensions"]["wall_height"];ridge=spec["dimensions"]["roof_ridge_height"]
block("foundation",(0,0,-.18),(w+.3,d+.3,.35),stone,"L0")
block("floor",(0,0,.02),(w,d,.12),floor,"L0")
# Perimeter posts and ring beams; front opening is genuinely open in the mesh.
for x in (-w/2+.12,w/2-.12):
 for y in (-d/2+.12,d/2-.12):block("post",(x,y,h/2),(.22,.22,h),wood,"L1")
for y in (-d/2+.1,d/2-.1):block("ring beam",(0,y,h-.12),(w,.22,.22),wood,"L1")
for x in (-w/2+.1,w/2-.1):block("side beam",(x,0,h-.12),(.22,d,.22),wood,"L1")
block("rear wall",(0,d/2-.12,h/2),(w-.3,.18,h-.2),plaster,"L1")
for x in (-w/2+.12,w/2-.12):block("side wall",(x,0,h/2),(.16,d-.3,h-.2),plaster,"L1")
door=spec["openings"][0];win_l,win_r=spec["openings"][1:]
front_y=-d/2+.12
# Front wall segmentation preserves door and window openings without boolean operations.
def wall_segment(x0,x1,z0,z1,name):
 if x1-x0>.01 and z1-z0>.01:block(name,((x0+x1)/2,front_y,(z0+z1)/2),(x1-x0,.16,z1-z0),plaster,"L1")
features=[(-w/2,-2.2),(-1.4,-.575),(.575,1.4),(2.2,w/2)]
for i,(a,b) in enumerate(features):wall_segment(a,b,0,h,"front solid "+str(i))
for i,window in enumerate((win_l,win_r)):
 x=window["center_x"];a=x-window["width"]/2;b=x+window["width"]/2
 # Wall between door and windows intentionally remains separated.
 wall_segment(a,b,0,1.15,"window sill "+str(i));wall_segment(a,b,2.15,h,"window lintel "+str(i))
wall_segment(-.575,.575,door["height"],h,"door lintel")
# Simple roof slopes; no roof meshes visible in indoor view.
for sign in (-1,1):
 o=block("roof half "+str(sign),(0,sign*d*.24,(h+ridge)/2+.2),(w+.5,d*.57,.18),roof,"L2")
 o.rotation_euler[0]=sign*math.atan2(ridge-h,d/2)
# Authored reusable detail modules; dimensions remain candidate pending art QA.
def trim(n,x,y,z,dx,dy,dz,mat=wood):return block(n,(x,y,z),(dx,dy,dz),mat,"L2")
# Exposed timber bracing and front facade: avoid hiding genuine window apertures.
for x in (-w/2+.14,w/2-.14):
 for y in (-d/2+.14,d/2-.14):trim("corner post",(x,y,1.55),.20,.20,3.12)
for x in (-2.5,2.5):
 trim("front vertical timber",(x,-d/2-.01,1.5),.14,.16,2.8)
trim("front horizontal beam",(0,-d/2-.04,2.62),w,.16,.14,wood_light)
# Tile courses conform to existing sloping roof planes.
slope=math.atan2(ridge-h,d/2)
for sign in (-1,1):
 for i in range(10):
  for j in range(5):
   yy=sign*(.25+j*.47)
   zz=h+(ridge-h)*(1-abs(yy)/(d/2))+.18
   tile=block("roof tile",(-w/2+.35+i*.59,yy,zz),(.57,.48,.06),roof_light if (i+j)%4 else roof_dark,"L2")
   tile.rotation_euler.x=sign*slope
# Chimney, door and window frames are coherent with the interior opening positions.
trim("stone chimney",w*.27,d*.18,ridge+.22,.58,.65,1.22,stone)
trim("chimney cap",w*.27,d*.18,ridge+.87,.76,.79,.13,stone)
trim("oak door leaf",0,-d/2-.03,door["height"]/2,door["width"]-.10,.10,door["height"]-.06,wood_light)
for win in (win_l,win_r):
 x=win["center_x"];wy=-d/2-.035
 trim("window lower frame",x,wy,1.17,win["width"]+.12,.14,.12)
 trim("window upper frame",x,wy,2.15,win["width"]+.12,.14,.12)
 for side in (-1,1):trim("window side frame",x+side*(win["width"]/2+.035),wy,1.66,.11,.14,1.04)
 trim("window glass",x,wy,1.66,win["width"]-.10,.04,.82,glass)
 trim("window mullion",x,wy-.08,1.66,.07,.08,.9)
# Garden, firewood, stone doorstep, ground for exterior only.
block("front stone doorstep",(0,-d/2-.85,.07),(1.7,.7,.17),stone,"L2")
for i in range(7):
 trim("stacked firewood",-w/2-.45+i*.14,d/2-.35,.22,.12,.9,.17,wood_light)
for i in range(18):
 xx=-w/2-.7+(i%9)*.42;yy=-d/2-1.25+(i//9)*.33
 trim("garden grasses",xx,yy,.13,.13,.13,.27,grass)
# Interior is deliberately empty until approved CG defines furniture locations.
block("interior placeholder hearth footprint",(0,d/2-.6,.09),(1.0,.6,.08),stone,"L3")
bpy.ops.object.camera_add(location=(10,-13,9));cam=bpy.context.object;scene.camera=cam
cam.rotation_euler=(Vector((0,0,1.5))-cam.location).to_track_quat("-Z","Y").to_euler();cam.data.type="ORTHO";cam.data.ortho_scale=11.8
bpy.ops.object.light_add(type="SUN",location=(-4,-6,9));bpy.context.object.data.energy=2.2
files={}
for mode in ("outside","inside"):
 for layer,c in collections.items():c.hide_render=layer not in spec["render_modes"][mode]
 p=out/("aidan_home_"+mode+"_candidate.png");scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 files[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
for c in collections.values():c.hide_render=False
blend=out/"aidan_home_candidate.blend";bpy.ops.wm.save_as_mainfile(filepath=str(blend));files[blend.name]=hashlib.sha256(blend.read_bytes()).hexdigest()
report={"task":"MAP-BUILDING-01","status":"PROVISIONAL_NOT_CANON","interior_furniture_positions":"UNCONFIRMED","cg_alignment":"NOT_RUN","art_qa":"NOT_RUN","files":files}
(out/"manifest.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("MAP-BUILDING-01 generated",sorted(files))
