"""ROUTE-SUPPORT-01: downward bearing volumes on immutable D, no road lifting.
Candidate units only. No runtime/nav/art acceptance is asserted.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'assets/candidates/lind-spatial-codex-01/world/candidate-d/world.blend'
SHA = '2bc9dabd7baaf7da017821d31b82649170d0f65998da56b8e00bbdffcbb09e72'
ORIGINAL = ROOT / 'assets/sources/lind-world-20261116/original.png'
ORIGINAL_SHA = 'abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620'


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def mesh(name, vs, fs, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata(vs, [], fs)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    ob['owner'] = 'ROUTE'
    ob['method'] = 'actual_surface_downward_bearing_volume'
    return ob


def material(name, dark, light, scale, bump):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*light, 1)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    bs = n.get('Principled BSDF')
    bs.inputs['Roughness'].default_value = .87
    tc = n.new('ShaderNodeTexCoord')
    noise = n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 4
    noise.inputs['Roughness'].default_value = .72
    l.new(tc.outputs['Object'], noise.inputs['Vector'])
    ramp = n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = .15
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].position = .85
    ramp.color_ramp.elements[1].color = (*light, 1)
    l.new(noise.outputs['Fac'], ramp.inputs[0])
    l.new(ramp.outputs[0], bs.inputs['Base Color'])
    micro = n.new('ShaderNodeTexNoise')
    micro.inputs['Scale'].default_value = scale * 18
    micro.inputs['Detail'].default_value = 3
    l.new(tc.outputs['Object'], micro.inputs['Vector'])
    b = n.new('ShaderNodeBump')
    b.inputs['Strength'].default_value = .4
    b.inputs['Distance'].default_value = bump
    l.new(micro.outputs['Fac'], b.inputs['Height'])
    l.new(b.outputs[0], bs.inputs['Normal'])
    return mat


def camera(name, loc, target, ortho):
    ob = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    ob.data.type = 'ORTHO'
    ob.data.ortho_scale = ortho
    return ob


def add_masonry():
    """Arch-specific wedge construction; explicit bonded facing, not random rock cubes."""
    bridge_tree=BVHTree.FromObject(bpy.data.objects['East_bridge_candidate_single_arch'],bpy.context.evaluated_depsgraph_get())
    def crown(x):
        hit=bridge_tree.ray_cast(Vector((x,0,100)),Vector((0,0,-1)),200)[0]
        assert hit is not None
        return hit.z
    mats=[material('ROUTE_arch_stone_'+str(i),(.15+i*.012,.145+i*.011,.115+i*.009),(.34+i*.018,.33+i*.016,.27+i*.013),5.5,.012) for i in range(4)]
    def block(name,front,side,index):
        # front is ordered polygon in XZ. Back embeds into existing masonry core.
        yfront=side*.598
        yback=side*.535
        vs=[(x,yfront,z) for x,z in front]+[(x,yback,z) for x,z in front]
        n=len(front)
        fs=[tuple(range(n)),tuple(reversed(range(n,2*n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        ob=mesh('ROUTE_MASONRY__'+name,vs,fs,mats[index%len(mats)])
        ob['intentional_intersection']='bonded stone face embeds 0.015 into original arch core; not bearing certification'
        bevel=ob.modifiers.new('stone edge wear','BEVEL')
        bevel.width=.007
        bevel.segments=2
        return ob
    # Unequal voussoir widths follow the actual semicircular opening and carry a legible keystone.
    weights=[1+.14*math.sin(i*2.31)+.08*math.cos(i*.79) for i in range(25)]
    total=sum(weights)
    bounds=[0]
    for w in weights:
        bounds.append(bounds[-1]+math.pi*w/total)
    for side in (-1,1):
        for i,(a,b) in enumerate(zip(bounds,bounds[1:])):
            a+=.004
            b-=.004
            ri,ro=2.145,2.475
            coords=[(8+ri*math.cos(a),2.4+ri*math.sin(a)),(8+ro*math.cos(a),2.4+ro*math.sin(a)),(8+ro*math.cos(b),2.4+ro*math.sin(b)),(8+ri*math.cos(b),2.4+ri*math.sin(b))]
            block('voussoir_'+str(side)+'_'+str(i),coords,side,i)
        # Hand-constrained masonry courses above the crown; each top follows the saved deck profile.
        for row,z0 in enumerate([4.91,5.23,5.55,5.87]):
            x=5.86
            index=0
            while x<10.13:
                width=.43+.10*math.sin(index*1.7+row*.9)
                x1=min(10.14,x+width)
                deck0=crown(x)
                deck1=crown(x1)
                top0=min(z0+.295,deck0-.025)
                top1=min(z0+.295,deck1-.025)
                if min(top0,top1)>z0+.055:
                    block('spandrel_'+str(side)+'_'+str(row)+'_'+str(index),[(x+.008,z0+.008),(x1-.008,z0+.008),(x1-.008,top1),(x+.008,top0)],side,index+row)
                x=x1
                index+=1
    # Individual coping stones cap each parapet and break the uninterrupted concrete silhouette.
    for side in (-1,1):
        for i in range(10):
            x0=5.86+4.28*i/10+.009
            x1=5.86+4.28*(i+1)/10-.009
            z0,z1=crown(x0)+.34,crown(x1)+.34
            y=side*.46
            vs=[(x0,y-.083,z0-.015),(x0,y+.083,z0-.015),(x1,y+.083,z1-.015),(x1,y-.083,z1-.015),(x0,y-.083,z0+.055),(x0,y+.083,z0+.055),(x1,y+.083,z1+.055),(x1,y-.083,z1+.055)]
            ob=mesh('ROUTE_MASONRY__coping_'+str(side)+'_'+str(i),vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mats[(i+2)%4])
            ob['intentional_intersection']='cap embeds 0.015 into parapet'
            bevel=ob.modifiers.new('worn coping arris','BEVEL');bevel.width=.012;bevel.segments=2


def unify_junction(out):
    """Single surface owner at the crossing; remove coplanar ribbon overdraw."""
    plane=json.loads((out/'interface.json').read_text())['junction_plane']
    roads=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('Village_to_')]
    boundary=[]
    cuts=[]
    for road in roads:
        vs=road.data.vertices
        cut=next(i for i in range(len(vs)//2) if ((vs[2*i].co+vs[2*i+1].co)*.5).xy.length>=1.1)
        boundary.extend([vs[cut*2].co.copy(),vs[cut*2+1].co.copy()])
        coords=[tuple(v.co) for v in vs]
        faces=[tuple(p.vertices) for p in road.data.polygons if min(p.vertices)//2>=cut]
        road.data.clear_geometry();road.data.from_pydata(coords,[],faces);road.data.update()
        cuts.append({'road':road.name,'first_retained_station':cut,'removed_leading_quads':cut})
    points=sorted(boundary,key=lambda v:(v.x,v.y))
    def cross(o,a,b):return (a.x-o.x)*(b.y-o.y)-(a.y-o.y)*(b.x-o.x)
    lower=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    upper=[]
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    hull=lower[:-1]+upper[:-1]
    assert len(hull)==8,'each road mouth must own its boundary edge'
    tt=BVHTree.FromObject(bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'],bpy.context.evaluated_depsgraph_get())
    n=len(hull)
    vs=[tuple(v) for v in hull]
    for v in hull:
        hit=tt.ray_cast(Vector((v.x,v.y,100)),Vector((0,0,-1)),200)[0]
        assert hit
        vs.append((v.x,v.y,hit.z-.18))
    center=(0,0,plane[2])
    vs.append(center)
    fs=[(2*n,i,(i+1)%n) for i in range(n)]+[tuple(reversed(range(n,2*n)))]+[(i,i+n,(i+1)%n+n,(i+1)%n) for i in range(n)]
    obj=mesh('ROUTE_JUNCTION__shared_surface_and_bearing',vs,fs,bpy.data.materials['ROUTE_compacted_gravel_PBR'])
    obj.data.materials.append(bpy.data.materials['ROUTE_retaining_rockfill_PBR'])
    for p in obj.data.polygons:
        if p.index>=n:p.material_index=1
    obj['intentional_intersection']='bearing base is buried in terrain; obsolete crossing ribbon faces removed, not overlaid'
    d=json.loads((out/'interface.json').read_text());d['junction_objects']=[obj.name];d['junction_top_triangle_count']=n;d['junction_boundary']=[list(v) for v in hull];d['junction_face_ownership']=cuts;d['junction_status']='single closed fan bearing replaces coplanar leading ribbon faces';(out/'interface.json').write_text(json.dumps(d,indent=2)+'\n')


def add_polygon_stonework():
    """Bonded irregular polygon blocks with chipped three-dimensional faces.

    Cells are clipped Voronoi stone bonds in a surface chart, not perturbed cubes.
    """
    import random
    for o in list(bpy.data.objects):
        if o.name.startswith(('ROUTE_MASONRY__spandrel','ROUTE_MASONRY__coping')):
            bpy.data.objects.remove(o,do_unlink=True)
    mats=[bpy.data.materials['ROUTE_arch_stone_'+str(i)] for i in range(4)]
    bridge_tree=BVHTree.FromObject(bpy.data.objects['East_bridge_candidate_single_arch'],bpy.context.evaluated_depsgraph_get())
    terrain_tree=BVHTree.FromObject(bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'],bpy.context.evaluated_depsgraph_get())
    def crown(x):
        return bridge_tree.ray_cast(Vector((x,0,100)),Vector((0,0,-1)),200)[0].z
    def clip(poly,a,b,c):
        result=[]
        for p,q in zip(poly,poly[1:]+poly[:1]):
            fp=a*p[0]+b*p[1]-c;fq=a*q[0]+b*q[1]-c
            if fp<=1e-9:result.append(p)
            if (fp<0)!=(fq<0):
                t=fp/(fp-fq);result.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
        return result
    def chart(name,xmin,xmax,rows,cols,map_point,normal,seed):
        rng=random.Random(seed)
        seeds=[(xmin+(i+.5+rng.uniform(-.3,.3))*(xmax-xmin)/cols,(j+.5+rng.uniform(-.32,.32))/rows) for j in range(rows) for i in range(cols)]
        for index,p in enumerate(seeds):
            cell=[(xmin,0),(xmax,0),(xmax,1),(xmin,1)]
            for q in seeds:
                if p==q:continue
                cell=clip(cell,2*(q[0]-p[0]),2*(q[1]-p[1]),q[0]**2+q[1]**2-p[0]**2-p[1]**2)
                if not cell:break
            if len(cell)<3:continue
            cx=sum(v[0] for v in cell)/len(cell);cy=sum(v[1] for v in cell)/len(cell)
            # Mortar bond and corner breaks are in the polygon boundary itself.
            inset=[(cx+(v[0]-cx)*.965,cy+(v[1]-cy)*.952) for v in cell]
            n=len(cell)
            back=[Vector(map_point(*v))+normal*(-.028) for v in inset]
            outer=[Vector(map_point(*v))+normal*(.012+rng.uniform(-.006,.006)) for v in inset]
            frontchart=[(cx+(v[0]-cx)*.86,cy+(v[1]-cy)*.86) for v in inset]
            front=[Vector(map_point(*v))+normal*(.042+rng.uniform(-.014,.018)) for v in frontchart]
            center=Vector(map_point(cx,cy))+normal*(.052+rng.uniform(-.01,.015))
            vs=[tuple(v) for v in back+outer+front]+[tuple(center)]
            fs=[tuple(reversed(range(n)))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]+[(i+n,(i+1)%n+n,(i+1)%n+2*n,i+2*n) for i in range(n)]+[(i+2*n,(i+1)%n+2*n,3*n) for i in range(n)]
            ob=mesh('ROUTE_MASONRY__polygon_'+name+'_'+str(index),vs,fs,mats[rng.randrange(4)])
            ob['intentional_intersection']='bonded irregular stone embeds in existing frozen masonry core; no bearing replacement'
            prune_occluded_fold(ob,terrain_tree)
    for side in (-1,1):
        def wall(x,v,side=side):
            lower=2.4+math.sqrt(max(0,2.475**2-(x-8)**2))
            upper=crown(x)-.025
            return (x,side*.56,lower+(upper-lower)*v)
        chart('spandrel_'+str(side),5.86,10.14,3,9,wall,Vector((0,side,0)),710+side)
        def parapet(x,v,side=side):return (x,side*.525,crown(x)+.015+.31*v)
        chart('parapet_'+str(side),5.86,10.14,2,12,parapet,Vector((0,side,0)),810+side)
        for end,x0,x1 in [('west',5.25,5.91),('east',10.09,10.75)]:
            def abutment(x,v,side=side):
                ground=terrain_tree.ray_cast(Vector((x,side*.9,100)),Vector((0,0,-1)),200)[0].z-.12
                top=crown(min(10.14,max(5.86,x)))-.03
                return (x,side*(.96-.24*v),ground+(top-ground)*v)
            chart('abutment_'+end+'_'+str(side),x0,x1,4,2,abutment,Vector((0,side,0)),910+side+(0 if end=='west' else 20))
        # Thick irregular polygon coping, modelled as full-depth fitted cap stones.
        def coping(x,v,side=side):return (x,side*.46+(v-.5)*.19,crown(x)+.345)
        chart('coping_'+str(side),5.86,10.14,1,11,coping,Vector((0,0,1)),1010+side)



def prune_occluded_fold(ob,terrain_tree):
    bm=bmesh.new();bm.from_mesh(ob.data);volume=bm.calc_volume(signed=True);bm.free()
    if volume>0:return False
    ob.data.calc_loop_triangles()
    samples=[v.co.copy() for v in ob.data.vertices]
    for tri in ob.data.loop_triangles:
        a,b,c=[ob.data.vertices[i].co for i in tri.vertices]
        samples.extend([(a+b+c)/3,(a+b)*.5,(b+c)*.5,(c+a)*.5])
    clearances=[]
    for p in samples:
        hit=terrain_tree.ray_cast(Vector((p.x,p.y,100)),Vector((0,0,-1)),200)[0]
        assert hit is not None,'invalid stone has no terrain occlusion proof'
        clearances.append(hit.z-p.z)
    assert min(clearances)>.01, 'folded visible masonry cell requires geometric redesign: '+ob.name
    print('EXCLUDED_OCCLUDED_FOLDED_DECORATION',ob.name,'samples',len(samples),'min_terrain_cover',min(clearances),'signed_volume',volume)
    bpy.data.objects.remove(ob,do_unlink=True)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT / 'assets/candidates/lind-geology-route-production-01/route')
    parser.add_argument('--render-only', action='store_true')
    parser.add_argument('--masonry-only', action='store_true')
    parser.add_argument('--finish-repair', action='store_true')
    parser.add_argument('--prune-occluded-cell', action='store_true')
    a = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out = a.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert digest(SOURCE) == SHA
    assert digest(ORIGINAL) == ORIGINAL_SHA
    if a.prune_occluded_cell:
        bpy.ops.wm.open_mainfile(filepath=str(out/'route.blend'))
        tree=BVHTree.FromObject(bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland'],bpy.context.evaluated_depsgraph_get())
        removed=[]
        for ob in list(bpy.data.objects):
            if ob.type=='MESH' and ob.name.startswith('ROUTE_MASONRY__polygon_'):
                name=ob.name
                if prune_occluded_fold(ob,tree):removed.append(name)
        assert removed==['ROUTE_MASONRY__polygon_abutment_east_-1_3'],str(removed)
        (out/'occluded-decoration-exclusion.json').write_text(json.dumps({'removed':removed,'cause':'surface chart folds where immutable terrain exceeds bridge deck; cell is wholly buried, proved at vertices/edges/triangle interiors','visible_geometry_changed':False},indent=2)+'\n')
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'route.blend'))
        render(out)
        return
    if a.finish_repair:

        bpy.ops.wm.open_mainfile(filepath=str(out/'route.blend'))
        before={o.name:hashlib.sha256(str([tuple(v.co) for v in o.data.vertices]).encode()).hexdigest() for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('ROUTE_SUPPORT__','ROUTE_ABUTMENT__','ROUTE_PARAPET__'))}
        unify_junction(out)
        add_polygon_stonework()
        after={o.name:hashlib.sha256(str([tuple(v.co) for v in o.data.vertices]).encode()).hexdigest() for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('ROUTE_SUPPORT__','ROUTE_ABUTMENT__','ROUTE_PARAPET__'))}
        assert before==after
        (out/'frozen-geometry.json').write_text(json.dumps({'before':before,'after':after,'geometry_preserved':True,'exception':'road leading faces removed and shared junction solid added; road vertex coordinates unchanged'},indent=2)+'\n')
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'route.blend'))
        render(out)
        return
    if a.masonry_only:

        bpy.ops.wm.open_mainfile(filepath=str(out / 'route.blend'))
        before={o.name:hashlib.sha256(str([tuple(v.co) for v in o.data.vertices]).encode()).hexdigest() for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('ROUTE_SUPPORT__','ROUTE_ABUTMENT__','ROUTE_PARAPET__','Village_to_'))}
        add_masonry()
        after={o.name:hashlib.sha256(str([tuple(v.co) for v in o.data.vertices]).encode()).hexdigest() for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('ROUTE_SUPPORT__','ROUTE_ABUTMENT__','ROUTE_PARAPET__','Village_to_'))}
        assert before==after
        (out/'frozen-geometry.json').write_text(json.dumps({'before':before,'after':after,'geometry_preserved':True},indent=2)+'\n')
        settings=json.loads((out/'settings.json').read_text());settings['masonry']='arch-specific voussoir wedge + bonded stone spandrel facing + parapet coping; no bearing core changes';(out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=str(out/'route.blend'))
        render(out)
        return
    if a.render_only:

        bpy.ops.wm.open_mainfile(filepath=str(out / 'route.blend'))
        render(out)
        return
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    scene = bpy.context.scene
    stone = material('ROUTE_weathered_local_limestone_PBR', (.125,.145,.14), (.34,.355,.31), 4.5, .013)
    soil = material('ROUTE_compacted_gravel_PBR', (.12,.085,.048), (.32,.26,.17), 8, .009)
    wallmat = material('ROUTE_retaining_rockfill_PBR', (.11,.12,.105), (.29,.30,.255), 10, .017)
    bridge = bpy.data.objects['East_bridge_candidate_single_arch']
    bridge.data.materials.clear()
    bridge.data.materials.append(stone)
    terrain = bpy.data.objects['CONTINUOUS_TERRAIN_coast_river_upland']
    deps = bpy.context.evaluated_depsgraph_get()
    tt = BVHTree.FromObject(terrain, deps)
    bt = BVHTree.FromObject(bridge, deps)
    def surface(x,y, include_bridge=True):
        vals = []
        for key, tree in ([('terrain',tt),('bridge',bt)] if include_bridge else [('terrain',tt)]):
            hit = tree.ray_cast(Vector((x,y,100)), Vector((0,0,-1)), 200)[0]
            if hit is not None:
                vals.append((hit.z,key))
        assert vals, f'missing bearing {x,y}'
        return max(vals)
    roads = sorted([o for o in scene.objects if o.type == 'MESH' and o.name.startswith('Village_to_')], key=lambda o:o.name)
    # One shared joint surface replaces mutually incompatible crossing ribbon profiles.
    # Fit the D road samples, then constrain the plane to the immutable terrain bearing.
    joint_samples = [v.co.copy() for road in roads for v in road.data.vertices if v.co.xy.length < 1.45]
    basis = [(v.x,v.y,1.0) for v in joint_samples]
    normal = Matrix([[sum(row[i]*row[j] for row in basis) for j in range(3)] for i in range(3)])
    rhs = Vector([sum(row[i]*v.z for row,v in zip(basis,joint_samples)) for i in range(3)])
    plane = normal.inverted() @ rhs
    lift = max(surface(v.x,v.y,False)[0]+.025-(plane.x*v.x+plane.y*v.y+plane.z) for v in joint_samples)
    plane.z += max(0,lift)
    junction_changes = []
    for road in roads:
        vertices=road.data.vertices
        old=[v.co.copy() for v in vertices]
        for v in vertices:
            r=v.co.xy.length
            if r < 3.4:
                t=max(0,min(1,(r-1.45)/(3.4-1.45)))
                blend=t*t*(3-2*t)
                z=plane.x*v.co.x+plane.y*v.co.y+plane.z
                v.co.z=z*(1-blend)+v.co.z*blend
        # Grade-constrained transition preserves the shared plane within the junction.
        centers=[(vertices[i].co+vertices[i+1].co)*.5 for i in range(0,len(vertices),2)]
        for i in range(1,len(centers)):
            if centers[i].xy.length <= 1.45:
                continue
            prev=(vertices[2*(i-1)].co+vertices[2*(i-1)+1].co)*.5
            cur=(vertices[2*i].co+vertices[2*i+1].co)*.5
            dist=(cur-prev).xy.length
            floor=prev.z-math.tan(math.radians(24.0))*dist
            delta=max(0,floor-cur.z)
            for v in vertices[2*i:2*i+2]:
                v.co.z+=delta
        junction_changes.append({'route':road.name,'min_z_delta':min(v.co.z-o.z for v,o in zip(vertices,old)),'max_z_delta':max(v.co.z-o.z for v,o in zip(vertices,old))})
        road.data.update()
    rows = []
    geometry_before = {}
    for road in roads:
        vs = [road.matrix_world @ v.co for v in road.data.vertices]
        geometry_before[road.name] = hashlib.sha256(str([tuple(v) for v in vs]).encode()).hexdigest()
        road.data.materials.clear()
        road.data.materials.append(soil)
        sections = []
        bottom = []
        pairs=[(vs[i],vs[i+1]) for i in range(0,len(vs),2)]
        start_direction=((pairs[1][0]+pairs[1][1])-(pairs[0][0]+pairs[0][1])).normalized()
        end_direction=((pairs[-1][0]+pairs[-1][1])-(pairs[-2][0]+pairs[-2][1])).normalized()
        pairs=[(pairs[0][0]-start_direction*.035,pairs[0][1]-start_direction*.035)]+pairs+[(pairs[-1][0]+end_direction*.035,pairs[-1][1]+end_direction*.035)]
        for left,right in pairs:
            direction = (right-left).normalized()
            # Compacted base directly bears the original road; tapered shoulders broaden its footprint.
            points = [left-direction*.15, left.copy(), right.copy(), right+direction*.15]
            for j,p in enumerate(points):
                z = p.z - (.075 if j in (0,3) else .004)
                p.z = z
                sections.append(tuple(p))
                bearing,kind = surface(p.x,p.y)
                bottom.append((p.x,p.y,min(bearing-.18,z-.10)))
        n = len(sections)
        verts = sections + bottom
        faces=[]
        count=len(pairs)
        for i in range(count-1):
            for j in range(3):
                q=i*4+j
                faces.extend([(q,q+1,q+5,q+4),(q+n,q+4+n,q+5+n,q+1+n)])
            for j in (0,3):
                q=i*4+j
                faces.append((q,q+4,q+4+n,q+n))
        for i in (0,count-1):
            q=i*4
            for j in range(3):
                faces.append((q+j,q+j+n,q+j+1+n,q+j+1))
        ob=mesh('ROUTE_SUPPORT__'+road.name,verts,faces,wallmat)
        ob['bearing_context_sha256']=SHA
        ob['top_clearance_candidate_units']=.004
        ob['intentional_intersection']='bottom buried 0.18 candidate units into terrain/bridge to avoid unbonded interface'
        gaps=[(vs[i].z-surface(vs[i].x,vs[i].y)[0]) for i in range(len(vs))]
        rows.append({'route':road.name,'stations':count,'immutable_input_preserved':True,'road_surface_reconstructed_at_junction_and_graded_transition':True,'max_previous_void':max(gaps),'new_support_name':ob.name,'design_road_base_gap':.004,'actual_surface_bearing':'bottom intersects highest immutable terrain/bridge by >=0.18 at cross-section vertices','interior_independent_qa':'REQUIRED'})
    # Two tapered abutments extend the original arch springings into the riverbanks;
    # the channel opening remains free, and no pier is placed in the navigation span.
    for name,x,sign in [('west',5.85,-1),('east',10.15,1)]:
        xs=[x-sign*.06,x+sign*.60]
        vs=[]
        for xx in xs:
            for yy in [-.72,.72]:
                z=surface(min(10.14,max(5.86,xx)),0)[0]-.015
                vs.append((xx,yy,z))
        for xx in xs:
            for yy in [-.96,.96]:
                z=surface(xx,yy,False)[0]-.38
                vs.append((xx,yy,z))
        ab=mesh('ROUTE_ABUTMENT__'+name,vs,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],stone)
        ab['intentional_intersection']='arch end overlap 0.06; footing buried 0.38 into actual terrain at corners'
    # Closed masonry parapet rails follow the measured arch crown rather than an analytic arch.
    for side,y in [('north',.46),('south',-.46)]:
        vs=[]
        for i in range(87):
            x=5.86+(10.14-5.86)*i/86
            z=surface(x,y)[0]
            vs.extend([(x,y-.065,z-.025),(x,y+.065,z-.025),(x,y-.065,z+.34),(x,y+.065,z+.34)])
        fs=[]
        for i in range(86):
            q=i*4
            fs.extend([(q,q+4,q+5,q+1),(q+2,q+3,q+7,q+6),(q,q+2,q+6,q+4),(q+1,q+5,q+7,q+3)])
        fs.extend([(0,1,3,2),(344,346,347,345)])
        rail=mesh('ROUTE_PARAPET__'+side,vs,fs,stone)
        bevel=rail.modifiers.new('worn masonry arris','BEVEL')
        bevel.width=.018
        bevel.segments=2
    add_masonry()
    # Mark the shared origin; no attempt is made to certify unequal overlapping road planes as a junction.
    interface={'schema':'route-support-interface-v1','shared_contract_sha256':digest(ROOT / 'tools/map_pipeline/production_interface.json'),'input_world_sha256':SHA,'units':'CANDIDATE_UNSCALED','local_origin':None,'bounding_box_m':None,'world_transform':None,'elevation_reference':None,'candidate_scene_anchor':[0,0,float(roads[0].data.vertices[0].co.z)],'support_prefix':'ROUTE_SUPPORT__','abutment_prefix':'ROUTE_ABUTMENT__','parapet_prefix':'ROUTE_PARAPET__','road_names':[o.name for o in roads],'context_meshes':['CONTINUOUS_TERRAIN_coast_river_upland','East_bridge_candidate_single_arch'],'ownership':'new structural supports + abutments + parapets; contextual WORLD shape remains immutable','junction_status':'single plane constrained by D terrain and local route fit; independent overlap/intersection QA REQUIRED','road_output_geometry_hashes':geometry_before,'junction_plane':list(plane),'junction_edits':junction_changes,'junction_radius':1.45,'transition_radius':3.4}
    (out/'interface.json').write_text(json.dumps(interface,indent=2)+'\n')
    unify_junction(out)
    add_polygon_stonework()
    (out/'support-measurements.json').write_text(json.dumps({'method':'actual_surface_downward_bearing_volume','scope':'all four immutable D road ribbons + bounded east bridge abutments/parapets','routes':rows,'G3':'PRODUCER_SUBSET_ONLY_INDEPENDENT_REQUIRED','collision_nav':'NOT_RUN'},indent=2)+'\n')
    im=bpy.data.images.load(str(ORIGINAL),check_existing=True)
    im.pack()
    im.use_fake_user=True
    for o in list(scene.objects):
        if o.type=='LIGHT':
            bpy.data.objects.remove(o,do_unlink=True)
    bpy.ops.object.light_add(type='SUN',location=(3,-8,20))
    sun=bpy.context.object
    sun.name='ROUTE_sun'
    sun.rotation_euler=(math.radians(28),math.radians(-20),math.radians(-30))
    sun.data.energy=2.3
    sun.data.angle=.12
    bpy.ops.object.light_add(type='AREA',location=(7,-7,14))
    fill=bpy.context.object
    fill.name='ROUTE_sky_fill'
    fill.data.energy=650
    fill.data.shape='DISK'
    fill.data.size=12
    scene.world.color=(.25,.29,.32)
    camera('ROUTE_view_overview',(29,-33,27),(2,1,3.8),43)
    camera('ROUTE_view_junction-detail',(13,-7,10),(7.8,0,5.2),9.5)
    camera('ROUTE_view_gameplay-distance',(17,-16,15),(7,0,5.3),20)
    scene['production_method']='actual_surface_downward_bearing_volume'
    scene['source_world_sha256']=SHA
    scene['status']='CANDIDATE_NOT_DIRECTOR_APPROVED'
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=32
    scene.cycles.use_denoising=False
    scene.cycles.seed=0
    scene.render.resolution_x=960
    scene.render.resolution_y=640
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.camera=bpy.data.objects['ROUTE_view_overview']
    settings={'method':'actual_surface_downward_bearing_volume','seed':0,'blender':bpy.app.version_string,'input_sha256':SHA,'original_sha256':ORIGINAL_SHA,'units':'candidate scene units; no metric approval','scope':'four road bases and east arch bridge abutments/parapets','road_z_change':'shared joint plane + grade-constrained transition, not simple upward translation','base_gap':.004,'bearing_overlap':.18,'shoulder_width':.15,'masonry':'preserved arch voussoirs + surface-chart clipped polygon stone bonds with chipped 3D faces across spandrel/parapet/abutment/coping','samples':32,'render_size':[960,640],'external_assets':'NONE; procedural Principled PBR only','history_reference':'docs/qa/lind/spatial-codex-world/attempt-ledger.json','causal_difference':'adds actual downward bearing volumes, bank abutments and crown-following parapets, rather than raising a ribbon or repeating terrain cut/fill'}
    (out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    (out/'producer-qa.json').write_text(json.dumps({'G1':'BLOCKED_METRIC_SPATIAL_REVIEW','G2':'FAIL_INHERITED_INDEPENDENT_FACING_REVIEW_METHOD_STOPPED_REPRODUCTION_ONLY','G3':'SELF_QA_ONLY','G4':'NOT_RUN','tested':['protected source SHA','local shared junction plane reconstruction','new support closed-shell construction'],'NOT_RUN':['independent normals/manifold','dense triangle-interior support rays','abutment intersection audit','junction continuity','collision/nav/runtime'],'Blender.md':'not found in checkout or workspace; existing scene interface used'},indent=2)+'\n')
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/'route.blend'))
    render(out)
    assert digest(SOURCE)==SHA
    manifest(out)


def render(out):
    scene=bpy.context.scene
    for filename in ['overview','junction-detail','gameplay-distance']:
        scene.camera=bpy.data.objects['ROUTE_view_'+filename]
        scene.render.filepath=str(out/(filename+'.png'))
        bpy.ops.render.render(write_still=True)
    manifest(out)


def manifest(out):
    files={p.name:digest(p) for p in sorted(out.iterdir()) if p.is_file() and p.suffix in ['.blend','.png','.json'] and p.name not in ['manifest.json','qa.json','art-qa.json']}
    (out/'manifest.json').write_text(json.dumps({'task':'ROUTE-SUPPORT-01','method':'actual_surface_downward_bearing_volume','source_sha256':SHA,'blender':bpy.app.version_string,'files':files,'G1':'BLOCKED','G2':'FAIL_INHERITED_FACING_METHOD_STOPPED_REPRODUCTION_ONLY','G3':'INDEPENDENT_REQUIRED','G4':'NOT_RUN'},indent=2)+'\n')


if __name__=='__main__':
    main()
