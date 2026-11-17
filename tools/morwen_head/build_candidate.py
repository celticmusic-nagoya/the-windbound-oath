"""CC0 topology-preserving Morwen head study. No canonical asset writes.
Run: blender -b -t 4 --python build_candidate.py -- --stage FILE --canonical DIR --output DIR
This is an UNAPPROVED sculpt/fit candidate, not finished character art.
"""
import argparse
import hashlib
import json
import math
import pathlib
import sys
import bmesh
import bpy
from mathutils import Vector

STAGE_SHA = 'd47d140586ba27ca2bc83dabbe3620b39a4d3e91dae57a65874d42defc60836e'
CROWN_INDEX, CHIN_INDEX = 8063, 8064

def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def smooth(a,b,x):
    t=max(0,min(1,(x-a)/(b-a)))
    return t*t*(3-2*t)

def material(name,color,metal=0,rough=.5):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes['Principled BSDF'];n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
    return m

def mesh(name,verts,faces,mat):
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
    bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob);me.materials.append(mat)
    for p in me.polygons:p.use_smooth=True
    return ob

def solid(ob,thickness):
    bpy.context.view_layer.objects.active=ob
    m=ob.modifiers.new('actual_closed_thickness','SOLIDIFY');m.thickness=thickness;m.offset=0
    bpy.ops.object.modifier_apply(modifier=m.name)
    m=ob.modifiers.new('sculpt_surface','SUBSURF');m.levels=1;m.render_levels=2

def sphere(name,loc,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,location=loc)
    ob=bpy.context.object;ob.name=name;ob.scale=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    ob.data.materials.append(mat)
    for p in ob.data.polygons:p.use_smooth=True
    return ob

def wire(name,pts,r,mat,closed=False):
    # Direct indexed solid rings replace Curve conversion: Blender cap conversion
    # duplicates endpoint vertices and left nonmanifold boundaries in two trials.
    points=list(map(Vector,pts));verts=[];segments=12
    for i,p in enumerate(points):
        before=points[(i-1)%len(points)] if closed or i else p
        after=points[(i+1)%len(points)] if closed or i<len(points)-1 else p
        tangent=(after-before).normalized()
        axis=Vector((0,0,1)) if abs(tangent.z)<.9 else Vector((0,1,0))
        u=tangent.cross(axis).normalized();v=tangent.cross(u).normalized()
        for j in range(segments):
            verts.append(tuple(p+r*(u*math.cos(j*math.tau/segments)+v*math.sin(j*math.tau/segments))))
    faces=[]
    count=len(points) if closed else len(points)-1
    for i in range(count):
        ni=(i+1)%len(points)
        for j in range(segments):
            nj=(j+1)%segments
            faces.append((i*segments+j,ni*segments+j,ni*segments+nj,i*segments+nj))
    if not closed:
        faces.append(tuple(reversed(range(segments))))
        faces.append(tuple((len(points)-1)*segments+j for j in range(segments)))
    return mesh(name,verts,faces,mat)

