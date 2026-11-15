"""Candidate-only Geometry Nodes harmonic upper/lower controls, preserving 58 keys.

Must run on a separately loaded saved baseline. Never invokes EYELID-06 or saves
its input. The target uses the existing UNREVIEWED EYELID-06 curve for evaluation,
not an adopted design. Four independent controls act before the armature.
"""
import json
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from structural_solver_07 import harmonic_field
from split_lid_loop_07 import split_loop
from correspondence_audit_07 import source_anchor_ids

HERE=Path(__file__).resolve().parent


def install(face, topology, baseline):
    ledger=json.loads((HERE.parent/'_qa/morwen_shared_attempt_ledger.json').read_text())
    failures=sum(a.get('outcome')=='FAIL' and a.get('asset_id')=='morwen-head'
                 and a.get('defect_id')=='MORWEN-EYELID-OPENING-RETOPO'
                 and a.get('method_family')=='DIRICHLET_HARMONIC_INDEPENDENT_LID_FIELDS'
                 for a in ledger['attempts'])
    if failures>=2:
        raise RuntimeError('STOPPED family: use saved candidate for read-only QA; next method requires authored contact targets')
    me=face.data; n=len(me.vertices)
    if len(me.shape_keys.key_blocks)!=58: raise ValueError('Expected protected 58-key baseline')
    if me.attributes.get('m07_rest') or face.modifiers.get('M07_HARMONIC_CANDIDATE'):
        raise ValueError('Candidate already installed')
    coords=np.array([v.co[:] for v in me.shape_keys.key_blocks[0].data])
    world=np.array([tuple(face.matrix_world@Vector(p)) for p in coords])
    tags=[x.value for x in me.attributes['elm_patch'].data]
    curve=json.loads((HERE/'CLOSED_CURVE_CANDIDATE_06.json').read_text())
    calibration=json.loads((HERE.parent/'_qa/eyelid_retopo_05/EYE_TARGETS_05.json').read_text())
    if calibration['source']['sha256'] != curve['source_sha256']:
        raise ValueError('Curve/calibration source mismatch')
    scale=float(calibration['calibration']['s'])
    all_fields=[]; metadata={}
    for side,pid in (('R',1),('L',2)):
        comp=topology['sides'][side]['components'][0]
        if len(comp['edge_ids'])!=28: raise ValueError('Expected 28-edge loop')
        anchors=source_anchor_ids(comp,baseline['build']['lid_'+side]['canthus_vertex_world'])
        pair=split_loop(comp,anchors)
        chains=[pair['chain_A'],pair['chain_B']]
        chains.sort(key=lambda chain:-np.mean(world[chain[1:-1],2]))
        upper,lower=chains; rim=set(upper+lower)
        domain={i for i,t in enumerate(tags) if t==pid}
        # Outer interface shares a polygon with unaffected skin; fixed zero.
        outer={v for p in me.polygons if any(tags[v]!=pid for v in p.vertices) and
               not any(tags[v]==pid+10 for v in p.vertices) for v in p.vertices if tags[v]==pid}
        fixed={v:np.zeros(8) for v in outer}
        p0,p1=world[anchors]; axis=p1-p0
        param=lambda p:float(np.clip((p[0]-p0[0])/(p1[0]-p0[0]),0,1))
        def target(p):
            u=param(p)
            points=curve['sides'][side]['points']
            # Preserve the recorded proposal's vertical arc relative to its chord.
            py=np.interp(u,[p['u'] for p in points],[p['y_px'] for p in points])
            chord=(1-u)*points[0]['y_px']+u*points[-1]['y_px']
            z=(1-u)*p0[2]+u*p1[2]-(py-chord)/scale
            y=np.interp(u,[param(world[v]) for v in upper],[world[v,1] for v in upper])
            return np.array([p[0],y,z])
        inv=np.array(face.matrix_world.inverted())[:3,:3]
        for which,chain in enumerate((upper,lower)):
            for v in chain:
                val=np.zeros(8); displacement=inv@(target(world[v])-world[v])
                val[which*4:which*4+3]=displacement
                val[which*4+3]=1
                if v in anchors:
                    val=np.zeros(8); val[3]=val[7]=0.5
                fixed[v]=val
        edges=[tuple(e.vertices) for e in me.edges]
        solved=harmonic_field(domain,edges,fixed)
        values=np.zeros((n,8))
        for v,a in solved.items(): values[v]=a
        # At full closure remove old expression deformation across the entire lid
        # patch, including its outer row. A harmonic zero at the fixed outer row
        # is correct for target displacement, not for expression cancellation.
        for v in domain:
            total=values[v,3]+values[v,7]
            if total>1e-10:
                values[v,3]/=total;values[v,7]/=total
            else:
                nearest=min(rim,key=lambda j:np.linalg.norm(world[v]-world[j]))
                values[v,3]=0.5 if nearest in anchors else float(nearest in upper)
                values[v,7]=1-values[v,3]
        # Feather cancellation only into adjacent untouched skin. No displacement
        # extrapolation, and no mouth/nose/brow/other-object editing.
        import heapq
        adjacency={i:[] for i in range(n)}
        for a,b in edges:
            distance=float(np.linalg.norm(world[a]-world[b]))
            adjacency[a].append((b,distance));adjacency[b].append((a,distance))
        queue=[(0,v) for v in outer];heapq.heapify(queue);distance={v:0 for v in outer}
        while queue:
            dist,v=heapq.heappop(queue)
            if dist!=distance[v]:continue
            for neighbor,length in adjacency[v]:
                new=dist+length
                if tags[neighbor]!=0 or new>=0.006 or new>=distance.get(neighbor,float('inf')):continue
                distance[neighbor]=new;heapq.heappush(queue,(new,neighbor))
        skin_vertices={v for p in me.polygons if 'SKIN' in me.materials[p.material_index].name for v in p.vertices}
        for v,dist in distance.items():
            if v in domain or v not in skin_vertices:continue
            nearest=min(domain,key=lambda j:np.linalg.norm(world[v]-world[j]))
            t=dist/0.006;falloff=1-t*t*(3-2*t)
            values[v,3]=values[nearest,3]*falloff;values[v,7]=values[nearest,7]*falloff
        # Thickness vertices inherit their unique source rim's displacement.
        # Diverge the back edge into each lid rather than duplicating closed walls.
        for v,t in enumerate(tags):
            if t==pid+10:
                nearest=min(rim,key=lambda j:np.linalg.norm(world[v,[0,2]]-world[j,[0,2]]))
                values[v]=values[nearest]
                if nearest not in anchors:
                    which=0 if nearest in upper else 1
                    values[v,which*4+2]+=0.0004 if which==0 else -0.0004
        # Cards retain rest offset to their nearest margin and follow its field.
        cards={v for p in me.polygons if any(k in me.materials[p.material_index].name for k in ('Eyeline','Eyelash','EyeExtra')) for v in p.vertices}
        for v in cards:
            if (world[v,0]>0.00026)!=(side=='R'): continue
            nearest=min(rim,key=lambda j:np.linalg.norm(world[v]-world[j]))
            if np.linalg.norm(world[v]-world[nearest])<0.012: values[v]=values[nearest]
        for which,label in enumerate(('upper','lower')):
            all_fields.append((side+'_'+label,values[:,which*4:which*4+3],values[:,which*4+3]))
        metadata[side]={'anchors_source_confirmed_not_art_approved':anchors,'upper':upper,'lower':lower,
                        'domain':sorted(domain),'outer_fixed':sorted(outer),'source_curve':'CLOSED_CURVE_CANDIDATE_06.json'}
    def attribute(name,kind,values,prop):
        a=me.attributes.new(name,kind,'POINT'); a.data.foreach_set(prop,np.asarray(values).ravel())
    attribute('m07_rest','FLOAT_VECTOR',coords,'vector')
    group=bpy.data.node_groups.new('M07_HARMONIC_CANDIDATE','GeometryNodeTree')
    group.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    nodes=group.nodes; links=group.links
    inp=nodes.new('NodeGroupInput'); out=nodes.new('NodeGroupOutput'); setpos=nodes.new('GeometryNodeSetPosition')
    links.new(inp.outputs['Geometry'],setpos.inputs['Geometry']);links.new(setpos.outputs['Geometry'],out.inputs['Geometry'])
    pos=nodes.new('GeometryNodeInputPosition').outputs['Position']
    def named(name,kind):
        node=nodes.new('GeometryNodeInputNamedAttribute');node.data_type=kind;node.inputs['Name'].default_value=name;return node.outputs['Attribute']
    def vec(op,a,b):
        node=nodes.new('ShaderNodeVectorMath');node.operation=op;links.new(a,node.inputs[0]);links.new(b,node.inputs['Scale'] if op=='SCALE' else node.inputs[1]);return node.outputs['Vector']
    diff=vec('SUBTRACT',named('m07_rest','FLOAT_VECTOR'),pos)
    offset=None;control_ids={}
    for name,delta,weight in all_fields:
        attribute('m07_d_'+name,'FLOAT_VECTOR',delta,'vector');attribute('m07_w_'+name,'FLOAT',weight,'value')
        socket=group.interface.new_socket(name=name,in_out='INPUT',socket_type='NodeSocketFloat')
        socket.min_value=0;socket.max_value=1;socket.default_value=0;control_ids[name]=socket.identifier
        term=vec('ADD',named('m07_d_'+name,'FLOAT_VECTOR'),vec('SCALE',diff,named('m07_w_'+name,'FLOAT')))
        term=vec('SCALE',term,inp.outputs[name]);offset=term if offset is None else vec('ADD',offset,term)
    links.new(offset,setpos.inputs['Offset'])
    modifier=face.modifiers.new('M07_HARMONIC_CANDIDATE','NODES');modifier.node_group=group
    # Shape keys -> candidate field -> existing armature. No application to source.
    bpy.context.view_layer.objects.active=face
    bpy.ops.object.modifier_move_up(modifier=modifier.name)
    return modifier,control_ids,metadata


def set_control(modifier,identifier,value):
    if not 0 <= value <= 1: raise ValueError('Control outside [0,1]')
    # Blender 5.3 exposes typed interface properties rather than IDProperties.
    if hasattr(modifier,'properties'):
        getattr(modifier.properties.inputs,identifier).value=float(value)
    else:
        modifier[identifier]=float(value)
