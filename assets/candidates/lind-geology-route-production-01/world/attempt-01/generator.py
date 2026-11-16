"""WORLD-GEO-02: bounded 3D joint-cell rock volume, no heightfield cliff generation.
All coordinates are local candidate units; no formal placement or metric inference.
Blender: --factory-startup --python this.py -- --out DIR [--render-only]
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import bpy
import bmesh
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'assets/sources/lind-world-20261116/original.png'
D = ROOT / 'assets/candidates/lind-spatial-codex-01/world/candidate-d/world.blend'
SOURCE_SHA = 'abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620'
D_SHA = '2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72'
SEED = 26719
METHOD = 'anisotropic-3d-halfspace-joint-cells-with-weathered-skin-v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def clip(faces, normal, distance):
    """Clip convex polygon soup to n.p<=d, retaining a correctly oriented cap."""
    out, cuts = [], []
    for face in faces:
        poly = []
        for a, b in zip(face, face[1:] + face[:1]):
            da, db = normal.dot(a) - distance, normal.dot(b) - distance
            if da <= 1e-7:
                poly.append(a)
            if (da < -1e-7 and db > 1e-7) or (da > 1e-7 and db < -1e-7):
                q = a + (b-a) * (da/(da-db))
                poly.append(q)
                cuts.append(q)
        if len(poly) >= 3:
            out.append(poly)
    unique = {tuple(round(v, 7) for v in p): p for p in cuts}
    pts = list(unique.values())
    if len(pts) >= 3:
        center = sum(pts, Vector()) / len(pts)
        ref = Vector((0, 0, 1)) if abs(normal.normalized().z) < .9 else Vector((1, 0, 0))
        u = normal.cross(ref).normalized()
        v = normal.normalized().cross(u)
        pts.sort(key=lambda p: math.atan2((p-center).dot(v), (p-center).dot(u)))
        out.append(pts)
    return out


def box_faces():
    v = [Vector(p) for p in [(-17,-9,-1),(17,-9,-1),(17,14,-1),(-17,14,-1),(-17,-9,12),(17,-9,12),(17,14,12),(-17,14,12)]]
    return [[v[i] for i in f] for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]


def material(name, colors, scale, rough=.83, bump=.19):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    bs = n.get('Principled BSDF')
    bs.inputs['Roughness'].default_value = rough
    tex = n.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = scale; tex.inputs['Detail'].default_value = 4.2; tex.inputs['Roughness'].default_value = .72
    coord = n.new('ShaderNodeTexCoord'); l.new(coord.outputs['Object'],tex.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position=.2; ramp.color_ramp.elements[0].color=(*colors[0],1)
    ramp.color_ramp.elements[1].position=.8; ramp.color_ramp.elements[1].color=(*colors[1],1)
    l.new(tex.outputs['Fac'],ramp.inputs['Fac']); l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=19;fine.inputs['Detail'].default_value=3
    l.new(coord.outputs['Object'],fine.inputs['Vector'])
    bn=n.new('ShaderNodeBump');bn.inputs['Strength'].default_value=bump;bn.inputs['Distance'].default_value=.085
    l.new(fine.outputs['Fac'],bn.inputs['Height']); l.new(bn.outputs['Normal'],bs.inputs['Normal'])
    return m


def mesh(name, faces, mat, weather=True):
    verts, ids, polygons = [], {}, []
    for f in faces:
        p=[]
        for v in f:
            k=tuple(round(x,6) for x in v)
            if k not in ids:
                ids[k]=len(verts);verts.append(tuple(v))
            p.append(ids[k])
        # Remove only adjacent numerical duplicates, never collapse geometry wholesale.
        p=[v for i,v in enumerate(p) if v!=p[i-1]]
        if len(set(p))>=3: polygons.append(p)
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],polygons);me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if weather:
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=2,use_grid_fill=True)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        for v in bm.verts:
            # Coherent spatial weathering: displacement shared by neighboring joint skins.
            q=v.co.copy(); v.co += Vector((noise.noise_vector(q*.77)[0],noise.noise_vector(q*.77)[1],noise.noise_vector(q*.77)[2]))*.075
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(me);bm.free();me.update()
    return o


def cap(name, outline, bottom, top, mat):
    lo=[Vector((x,y,bottom)) for x,y in outline];hi=[Vector((x,y,top)) for x,y in outline]
    fs=[list(reversed(lo)),hi]
    for i in range(len(lo)):
        j=(i+1)%len(lo);fs.append([lo[i],lo[j],hi[j],hi[i]])
    return mesh(name,fs,mat,weather=False)


def cam(name,pos,target,scale):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale
    return o


def build(out):
    r=random.Random(SEED)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    stone=[material('PBR_weathered_sandstone_'+str(i),((.20+i*.009,.185+i*.008,.15+i*.007),(.49+i*.009,.45+i*.008,.35+i*.007)),.72) for i in range(4)]
    soil=material('PBR_root_soil',((.075,.045,.019),(.20,.135,.055)),3.4,bump=.32)
    turf=material('PBR_coastal_turf',((.065,.085,.025),(.21,.24,.075)),1.6,bump=.32)
    grass=material('PBR_dry_grass',((.12,.16,.035),(.32,.34,.09)),4,bump=.06)
    wet=material('PBR_wet_rock',((.055,.065,.055),(.17,.17,.13)),1.9,rough=.55)
    outline=[(-15,5),(-13,-1),(-8,-5),(-1,-7),(7,-5.3),(13,-1),(15,6),(11,13),(-8,14)]
    outer=[]
    for a,b in zip(outline,outline[1:]+outline[:1]):
        n=Vector((b[1]-a[1],a[0]-b[0],0));outer.append((n,n.dot(Vector((*a,0)))))
    sites=[]
    # Irregular 3D joints; neither cubic tessellation nor height-field strips.
    for _ in range(57): sites.append(Vector((r.uniform(-16,16),r.uniform(-8,14),r.uniform(-3,17))))
    cells=[]
    for k,s in enumerate(sites):
        fs=box_faces()
        for n,d in outer: fs=clip(fs,n,d)
        for j,t in enumerate(sites):
            if j==k:continue
            # Vertical anisotropy makes occasional tall joints but does not impose rings.
            n=Vector(((t.x-s.x),(t.y-s.y),(t.z-s.z)*.27))
            d=((t.x*t.x-s.x*s.x)+(t.y*t.y-s.y*s.y)+(t.z*t.z-s.z*s.z)*.27)*.5
            fs=clip(fs,n,d)
            if not fs:break
        if not fs:continue
        allpts=[p for f in fs for p in f];center=sum(allpts,Vector())/len(allpts)
        # Narrow open joint is physical negative space, not a stripe shader.
        fs=[[center+(p-center)*.995 for p in f] for f in fs]
        o=mesh('JOINT_ROCK_VOLUME_%03d'%k,fs,stone[k%len(stone)])
        o['world_role']='joint_constrained_rock_volume';o['method']=METHOD;cells.append(o)
    cap('ROOTED_SOIL_CONTACT',outline,11.82,12.26,soil)
    # Turf rim follows the same contour as the engineered soil contact, with local eroded patches.
    cap('COASTAL_TURF_CAP',[(x*.995,y*.995) for x,y in outline],12.24,12.39,turf)
    # Irregular tufts grow inland; all are small grouped blades, no tree/ECO scope expansion.
    for k in range(240):
        x,y=r.uniform(-12,12),r.uniform(-3.8,11)
        if (x/13)**2+((y-3)/10)**2>1:continue
        h=r.uniform(.15,.42);w=r.uniform(.035,.085)
        fs=[]
        for j in range(3):
            a=r.random()*math.tau;dx,dy=math.cos(a)*w,math.sin(a)*w
            fs.append([Vector((x-dx,y-dy,12.36)),Vector((x+dx,y+dy,12.36)),Vector((x+r.uniform(-.1,.1),y+r.uniform(-.1,.1),12.36+h))])
        o=mesh('ROOT_TUFT_%03d'%k,fs,grass,False);o['qa_surface_open']=True;o['qa_open_surface']='intentional grass blade'
    # Talus volumes at the wave-worn toe; random convex polyhedra, not duplicated cubes.
    for k in range(34):
        x=r.uniform(-12,12);y=-6.7+abs(x)*.22+r.uniform(-1.7,.1);z=r.uniform(-.3,.4)
        radius=r.uniform(.19,.9)
        bm=bmesh.new()
        for j in range(13):
            a=r.random()*math.tau;h=r.uniform(-.65,.8)
            bm.verts.new((x+math.cos(a)*radius*r.uniform(.6,1.2),y+math.sin(a)*radius,z+h*radius))
        bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
        me=bpy.data.meshes.new('talus');bm.to_mesh(me);bm.free()
        o=bpy.data.objects.new('ANGULAR_TALUS_%03d'%k,me);bpy.context.collection.objects.link(o);o.data.materials.append(wet);o['world_role']='talus';
    sea=material('PBR_sea',((.012,.07,.095),(.035,.14,.16)),.8,rough=.26,bump=.15)
    bpy.ops.mesh.primitive_plane_add(size=220,location=(0,0,-.22));o=bpy.context.object;o.name='OCEAN_CONTEXT';o.data.materials.append(sea);o['qa_surface_open']=True;o['qa_open_surface']='intentional water plane'
    bpy.context.scene.world.use_nodes=True
    bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.53,.64,1)
    bpy.context.scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    bpy.ops.object.light_add(type='SUN',location=(-30,-20,45));sun=bpy.context.object;sun.rotation_euler=(.48,-.52,-.5);sun.data.energy=3.;sun.data.angle=.10;sun.data.color=(1,.86,.66)
    bpy.ops.object.light_add(type='AREA',location=(0,-18,30));area=bpy.context.object;area.data.energy=1800;area.data.shape='DISK';area.data.size=24;area.rotation_euler=(Vector((0,0,8))-area.location).to_track_quat('-Z','Y').to_euler()
    cam('overview',(36,-52,33),(0,3,6),54)
    cam('detail',(9,-25,17),(-1,-3,7.2),22)
    cam('gameplay-distance',(45,-64,44),(0,3,6),76)
    im=bpy.data.images.load(str(SOURCE));im.pack();im.use_fake_user=True
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=32;s.cycles.use_denoising=False;s.cycles.seed=0;s.render.image_settings.file_format='PNG';s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100
    s.view_settings.view_transform='AgX';s['status']='CANDIDATE_NOT_ADOPTED';s['source_image_sha256']=SOURCE_SHA;s['method']=METHOD;s['meters_per_unit']='UNAPPROVED';s['random_seed']=SEED
    s.camera=bpy.data.objects['overview'];bpy.ops.wm.save_as_mainfile(filepath=str(out/'world.blend'))
    settings={'schema':1,'method':METHOD,'seed':SEED,'causal_difference':'3D polyhedral rock cells retain independent closed volumes and spatial joints; no heightfield cliff or periodic band material','source_sha256':SOURCE_SHA,'candidate_D_sha256':D_SHA,'materials':'authored procedural Principled PBR; no downloaded texture or external asset','blender':bpy.app.version_string,'local_candidate_bounds':[[-17,-9,-1],[17,14,12.5]],'metric_approval':False,'cells':len(cells),'coordinate_status':'local design study only, not an approved site transform','views':['overview','detail','gameplay-distance']}
    (out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    (out/'interface.json').write_text(json.dumps({'lane':'WORLD','interface_contract_sha256':sha(ROOT/'tools/map_pipeline/production_interface.json'),'source_image_sha256':SOURCE_SHA,'context_world_sha256':D_SHA,'method':METHOD,'scope':'bounded ocean-facing cliff study; not east river cliff; no scene adoption','local_origin':None,'bounding_box_m':None,'world_transform':None,'elevation_reference':None,'units':'candidate units only','contact_surface':'COASTAL_TURF_CAP local z12.39; not a proposed route interface','dependencies':[],'route_dependency_policy':'ROUTE must keep immutable D input until approved common interface exists','art_status':'INDEPENDENT_REVIEW_REQUIRED'},indent=2)+'\n')
    # Independent checks/reopen are performed by separate coordinator; do not invent gate PASS.
    (out/'producer-qa.json').write_text(json.dumps({'G1':'BLOCKED_METRIC_SPATIAL_REVIEW','G2':'INDEPENDENT_IMAGE_REVIEW_REQUIRED','G3':'PRODUCER_BUILD_RENDER_ONLY','G4':'NOT_RUN','history':'A/B heightfield geological art family remains stopped after 2 failures','new_method_attempt':1,'Blender.md':'not found in repository/workspace; scene interface v1 read'},indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--render-only',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert sha(SOURCE)==SOURCE_SHA and sha(D)==D_SHA,'immutable source mismatch'
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if a.render_only:
        bpy.ops.wm.open_mainfile(filepath=str(out/'world.blend'))
    else:
        assert not (out/'world.blend').exists(),'do not overwrite existing attempt'
        build(out)
    s=bpy.context.scene
    for view in ['overview','detail','gameplay-distance']:
        s.camera=bpy.data.objects[view];s.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)
    paths=['world.blend','overview.png','detail.png','gameplay-distance.png','settings.json','interface.json','producer-qa.json']
    (out/'manifest.json').write_text(json.dumps({'schema':1,'lane':'WORLD','method':METHOD,'input_sha256':{'candidate_D':D_SHA,'formal_image':SOURCE_SHA,'generator':sha(__file__)},'outputs':{f:sha(out/f) for f in paths},'G1':'BLOCKED','G2':'INDEPENDENT_REVIEW_REQUIRED','G3':'INDEPENDENT_QA_PENDING','G4':'NOT_RUN'},indent=2)+'\n')
    print('WORLD_GEO_02_RENDERED',out)


if __name__=='__main__': main()
