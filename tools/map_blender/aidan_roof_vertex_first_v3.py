"""Aidan slate roof v3: structural control cage + five nonuniform slate silhouette families.
Geometry-only candidate. No canonical assets overwritten. Blender 4/5.
"""
import bpy, math, random, json
SEED=1311
COLLECTION="AIDAN_ROOF_V3_CANDIDATE"
def material(name,rgb,roughness=.84):
 m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
 bs=m.node_tree.nodes.get("Principled BSDF")
 bs.inputs["Base Color"].default_value=(*rgb,1)
 bs.inputs["Roughness"].default_value=roughness
 return m
def mesh(col,name,verts,faces,mat):
 data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
 ob=bpy.data.objects.new(name,data);col.objects.link(ob);data.materials.append(mat);return ob
def build():
 if bpy.data.collections.get(COLLECTION):raise RuntimeError("Candidate already exists; refusing overwrite")
 rng=random.Random(SEED);col=bpy.data.collections.new(COLLECTION);bpy.context.scene.collection.children.link(col)
 slate=[material("v3 blue gray slate %d"%i,c) for i,c in enumerate([(0.26,.31,.36),(.28,.34,.38),(.32,.37,.40),(.23,.29,.34),(.30,.35,.40)])]
 timber=material("v3 weathered oak",(.22,.17,.13))
 ridgecap=material("v3 ridge cap",(.29,.34,.38))
 length=8.4;halfspan=3.55;eave=3.05;ridge=6.60;courses=14;cols=14
 control={}
 for side in (-1,1):
  control[str(side)]=[[-length/2,0,ridge],[length/2,0,ridge],[length/2,side*halfspan,eave],[-length/2,side*halfspan,eave]]
  mesh(col,"structural roof deck %d"%side,control[str(side)],[(0,1,2,3)],slate[0])
 def roofz(y):return ridge-(ridge-eave)*y/halfspan
 count=0;families=[0]*5;minclear=1.
 for side in (-1,1):
  for row in range(courses):
   pitch=halfspan/courses
   y0=row*pitch
   y1=min(halfspan+.095,y0+pitch*1.34)
   offset=(row%2)*length/(cols*2)
   for i in range(-1,cols+1):
    x0=max(-length/2,-length/2+i*length/cols+offset)
    x1=min(length/2,-length/2+(i+1)*length/cols+offset-.009)
    if x1-x0<.10:continue
    family=rng.randrange(5);families[family]+=1
    width=x1-x0
    # Edge-only variation; preserve common course spacing and positive surface clearance.
    trim=(.014,.027,.036,.020,.031)[family]
    inset=rng.uniform(.0,.016)
    xmid=(x0+x1)/2+rng.uniform(-.022,.022)
    top=[(x0+inset,y0),(xmid,y0),(x1-inset,y0)]
    bottom=[(x0+trim,y1-rng.uniform(.003,.020)),
            (xmid+rng.uniform(-.018,.018),y1-rng.uniform(.001,.016)),
            (x1-trim,y1-rng.uniform(.002,.024))]
    if family==2:bottom[1]=(bottom[1][0],bottom[1][1]-.043) # shallow chipped edge
    if family==3:bottom[0]=(bottom[0][0]+.027,bottom[0][1]-.028)
    outline=top+list(reversed(bottom))
    clearance=.043;thickness=.023+rng.uniform(0,.008)
    # Two six-point loops, closed 3D slate; camber across width is subtle.
    def loop(offset):
     return [(x,side*y,roofz(y)+clearance+offset+(.012 if j in (1,4) else 0)) for j,(x,y) in enumerate(outline)]
    verts=loop(0)+loop(thickness)
    n=len(outline)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces +=[(j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n)]
    mesh(col,"v3 slate %d %02d %02d"%(side,row,i),verts,faces,slate[rng.randrange(len(slate))])
    count+=1;minclear=min(minclear,clearance)
 # Ridge caps: distinct curved-ish profiles along x, no decorative excess at game scale.
 for i in range(17):
  xa=-length/2+i*length/17;xb=xa+length/17*.99
  z=ridge+.08
  vertices=[(xa,-.17,z-.13),(xa,-.10,z+.045),(xa,0,z+.07),(xa,.10,z+.045),(xa,.17,z-.13),
            (xb,-.17,z-.13),(xb,-.10,z+.045),(xb,0,z+.07),(xb,.10,z+.045),(xb,.17,z-.13)]
  faces=[(j,j+1,j+6,j+5) for j in range(4)]
  mesh(col,"ridge cap %02d"%i,vertices,faces,ridgecap)
 for side in (-1,1):
  y=side*(halfspan+.12);z=eave-.12
  mesh(col,"eave fascia %d"%side,[(-4.25,y,z),(4.25,y,z),(4.25,y,z+.17),(-4.25,y,z+.17)],[(0,1,2,3)],timber)
 result={"status":"VERTEX_FIRST_V3_GEOMETRY_CANDIDATE_NOT_ART_APPROVED","seed":SEED,
         "control_vertices":control,"slate_count":count,"silhouette_families":families,
         "minimum_clearance":minclear,"ridge_cap_count":17,"pbr":"NOT_APPLIED","uv":"NOT_RUN"}
 print("AIDAN_V3_GEOMETRY="+json.dumps(result,sort_keys=True))
 return result
if __name__=="__main__":build()
