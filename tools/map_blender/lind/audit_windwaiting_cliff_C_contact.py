"""Independent spatial skeleton audit for Windwaiting Cliff C.
Runs inside Blender on the saved .blend. Detects unsupported/floating scan groups
and missing contact between editable CC0 instances. Conservative AABB broad phase;
AABB overlap is only a candidate, never proof of real mesh contact.
"""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
out=Path(args[0]) if args else Path('out/lind-scan-c/contact_audit.json')
roots=sorted((o for o in bpy.data.objects if o.name.startswith('ART_DIRECTED_SCAN_ROOT_')),key=lambda o:o.name)
def world_bounds(root):
    children=[o for o in root.children_recursive if o.type=='MESH']
    pts=[o.matrix_world @ Vector(p) for o in children for p in o.bound_box]
    if not pts:raise RuntimeError('EMPTY_SCAN_INSTANCE:'+root.name)
    return [min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)],len(children)
boxes=[world_bounds(r) for r in roots]
pairs=[]
for i in range(len(roots)):
    for j in range(i+1,len(roots)):
        a,b=boxes[i],boxes[j]
        overlap=[min(a[1][k],b[1][k])-max(a[0][k],b[0][k]) for k in range(3)]
        if min(overlap)>0:
            pairs.append({'a':roots[i].name,'b':roots[j].name,'overlap_xyz':overlap,'classification':'AABB_CANDIDATE_NOT_MESH_CONTACT'})
graph={r.name:set() for r in roots}
for p in pairs:
    graph[p['a']].add(p['b']);graph[p['b']].add(p['a'])
components=[]
unseen=set(graph)
while unseen:
    seed=sorted(unseen)[0];unseen.remove(seed);stack=[seed];comp=[]
    while stack:
        n=stack.pop();comp.append(n)
        for nxt in sorted(graph[n]&unseen):
            unseen.remove(nxt);stack.append(nxt)
    components.append(sorted(comp))
floor_epsilon=0.03
floor_candidates=[r.name for r,b in zip(roots,boxes) if abs(b[0][2])<=floor_epsilon]
report={
 'asset':'Windwaiting Cliff C local spatial skeleton',
 'status':'STRUCTURAL_AUDIT_NOT_ART_APPROVAL',
 'roots':[{'name':r.name,'min_xyz':b[0],'max_xyz':b[1],'mesh_count':b[2]} for r,b in zip(roots,boxes)],
 'floor_aabb_candidates':floor_candidates,
 'aabb_overlap_candidates':pairs,
 'aabb_connected_components':components,
 'aabb_connectivity_gate':'FAIL' if len(components)>1 else 'CANDIDATE_ONLY',
 'mesh_surface_contact':'NOT_RUN',
 'physical_support':'NOT_RUN',
 'official_cg_alignment':'NOT_RUN',
 'G2':'NOT_RUN',
 'G3':'PARTIAL_AABB_ONLY',
 'note':'AABB overlap does not prove mesh intersections, real contact, collision, or physical support; isolated components are a definite negative signal.'
}
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('CLIFF_C_SPATIAL_AUDIT',json.dumps({'components':len(components),'overlap_candidates':len(pairs),'floor_candidates':len(floor_candidates)}),flush=True)
