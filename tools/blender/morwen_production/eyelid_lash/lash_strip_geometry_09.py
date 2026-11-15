"""EYELID-09 isolated lash-strip geometry builder.

Technical scaffold only: generated strips are NOT approved character artwork.
Input frames must come from evaluated lid triangles. No original mesh edits.
"""
import math
from lash_attachment_09 import add, mul, unit, dot, sub

def build_lash_strip(frame, length_m, width_m, root_offset_m=0.0001,
                     curl=0.22, samples=5):
    if samples<3 or not isinstance(samples,int): raise ValueError("samples must be >= 3")
    if any(not math.isfinite(x) for x in (length_m,width_m,root_offset_m,curl)):
        raise ValueError("nonfinite strip parameter")
    if length_m<=0 or width_m<=0 or root_offset_m<0 or not 0<=curl<=1:
        raise ValueError("invalid strip dimensions")
    p=frame["position"]
    normal=unit(frame["normal"]); tangent=unit(frame["tangent"])
    binormal=unit(frame["binormal"])
    if abs(dot(normal,tangent))>1e-5 or abs(dot(normal,binormal))>1e-5:
        raise ValueError("invalid attachment frame")
    # Normal clearance increases along the strip. The curl is a design
    # parameter, NOT a collision guarantee against surrounding geometry.
    verts=[];uv=[]
    for i in range(samples):
        t=i/(samples-1)
        center=add(add(p,mul(binormal,length_m*t)),
                   mul(normal,root_offset_m+curl*length_m*t*t))
        half_width=width_m*(1-t)**1.3/2
        for sign in (-1,1):
            verts.append(add(center,mul(tangent,sign*half_width)))
            uv.append(((sign+1)/2,t))
    faces=[]
    for i in range(samples-1):
        a=2*i
        faces.append((a,a+1,a+3,a+2))
    return {"vertices":verts,"faces":faces,"uv":uv,
            "metadata":{"root_offset_m":root_offset_m,
                        "length_m":length_m,"width_m":width_m,
                        "collision_qa":"NOT_RUN","art_qa":"NOT_RUN"}}
