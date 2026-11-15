"""Piecewise-linear anterior clearance inequalities on overlapping projected triangles."""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import coo_matrix


def overlap_polygon(a,b):
    cross=lambda x,y:float(x[0]*y[1]-x[1]*y[0])
    if cross(b[1]-b[0],b[2]-b[0])<0:b=b[::-1]
    polygon=list(a)
    for x,y in zip(b,np.roll(b,-1,axis=0)):
        old=polygon;polygon=[]
        if not old:break
        for p,q in zip(old,old[1:]+old[:1]):
            dp=cross(y-x,p-x);dq=cross(y-x,q-x)
            if dp>=-1e-14:polygon.append(p)
            if (dp>=0)!=(dq>=0):polygon.append(p+(q-p)*dp/(dp-dq))
    return polygon


def barycentric_2d(p,triangle):
    ab=triangle[1:]-triangle[0];weights=np.linalg.solve(ab.T,p-triangle[0])
    return np.r_[1-sum(weights),weights]


def clear_eye(front,triangles,eye,eye_triangles,locked,thickness=.0006,clearance=.0002,max_lift=.003):
    projected=front[:,[0,2]];et=eye[eye_triangles];ep=et[:,:,[0,2]]
    emin=ep.min(axis=1);emax=ep.max(axis=1)
    rows=[];columns=[];values=[];rhs=[]
    for ids in triangles:
        t=projected[ids];low=t.min(axis=0);high=t.max(axis=0)
        candidates=np.flatnonzero(np.all(emax>=low-1e-12,axis=1)&np.all(emin<=high+1e-12,axis=1))
        for j in candidates:
            if abs(np.linalg.det((ep[j,1:]-ep[j,0]).T))<1e-14:continue
            for point in overlap_polygon(t,ep[j]):
                wc=barycentric_2d(point,t);we=barycentric_2d(point,ep[j])
                need=float(we@et[j,:,1]+thickness+clearance-wc@front[ids,1])
                if need<=1e-9:continue
                i=len(rhs);rhs.append(-need)
                for v,w in zip(ids,wc):rows.append(i);columns.append(int(v));values.append(-float(w))
    if not rhs:return front,{'constraint_count':0,'max_lift_m':0.,'eye_clearance_m':clearance}
    matrix=coo_matrix((values,(rows,columns)),shape=(len(rhs),len(front))).tocsr()
    result=linprog(np.ones(len(front)),A_ub=matrix,b_ub=rhs,bounds=[(0,0) if i in locked else (0,max_lift) for i in range(len(front))],method='highs')
    if not result.success:raise ValueError('No source-anchor-preserving eye clearance solution: '+result.message)
    lifted=front.copy();lifted[:,1]+=result.x
    return lifted,{'constraint_count':len(rhs),'max_lift_m':float(max(result.x)),'eye_clearance_m':clearance,'maximum_allowed_lift_m':max_lift,'locked_vertex_count':len(locked),'solver':'HiGHS linear inequalities at every projected triangle-overlap polygon vertex'}