def interp(ctrl,t):
    u=t*(len(ctrl)-1);i=min(len(ctrl)-2,int(u));v=u-i
    p0=Vector(ctrl[max(0,i-1)]);p1=Vector(ctrl[i]);p2=Vector(ctrl[i+1]);p3=Vector(ctrl[min(len(ctrl)-1,i+2)])
    return .5*((2*p1)+(-p0+p2)*v+(2*p0-5*p1+4*p2-p3)*v*v+(-p0+3*p1-3*p2+p3)*v*v*v)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--stage',required=True);ap.add_argument('--canonical',required=True);ap.add_argument('--output',required=True);ap.add_argument('--samples',type=int,default=32)
    a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);src=pathlib.Path(a.stage).resolve();canon=pathlib.Path(a.canonical).resolve();out=pathlib.Path(a.output).resolve()
    if src==out or out==canon or canon in out.parents:raise ValueError('unsafe output')
    assert sha(src)==STAGE_SHA,'source stage SHA mismatch'
    out.mkdir(parents=True,exist_ok=True)
    refs=json.loads((canon/'MANIFEST.json').read_text());integrity=[]
    for f in refs['files']:
        p=canon/f['filename'];assert sha(p)==f['sha256'] and p.stat().st_size==f['bytes']
        integrity.append({'file':f['filename'],'sha256':sha(p),'bytes':p.stat().st_size})
    bpy.ops.wm.open_mainfile(filepath=str(src),load_ui=False)
    body=bpy.data.objects['MORWEN_PROPORTION_STAGE_UNAPPROVED'];assert len(body.data.vertices)==10582
    original=[body.matrix_world@v.co for v in body.data.vertices]
    cx=(min(v.x for v in original)+max(v.x for v in original))/2
    # Explicit source vertex identity, not the old target-derived chin placeholder.
    crown0=original[CROWN_INDEX].z;chin0=original[CHIN_INDEX].z;sole0=min(v.z for v in original)
    neck=1.37;scale=(neck-sole0)/(7.75*(crown0-chin0)-(crown0-neck))
    body.matrix_world.identity();body.name='Morwen_anatomical_body_head_UNAPPROVED'
    for v,p in zip(body.data.vertices,original):v.co=p-Vector((cx,0,sole0))
    body.shape_key_add(name='CC0_source_topology')
    fit=body.shape_key_add(name='Morwen_proportion_and_face_study')
    for v,p in zip(fit.data,original):
        x,y,z=p.x-cx,p.y,p.z
        # Smooth neck blend, uniform cranial scale; all face loops retained.
        w=smooth(1.34,1.415,z);k=1+(scale-1)*w
        x*=k;y=-.055+(y+.055)*k;z=z+(scale-1)*(z-neck)*w-sole0
        # Broad, conservative face-plane edits to the licensed topology.
        fw=1-smooth(-.14,-.09,y)
        jaw=math.exp(-((z-1.445)/.032)**2)*fw
        x*=1-.07*jaw
        nose=math.exp(-(x/.018)**2-((z-1.50)/.027)**2)*fw
        y+=.006*nose
        mouth=math.exp(-((z-1.45)/.016)**2)*fw
        x*=1-.07*mouth
        # Existing eye sockets/lid loops expand locally; no new annulus/zipper.
        for sign in (-1,1):
            ex=sign*.032*scale;ez=neck+(1.533-neck)*scale-sole0
            g=math.exp(-((x-ex)/.024)**4-((z-ez)/.021)**4)*fw
            x+=(x-ex)*.18*g;z+=(z-ez)*.28*g
        v.co=(x,y,z)
    fit.value=1
    coords=[v.co.copy() for v in fit.data]
    crown=coords[CROWN_INDEX];chin=coords[CHIN_INDEX];sole=min(p.z for p in coords)
    ratio=(crown.z-sole)/(crown.z-chin.z)
    assert 7.5<=ratio<=8.0,ratio
    # Keep reference empties but remove misleading inherited measurement placeholders.
    for ob in list(bpy.data.objects):
        if ob.name.startswith('MEASURE_') or ob.type in {'CAMERA','LIGHT'}:bpy.data.objects.remove(ob,do_unlink=True)
    skin=material('skin_neutral_peach',(.58,.36,.30),rough=.54)
    lips=material('lips_muted_rose',(.40,.16,.17),rough=.58)
    hair=material('hair_deep_violet',(.075,.022,.125),rough=.31)
    hair2=material('hair_plum_planes',(.12,.038,.18),rough=.34)
    gold=material('glasses_antique_gold',(.58,.32,.08),metal=.78,rough=.28)
    white=material('eye_ivory',(.78,.76,.73),rough=.23)
    iris=material('iris_violet',(.22,.045,.38),rough=.3)
    dark=material('lash_and_pupil',(.012,.005,.022),rough=.4)
    body.data.materials.clear();body.data.materials.append(skin);body.data.materials.append(lips)
    for p in body.data.polygons:
        p.use_smooth=True
        center=sum((coords[i] for i in p.vertices),Vector())/len(p.vertices)
        p.material_index=0  # Local lip sculpt/material painting remains pending; no face-coordinate mask.
    sub=body.modifiers.new('sculpt_ready_subdivision','SUBSURF');sub.levels=2;sub.render_levels=2
    for label,point,index in [('CROWN',crown,CROWN_INDEX),('CHIN_UNDERSIDE',chin,CHIN_INDEX),('SOLE',min(coords,key=lambda p:p.z),None)]:
        e=bpy.data.objects.new('ANATOMY_'+label,None);bpy.context.scene.collection.objects.link(e);e.location=point;e.empty_display_type='SPHERE';e.empty_display_size=.004;e['source_vertex_index']=index if index is not None else -1;e.hide_render=True
    ez=neck+(1.533-neck)*scale-sole0;ey=-.055+(-.107+.055)*scale
    # Separate real eyeball and curved iris/pupil meshes. Eye-socket fit is reviewed visually.
    for sign in (-1,1):
        x=sign*.032*scale
        sphere('Eye_'+str(sign),(x,ey,ez),(.0205,.0205,.0205),white)
        sphere('Iris_'+str(sign),(x,ey-.0195,ez),(.0088,.002,.0095),iris)
        sphere('Pupil_'+str(sign),(x,ey-.0212,ez),(.0037,.0008,.0061),dark)
        sphere('Catchlight_'+str(sign),(x-.0027,ey-.0218,ez+.004),(.0017,.0007,.0017),white)
        # Eyebrow is a closed thin sculpt surface, not a generated eyelid.
        verts=[]
        for j in range(17):
            t=j/16;xx=x+sign*(t-.5)*.040;zz=ez+.025+.004*math.sin(math.pi*t)
            for d in (-1,1):verts.append((xx,-.137,zz+d*.0014*(.4+.6*math.sin(math.pi*t))))
        ob=mesh('Brow_'+str(sign),verts,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(16)],hair);solid(ob,.0007)
        pts=[(x+.026*math.cos(t*math.tau/96),ey-.047-.003*math.cos(t*math.tau/96),ez+.022*math.sin(t*math.tau/96)-.001) for t in range(96)]
        wire('Glasses_rim_'+str(sign),pts,.0009,gold,True)
        wire('Glasses_temple_'+str(sign),[(sign*.057,ey-.046,ez+.003),(sign*.075,-.105,ez+.006),(sign*.077,-.045,ez+.005),(sign*.074,-.024,ez-.008)],.0008,gold)
    wire('Glasses_bridge',[(-.006,ey-.048,ez+.002),(0,ey-.051,ez+.006),(.006,ey-.048,ez+.002)],.00085,gold)
    # Broad bob locks: two-dimensional sculpted quad surfaces with closed thickness.
    # Width is angular surface coverage; this is not a circular strand sweep.
    top=crown.z;cy=-.043
    def lock(name,theta,width,endz,tip_shift,mat):
        controls=[(.009,.011,top+.008),(.052,.071,top-.012),(.078,.102,top-.065),(.087,.108,top-.135),(.073,.087,endz)]
        verts=[];n,m=28,12
        for i in range(n+1):
            t=i/n;rx,ry,z=interp(controls,t)
            for j in range(m+1):
                u=j/m*2-1
                taper=1-.38*smooth(.76,1,t)
                th=theta+tip_shift*t*t+u*width/2*taper
                bulge=.0025*(1-u*u)*math.sin(math.pi*t)
                zz=z+.010*u*u*smooth(.72,1,t)
                verts.append(((rx+bulge)*math.sin(th),cy-(ry+bulge)*math.cos(th),zz))
        faces=[(i*(m+1)+j,(i+1)*(m+1)+j,(i+1)*(m+1)+j+1,i*(m+1)+j+1) for i in range(n) for j in range(m)]
        ob=mesh(name,verts,faces,mat);solid(ob,.0024);ob['method']='broad_quad_surface_closed_thickness';ob['not_tubular']=True
    # Back and side masses intentionally overlap and vary in termination length.
    for i in range(11):
        th=.93+i*(math.tau-1.86)/10
        lock('Bob_layer_%02d'%i,th,.53,chin.z-.014+.006*math.cos(i*1.7),.035*math.sin(i),hair if i%3 else hair2)
    # Curved front fringe lobes, following the scalp before falling to the brow.
    for i in range(7):
        theta=-.86+i*.286
        end=ez+.023+.008*abs(theta)+.003*math.cos(i*2.1)
        controls=[(theta*.008,cy-.011,top+.010),(math.sin(theta)*.055,cy-math.cos(theta)*.073,top-.012),(math.sin(theta)*.077,cy-math.cos(theta)*.105,top-.062),(math.sin(theta)*.077+.004*math.sin(i),cy-math.cos(theta)*.108,end)]
        verts=[];n,m=25,10
        for j in range(n+1):
            t=j/n;p=interp(controls,t);width=(.003+.021*math.sin(t*math.pi/2))*(1-.56*smooth(.80,1,t))
            for k in range(m+1):
                u=k/m*2-1
                verts.append(tuple(p+Vector((u*width,-.0025*(1-u*u),.007*u*u*smooth(.7,1,t)))))
        faces=[(j*(m+1)+k,(j+1)*(m+1)+k,(j+1)*(m+1)+k+1,j*(m+1)+k+1) for j in range(n) for k in range(m)]
        ob=mesh('Fringe_%02d'%i,verts,faces,hair if i%2 else hair2);solid(ob,.002)
    sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.samples=a.samples;sc.cycles.seed=0;sc.cycles.use_denoising=False
    sc.render.film_transparent=True;sc.render.resolution_x=768;sc.render.resolution_y=768;sc.render.resolution_percentage=100
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.image_settings.color_depth='8'
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=-.3;sc.view_settings.gamma=1
    sc.world.use_nodes=True;sc.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.45,.45,.45,1);sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
    target=Vector((0,-.04,(crown.z+chin.z)/2))
    for name,offset,energy,size in [('Key',(-.5,-.65,.65),10,.65),('Fill',(.6,-.35,.25),6,.7),('Rim',(.2,.5,.6),10,.5)]:
        ld=bpy.data.lights.new(name,'AREA');ld.energy=energy;ld.shape='DISK';ld.size=size
        ob=bpy.data.objects.new(name,ld);sc.collection.objects.link(ob);ob.location=target+Vector(offset);ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    cd=bpy.data.cameras.new('Review_camera');cam=bpy.data.objects.new('Review_camera',cd);sc.collection.objects.link(cam);sc.camera=cam;cd.type='ORTHO'
    evidence={'status':'UNAPPROVED_HEAD_STUDY','source_sha256':STAGE_SHA,'references':integrity,'blender':bpy.app.version_string,'engine':'CYCLES CPU','samples':a.samples,'seed':0,'view_transform':'AgX','landmarks':{'source_crown_vertex':CROWN_INDEX,'source_chin_underside_vertex':CHIN_INDEX,'source_crown':list(original[CROWN_INDEX]),'source_chin':list(original[CHIN_INDEX]),'source_ratio':(crown0-sole0)/(crown0-chin0),'head_scale':scale,'crown':list(crown),'chin_underside':list(chin),'sole_z':sole,'head_count':ratio,'classification':'SELF_REVIEWED_VERTEX_LANDMARKS; independent anatomy review pending'},'views':[], 'denoising':False, 'independent_anatomy_review':'NOT_RUN'}
    views=[('front',(0,-1,0)),('back',(0,1,0)),('character_left',(1,0,0)),('character_right',(-1,0,0)),('three_quarter',(.65,-1,.10)),('three_quarter_other',(-.65,-1,.10))]
    for name,d in views:
        cd.ortho_scale=.37;cam.location=target+Vector(d).normalized()*1.5;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
        from bpy_extras.object_utils import world_to_camera_view
        bpy.context.view_layer.update()
        head_points=[p for p in coords if p.z>=chin.z-.005]
        for ob in bpy.data.objects:
            if ob.type=='MESH' and ob!=body:
                head_points.extend(ob.matrix_world@v.co for v in ob.data.vertices)
        projected=[world_to_camera_view(sc,cam,p) for p in head_points]
        frame=[min(p.x for p in projected),min(p.y for p in projected),max(p.x for p in projected),max(p.y for p in projected)]
        evidence['views'].append({'name':name,'camera':list(cam.location),'target':list(target),'ortho_scale':cd.ortho_scale,'file':name+'.png','head_bounds_uv':frame,'head_geometry_in_frame':all(.01<v<.99 for v in frame),'crop_policy':'head fully in frame; shoulders intentionally cropped'})
    # Full body proportion proof at identical four-view scale; kept separate from head art.
    for name,d in views[:4]:
        center=Vector((0,-.02,crown.z/2));cd.ortho_scale=1.9;cam.location=center+Vector(d)*3;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        sc.render.resolution_x=640;sc.render.resolution_y=960;sc.render.filepath=str(out/('body_'+name+'.png'));bpy.ops.render.render(write_still=True)
        evidence['views'].append({'name':'body_'+name,'camera':list(cam.location),'target':list(center),'ortho_scale':cd.ortho_scale,'file':'body_'+name+'.png'})
    # Editable candidate opens on face view; embedded original images are preserved.
    cd.ortho_scale=.37;cam.location=target+Vector((.65,-1,.1)).normalized()*1.5;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.resolution_x=768;sc.render.resolution_y=768
    body['canonical_approval']=False;body['head_count_actual_self_qa']=ratio;body['source_license']='CC0; Blender Human Base Meshes v1.4.1';body['source_object']='GEO-body_female_realistic'
    path=out/'morwen_head_study_UNAPPROVED.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    evidence['candidate_sha256']=sha(path);bpy.ops.wm.open_mainfile(filepath=str(path),load_ui=False)
    stats=[]
    for ob in bpy.data.objects:
        if ob.type!='MESH':continue
        bm=bmesh.new();bm.from_mesh(ob.data)
        stats.append({'object':ob.name,'vertices':len(bm.verts),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True)})
        bm.free()
    evidence['mesh_stats']=stats;evidence['reopen_pass']=True;evidence['source_unchanged']=sha(src)==STAGE_SHA
    for f in integrity:assert sha(canon/f['file'])==f['sha256']
    assert evidence['source_unchanged']
    (out/'build_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('MORWEN_RESULT',json.dumps({'head_count':ratio,'mesh_count':len(stats),'reopen':True}))

if __name__=='__main__':main()
