"""Standalone Blender structural and image QA for irregular limestone candidate."""
import bpy, sys, json, hashlib, os, math
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from aidan_dressed_stone_v2 import create_dressed_stone_v2, make_limestone_material
out=Path(os.environ.get("AIDAN_DRESSED_OUTPUT","/tmp/aidan-dressed-qa"))
out.mkdir(parents=True,exist_ok=True)
# Remove Blender's default startup cube and other objects before QA.
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
group=bpy.data.collections.new("DRESSED_STONE_QA")
bpy.context.scene.collection.children.link(group)
sizes=((.57,.32,.29),(.82,.34,.31),(.39,.30,.27))
records=[]
stone_material=make_limestone_material()
stone_material.diffuse_color=(.42,.36,.27,1)
stone_material.use_nodes=True
stone_material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.42,.36,.27,1)
stone_material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value=.94
for i,size in enumerate(sizes):
 obj=create_dressed_stone_v2("dressed_stone_%02d"%i,(i*.85,0,0),size,stone_material,group,seed=141127+i)
 mesh=obj.data
 assert len(mesh.vertices)>100 and len(mesh.polygons)>100
 assert all(abs(v.co[j])<=size[j]/2+1e-6 for v in mesh.vertices for j in range(3))
 assert all(len(p.vertices)>=3 for p in mesh.polygons)
 assert all(p.area>1e-8 for p in mesh.polygons)
 # Signed volume must be positive: all outward normals.
 volume=0.0
 for poly in mesh.polygons:
  verts=[mesh.vertices[idx].co for idx in poly.vertices]
  for j in range(1,len(verts)-1):
   volume+=verts[0].dot(verts[j].cross(verts[j+1]))/6
 assert volume>0,(obj.name,volume)
 # A closed manifold must have exactly two incident polygons per edge.
 incidence={tuple(sorted(e.vertices)):0 for e in mesh.edges}
 for face in mesh.polygons:
  vs=list(face.vertices)
  for j in range(len(vs)):
   incidence[tuple(sorted((vs[j],vs[(j+1)%len(vs)])))]+=1
 assert all(n==2 for n in incidence.values()),(obj.name,"non-manifold edges")
 records.append({"name":obj.name,"size":size,"volume_m3":round(volume,7)})
# Distinct seeds must yield visibly distinct corner positions.
assert tuple(group.objects[0].data.vertices[0].co)!=tuple(group.objects[1].data.vertices[0].co)
world=bpy.context.scene.world or bpy.data.worlds.new("stone neutral world")
bpy.context.scene.world=world;world.use_nodes=True
world.node_tree.nodes["Background"].inputs["Color"].default_value=(.20,.23,.27,1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value=.35
bpy.ops.mesh.primitive_plane_add(size=2,location=(.85,0,-.18))
ground=bpy.context.object;ground.name="QA neutral backdrop"
ground.scale=(2.0,1.0,1.0)
backdrop=bpy.data.materials.new("charcoal backdrop")
backdrop.diffuse_color=(.10,.12,.14,1)
backdrop.use_nodes=True
backdrop.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(.10,.12,.14,1)
ground.data.materials.append(backdrop)
bpy.ops.object.light_add(type="AREA",location=(-3,-4,6))
bpy.context.object.data.energy=900;bpy.context.object.data.size=5
bpy.ops.object.camera_add(location=(1.0,-4.5,2.2))
cam=bpy.context.object;cam.data.type="ORTHO";cam.data.ortho_scale=3.25
cam.rotation_euler=(Vector((.85,0,0))-cam.location).to_track_quat("-Z","Y").to_euler()
scene=bpy.context.scene;scene.camera=cam
scene.render.engine="BLENDER_EEVEE_NEXT" if bpy.app.version>=(4,2,0) else "BLENDER_EEVEE"
scene.render.resolution_x=720;scene.render.resolution_y=480
scene.render.resolution_percentage=100
scene.render.image_settings.file_format="PNG"
p=out/"dressed_stone_v2_three_samples.png"
scene.render.filepath=str(p)
bpy.ops.render.render(write_still=True)
assert p.stat().st_size>1000
assert not any(o.name=="Cube" for o in scene.objects), "Startup cube obscures QA stones"
report={"status":"CANDIDATE_NOT_ART_APPROVED","blender_version":bpy.app.version_string,
        "samples":records,"image":p.name,"sha256":hashlib.sha256(p.read_bytes()).hexdigest()}
(out/"manifest.json").write_text(json.dumps(report,indent=2))
print("DRESSED_STONE_V2_QA="+json.dumps(report))
