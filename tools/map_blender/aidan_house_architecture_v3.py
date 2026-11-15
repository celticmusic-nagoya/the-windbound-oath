"""Aidan house v3: architecture-first diagnostic candidate, NOT approved art.
Blender 3.x/4.x; deterministic seed, metres, Z up. No canonical assets touched.
"""
import bpy, math, json, os, random, hashlib
from pathlib import Path

SEED=141127
R=random.Random(SEED)
P={'length':8.4,'width':7.1,'eaves':3.05,'ridge':6.60,
   'door_width':1.25,'door_height':2.20,'window_width':1.65,
   'window_height':1.35,'porch_projection':1.55}
COUNT={'wall_segments':0,'roof_slates':0,'joinery':0}
def material(name,color,roughness=0.85):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bs=m.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(*color,1)
 bs.inputs['Roughness'].default_value=roughness
 return m
def obj(name,verts,faces,mat,group):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 o=bpy.data.objects.new(name,mesh);group.objects.link(o);o.data.materials.append(mat)
 return o
def prism(name,lo,hi,mat,group,bevel=0):
 x,y,z=lo;X,Y,Z=hi
 v=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
 o=obj(name,v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,group)
 if bevel:
  mod=o.modifiers.new('soft dressed edges','BEVEL');mod.width=bevel;mod.segments=2
  o.modifiers.new('weighted normals','WEIGHTED_NORMAL')
 return o
def beam(name,a,b,width,depth,mat,group):
 # oriented solid timber between two endpoints, including pitched rafters
 ax,ay,az=a;bx,by,bz=b
 dx,dy,dz=bx-ax,by-ay,bz-az
 length=math.sqrt(dx*dx+dy*dy+dz*dz)
 o=prism(name,(-width/2,-depth/2,-length/2),(width/2,depth/2,length/2),mat,group,.012)
 o.location=((ax+bx)/2,(ay+by)/2,(az+bz)/2)
 o.rotation_mode='QUATERNION'
 from mathutils import Vector
 o.rotation_quaternion=Vector((0,0,1)).rotation_difference(Vector((dx,dy,dz)))
 return o
