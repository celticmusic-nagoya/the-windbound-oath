"""Morwen facial surface sculpt study v1: independent quad-grid facial plane, not old ring cage.
Produces an editable candidate only; no G2 art pass. Requires official Layer 0 reference scene.
"""
import bpy,math,json,pathlib,sys
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
reference,out=map(pathlib.Path,args[:2]);out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(reference))
assert tuple(bpy.app.version)==(5,3,0)
assert all(bpy.data.objects.get("REF_"+v) for v in ("FRONT","RIGHT","BACK","LEFT"))
sc=bpy.context.scene
coll=bpy.data.collections.get("SCULPT__EMPTY__AUTHOR_HERE")
assert coll is not None
# Parametric transverse quad grid; each point independently displaced for brows,
# recessed orbital planes, nose bridge, cheekbone, muzzle and chin. This is a new
# topology family and not a ring cage, voxel sphere union or legacy mesh repair.
nx,nz=65,85
verts=[];faces=[]
for iz in range(nz):
 z=1.22+iz/(nz-1)*.61
 u=(z-1.525)/.305
 width=.223*max(.13,1-.39*max(0,-u)**2-.27*max(0,u)**3)
 for ix in range(nx):
  x=(ix/(nx-1)*2-1)*width
  xn=x/max(width,.0001)
  base=-.115-.048*math.sqrt(max(0,1-xn*xn))
  eye=math.exp(-((z-1.595)/.039)**2)*math.exp(-((abs(x)-.092)/.050)**2)
  brow=math.exp(-((z-1.648)/.028)**2)*math.exp(-((abs(x)-.093)/.064)**2)
  cheek=math.exp(-((z-1.482)/.067)**2)*math.exp(-((abs(x)-.136)/.063)**2)
  bridge=math.exp(-(x/.031)**2)*math.exp(-((z-1.533)/.097)**2)
  tip=math.exp(-(x/.041)**2)*math.exp(-((z-1.474)/.027)**2)
  lips=math.exp(-(x/.073)**2)*math.exp(-((z-1.392)/.019)**2)
  chin=math.exp(-(x/.078)**2)*math.exp(-((z-1.303)/.044)**2)
  y=base+.021*eye-.012*brow-.020*cheek-.027*bridge-.026*tip-.010*lips-.014*chin
  verts.append((x,y,z))
for iz in range(nz-1):
 for ix in range(nx-1):
  a=iz*nx+ix;faces.append((a,a+1,a+1+nx,a+nx))
mesh=bpy.data.meshes.new("FACE_FRONT_QUAD_GRID_EDITABLE")
mesh.from_pydata(verts,[],faces);mesh.update()
ob=bpy.data.objects.new("MORWEN_FACE_PLANES_CANDIDATE_NOT_ADOPTED",mesh)
coll.objects.link(ob)
for poly in mesh.polygons:poly.use_smooth=True
solid=bpy.context.view_layer.objects.active=ob
ob.select_set(True)
mod=ob.modifiers.new("Preview_subdivision_not_applied","SUBSURF");mod.levels=2;mod.render_levels=2
sc["production_status"]="FACE_SURFACE_STUDY_NOT_G2_APPROVED"
sc["sculpt_source"]="independent_quad_grid_no_old_cage"
# Save with reference images packed; no main/legacy source changes.
blend=out/"morwen_face_surface_530_candidate.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
# Isolated clay preview, orthographic cameras; preserve canonical reference empties.
mat=bpy.data.materials.new("Neutral_Clay");mat.diffuse_color=(.65,.55,.53,1)
mat.use_nodes=True;mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.65,.55,.53,1)
mesh.materials.append(mat)
for v,loc in (("front",(0,-4,1.54)),("right",(4,0,1.54)),("three_quarter",(3,-4,1.67))):
 bpy.ops.object.camera_add(location=loc)
 cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1.54))-cam.location).to_track_quat("-Z","Y").to_euler()
 cam.data.type="ORTHO";cam.data.ortho_scale=.85;sc.camera=cam
 bpy.ops.object.light_add(type="AREA",location=(1,-3,4))
 bpy.context.object.data.energy=450
 sc.render.engine="CYCLES";sc.cycles.samples=8;sc.render.resolution_x=512;sc.render.resolution_y=640;sc.render.resolution_percentage=100
 sc.render.filepath=str(out/("face_"+v+".png"));bpy.ops.render.render(write_still=True)
 bpy.data.objects.remove(cam,do_unlink=True)
 # Remove only lights added for render; scene contains no original lights.
 for light in [o for o in bpy.data.objects if o.type=="LIGHT"]:bpy.data.objects.remove(light,do_unlink=True)
report={"status":"CANDIDATE_NOT_G2_PASS","blender":bpy.app.version_string,"mesh_vertices":len(mesh.vertices),"mesh_quads":len(mesh.polygons),"reference_count":4,"source":"new_front_quad_grid","limitations":["open back","no eyelids/ears/eyes","not complete head","no independent art QA"]}
(out/"qa.json").write_text(json.dumps(report,indent=2))
