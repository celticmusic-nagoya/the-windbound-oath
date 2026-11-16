"""Candidate-only continuous coastal terrain. No DOM coordinates or approved metric scale."""
import bpy,math,json,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector,noise
P=argparse.ArgumentParser();P.add_argument('--out',required=True);a=P.parse_args(sys.argv[sys.argv.index('--')+1:]);out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
if (out/'world.blend').exists():raise FileExistsError('Preserve previous candidate; choose new output directory')
root=Path(__file__).resolve().parents[2];source=root/'assets/sources/lind-world-20261116/original.png';expected='abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620';assert hashlib.sha256(source.read_bytes()).hexdigest()==expected
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def mat(name,col,rough=0.85):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough;return m
rock=mat('Authored stratified sandstone',(0.25,.23,.19));grass=mat('Upland turf',(0.21,.28,.10));sand=mat('Tidal sandstone shelf',(.46,.38,.24));water=mat('River and sea independent of wind',(.035,.16,.21),.25);roadmat=mat('Compacted earth',(.46,.35,.19));wood=mat('Harbor oak',(.23,.13,.055));field=mat('North cultivated ground',(.36,.32,.12))
for m in [rock,grass,sand,roadmat,field]:
 ns=m.node_tree.nodes;ls=m.node_tree.links;tex=ns.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=9;tex.inputs['Detail'].default_value=4;bump=ns.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.3;bump.inputs['Distance'].default_value=.09;ls.new(tex.outputs['Fac'],bump.inputs['Height']);ls.new(bump.outputs['Normal'],ns.get('Principled BSDF').inputs['Normal'])
# Sedimentary color variation in world coordinates, warped by fine noise.
ns=rock.node_tree.nodes;ls=rock.node_tree.links;wave=ns.new('ShaderNodeTexWave');wave.bands_direction='Z';wave.inputs['Scale'].default_value=.8;wave.inputs['Distortion'].default_value=18;ramp=ns.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.22,.20,.17,1);ramp.color_ramp.elements[1].color=(.37,.33,.26,1);ls.new(wave.outputs['Color'],ramp.inputs[0]);ls.new(ramp.outputs[0],ns.get('Principled BSDF').inputs['Base Color'])
def n(x,y):return noise.fractal(Vector((x*.17,y*.17,2.13)),1.1,2.1,4)
def coast(y):return -11+2.5*math.sin(y*.28)+1.25*math.sin(y*.73)+5.8*math.exp(-((y+10)/4.5)**2)
def river(y):return 8+2.8*math.sin(y*.19)+.8*math.sin(y*.45)
def wz(y):return 3.55+.012*(y+20)
def height(x,y):
 d=x-coast(y);h=-2.2+7.6/(1+math.exp(max(-50,min(50,-d*4))))
 h+=max(0,min(1,d))* (.6*n(x,y)+.45*math.sin(y*.18)+.3*math.cos(x*.25))
 h+=2.3*math.exp(-((x+7)/5)**2-((y-10)/7)**2)
 h+=3*math.exp(-((x-river(y)-4)/3)**2-((y-2)/4)**2)
 # A low tidal access fan opens the harbor without collapsing the northern promontory.
 h-=2.8*math.exp(-((x-coast(y)-1.5)/3)**2-((y+10)/3)**2)
 h+=.55*math.sin(y*2.6+n(x,y)*3)*math.exp(-((d-.25)/1.1)**2)
 dist=abs(x-river(y));cut=math.exp(-(dist/2.9)**4);h=h*(1-cut)+(wz(y)-.5)*cut
 return h

def mesh(name,v,f,material):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material);return o
N=240;vs=[(x,y,height(x,y)) for j in range(N+1) for i in range(N+1) for x,y in [(-30+70*i/N,-36+72*j/N)]];fs=[(j*(N+1)+i,j*(N+1)+i+1,(j+1)*(N+1)+i+1,(j+1)*(N+1)+i) for j in range(N) for i in range(N)]
o=mesh('CONTINUOUS_TERRAIN_coast_river_upland',vs,fs,grass);o.data.materials.append(rock);o.data.materials.append(sand)
for p in o.data.polygons:
 p.material_index=1 if p.normal.z<.72 else (2 if p.center.z<1.5 else 0);p.use_smooth=True
mesh('Ocean_tidal_surface',[(-150,-150,0),(150,-150,0),(150,150,0),(-150,150,0)],[(0,1,2,3)],water)
# River ribbon follows independently downhill to the south, not a wind animation driver.
v=[]
for j in range(721):
 y=-36+j*.1;v.extend([(river(y)-2.0,y,wz(y)),(river(y)+2.0,y,wz(y))])
mesh('North_to_south_river',v,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(720)],water)
# Paths are surface-conforming continuous ribbons; footprints are proposals only.
def ribbon(name,points,width,material):
 v=[]
 for k,(x,y) in enumerate(points):
  prev=points[max(0,k-1)];nxt=points[min(len(points)-1,k+1)];dx=nxt[0]-prev[0];dy=nxt[1]-prev[1];l=max(.001,math.hypot(dx,dy));sx=-dy/l*width;sy=dx/l*width
  for xx,yy in [(x+sx,y+sy),(x-sx,y-sy)]:v.append((xx,yy,height(xx,yy)+.045))
 return mesh(name,v,[(2*j,2*j+1,2*j+3,2*j+2) for j in range(len(points)-1)],material)
