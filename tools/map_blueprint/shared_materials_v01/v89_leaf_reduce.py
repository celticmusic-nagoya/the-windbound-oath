"""Retain leaf outlines, simplify only interior vertices in UV topology."""
from collections import Counter
from math import dist, sqrt

def cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])

def boundary(faces):
    e=Counter(tuple(sorted((t[i],t[(i+1)%3]))) for t in faces for i in range(3))
    if any(n>2 for n in e.values()):raise ValueError('nonmanifold leaf')
    return {k for k,n in e.items() if n==1}

def sample(p, faces, uv, xyz, q):
    best=None
    for t in faces:
        a,b,c=(uv[i] for i in t);den=cross(a,b,c)
        if abs(den)<1e-15:continue
        w=(cross(p,b,c)/den,cross(a,p,c)/den,cross(a,b,p)/den)
        if min(w)<-1e-7:continue
        x=tuple(sum(w[k]*xyz[t[k]][j] for k in range(3)) for j in range(3))
        err=dist(x,q)
        best=err if best is None else max(best,err)
    return best

def area3(t,p):
    a,b,c=(p[i] for i in t);u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    return .5*sqrt(sum((u[i]*v[(i+1)%3]-u[(i+1)%3]*v[i])**2 for i in range(3)))

def reduce_leaf(xyz,uv,faces,relative_tol=.04):
    faces=[tuple(t) for t in faces]
    if len(xyz)!=21 or len(uv)!=21 or len(faces)!=24:return faces,0.0
    edge=boundary(faces);outer={i for e in edge for i in e}
    if len(outer)!=16:return faces,0.0
    span=sqrt(sum((max(v[i] for v in xyz)-min(v[i] for v in xyz))**2 for i in range(3)))
    if span<=1e-9:return faces,0.0
    uvareas=[cross(*(uv[i] for i in t)) for t in faces]
    if min(map(abs,uvareas))<1e-12 or min(uvareas)*max(uvareas)<=0:return faces,0.0
    sign=1 if uvareas[0]>0 else -1
    oldarea=sum(area3(t,xyz) for t in faces)
    current=faces[:];removed=[];worst=0.
    for v in sorted(set(range(21))-outer):
        star=[t for t in current if v in t];rest=[t for t in current if v not in t]
        nxt={t[(t.index(v)+1)%3]:t[(t.index(v)+2)%3] for t in star}
        if len(nxt)!=len(star) or len(nxt)<3:continue
        ring=[min(nxt)]
        while len(ring)<len(nxt):
            k=nxt.get(ring[-1]);
            if k is None or k in ring:break
            ring.append(k)
        if len(ring)!=len(nxt) or nxt.get(ring[-1])!=ring[0]:continue
        best=None
        for i in range(len(ring)):
            rr=ring[i:]+ring[:i];fan=[(rr[0],rr[j],rr[j+1]) for j in range(1,len(rr)-1)]
            if any(sign*cross(*(uv[k] for k in t))<=1e-12 or area3(t,xyz)<=1e-15 for t in fan):continue
            candidate=rest+fan
            # Verify every previously removed vertex in the entire new UV triangulation.
            errors=[sample(uv[k],candidate,uv,xyz,xyz[k]) for k in removed+[v]]
            if any(e is None for e in errors):continue
            residual=max(errors)/span
            if residual>relative_tol:continue
            if best is None or residual<best[0]:best=(residual,candidate)
        if best is not None:worst,current=best;removed.append(v)
    if not removed:return faces,0.0
    ratio=sum(area3(t,xyz) for t in current)/oldarea
    if not .85<=ratio<=1.15 or boundary(current)!=edge or abs(sum(cross(*(uv[i] for i in t)) for t in current)-sum(uvareas))>1e-9:return faces,0.0
    assert len(current)==24-2*len(removed)
    return current,worst
