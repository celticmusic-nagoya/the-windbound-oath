"""Method C: fit real CC0 scan solids to explicitly authored masonry bond domains.
No A/B code, cuboid stones, image displacement, randomized courses or bevel array.
Blender 4.3.2 -b --factory-startup --python-exit-code 1 --python build_curated.py -- --root ROOT --out OUT
"""
import argparse, hashlib, json, math, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector, Matrix

# Individually drawn, shared joint network. Coordinates are study metres, NOT canon.
# A broad bed bridges two lower joints; no repeated rectangle/silhouette template.
DOMAINS = [
('F01',[(0,0),(.75,0),(.71,.28),(.48,.46),(0,.38)]),
('F02',[(.75,0),(1.60,0),(1.60,.35),(1.22,.44),(.71,.28)]),
('F03',[(0,.38),(.48,.46),(.55,.81),(.23,.91),(0,.78)]),
('F04',[(.48,.46),(.71,.28),(1.22,.44),(1.12,.78),(.55,.81)]),
('F05',[(1.22,.44),(1.60,.35),(1.60,.87),(1.12,.78)]),
('F06',[(0,.78),(.23,.91),(.29,1.22),(0,1.29)]),
('F07',[(.23,.91),(.55,.81),(1.12,.78),(1.,1.17),(.68,1.32),(.29,1.22)]),
('F08',[(1.12,.78),(1.60,.87),(1.69,1.30),(1.26,1.42),(1.,1.17)]),
('F09',[(0,1.29),(.29,1.22),(.68,1.32),(.58,1.69),(.21,1.77),(0,1.62)]),
('F10',[(.68,1.32),(1.,1.17),(1.26,1.42),(1.18,1.76),(.58,1.69)]),
('F11',[(1.26,1.42),(1.69,1.30),(1.88,1.66),(1.67,1.91),(1.18,1.76)]),
('F12',[(0,1.62),(.21,1.77),(.58,1.69),(.55,2.13),(0,2.20)]),
('F13',[(.58,1.69),(1.18,1.76),(1.11,2.10),(.84,2.24),(.55,2.13)]),
('F14',[(1.18,1.76),(1.67,1.91),(1.88,1.66),(2.13,1.98),(1.94,2.24),(1.49,2.32),(1.11,2.10)]),
('F15',[(0,2.20),(.55,2.13),(.84,2.24),(.78,2.56),(0,2.55)]),
('F16',[(.84,2.24),(1.11,2.10),(1.49,2.32),(1.43,2.56),(.78,2.56)]),
('F17',[(1.49,2.32),(1.94,2.24),(2.13,1.98),(2.49,2.24),(2.40,2.57),(1.43,2.56)]),
('F18',[(2.49,2.24),(3.10,2.46),(3.10,2.58),(2.40,2.57)]),
]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def aim(o,t):o.rotation_euler=(Vector(t)-o.location).to_track_quat('-Z','Y').to_euler()
def mat(name,v):
 m=bpy.data.materials.new(name);m.diffuse_color=(*[v]*3,1);m.use_nodes=True
 s=m.node_tree.nodes.get('Principled BSDF');s.inputs['Base Color'].default_value=(*[v]*3,1);s.inputs['Roughness'].default_value=.84;return m

def mesh_obj(name,verts,faces,material):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o)
 if material:me.materials.append(material)
 return o

def prism(name,poly,front,back,material):
 n=len(poly);v=[(x,y,z) for y in (front,back) for x,z in poly]
 return mesh_obj(name,v,[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],material)

def inset(poly,gap):
 # Offset every edge inward by half joint width. Handles non-convex outlines.
 out=[];n=len(poly)
 area=sum(poly[i][0]*poly[(i+1)%n][1]-poly[(i+1)%n][0]*poly[i][1] for i in range(n))
 if area<0:poly=list(reversed(poly))
 for i,b in enumerate(poly):
  a=Vector(poly[i-1]);b=Vector(b);c=Vector(poly[(i+1)%n]);d1=(b-a).normalized();d2=(c-b).normalized()
  n1=Vector((-d1.y,d1.x));n2=Vector((-d2.y,d2.x));bis=n1+n2
  out.append(tuple(b+bis*(gap/max(.15,bis.dot(n1)))))
 return out

def unwrap(o):
 if not len(o.data.polygons):raise RuntimeError('Empty Boolean result: '+o.name+' source '+str(o.get('scan_source')))
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')

