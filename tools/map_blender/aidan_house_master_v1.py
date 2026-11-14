"""Deterministic high-detail candidate. No approved assets overwritten. Blender 4/5."""
import bpy,random,math,json
R=random.Random(141126)
D={'length':8.4,'width':7.1,'wall_top':3.05,'ridge_z':6.60,'door_width':1.25}
COUNT={'slates':0,'stones':0,'timbers':0,'ridge_caps':0}
def mat(n,c):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True
 m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(*c,1)
 return m
def mesh(col,n,v,f,m):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update()
 o=bpy.data.objects.new(n,me);col.objects.link(o);me.materials.append(m);return o
def box(col,n,center,size,m):
 x,y,z=center;a,b,c=[q/2 for q in size]
 v=[(x+i*a,y+j*b,z+k*c) for k in (-1,1) for j in (-1,1) for i in (-1,1)]
 o=mesh(col,n,v,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],m)
 b=o.modifiers.new('edge rounding','BEVEL');b.width=.035;b.segments=2
 o.modifiers.new('weighted normals','WEIGHTED_NORMAL');return o
def build():
 name='AIDAN_HIGH_DETAIL_MASTER_CANDIDATE_V1'
 if bpy.data.collections.get(name):raise RuntimeError('Refuse overwrite')
 root=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(root)
 def layer(n):
  c=bpy.data.collections.new(n);root.children.link(c);return c
 base=layer('01_FOUNDATION_FRAME');wall=layer('02_STONEWORK');roof=layer('03_INDIVIDUAL_SLATES');detail=layer('04_JOINERY')
 stone=[mat('stone %s'%i,c) for i,c in enumerate([(.55,.51,.45),(.62,.57,.49),(.46,.46,.42),(.65,.61,.53)])]
 slate=[mat('bluegray slate %s'%i,c) for i,c in enumerate([(.22,.29,.35),(.28,.34,.40),(.34,.39,.44),(.19,.25,.31)])]
 wood=mat('weathered oak',(.30,.20,.13));iron=mat('iron',(.12,.11,.10))
 L=D['length']/2;W=D['width']/2;H=D['wall_top'];Z=D['ridge_z']
 box(base,'foundation',(0,0,-.20),(8.7,7.4,.4),stone[0])
 for x in (-L,L):
  for y in (-W,W):
   box(base,'load-bearing post',(x,y,H/2),(.25,.25,H),wood);COUNT['timbers']+=1
 for y in (-W,W):
  box(base,'long eave beam',(0,y,H),(8.9,.25,.25),wood);COUNT['timbers']+=1
 box(base,'ridge beam',(0,0,Z),(9.0,.23,.24),wood);COUNT['timbers']+=1
 # Each stone is a separate, irregularly sized 3D block, staggered by course.
 for axis,fixed,start,end,front in [('x',-W,-L,L,True),('x',W,-L,L,False),('y',-L,-W,W,False),('y',L,-W,W,False)]:
  z=.08
  while z<H-.12:
   height=min(R.uniform(.24,.38),H-z-.02);p=start+R.uniform(-.4,0)
   while p<end:
    width=R.uniform(.44,.90);a=max(p,start);b=min(p+width,end);mid=(a+b)/2
    if b-a>.20 and not (front and a<.72 and b>-.72 and z<2.3):
     depth=R.uniform(.23,.35)
     pos=(mid,fixed,z+height/2) if axis=='x' else (fixed,mid,z+height/2)
     size=(b-a-.025,depth,height-.02) if axis=='x' else (depth,b-a-.025,height-.02)
     box(wall,'stone_%04d'%COUNT['stones'],pos,size,R.choice(stone))
     COUNT['stones']+=1
    p+=width+.025
   z+=height+.02
 # Door: physically open masonry area and recessed framed door.
 box(detail,'door leaf',(0,-W+.13,1.08),(1.15,.15,2.14),wood)
 for x in (-.73,.73):
  box(detail,'door jamb',(x,-W,1.16),(.15,.32,2.32),wood);COUNT['timbers']+=1
 box(detail,'door lintel',(0,-W,2.34),(1.65,.34,.20),wood)
 for x in (-.4,.4):box(detail,'iron hinge',(x,-W-.10,.8),(.22,.05,.08),iron)
 # Side window assembly is candidate; openings in masonry NOT YET CUT.
 for x in (-L-.18,L+.18):
  for z in (1.28,2.44):box(detail,'window crossbar',(x,.6,z),(.24,1.4,.13),wood)
  for y in (-.10,1.30):box(detail,'window jamb',(x,y,1.85),(.24,.13,1.20),wood)
 # Individually modeled slate prisms, varied overlap, thickness and camber.
 for side in (-1,1):
  for row in range(20):
   t=row/20;t2=min(1,(row+1.35)/20)
   for column in range(28):
    x=-L-.34+(column+(.5 if row%2 else 0))*(D['length']+.68)/28
    x2=min(x+(D['length']+.68)/28*.97,L+.34)
    if x2-x<.10:continue
    dz=R.uniform(-.015,.015)
    def point(px,tt):return (px,side*(W+.34)*tt,Z+(H-.08-Z)*tt+dz)
    verts=[point(x,t),point((x+x2)/2,t),point(x2,t),point(x2,t2),point((x+x2)/2,t2),point(x+R.uniform(.0,.04),t2)]
    verts[1]=(verts[1][0],verts[1][1],verts[1][2]+R.uniform(.01,.035))
    n=len(verts);verts+= [(a,b,c-.05) for a,b,c in verts]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    mesh(roof,'slate_%04d'%COUNT['slates'],verts,faces,R.choice(slate));COUNT['slates']+=1
 for i in range(30):
  x=-L-.30+(i+.5)*(D['length']+.60)/30
  box(roof,'ridge cap',(x,0,Z+.07),(.28,.34,.13),R.choice(slate));COUNT['ridge_caps']+=1
 # Candidate porch control members, not final detailing.
 for x in (-1.22,1.22):
  box(detail,'porch post',(x,-W-1.0,1.3),(.18,.18,2.6),wood);COUNT['timbers']+=1
 box(detail,'porch header',(0,-W-1.0,2.63),(2.70,.23,.22),wood)
 result={'status':'HIGH_DETAIL_MASTER_CANDIDATE_NOT_ART_APPROVED','seed':141126,
 'dimensions_candidate':D,'counts':COUNT,'objects':sum(len(c.objects) for c in (base,wall,roof,detail)),
 'uv':'NOT_RUN','pbr_textures':'NOT_APPLIED','window_openings':'NOT_CUT',
 'chimney':'POSITION_UNRESOLVED','visual_target':'APPROVED_V1'}
 print('AIDAN_HD_QA='+json.dumps(result,sort_keys=True));return result
if __name__=='__main__':build()
