"""Mesh-independent contact cage QA: closed orientation and interior intersections."""
from collections import defaultdict
import numpy as np


def edge_audit(faces):
    edges=defaultdict(list)
    for i,face in enumerate(faces):
        for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((a,b)))].append((i,a<b))
    return {'boundary_or_nonmanifold_edges':sum(len(v)!=2 for v in edges.values()),
            'inconsistent_edge_directions':sum(len(v)==2 and v[0][1]==v[1][1] for v in edges.values()),
            'edge_count':len(edges)}


def proper_triangle_crossing(a,b,epsilon=1e-9):
    for triangle,segments in ((a,b),(b,a)):
        v0,v1,v2=triangle;e1=v1-v0;e2=v2-v0
        for i in range(3):
            start=segments[i];d=segments[(i+1)%3]-start;h=np.cross(d,e2);det=e1@h
            if abs(det)<1e-14:continue
            s=start-v0;u=(s@h)/det;q=np.cross(s,e1);v=(d@q)/det;t=(e2@q)/det
            if epsilon<u<1-epsilon and epsilon<v and u+v<1-epsilon and epsilon<t<1-epsilon:return True
    return False


def coplanar_overlap_area(a,b):
    n=np.cross(a[1]-a[0],a[2]-a[0]);m=np.cross(b[1]-b[0],b[2]-b[0])
    if np.linalg.norm(n)<1e-14 or np.linalg.norm(m)<1e-14:return 0.
    n=n/np.linalg.norm(n);m=m/np.linalg.norm(m)
    if abs(n@m)<1-1e-8 or max(abs((b-a[0])@n))>1e-8:return 0.
    axis=np.argmax(abs(n));aa=np.delete(a,axis,axis=1);bb=np.delete(b,axis,axis=1)
    cross=lambda x,y:float(x[0]*y[1]-x[1]*y[0])
    if cross(bb[1]-bb[0],bb[2]-bb[0])<0:bb=bb[::-1]
    polygon=list(aa)
    for x,y in zip(bb,np.roll(bb,-1,axis=0)):
        old=polygon;polygon=[]
        if not old:break
        for p,q in zip(old,old[1:]+old[:1]):
            dp=cross(y-x,p-x);dq=cross(y-x,q-x)
            if dp>=0:polygon.append(p)
            if (dp>=0)!=(dq>=0):polygon.append(p+(q-p)*dp/(dp-dq))
    if len(polygon)<3:return 0.
    return abs(sum(cross(p,q) for p,q in zip(polygon,polygon[1:]+polygon[:1])))*.5/max(abs(n[axis]),1e-12)
