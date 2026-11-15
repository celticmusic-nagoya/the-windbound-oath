"""EYELID-09: deterministic evaluated-triangle lash root attachment (no Blender mutation)."""
import math

def sub(a,b): return tuple(x-y for x,y in zip(a,b))
def add(a,b): return tuple(x+y for x,y in zip(a,b))
def mul(a,s): return tuple(x*s for x in a)
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def cross(a,b): return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def unit(a):
    n=math.sqrt(dot(a,a))
    if n<1e-12 or not math.isfinite(n): raise ValueError("degenerate vector")
    return mul(a,1/n)

def evaluated_root(vertices,triangle,weights,anterior=(0,1,0),tangent_hint=(1,0,0)):
    """Return root position and oriented orthonormal frame for an evaluated lid triangle.

    Triangle topology/indexing must remain stable between poses. Weights are
    invariant barycentric coordinates. All coordinates use model units.
    """
    if len(triangle)!=3 or len(set(triangle))!=3: raise ValueError("invalid triangle")
    if len(weights)!=3 or not all(math.isfinite(w) and -1e-9<=w<=1+1e-9 for w in weights) or abs(sum(weights)-1)>1e-8:
        raise ValueError("invalid barycentric weights")
    try: a,b,c=[tuple(float(x) for x in vertices[i]) for i in triangle]
    except (IndexError,KeyError,TypeError) as exc: raise ValueError("invalid vertex index") from exc
    if any(len(p)!=3 or not all(math.isfinite(x) for x in p) for p in (a,b,c)):
        raise ValueError("invalid vertex coordinates")
    normal=unit(cross(sub(b,a),sub(c,a)))
    if dot(normal,unit(anterior))<0: normal=mul(normal,-1)
    tangent=sub(tangent_hint,mul(normal,dot(tangent_hint,normal)))
    if dot(tangent,tangent)<1e-20:
        edge=sub(b,a)
        tangent=sub(edge,mul(normal,dot(edge,normal)))
    tangent=unit(tangent)
    binormal=unit(cross(normal,tangent))
    position=add(add(mul(a,weights[0]),mul(b,weights[1])),mul(c,weights[2]))
    return {"position":position,"normal":normal,"tangent":tangent,"binormal":binormal}

def offset_root(vertices,triangle,weights,offset,**kwargs):
    if not math.isfinite(offset) or offset<0: raise ValueError("invalid offset")
    frame=evaluated_root(vertices,triangle,weights,**kwargs)
    frame["root_position"]=add(frame["position"],mul(frame["normal"],offset))
    return frame