ribbon('Village_to_north_farmland',[(.8*math.sin(t*.2),t) for t in [j*.2 for j in range(96)]],.32,roadmat)
ribbon('Village_to_harbor_access',[(coast(-10)*t/100,-10*t/100) for t in range(101)],.28,roadmat)
ribbon('Village_to_coastal_promontory',[(-t*.11,7*(t/100)**.8) for t in range(101)],.25,roadmat)
bridgepath=ribbon('Village_to_east_bridge',[(t*.1,0) for t in range(121)],.3,roadmat)
for vert in bridgepath.data.vertices:
 if vert.co.x>river(0)-3.4 and vert.co.x<river(0)+3.4:vert.co.z=6.14
# Stone bridge shell: semicircular intrados and continuous masonry spandrel mesh.
xc=river(0);v=[];segments=40
for yy in [-.55,.55]:
 for i in range(segments+1):
  t=math.pi*i/segments;x=xc+2.15*math.cos(t);z=2.4+2.15*math.sin(t);v.extend([(x,yy,z),(x,yy,5.8+.3*math.sin(t))])
f=[];stride=2*(segments+1)
for i in range(segments):
 for side in [0,1]:b=side*stride+2*i;f.append((b,b+2,b+3,b+1))
 f.extend([(2*i,2*i+2,stride+2*i+2,stride+2*i),(2*i+1,stride+2*i+1,stride+2*i+3,2*i+3)])
f.extend([(0,1,stride+1,stride),(2*segments,stride+2*segments,stride+2*segments+1,2*segments+1)])
mesh('East_bridge_candidate_single_arch',v,f,rock)
# Harbor landing: authored mesh deck strips on an eroded inlet shelf, no building production.
y=-10;xx=coast(y)
for j in range(14):
 x=xx-.6-j*.14;mesh('Harbor_deck_plank_%02d'%j,[(x,y-.65,1.7),(x-.12,y-.65,1.7),(x-.12,y+.65,1.7),(x,y+.65,1.7)],[(0,1,2,3)],wood)
# Cultivated north terrain follows real height and remains part of the connected upland.
for k in range(5):ribbon('North_field_furrow_%02d'%k,[(2+k*.48,7+j*.08) for j in range(80)],.15,field)
img=bpy.data.images.load(str(source),check_existing=True);img.pack();img.use_fake_user=True
s=bpy.context.scene;s.unit_settings.system='NONE';s['status']='CANDIDATE_UNSCALED_NOT_DIRECTOR_APPROVED';s['source_sha256']=expected;s['method']='continuous_signed_distance_coast_and_river_incision';s['meters_per_unit']='UNAPPROVED'
s.world.color=(.2,.25,.3);s.render.engine='CYCLES';s.cycles.samples=20;s.cycles.use_denoising=False;s.render.resolution_x=1152;s.render.resolution_y=864;s.render.resolution_percentage=100
bpy.ops.object.light_add(type='SUN',location=(-15,-15,25));bpy.context.object.rotation_euler=(.45,-.4,-.5);bpy.context.object.data.energy=3
bpy.ops.object.light_add(type='AREA',location=(0,-5,30));bpy.context.object.data.energy=1300;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=25
cameras=[('overview',(46,-62,53),(0,0,1),53),('coast',(-34,-24,20),(-8,3,2),38),('river',(29,-19,23),(8,2,3),32)]
for name,pos,target,scale in cameras:
 bpy.ops.object.camera_add(location=pos);cam=bpy.context.object;cam.name=name;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
s.camera=bpy.data.objects['overview'];bpy.ops.wm.save_as_mainfile(filepath=str(out/'world.blend'))
for name,*_ in cameras:s.camera=bpy.data.objects[name];s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
report={'status':'CANDIDATE_NOT_FINAL_ART','method_family':'signed_distance_continuous_heightfield_river_incision','seed':'noise fixed position 2.13','grid':[241,241],'source_sha256':expected,'blender_version':bpy.app.version_string,'meters_per_unit':None,'approved_coordinates':False,'views':[x[0]+'.png' for x in cameras],'meshes':len([o for o in s.objects if o.type=='MESH']),'terrain_vertices':len(vs),'terrain_faces':len(fs),'G1':'BLOCKED_METRIC_AND_EVENT_REVIEW','G2':'INDEPENDENT_REVIEW_REQUIRED','G3':'PARTIAL_RENDER_AND_SOURCE_ONLY','G4':'NOT_RUN','limitations':['not final art: no scanned PBR/no production vegetation/architecture','bridge placement and dimensions proposed only','river mouth outside this study extent; estuary and sea outlet need authoring','collision/nav/LOD/physical geological validity not approved'],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir() if p.suffix in ['.blend','.png']}}
(out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('WORLD_CANDIDATE_GENERATED',json.dumps(report))
