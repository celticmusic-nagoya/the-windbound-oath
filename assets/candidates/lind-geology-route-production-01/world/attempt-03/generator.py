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
METHOD = 'authored-inclined-bedrock-outcrops-with-bvh-rooted-soil-pockets-v1'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()



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


def make_mesh(name,vs,faces,mat,rough=False):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if rough:
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        bmesh.ops.subdivide_edges(bm,edges=list(bm.edges),cuts=3,use_grid_fill=True)
        bmesh.ops.triangulate(bm,faces=list(bm.faces))
        for v in bm.verts:
            q=v.co.copy()
            v.co+=noise.noise_vector(q*.81)*.16+noise.noise_vector(q*2.7)*.035
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    bm.to_mesh(me);bm.free();me.update()
    o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(mat)
    return o


def crag(index,center,size,height,lean,angle,mat):
    """Authored irregular fracture contour, weathering ledges, leaning bedding.
    Neither a cube perturbation nor a single clipped exterior hull.
    """
    outline=[(-.94,-.24),(-.64,-.81),(-.15,-1.02),(.29,-.88),(.82,-.42),(.91,.19),(.35,.79),(-.48,.74)]
    # Distinct hand-picked shoulders; levels are nonperiodic and noncoplanar.
    levels=[(0,1.16),(.23,1.03),(.71,.91),(1,.72)]
    profiles=[0,.12,-.07,.19,-.03,.09,-.11,.05]
    vertices=[];cx,cy,cz=center;sx,sy=size
    co,si=math.cos(angle),math.sin(angle)
    for layer,(f,scale) in enumerate(levels):
        for j,(ox,oy) in enumerate(outline):
            # Authored erosion notch changes between crags and fractures.
            side=1+(.08*math.sin(index*1.7+j*2.1))
            x=ox*sx*scale*side+lean[0]*f
            y=oy*sy*scale*side+lean[1]*f
            # Front face contains two broad, irregularly spaced rain-weathered gullies.
            if oy<-.35 and 0<layer<3:
                y+=(.14+.12*(index%3))*sy*math.exp(-((ox+.21)/.31)**2)
            z=height*(f+profiles[j]*(.2+.8*f))
            vertices.append((cx+co*x-si*y,cy+si*x+co*y,cz+z))
    n=len(outline);faces=[tuple(reversed(range(n))),tuple(range(3*n,4*n))]
    for layer in range(3):
        for j in range(n):
            k=(j+1)%n;faces.append((layer*n+j,layer*n+k,(layer+1)*n+k,(layer+1)*n+j))
    o=make_mesh('WORLD_INCLINED_BEDROCK_%02d'%index,vertices,faces,mat,True)
    o['world_role']='authored_joint_bounded_bedrock';o['method']=METHOD
    o['qa_contact_intent']='overlapping rooted bedrock assemblage; intersections intentional rock contacts, independent clearance NOT_RUN'
    return o


def camera(name,pos,target,scale):
    data=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o)
    o.location=pos;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale
    return o


def rooted_patch(index,center,radius,trees,soil,turf,rng):
    """A closed root/soil volume sampled against actual bedrock triangles."""
    cx,cy=center;rx,ry=radius;ring=[]
    for j in range(12):
        a=j*math.tau/12;factor=1+.16*math.sin(j*2.7+index)
        ring.append((cx+rx*factor*math.cos(a),cy+ry*factor*math.sin(a)))
    # Rings+center triangulation provide exact top/base correspondence and BVH contact evidence.
    xy=[(cx,cy)]+ring
    z=[]
    for x,y in xy:
        hits=[t.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),60)[0] for t in trees]
        heights=[h.z for h in hits if h is not None]
        if not heights:return None
        z.append(max(heights))
    verts=[(x,y,h-.035) for (x,y),h in zip(xy,z)]+[(x,y,h+.19) for (x,y),h in zip(xy,z)]
    n=len(xy);faces=[]
    for j in range(1,13):
        k=1+j%12;faces.extend([(0,k,j),(n,n+j,n+k),(j,k,n+k,n+j)])
    o=make_mesh('WORLD_ROOTED_SOIL_POCKET_%02d'%index,verts,faces,soil)
    o['world_role']='bvh_rooted_soil_pocket';o['qa_contact_intent']='sampled bedrock contact at pocket center and 12 boundary vertices; full soil/rock intersection acceptance NOT_RUN'
    # Grass covers each supported pocket as an independent open top surface.
    top=[(x,y,h+.195) for (x,y),h in zip(xy,z)]
    fs=[(0,j,1+j%12) for j in range(1,13)]
    g=make_mesh('WORLD_TURF_POCKET_%02d'%index,top,fs,turf);g['qa_surface_open']=True;g['world_role']='soil_surface_cover'
    return top,fs