ROTATIONS=[(0.1,.3,0),(.6,1.4,.5),(1.1,.2,1.4),(.2,2.1,.6),(2.5,.7,2.1),(1.5,1.7,.1),(.8,2.6,1.2)]
def scanned_stone(name,poly,front,back,index,scans,clay):
 """True scanned boundary -> individually rotated quarry blank -> cut bearing planes.
 Surface retains actual scan vertices; side caps are closed polygonal bearing faces.
 """
 poly=inset(poly,.0065);src=scans[index%len(scans)]
 o=bpy.data.objects.new(name,src.copy());bpy.context.collection.objects.link(o)
 rot=ROTATIONS[index%len(ROTATIONS)];R=Matrix.Rotation(rot[0],4,'X')@Matrix.Rotation(rot[1],4,'Y')@Matrix.Rotation(rot[2],4,'Z')
 for v in o.data.vertices:v.co=R@v.co
 lo=Vector([min(v.co[j] for v in o.data.vertices) for j in range(3)]);hi=Vector([max(v.co[j] for v in o.data.vertices) for j in range(3)])
 minx=min(p[0] for p in poly);maxx=max(p[0] for p in poly);minz=min(p[1] for p in poly);maxz=max(p[1] for p in poly)
 # Oversize in the bed plane to preserve continuous bearing at seams.
 # Exposed face remains a volumetric scan (no texture/height-map substitute).
 for v in o.data.vertices:
  t=(v.co-lo)/(hi-lo) if False else [(v.co[j]-lo[j])/(hi[j]-lo[j]) for j in range(3)]
  v.co=((minx+maxx)/2+(t[0]-.5)*(maxx-minx)*2.4,front-.085+t[1]*(back-front+.30), (minz+maxz)/2+(t[2]-.5)*(maxz-minz)*2.4)
 o.data.update();bpy.context.view_layer.update()
 # Front cutter lies beyond scan envelope; rear/beds are accurately cut.
 cutter=prism(name+'_quarry_cut',poly,front-.30,back,None)
 bpy.context.view_layer.objects.active=o
 mod=o.modifiers.new('AuthoredBearingCut','BOOLEAN');mod.operation='INTERSECT';mod.solver='EXACT';mod.object=cutter
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
 o.data.materials.clear();o.data.materials.append(clay)
 # Deterministically triangulate and merge boolean seam duplicates.
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.00001);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 for f in o.data.polygons:f.use_smooth=False
 o['role']='load_bearing_scan_stone';o['scan_source']=src.name;o['bond_domain']=name;o['adoption']='CANDIDATE';unwrap(o)
 return o

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--geometry-only',action='store_true');p.add_argument('--source-quality',choices=['recorded-01','lod0-experimental'],default='recorded-01')
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.root.resolve();out=a.out.resolve();out.mkdir(parents=True,exist_ok=True)
 sources=root/'assets/candidates/route-mat-01/method-c-01/sources'
 manifest=json.loads((sources.parent/'source-manifest.json').read_text())
 for entry in manifest['source_assets']:
  if sha(sources.parent/entry['original_file'])!=entry['source_sha256']:raise RuntimeError('Source hash mismatch')
 if a.source_quality=='lod0-experimental':raise RuntimeError('BLOCKED: LOD0 exact intersection failed on Far_F12 twice; investigate recorded diagnostics, do not blindly retry')
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 scans=[]
 for fn in ['boulder_01_1k.blend','rock_07_1k.blend']:
  with bpy.data.libraries.load(str(sources/fn),link=False) as (fr,to):
   lod='_LOD3' if a.source_quality=='recorded-01' else '_LOD0'
   names=[n for n in fr.objects if n.endswith(lod)]
   if len(names)!=1:raise RuntimeError('Ambiguous source LOD: '+str(fr.objects))
   to.objects=names
  source_obj=to.objects[0];scans.append(source_obj.data.copy());scans[-1].name=fn+lod+'_verified';bpy.data.objects.remove(source_obj,do_unlink=True)
 if len(scans)!=2:raise RuntimeError('Two verified real scan meshes required')
 clay=mat('NeutralClay_Stone',.48);mortar=mat('NeutralClay_LimeJoint',.43);soil=mat('NeutralClay_Foundation',.34)
 objects=[]
 # Full-thickness lime-rubble abutment core, shaped to the arch extrados.
 # The mortar/core supports stones; no exposed rectangular white backing panel.
 core_poly=[(0,-.18),(1.6,-.18),(1.6,.65)]+[(3.1-1.82*math.cos(t),.65+1.82*math.sin(t)) for t in [i*math.pi/2/24 for i in range(5,25)]]+[(3.1,2.60),(0,2.57)]
 core=prism('BondedLimeRubbleCore',core_poly,-.675,.675,mortar);core['role']='support_core';unwrap(core);objects.append(core)
 for side in [-1,1]:
  for i,(name,poly) in enumerate(DOMAINS):
   if side==-1:front,back=-.80,-.08
   else:front,back=.05,.79
   o=scanned_stone(('Near_' if side==-1 else 'Far_')+name,poly,front,back,i+(7 if side==1 else 0),scans,clay)
   # Rear leaf mirrored about y=0 so its exposed scan face looks outward.
   if side==1:
    for v in o.data.vertices:v.co.y=.0-v.co.y
    # Translation yields symmetric depth of two independently shaped leaves.
    for v in o.data.vertices:v.co.y+=.85
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
   objects.append(o)
 # Radial springer/voussoir chain: full wall depth. Authored angles, not box rows.
 angles=[0,.17,.36,.55,.75,.96,1.18,1.38,math.pi/2]
 for i,(u,v) in enumerate(zip(angles[:-1],angles[1:])):
  # Arch is to the right of the abutment, span continues beyond the cut section.
  poly=[(3.1-r*math.cos(t),.65+r*math.sin(t)) for r,t in [(1.5,u),(1.5,v),(1.82,v),(1.82,u)]]
  o=scanned_stone('RadialVoussoir_%02d'%i,poly,-.80,.80,i+3,scans,clay);o['role']='full_depth_voussoir';objects.append(o)
 # Deep headers tie the two leaves; each sits across a staggered bed.
 for i,(x,z,w,h) in enumerate([(.12,.36,.45,.17),(.70,1.30,.50,.17),(1.02,2.10,.44,.15)]):
  poly=[(x,z),(x+w,z+.018),(x+w-.04,z+h),(x+.02,z+h-.014)]
  o=scanned_stone('ThroughBond_%02d'%i,poly,-.83,.83,i+11,scans,clay);o['role']='through_bond';objects.append(o)
 # Coping stones are independent, shallow and full depth, bedded on the core.
 for i,(x0,x1,z) in enumerate([(0,.76,2.57),(.76,1.44,2.58),(1.44,2.38,2.59),(2.38,3.1,2.61)]):
  poly=[(x0,z),(x1,z+.015),(x1-.018,z+.21),(x0+.025,z+.20)]
  o=scanned_stone('Coping_%02d'%i,poly,-.86,.86,i+15,scans,clay);o['role']='coping';objects.append(o)
 # Stepped rubble footing, actual volume under the abutment; no display plinth.
 for i,(x0,x1) in enumerate([(-.13,.57),(.57,1.21),(1.21,1.76)]):
  poly=[(x0,-.23),(x1,-.23),(x1-.03,.035),(x0+.04,.025)]
  o=scanned_stone('Foundation_%02d'%i,poly,-.94,.94,i+5,scans,clay);o['role']='foundation';objects.append(o)
 # Neutral ground is a distinct QA stage object and excluded from model audit.
 ground=prism('QA_Ground',[(-20,-.30),(20,-.30),(20,-.25),(-20,-.25)],-20,20,soil);ground['role']='qa_stage'
 scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene['adoption']='CANDIDATE_NOT_ADOPTED';scene['metric_status']='STUDY_SCALE_ONLY_UNAPPROVED';scene['method']='C_SCAN_QUARRY_AUTHORED_BOND';scene['blender_required']='4.3.2'
 scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=False
 scene.render.resolution_x=1280;scene.render.resolution_y=1024;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
 scene.world.color=(.28,.28,.28);scene.view_settings.view_transform='AgX'
 for name,loc,power,size in [('Key',(-3,-5,7),1400,5),('Fill',(5,-1,5),800,4),('Rim',(1,5,6),1100,4)]:
  bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(1.4,0,1.1))
 views=[('front',(1.55,-8,2.7),(1.5,0,1.25),4.35),('oblique',(-4.6,-6.4,4.2),(1.40,0,1.20),4.9),('side',(6.0,-3.8,3.3),(1.65,0,1.2),4.9)]
 cameras=[]
 for name,loc,target,scale in views:
  bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name='QA_'+name;c.data.type='ORTHO';c.data.ortho_scale=scale;aim(c,target);cameras.append(c)
 scene.camera=cameras[1]
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'abutment.blend'),compress=True)
 if a.geometry_only:return
 for (name,_,_,_),c in zip(views,cameras):
  scene.camera=c;scene.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
 (out/'build.json').write_text(json.dumps({'method':scene['method'],'blender':bpy.app.version_string,'mesh_count':len(objects),'source_meshes':[m.name for m in scans],'study_scale_only':True,'canonical_world_transform':None,'cameras':views,'materials':'neutral clay; no image textures or displacement','builder_sha256':sha(__file__),'G1':'BLOCKED_METRIC_ADOPTION','G2':'NOT_RUN_INDEPENDENT','G3':'NOT_RUN_AUDIT','G4':'NOT_RUN'},indent=2))
 print('METHOD_C_BUILD_COMPLETE',out)
if __name__=='__main__':main()
