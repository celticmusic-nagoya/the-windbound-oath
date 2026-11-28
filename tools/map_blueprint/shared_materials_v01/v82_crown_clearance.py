"""V82 candidate: conservative finite camera corridor vs transformed crown bounds.
Pure Python; no Blender dependency. Run directly for synthetic regression tests.
A possible overlap is a placement rejection/inspection signal, NOT proof of pixel occlusion.
All units are provisional asset-local; never changes a native file.
"""
from math import isfinite, sqrt


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def unit(a):
    n = sqrt(dot(a, a))
    if not isfinite(n) or n < 1e-9:
        raise ValueError('degenerate camera basis')
    return tuple(x/n for x in a)


def vec(a):
    a = tuple(float(x) for x in a)
    if len(a) != 3 or not all(isfinite(x) for x in a):
        raise ValueError('expected finite XYZ')
    return a


def bounds(points):
    pts = [vec(p) for p in points]
    if not pts:
        raise ValueError('empty crown')
    return tuple(min(p[i] for p in pts) for i in range(3)), tuple(max(p[i] for p in pts) for i in range(3))


def possible_overlap(eye, target, lo, hi, half_width, half_height, *, padding=0.15, near=0.05, behind=0.0):
    """Conservative plane rejection; half extents refer to target plane, not lens/FOV.
    Supply transformed actual foliage vertices (not trunk origin) to bounds().
    Boxes intersecting the near-to-target sight corridor are flagged. Padding is local units.
    """
    eye, target, lo, hi = map(vec, (eye, target, lo, hi))
    scalars = (half_width, half_height, padding, near, behind)
    if not all(isfinite(x) for x in scalars) or min(half_width, half_height, near) <= 0 or min(padding, behind) < 0 or any(a>b for a,b in zip(lo,hi)):
        raise ValueError('invalid corridor/bounds')
    f = unit(sub(target, eye)); depth = sqrt(dot(sub(target, eye), sub(target, eye)))
    if near >= depth:
        raise ValueError('near plane beyond target')
    up_hint = (0,0,1) if abs(f[2]) < .99 else (0,1,0)
    right = unit(cross(f, up_hint)); up = cross(right, f)
    def mul(a,s): return tuple(x*s for x in a)
    def add(a,b): return tuple(x+y for x,y in zip(a,b))
    # Every plane is dot(normal, point-eye) >= offset. A box outside any plane is clear.
    planes = [(f,near),(mul(f,-1),-depth-behind)]
    for axis, extent in ((right,half_width),(up,half_height)):
        for sign in (-1,1):
            planes.append((add(mul(f,extent/depth),mul(axis,sign)),0.0))
    lo = tuple(x-padding for x in lo); hi = tuple(x+padding for x in hi)
    for n, offset in planes:
        farthest = tuple(hi[i] if n[i]>=0 else lo[i] for i in range(3))
        if dot(n,sub(farthest,eye)) < offset - 1e-9:
            return False
    return True


def selftest():
    e=(0,0,1.7); t=(0,10,1.7)
    cases=[('central',( -.5,4,1),(.5,5,3),True),('off-axis trunk but spreading crown',(.5,4,1.5),(3,6,3),True),('clear side',(4,4,1),(5,5,3),False),('clear above',(-1,4,5),(1,6,7),False),('behind target',(-1,12,0),(1,13,4),False),('behind camera',(-1,-3,0),(1,-1,3),False),('near camera',(-.1,.01,1.6),(.1,.2,1.8),True),('touch with padding',(1.15,5,1.6),(2,5,1.8),True)]
    for name,lo,hi,want in cases:
        assert possible_overlap(e,t,lo,hi,2,2)==want,name
    assert bounds([(2,3,4),(-1,5,0)])==((-1.,3.,0.),(2.,5.,4.))
    assert possible_overlap((0,0,0),(0,0,10),(-.2,-.2,4),(.2,.2,5),2,2)
    for args in [(e,e,(0,0,0),(1,1,1),2,2),(e,t,(1,1,1),(0,0,0),2,2),(e,t,(0,0,0),(1,1,1),float('nan'),2)]:
        try: possible_overlap(*args)
        except ValueError: pass
        else: raise AssertionError('invalid input accepted')
    print('V82_CROWN_CLEARANCE: 13/13 synthetic assertions PASS')


if __name__=='__main__':
    selftest()