def build():
 root=bpy.data.collections.new('AIDAN_V3_ARCHITECTURE_DIAGNOSTIC')
 bpy.context.scene.collection.children.link(root)
 def layer(n):
  c=bpy.data.collections.new(n);root.children.link(c);return c
 foundation=layer('01_FOUNDATION');walls=layer('02_STRUCTURAL_WALLS')
 roof=layer('03_ROOF_STRUCTURE');tiles=layer('04_ROOF_SLATES')
 joinery=layer('05_OPENINGS_AND_JOINERY');porch=layer('06_PORCH_STRUCTURE')
 stone=material('v3 warm grey limestone',(.43,.42,.38))
 mortar=material('v3 recessed mortar',(.28,.27,.25))
 wood=material('v3 dark aged oak',(.22,.14,.085))
 slate=[material('v3 slate %d'%i,c) for i,c in enumerate(((.18,.23,.29),(.21,.27,.32),(.24,.29,.34)))]
 glass=material('v3 amber glazing',(.42,.25,.10),.22)
 L=P['length']/2;W=P['width']/2;H=P['eaves'];Z=P['ridge']
 prism('continuous footing',(-L-.2,-W-.2,-.32),(L+.2,W+.2,0),stone,foundation,.045)
 # Wall openings are genuine empty space, not windows pasted over solid walls.
 def wall(name,lo,hi):
  prism(name,lo,hi,stone,walls,.022);COUNT['wall_segments']+=1
 # Front -Y: centered door with proper structural lintel
 dw=P['door_width']/2+.16;dh=P['door_height']
 wall('front left',(-L,-W-.16,0),(-dw,-W+.16,H))
 wall('front right',(dw,-W-.16,0),(L,-W+.16,H))
 wall('front lintel wall',(-dw,-W-.16,dh),(dw,-W+.16,H))
 wall('rear',(-L,W-.16,0),(L,W+.16,H))
 wall('left',(-L-.16,-W+.16,0),(-L+.16,W-.16,H))
 # Right wall: real window void, separate lower, upper and side piers
 wy=.45; ww=P['window_width']/2+.12; z0=1.12;z1=z0+P['window_height']
 wall('right below window',(L-.16,-W+.16,0),(L+.16,W-.16,z0))
 wall('right above window',(L-.16,-W+.16,z1),(L+.16,W-.16,H))
 wall('right front pier',(L-.16,-W+.16,z0),(L+.16,wy-ww,z1))
 wall('right rear pier',(L-.16,wy+ww,z0),(L+.16,W-.16,z1))
 # Exposed structural timber frame and braces.
 for x in (-L,L):
  for y in (-W,W):
   prism('corner post',(x-.14,y-.14,0),(x+.14,y+.14,H+.12),wood,joinery,.025);COUNT['joinery']+=1
 for y in (-W,W):
  prism('wall plate',(-L-.2,y-.13,H-.12),(L+.2,y+.13,H+.13),wood,joinery,.02)
 beam('ridge structural beam',(-L-.38,0,Z),(L+.38,0,Z),.22,.20,wood,roof)
 for x in (-L-.2,0,L+.2):
  for side in (-1,1):
   beam('principal rafter',(x,0,Z),(x,side*(W+.34),H-.06),.16,.22,wood,roof)
 # Structural continuous roof deck. Separate from individually modelled slates.
 for side in (-1,1):
  a=[(-L-.34,0,Z-.12),(L+.34,0,Z-.12),
     (L+.34,side*(W+.34),H-.16),(-L-.34,side*(W+.34),H-.16)]
  b=[(x,y,z-.11) for x,y,z in a]
  obj('roof structural deck',a+b,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],wood,roof)
 # Slates with actual thickness and stagger; no material-only pseudo-detail.
 rows=18;columns=26
 for side in (-1,1):
  for row in range(rows):
   t=row/rows;u=min(1,(row+1.18)/rows)
   for col in range(columns):
    stagger=.5 if row%2 else 0
    x=-L-.30+(col+stagger)*(P['length']+.60)/columns
    X=min(x+(P['length']+.60)/columns*.98,L+.30)
    if X-x<.08:continue
    jitter=R.uniform(-.010,.010)
    def at(xx,v,offset=0):
     return (xx,side*(W+.34)*v,Z+(H-.06-Z)*v+jitter+offset)
    q=[at(x,t,.025),at(X,t,.025),at(X,u,.025),at(x,u,.025)]
    q+= [at(x,t,-.035),at(X,t,-.035),at(X,u,-.035),at(x,u,-.035)]
    obj('slate_%04d'%COUNT['roof_slates'],q,[(0,1,2,3),(7,6,5,4),
       (0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],slate[R.randrange(len(slate))],tiles)
    COUNT['roof_slates']+=1
 # Joinery: leaf in actual door opening; window in actual void.
 prism('inset front door',(-.59,-W+.03,.06),(.59,-W+.02,2.15),wood,joinery,.02)
 for x in (-dw,dw):
  prism('door jamb',(x-.07,-W-.22,0),(x+.07,-W-.08,dh+.15),wood,joinery,.012)
 prism('door header',(-dw-.10,-W-.23,dh),(dw+.10,-W-.07,dh+.18),wood,joinery,.012)
 prism('window glazing',(L-.055,wy-ww+.10,z0+.08),(L+.055,wy+ww-.10,z1-.08),glass,joinery)
 for y in (wy-ww,wy+ww):
  prism('window vertical frame',(L-.22,y-.065,z0),(L+.22,y+.065,z1),wood,joinery,.008)
 for z in (z0,z1):
  prism('window horizontal frame',(L-.22,wy-ww,z-.065),(L+.22,wy+ww,z+.065),wood,joinery,.008)
 prism('window mullion',(L-.23,wy-.05,z0),(L+.23,wy+.05,z1),wood,joinery)
 # Porch has posts, a ridge, true solid roof planes and diagonal rafters.
 pf=-W-P['porch_projection'];pb=-W+.12;pr=3.85;pe=2.78
 for x in (-1.34,1.34):
  prism('porch post',(x-.11,pf-.10,0),(x+.11,pf+.10,pe+.05),wood,porch,.014)
 for side in (-1,1):
  a=[(0,pb,pr),(side*1.58,pb,pe),(side*1.58,pf,pe),(0,pf,pr)]
  b=[(x,y,z-.13) for x,y,z in a]
  obj('porch solid roof',a+b,[(0,1,2,3),(7,6,5,4),(0,4,5,1),
      (1,5,6,2),(2,6,7,3),(3,7,4,0)],slate[1],porch)
  for y in (pf+.12,pb-.12):
   beam('porch sloped rafter',(0,y,pr-.16),(side*1.58,y,pe-.16),.13,.16,wood,porch)
 beam('porch ridge',(0,pf,pr),(0,pb,pr),.16,.16,wood,porch)
 # Explicitly unresolved features must not be guessed into canon.
 return {'status':'V3_ARCHITECTURE_DIAGNOSTIC_NOT_ART_APPROVED',
         'seed':SEED,'dimensions':P,'counts':COUNT,
         'chimney':'UNRESOLVED','ivy':'NOT_MODELLED',
         'uv':'NOT_APPLIED','pbr_textures':'NOT_APPLIED'}
if __name__=='__main__':
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 print('AIDAN_V3='+json.dumps(build(),sort_keys=True))
