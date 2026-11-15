"""Matched-column thick contact cage; no harmonic solver or expression transfer."""
import numpy as np


def walk_cycle(edges):
    graph={}
    unique=set()
    for a,b in edges:
        edge=tuple(sorted((a,b)))
        if a==b or edge in unique:raise ValueError('Degenerate/duplicate edge')
        unique.add(edge);graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    if not graph or any(len(n)!=2 for n in graph.values()):raise ValueError('Expected degree-two cycle')
    start=min(graph);ordered=[start];previous=None;current=start
    while True:
        nxt=min(graph[current]-({previous} if previous is not None else set()))
        if nxt==start:break
        if nxt in ordered:raise ValueError('Repeated vertex')
        ordered.append(nxt);previous,current=current,nxt
    if len(ordered)!=len(graph):raise ValueError('Disconnected cycles')
    return ordered


def split(ids,a,b,xyz):
    i=ids.index(a);ring=ids[i:]+ids[:i];j=ring.index(b)
    first=ring[:j+1];second=[ring[0]]+list(reversed(ring[j:]))
    if min(len(first),len(second))<3:raise ValueError('Degenerate arc')
    return sorted((first,second),key=lambda chain:-np.mean([xyz[v][2] for v in chain[1:-1]]))


def parameters(points):
    points=np.asarray(points,float);ds=np.linalg.norm(np.diff(points,axis=0),axis=1)
    if not np.isfinite(points).all() or np.any(ds<1e-10):raise ValueError('Invalid polyline')
    return np.r_[0,np.cumsum(ds)]/sum(ds)


def sample(points,u):
    p=np.asarray(points,float);us=parameters(p)
    return np.array([np.interp(u,us,p[:,k]) for k in range(3)]).T


def shared_columns(curves):
    # Include every original polyline knot so the attachment boundary is exact,
    # not chords across missing corners. Both arcs use this identical knot set.
    knots=list(np.linspace(0,1,33))
    for curve in curves:knots.extend(parameters(curve))
    knots=sorted(float(x) for x in knots)
    result=[]
    for u in knots:
        if not result or u-result[-1]>1e-8:result.append(u)
    return np.array(result)


def shell(inner_upper,inner_lower,outer_upper,outer_lower,rows=(0,.2,.45,.7,1),thickness=.0006):
    """Return one connected, watertight genus-one shell with a real open aperture.

    Front rows run from inner opening to fixed skin attachment. Rear lies exactly
    thickness behind the front in model anterior Y. Shared canthus columns have
    one vertex, not overlapping upper/lower duplicate walls.
    """
    curves=[np.asarray(c,float) for c in (inner_upper,inner_lower,outer_upper,outer_lower)]
    count=len(curves[0])
    if any(c.shape!=(count,3) for c in curves) or count<3:raise ValueError('Matched XYZ columns required')
    if thickness<=0 or not np.isfinite(curves).all():raise ValueError('Invalid shell')
    for a,b in ((curves[0][0],curves[1][0]),(curves[0][-1],curves[1][-1]),(curves[2][0],curves[3][0]),(curves[2][-1],curves[3][-1])):
        if np.linalg.norm(a-b)>1e-9:raise ValueError('Canthus columns must coincide')
    inner=np.r_[curves[0],curves[1][-2:0:-1]]
    outer=np.r_[curves[2],curves[3][-2:0:-1]]
    n=len(inner);front=[]
    for t in rows:front.extend((1-t)*inner+t*outer)
    front=np.asarray(front);rear=front-[0,thickness,0];verts=np.r_[front,rear];stride=len(front)
    faces=[];roles=[]
    def face(vs,role):faces.append(vs);roles.append(role)
    for r in range(len(rows)-1):
        for i in range(n):
            j=(i+1)%n
            vs=[r*n+i,r*n+j,(r+1)*n+j,(r+1)*n+i]
            # One consistent ring winding determined once, not per-face flips.
            if i==0 and r==0:
                p=verts[vs];orientation=np.cross(p[1]-p[0],p[2]-p[0])[1]
                reverse=orientation<0
            if reverse:vs=vs[::-1]
            face(vs,'front');face([v+stride for v in vs[::-1]],'rear')
    # Close each boundary by opposite winding to its neighboring front face.
    for r,role in ((0,'opening_wall'),(len(rows)-1,'attachment_wall')):
        for i in range(n):
            j=(i+1)%n;a,b=r*n+i,r*n+j
            vs=[a,a+stride,b+stride,b] if r==0 else [a,b,b+stride,a+stride]
            if reverse:vs=vs[::-1]
            face(vs,role)
    return verts,faces,roles,{'ring_vertices':n,'rows':list(rows),'front_vertex_count':stride,'thickness_anterior_m':thickness}


def inside_polygon(p,polygon):
    x,y=p;result=False
    for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result


def triangulate_aperture(outer,inner,spacing=.003):
    import triangle
    points=np.r_[outer,inner].tolist();segments=[]
    for offset,count in ((0,len(outer)),(len(outer),len(inner))):
        segments.extend([[offset+i,offset+(i+1)%count] for i in range(count)])
    for x in np.arange(outer[:,0].min()+spacing/2,outer[:,0].max(),spacing):
        for y in np.arange(outer[:,1].min()+spacing/2,outer[:,1].max(),spacing):
            if inside_polygon([x,y],outer) and not inside_polygon([x,y],inner):points.append([x,y])
    hole=inner.mean(axis=0)
    if not inside_polygon(hole,inner):raise ValueError('Explicit interior hole seed required')
    answer=triangle.triangulate({'vertices':np.array(points),'segments':np.array(segments),'holes':np.array([hole])},'pYQ')
    return answer
