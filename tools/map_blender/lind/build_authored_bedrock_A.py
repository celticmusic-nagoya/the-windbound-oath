"""Windwaiting Cliff | authored provisional rock module A.

A new, non-canonical, editable 3D rock mass. Control sections and hand-placed
fracture paths are authored explicitly; this is NOT a repetition of the stopped
periodic profile extrusion, radial boundary or scan-edge patch methods.
Usage: blender -b --factory-startup --python this_file.py -- --out out/cliff
Art acceptance is deliberately NOT asserted.
"""
import bpy, math, json, hashlib, sys, random
from pathlib import Path
from mathutils import Vector

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mesh_object(name, verts, faces, mat):
    mesh=bpy.data.meshes.new(name+"_mesh")
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    for poly in mesh.polygons: poly.use_smooth=True
    return obj

def material(name, color, roughness):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1)
    m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Roughness"].default_value=roughness
    return m

def main():
    args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    out=Path(args[args.index("--out")+1] if "--out" in args else "out/cliff")
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    scene["coordinate_space"]="asset-local-provisional"
    scene["unit_scale_status"]="UNAPPROVED"
    scene["origin_convention"]="module geometric center XY, ground contact Z=0 (provisional)"
    scene["ground_contact_convention"]="underside at Z=0; world attachment BLOCKED"
    scene["source_manifest_sha256"]="NONE_NEW_AUTHORED_GEOMETRY"
    scene["source_license"]="original authored procedural construction; no external meshes/textures"
    scene["producer_commit"]="UNSET_AT_GENERATION"
    scene["canonical_world_placement"]="BLOCKED_FOR_INTEGRATION"
    scene["art_status"]="UNAPPROVED_G2_REVIEW_REQUIRED"
    stone=material("Slate limestone | weathered warm grey",(0.31,0.30,0.27),0.86)
    seams=material("Fracture shadow | dark mineral",(0.075,0.072,0.068),0.94)
    # Authored cross-sectional control points, in provisional local Blender units.
    # Each row: x, front y, rear y, top z, toe z, crest overhang y.
    sections=[
      (-3.40,-0.60,1.20,2.25,0.00,-0.28),
      (-2.94,-0.93,1.42,3.07,0.00,-0.54),
      (-2.43,-0.77,1.36,3.44,0.00,-0.43),
      (-1.91,-1.22,1.70,3.14,0.00,-0.79),
      (-1.28,-1.01,1.54,4.08,0.00,-0.84),
      (-0.76,-1.47,1.83,3.77,0.00,-1.10),
      (-0.17,-1.19,1.57,4.42,0.00,-0.98),
      (0.40,-1.61,1.91,3.83,0.00,-1.27),
      (0.93,-1.32,1.73,3.53,0.00,-0.91),
      (1.51,-1.13,1.56,4.01,0.00,-0.92),
      (2.04,-1.48,1.76,3.33,0.00,-1.11),
      (2.57,-0.97,1.48,3.62,0.00,-0.66),
      (3.15,-0.82,1.26,2.86,0.00,-0.43),
      (3.51,-0.51,1.04,2.19,0.00,-0.20),
    ]
    # Continuous perimeter ring around each section. Nonuniform overhang
    # produces an undercut, rather than a flat extruded cliff wall.
    verts=[]
    for x,front,rear,top,toe,lip in sections:
        pts=[
          (front+0.22,0.00), (front-0.07,0.24*top),
          (front-0.12,0.43*top), (front+0.18,0.61*top),
          (front-0.03,0.76*top), (lip,0.91*top),
          (lip+0.27,top), (0.10,top+0.06),
          (rear-0.15,top-0.19),(rear,0.68*top),
          (rear+0.03,0.31*top),(rear-0.10,0.00),
        ]
        for j,(y,z) in enumerate(pts):
            # Aperiodic shallow bedding distortions; the silhouette is authored.
            offset=0.055*math.sin(x*3.17+j*1.83)+0.035*math.sin(x*7.41-j*2.57)
            verts.append((x+offset,y,z))
    N=12;faces=[]
    for i in range(len(sections)-1):
        for j in range(N):
            a=i*N+j;b=i*N+(j+1)%N
            faces.append((a,(i+1)*N+j,(i+1)*N+(j+1)%N,b))
    faces.append(tuple(reversed(tuple(range(N)))))
    faces.append(tuple((len(sections)-1)*N+j for j in range(N)))
    rock=mesh_object("AUTHORED_BEDROCK_A_UNAPPROVED",verts,faces,stone)
    # Surface subdivision only: preserves a real editable source cage.
    sub=rock.modifiers.new("Author cage surface refinement","SUBSURF")
    sub.levels=2;sub.render_levels=2
    # Fine mineral roughness: material-only noise, no substitute for macro sculpt.
    nodes=stone.node_tree.nodes;links=stone.node_tree.links
    noise=nodes.new("ShaderNodeTexNoise");noise.inputs["Scale"].default_value=11.0
    noise.inputs["Detail"].default_value=4.0
    bump=nodes.new("ShaderNodeBump");bump.inputs["Strength"].default_value=0.19
    bump.inputs["Distance"].default_value=0.055
    links.new(noise.outputs["Fac"],bump.inputs["Height"])
    links.new(bump.outputs["Normal"],nodes.get("Principled BSDF").inputs["Normal"])
    # Authored non-intersecting fracture strokes on the visible face.
    fracture_paths=[
      [(-2.79,-1.00,2.65),(-2.59,-0.99,2.18),(-2.47,-0.96,1.64),(-2.30,-0.92,1.29)],
      [(-1.22,-1.36,3.44),(-1.09,-1.43,2.92),(-0.88,-1.48,2.34),(-0.64,-1.50,1.97)],
      [(0.28,-1.70,3.22),(0.41,-1.73,2.71),(0.57,-1.65,2.12),(0.82,-1.53,1.73)],
      [(1.87,-1.53,2.83),(2.01,-1.52,2.29),(2.18,-1.39,1.86),(2.39,-1.20,1.41)],
    ]
    # Fracture guides are isolated from the watertight rock and excluded from
    # topology preflight until an artist cuts true recessed fractures.
    for i,path in enumerate(fracture_paths):
        curve=bpy.data.curves.new("FRACTURE_GUIDE_%02d"%i,"CURVE")
        curve.dimensions="3D";curve.bevel_depth=0.016;curve.bevel_resolution=2
        spline=curve.splines.new("POLY");spline.points.add(len(path)-1)
        for p,xyz in zip(spline.points,path):p.co=(*xyz,1)
        ob=bpy.data.objects.new("FRACTURE_GUIDE_UNCUT_%02d"%i,curve)
        scene.collection.objects.link(ob);ob.data.materials.append(seams)
        ob["qa_exclude"]=True
    # UVs for the authored source cage; final art UV unwrap still required.
    uv=rock.data.uv_layers.new(name="PROVISIONAL_CAGE_UV")
    for poly in rock.data.polygons:
        for li in poly.loop_indices:
            v=rock.data.vertices[rock.data.loops[li].vertex_index].co
            uv.data[li].uv=((v.x+3.6)/7.2,v.z/4.7)
    # Independent studio lighting and camera, not a canonical game camera.
    world=bpy.data.worlds.new("Studio neutral");scene.world=world
    world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(0.20,0.23,0.28,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value=0.6
    for name,loc,power,size in [
      ("Key",(-4,-6,9),1500,5),("Fill",(4,-4,5),850,4),("Rim",(0,5,8),1800,5)]:
        data=bpy.data.lights.new(name,"AREA");data.energy=power;data.shape="DISK";data.size=size
        ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc
        ob.rotation_euler=(Vector((0,0,2))-ob.location).to_track_quat("-Z","Y").to_euler()
    camdata=bpy.data.cameras.new("Studio orthographic camera")
    cam=bpy.data.objects.new("Studio orthographic camera",camdata)
    scene.collection.objects.link(cam);scene.camera=cam;camdata.type="ORTHO";camdata.ortho_scale=9.8
    scene.render.engine="CYCLES";scene.cycles.samples=24
    scene.render.resolution_x=1200;scene.render.resolution_y=850
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"
    bpy.ops.file.pack_all()
    blend=out/"windwaiting_bedrock_A_UNAPPROVED.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    views={"front":(0,-12,5),"left":(-10,-7,5),"right":(10,-7,5),"elevated":(8,-10,11)}
    for label,pos in views.items():
        cam.location=pos
        cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat("-Z","Y").to_euler()
        scene.render.filepath=str(out/(label+".png"))
        bpy.ops.render.render(write_still=True)
    outputs=[blend]+[out/(k+".png") for k in views]
    report={"status":"UNAPPROVED_ART_CANDIDATE","coordinate_space":"asset-local-provisional",
      "unit_scale_status":"UNAPPROVED","method":"authored irregular cross-section cage + subdivision",
      "fractures":"visual guides only; NOT cut into mesh",
      "G1":"NOT_RUN","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN",
      "integration":"BLOCKED_FOR_INTEGRATION",
      "files":{p.name:sha(p) for p in outputs}}
    (out/"manifest.json").write_text(json.dumps(report,indent=2)+"\n")
    print("LIND_AUTHORED_CLIFF_CANDIDATE_GENERATED",json.dumps(report),flush=True)

if __name__=="__main__":main()