def build(out):
    from mathutils.bvhtree import BVHTree
    rng=random.Random(SEED)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    rock=[material('PBR_weathered_sandstone_'+str(i),((.20+i*.009,.185+i*.008,.15+i*.007),(.49+i*.009,.45+i*.008,.35+i*.007)),.72) for i in range(4)]
    soil=material('PBR_root_soil',((.075,.045,.019),(.20,.135,.055)),3.4,bump=.32)
    turf=material('PBR_coastal_turf',((.065,.085,.025),(.21,.24,.075)),1.6,bump=.32)
    grass=material('PBR_dry_grass',((.12,.16,.035),(.32,.34,.09)),4,bump=.06)
    wet=material('PBR_wet_rock',((.055,.065,.055),(.17,.17,.13)),1.9,rough=.55)
    # Position, section radii, rise, inclination and joint strike are authored independently.
    orders=[((-11,3,-1),(4.3,4.3),9.5,(.5,2.1),-.27),((-6,1,-1),(4.6,4.8),13.4,(-1.0,1.7),.12),((-.5,2,-1),(4.2,5.1),15.1,(.9,2.8),-.08),((5.6,3,-1),(5.0,4.6),12.2,(-.8,2.0),.23),((11,5,-1),(3.7,4.0),8.8,(-.6,1.4),.44),((-10,9,-1),(4.1,4.9),12.2,(1.2,.8),-.12),((-3.7,10,-1),(5.0,4.4),15.6,(.2,1.6),.24),((4,11,-1),(5.5,4.8),13.8,(-1.1,.9),-.18),((10.6,10,-1),(3.8,3.8),10.8,(-.5,.9),.12),((-6.5,-4.5,-1),(3.4,3),5.7,(.3,.4),.42),((1,-4.2,-1),(3.2,3.3),7.6,(-.4,1.2),-.38),((7.1,-2.6,-1),(3.4,3.5),5.4,(-.5,.5),.26)]
    rocks=[crag(i,*order,rock[i%4]) for i,order in enumerate(orders)]
    trees=[BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(f.vertices) for f in o.data.polygons]) for o in rocks]
    patches=[]
    for i,(c,rad) in enumerate([((-9,5),(2.4,2.1)),((-6,3.2),(2.9,2.4)),((0,4),(2.5,2.8)),((4.9,5.3),(3,2.5)),((-8,10),(2.9,2.6)),((-2,11),(3,2.4)),((4.8,11),(3.1,2.8)),((9.8,9),(2.1,2.0))]):
        p=rooted_patch(i,c,rad,trees,soil,turf,rng)
        if p:patches.append(p)
    # Short rooted tufts use actual pocket triangles, not a flat cap elevation.
    for i,(top,faces) in enumerate(patches):
        for k in range(45):
            f=faces[rng.randrange(len(faces))];a,b,c=[Vector(top[j]) for j in f]
            u,v=rng.random(),rng.random()
            if u+v>1:u,v=1-u,1-v
            q=a+(b-a)*u+(c-a)*v;h=rng.uniform(.15,.42);w=.05
            vs=[q+Vector((-w,0,0)),q+Vector((w,0,0)),q+Vector((.08,0,h)),q+Vector((0,-w,0)),q+Vector((0,w,0)),q+Vector((0,.03,h*.85))]
            o=make_mesh('WORLD_ROOT_TUFT_%02d_%03d'%(i,k),vs,[(0,1,2),(3,4,5)],grass);o['qa_surface_open']=True
    for k in range(28):
        x=rng.uniform(-11,12);y=-7.3+abs(x)*.15+rng.uniform(-1.2,.5)
        o=crag(50+k,(x,y,-.5),(rng.uniform(.25,.7),rng.uniform(.25,.8)),rng.uniform(.5,1.4),(.05,.12),rng.random()*math.tau,wet)
        o.name='WORLD_WAVE_WORN_TALUS_%02d'%k
    sea=material('PBR_sea',((.012,.07,.095),(.035,.14,.16)),.8,rough=.26,bump=.15)
    bpy.ops.mesh.primitive_plane_add(size=220,location=(0,0,-.22));o=bpy.context.object;o.name='WORLD_OCEAN_CONTEXT';o.data.materials.append(sea);o['qa_surface_open']=True
    s=bpy.context.scene;s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.42,.53,.64,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    bpy.ops.object.light_add(type='SUN',location=(-30,-20,45));sun=bpy.context.object;sun.rotation_euler=(.48,-.52,-.5);sun.data.energy=3.;sun.data.angle=.10;sun.data.color=(1,.86,.66)
    bpy.ops.object.light_add(type='AREA',location=(0,-18,30));area=bpy.context.object;area.data.energy=1800;area.data.shape='DISK';area.data.size=24;area.rotation_euler=(Vector((0,0,8))-area.location).to_track_quat('-Z','Y').to_euler()
    camera('overview',(36,-52,33),(0,4,6),54);camera('detail',(9,-25,17),(-1,-1,7.2),22);camera('gameplay-distance',(45,-64,44),(0,4,6),76)
    im=bpy.data.images.load(str(SOURCE));im.pack();im.use_fake_user=True
    s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False;s.cycles.seed=0;s.render.image_settings.file_format='PNG';s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.view_transform='AgX'
    s['status']='CANDIDATE_NOT_ADOPTED';s['source_image_sha256']=SOURCE_SHA;s['method']=METHOD;s['meters_per_unit']='UNAPPROVED';s['random_seed']=SEED
    s.camera=bpy.data.objects['overview'];bpy.ops.wm.save_as_mainfile(filepath=str(out/'world.blend'))
    settings={'schema':1,'method':METHOD,'seed':SEED,'causal_difference':'discards shared external clip and continuous turf cap; authored separate sloping bedrock crags define contour, upper edge and geological relief; BVH-rooted soil pockets replace flat lid','hypothesis':'visible irregular noncoplanar crag silhouettes, varied slope and rooted soil at all views; independent G2 required','source_sha256':SOURCE_SHA,'candidate_D_sha256':D_SHA,'materials':'reused authored procedural Principled PBR; no downloads','blender':bpy.app.version_string,'rock_volumes':len(rocks),'soil_pockets':len(patches),'metric_approval':False,'views':['overview','detail','gameplay-distance'],'attempt':3,'method_attempt':1}
    (out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    interface={'lane':'WORLD','interface_contract_sha256':sha(ROOT/'tools/map_pipeline/production_interface.json'),'source_image_sha256':SOURCE_SHA,'context_world_sha256':D_SHA,'method':METHOD,'scope':'bounded ocean-facing bedrock study; not east river cliff; no scene adoption','local_origin':None,'bounding_box_m':None,'world_transform':None,'elevation_reference':None,'units':'candidate units only','dependencies':[],'route_dependency_policy':'ROUTE keeps immutable D until reviewed WORLD interface','art_status':'INDEPENDENT_REVIEW_REQUIRED','contact_scope':'soil center/boundary BVH contact; full rock/soil interpenetration audit NOT_RUN'}
    (out/'interface.json').write_text(json.dumps(interface,indent=2)+'\n')
    (out/'producer-qa.json').write_text(json.dumps({'G1':'BLOCKED_METRIC_SPATIAL_REVIEW','G2':'INDEPENDENT_IMAGE_REVIEW_REQUIRED','G3':'PRODUCER_BUILD_RENDER_ONLY','G4':'NOT_RUN','history':'heightfield geology2FAIL STOP; halfspace-cell shared outer hull2G2FAIL STOP; this is separate crag contour family attempt1','Blender.md':'not found; scene interface v1 read'},indent=2)+'\n')


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--render-only',action='store_true');a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
    assert sha(SOURCE)==SOURCE_SHA and sha(D)==D_SHA,'immutable source mismatch'
    out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
    if a.render_only:bpy.ops.wm.open_mainfile(filepath=str(out/'world.blend'))
    else:
        assert not (out/'world.blend').exists(),'preserve previous attempt'
        build(out)
    for view in ['overview','detail','gameplay-distance']:
        bpy.context.scene.camera=bpy.data.objects[view];bpy.context.scene.render.filepath=str(out/(view+'.png'));bpy.ops.render.render(write_still=True)
    files=['world.blend','overview.png','detail.png','gameplay-distance.png','settings.json','interface.json','producer-qa.json']
    (out/'manifest.json').write_text(json.dumps({'schema':1,'lane':'WORLD','method':METHOD,'input_sha256':{'candidate_D':D_SHA,'formal_image':SOURCE_SHA,'generator':sha(__file__)},'outputs':{f:sha(out/f) for f in files},'G1':'BLOCKED','G2':'INDEPENDENT_REVIEW_REQUIRED','G3':'INDEPENDENT_QA_PENDING','G4':'NOT_RUN'},indent=2)+'\n')
    print('WORLD_GEO_02_RENDERED',out)


if __name__=='__main__':main()
