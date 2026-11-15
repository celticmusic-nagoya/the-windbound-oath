"""Strict interior triangle crossings; boundary contacts are reported separately."""
import numpy as np


def segment_triangle(a,b,triangle,epsilon=1e-9):
    # Moller-Trumbore, excluding endpoints/triangle boundary contacts.
    v0,v1,v2=triangle;d=b-a;e1=v1-v0;e2=v2-v0
    h=np.cross(d,e2);det=float(e1@h)
    if abs(det)<1e-14:return False
    s=a-v0;u=float(s@h)/det
    q=np.cross(s,e1);v=float(d@q)/det;t=float(e2@q)/det
    return epsilon<u<1-epsilon and epsilon<v and u+v<1-epsilon and epsilon<t<1-epsilon


def proper_crossing(a,b):
    for first,second in ((a,b),(b,a)):
        for i in range(3):
            if segment_triangle(first[i],first[(i+1)%3],second):return True
    return False
