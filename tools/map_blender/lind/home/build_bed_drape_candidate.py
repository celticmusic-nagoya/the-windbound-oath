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
        y=.51*t
        edge=max(0,(abs(t)-.76)/.24)
        z=.62-.21*edge**1.6
        z+=(.012+.023*edge)*math.sin(19*u+3*t+1.2*math.sin(8*u))*math.sin(math.pi*(.12+.76*u))
        verts.append((x,y,z));uv.append((1.15*u,1.02*v))
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
