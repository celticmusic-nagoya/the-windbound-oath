"""Nonperiodic silhouette *technical candidate*, not a finished natural cliff.
Piecewise hand-authored profile and compact local erosion lobes, no periodic waves.
Nonmetric, does not assign official placement or physical scale.
"""
import argparse,collections,hashlib,json,math
from pathlib import Path

# Asymmetric authored control points, normalized, not official world coordinates.
COAST=[(0,.14),(.09,.08),(.19,.12),(.29,.03),(.38,.18),(.47,.11),(.58,.06),(.66,.17),(.77,.10),(.89,.21),(1,.16)]
CREST=[(0,.86),(.14,1.02),(.25,.94),(.37,1.11),(.51,.91),(.62,1.06),(.74,.98),(.86,1.13),(1,1.03)]
# Local erosion notches with different widths and depths; not repeated sinusoids.
NOTCHES=[(.16,.035,.10),(.34,.018,.065),(.55,.042,.09),(.72,.027,.055),(.91,.020,.075)]

def profile(knots,u):
 for (x0,y0),(x1,y1) in zip(knots,knots[1:]):
  if u<=x1:
   t=max(0.,min(1.,(u-x0)/(x1-x0)))
   t=t*t*(3-2*t)
   return y0+(y1-y0)*t
 return knots[-1][1]

def build(nx=81,ny=35):
 vertices=[]
 for i in range(nx):
  u=i/(nx-1)
  shoreline=profile(COAST,u)
  crest=profile(CREST,u)
  for j in range(ny):
   v=j/(ny-1)
   # Narrow vertical cliff wall transitioning into a sloping grassy shelf.
   # Terrain support only; scan surface dressing is a later separate stage.
   z=.08+(crest-.08)*v**.38
   notch=sum(depth*math.exp(-((u-c)/w)**2) for c,w,depth in NOTCHES)
   z-=notch*(math.sin(math.pi*v)**2)
   y=shoreline+1.34*v+.035*v*(1-v)*(2*u-1)
   vertices.append((3.2*u-1.6,y,z))
 n=len(vertices)
 vertices.extend((x,y,-.25) for x,y,z in vertices[:])
 idx=lambda i,j:i*ny+j
 top=[(idx(i,j),idx(i+1,j),idx(i+1,j+1),idx(i,j+1)) for i in range(nx-1) for j in range(ny-1)]
 faces=top+[tuple(reversed(tuple(n+k for k in f))) for f in top]
 for i in range(nx-1):
  for j in (0,ny-1):
   a,b=idx(i,j),idx(i+1,j)
   faces.append((a,n+a,n+b,b) if j==0 else (b,n+b,n+a,a))
 for j in range(ny-1):
  for i in (0,nx-1):
   a,b=idx(i,j),idx(i,j+1)
   faces.append((b,n+b,n+a,a) if i==0 else (a,n+a,n+b,b))
 return vertices,faces

def main():
 p=argparse.ArgumentParser();p.add_argument("--out",required=True);a=p.parse_args()
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 vertices,faces=build()
 path=out/"lind_nonperiodic_silhouette_candidate.obj"
 with path.open("w") as f:
  f.write("# NONMETRIC NONCANONICAL TECHNICAL CANDIDATE\n")
  for v in vertices:f.write("v "+" ".join(f"{x:.9f}" for x in v)+"\n")
  for face in faces:f.write("f "+" ".join(str(x+1) for x in face)+"\n")
 m={"production_ready":False,"world_alignment":"NOT_DEFINED","method":"HAND_AUTHORED_NONPERIODIC_PROFILES","scan_dressing":"NOT_RUN","vertices":len(vertices),"faces":len(faces),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"G1":"BLOCKED","G2":"NOT_RUN","G3":"NOT_RUN","G4":"NOT_RUN"}
 (out/"candidate_manifest.json").write_text(json.dumps(m,indent=2)+"\n")
 print(json.dumps(m))
if __name__=="__main__":main()
