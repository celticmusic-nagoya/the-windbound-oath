import json,re,math,copy
K=2.5; SPEED=300.0; FOOT_W,FOOT_H=22,10; STRIPE=8
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])
def seg_proj(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]; L2=dx*dx+dy*dy
    t=0 if L2==0 else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/L2))
    q=(a[0]+t*dx,a[1]+t*dy); return dist(p,q),q
def project(p,skel):
    best=(1e18,None)
    for pl in skel:
        for i in range(len(pl)-1):
            d,q=seg_proj(p,pl[i],pl[i+1])
            if d<best[0]: best=(d,q)
    return best[1]
def poly_len(pl): return sum(dist(pl[i],pl[i+1]) for i in range(len(pl)-1))
# ---- ellipse/polygon -> stripe rects (inscribed, deterministic)
def ellipse_rects(cx,cy,rx,ry,n=None,step=None,shrink=0.92):
    top,bot=cy-ry,cy+ry; n=n or max(1,round((2*ry)/step)); h=(bot-top)/n; out=[]
    for i in range(n):
        y0=top+i*h; ym=y0+h/2; t=(ym-cy)/ry
        hw=rx*math.sqrt(max(0,1-t*t))*shrink
        if hw<2: continue
        out.append([round(cx-hw,1),round(y0,1),round(2*hw,1),round(h,1)])
    return out
def poly_rects(pts,step=STRIPE):
    ys=[p[1] for p in pts]; y0,y1=min(ys),max(ys); out=[]; y=y0
    while y<y1:
        ym=y+step/2; xs=[]
        for i in range(len(pts)):
            a,b=pts[i],pts[(i+1)%len(pts)]
            if (a[1]<=ym<b[1]) or (b[1]<=ym<a[1]):
                xs.append(a[0]+(ym-a[1])*(b[0]-a[0])/(b[1]-a[1]))
        xs.sort()
        for j in range(0,len(xs)-1,2):
            if xs[j+1]-xs[j]>=2: out.append([round(xs[j],1),round(y,1),round(xs[j+1]-xs[j],1),step])
        y+=step
    return merge_rects(out)
def merge_rects(rs):
    rs=sorted(rs,key=lambda r:(r[0],r[2],r[1])); out=[]
    for r in rs:
        if out and abs(out[-1][0]-r[0])<.5 and abs(out[-1][2]-r[2])<.5 and abs(out[-1][1]+out[-1][3]-r[1])<.5:
            out[-1][3]=round(out[-1][3]+r[3],1)
        else: out.append(list(r))
    return out
# asset collision presets: rects relative to anchor (bottom-center), y<=0 is above base
TREE_L=ellipse_rects(0,-6,24,10,n=3); TREE_M=ellipse_rects(0,-4,16,7,n=3); TREE_S=ellipse_rects(0,-2,8,4,n=2)
PRESET={
 'tree_oak_L':TREE_L,'tree_mossy_L':TREE_L,'tree_oak_M':TREE_M,'tree_birch_M':TREE_M,'tree_dead_taint_M':TREE_M,
 'tree_stump':[[-14,-8,28,8]],'tree_log_fallen_H':[[-90,-22,180,22]],'tree_log_fallen_D':[[-60,-30,120,30]],
 'tree_ancient_sentinel':ellipse_rects(0,-20,70,26,n=5),
 'tree_ancient_great':ellipse_rects(0,-30,150,55,step=12),
 'tree_log_hollow_A3':[[-170,-72,340,28],[-170,-8,340,8]],
 'rock_S':[[-18,-14,36,14]],'rock_M':[[-38,-10,76,10],[-30,-24,60,14]],'rock_L':[[-66,-12,132,12],[-56,-28,112,16],[-40,-44,80,16]],
 'rock_moss_S':[[-18,-14,36,14]],'rock_moss_M':[[-38,-10,76,10],[-30,-24,60,14]],'rock_moss_L':[[-66,-12,132,12],[-56,-28,112,16],[-40,-44,80,16]],
 'prop_marker_signpost':[[-12,-10,24,10]],'prop_marker_fork':[[-14,-10,28,10]],'prop_post_boundary_wood':[[-8,-8,16,8]],
 'prop_lean_to':[[-70,-30,140,30]],'prop_campfire_cold':[[-14,-8,28,8]],
 'anc_boundary_stone':[[-22,-14,44,14]],'anc_standing_L':[[-24,-16,48,16]],'anc_rune_broken':[[-30,-14,60,14]],
 'anc_shrine_frag':[[-34,-20,68,20]],'anc_arch_broken':[[-110,-14,40,14],[70,-14,40,14]],
 'veg_thorn_L':[[-22,-12,44,12]],'veg_thorn_M':[[-14,-8,28,8]],
}
def preset(asset):
    a=re.sub(r'_\d+$','',asset)
    return PRESET.get(a)
