"""Isolated provisional bedding mesh; run inside Blender. No house writes."""
import bpy, math, sys
from pathlib import Path
out=Path(sys.argv[sys.argv.index('--')+1])
assert not out.exists(), "refuse overwrite"
bpy.ops.wm.read_factory_settings(use_empty=True)
nx,ny=65,41
verts=[]; uv=[]
for i in range(nx):
    u=i/(nx-1)
    x=.70+1.15*u
    for j in range(ny):
        v=j/(ny-1); t=2*v-1
        y=.51*t + .012*math.sin(5*u+1.7*t)*abs(t)**5
        edge=max(0,(abs(t)-.76)/.24)
        z=.625-.19*edge**1.6
        # Nonperiodic tension ridges from distinct fold origins; no sinusoidal hem.
        for center,slope,width,amp in ((.18,.23,.055,.025),(.46,-.31,.085,.019),(.78,.19,.045,.034)):
            d=u-center-slope*t-.045*t*t
            z+=amp*math.exp(-(d/width)**2)*(.45+.55*abs(t))
            z-=.009*math.exp(-((d-.065)/(.8*width))**2)
        z=max(z,.611 if abs(t)<=.76 else .40)
        # Soft raised hem within the same continuous surface.
        z+=.003*math.exp(-((abs(t)-.965)/.022)**2)
        verts.append((x,y,z));uv.append((1.15*u,1.12*v))
faces=[(i*ny+j,(i+1)*ny+j,(i+1)*ny+j+1,i*ny+j+1) for i in range(nx-1) for j in range(ny-1)]
mesh=bpy.data.meshes.new("BED_DRAPE_GRID");mesh.from_pydata(verts,[],faces);mesh.update()
assert not mesh.validate()
obj=bpy.data.objects.new("BED_DRAPE_CANDIDATE",mesh);bpy.context.collection.objects.link(obj)
layer=mesh.uv_layers.new(name="Metric")
for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
for poly in mesh.polygons:poly.use_smooth=True
mod=obj.modifiers.new("Wool thickness","SOLIDIFY");mod.thickness=.008;mod.offset=-1
obj["status"]="provisional isolated candidate; contact QA pending"
assert len(mesh.vertices)==2665 and len(mesh.polygons)==2560
bpy.ops.wm.save_as_mainfile(filepath=str(out))
bpy.ops.wm.open_mainfile(filepath=str(out))
assert len(bpy.data.objects["BED_DRAPE_CANDIDATE"].data.vertices)==2665