def shape_rects(s):
    t=s.get('shape')
    if t=='rects': return [list(r) for r in s['rects']]
    if t=='rect': return [[s['x'],s['y'],s['w'],s['h']]]
    if t=='ellipse': return ellipse_rects(s['cx'],s['cy'],s['rx'],s['ry'],step=12)
    if t=='circle': return ellipse_rects(s['cx'],s['cy'],s['r'],s['r'],step=12)
    if t=='polygon': return poly_rects(s['points'])
    raise ValueError(t)
def compile_collision(m,flags=None):
    flags=flags or {}; R=[]
    for s in m['collision']['edgeBlockers']: R+= [(('edge',),*shape_rects(s))] if False else [('edge',r) for r in shape_rects(s)]
    for b in m['collision']['blockers']:
        w=b.get('enabledWhen')
        if w and flags.get(w['flag'],False)!=w['is']: continue
        R+=[(b['id'],r) for r in shape_rects(b)]
    for p in m['props']:
        if p.get('noCollision'): continue
        pr=preset(p['asset'])
        if not pr: continue
        for r in pr:
            x=r[0]; 
            if p.get('flip'): x=-r[0]-r[2]
            R.append((p['id'],[p['x']+x,p['y']+r[1],r[2],r[3]]))
    return R
class Hash:
    def __init__(s,rects,cell=128):
        s.c=cell; s.g={}; s.n=len(rects)
        for o,r in rects:
            for gx in range(int(r[0]//cell),int((r[0]+r[2])//cell)+1):
                for gy in range(int(r[1]//cell),int((r[1]+r[3])//cell)+1): s.g.setdefault((gx,gy),[]).append((o,r))
    def hit(s,fx,fy):
        x0,x1,y0,y1=fx-FOOT_W/2,fx+FOOT_W/2,fy-FOOT_H,fy
        for gx in range(int(x0//s.c),int(x1//s.c)+1):
            for gy in range(int(y0//s.c),int(y1//s.c)+1):
                for o,r in s.g.get((gx,gy),()):
                    if x1>r[0] and x0<r[0]+r[2] and y1>r[1] and y0<r[1]+r[3]: return o
        return None
def sample(pl,step=8):
    out=[pl[0]]
    for i in range(len(pl)-1):
        a,b=pl[i],pl[i+1]; n=max(1,int(dist(a,b)//step))
        for j in range(1,n+1): out.append((a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n))
    return out
def validate(m,label):
    rects=compile_collision(m); H=Hash(rects); rep=[]; ok=True
    W,Hh=m['world']['width'],m['world']['height']
    for name,pl in m['_routes'].items():
        bad=[]
        for p in sample(pl):
            o=H.hit(*p)
            if o and not(name.startswith('edge')): bad.append((round(p[0]),round(p[1]),o))
        # allow the last sample at world edge (transition mouth)
        rep.append((name,round(poly_len(pl)),round(poly_len(pl)/SPEED,1),len(bad),bad[:3])); ok&=(len(bad)==0)
    for k,s in m['spawns']['points'].items():
        o=H.hit(s['x'],s['y']); inb=0<s['x']<W and 0<s['y']<Hh
        rep.append(('spawn:'+k,None,None,0 if (not o and inb) else 1,[o])); ok&=(not o and inb)
    return ok,rep,len(rects)

def validate2(m,flags):
    global compile_collision
    rects=compile_collision(m,flags); H=Hash(rects); rep=[]; ok=True
    for name,pl in m['_routes'].items():
        bad=[p for p in sample(pl) if H.hit(*p)]
        rep.append((name,len(bad),[ (round(p[0]),round(p[1]),H.hit(*p)) for p in bad[:2]])); ok&=(not bad)
    return ok,rep,H
def reach(m,H,start,step=12):
    from collections import deque
    W,Hh=m['world']['width'],m['world']['height']; sx,sy=round(start[0]/step),round(start[1]/step)
    seen={(sx,sy)}; q=deque([(sx,sy)])
    while q:
        x,y=q.popleft()
        for dx,dy in((1,0),(-1,0),(0,1),(0,-1)):
            nx,ny=x+dx,y+dy
            if (nx,ny) in seen or not(0<nx*step<W and 0<ny*step<Hh): continue
            if H.hit(nx*step,ny*step): continue
            seen.add((nx,ny)); q.append((nx,ny))
    return lambda p:(round(p[0]/step),round(p[1]/step)) in seen, len(seen)
