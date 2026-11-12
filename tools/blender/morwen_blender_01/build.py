"""Blender: four calibrated reference planes, blockouts and 17-bone candidates.

blender -b -t 1 --python tools/blender/morwen_blender_01/build.py -- --output DIR
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
DEFAULT=ROOT/'assets/candidates/morwen-blender-01'


def material(name, color):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*color,1)
    m.use_nodes=True
    shader=m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Roughness'].default_value=0.75
    shader.inputs['Emission Color'].default_value=(*color,1)
    shader.inputs['Emission Strength'].default_value=1
    return m


def line(name, a, b, radius, mat, collection):
    curve=bpy.data.curves.new(name,'CURVE')
    curve.dimensions='3D'
    curve.bevel_depth=radius
    curve.bevel_resolution=2
    spline=curve.splines.new('POLY')
    spline.points.add(1)
    for point,co in zip(spline.points,(a,b)):
        point.co=(*co,1)
    obj=bpy.data.objects.new(name,curve)
    collection.objects.link(obj)
    curve.materials.append(mat)
    return obj


def build(output):
    receipt=json.loads((HERE/'SOURCE_RECEIPT.json').read_text())
    for entry in receipt['files']:
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256'], entry['path']
    data=json.loads((output/'anchors_candidate.json').read_text())
    contract=json.loads((ROOT/'tools/blender/rigs/humanoid_v1.json').read_text())
    # Pure stdlib mapping duplicated explicitly here to avoid importing Pillow
    # into Blender's Python. Keep synchronized with prepare.bone_points in tests.
    parents={b['id']:b['parent'] for b in contract['bones']}
    assert len(parents)==17
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene
    # CPU Cycles avoids EGL/GPU dependencies in headless local and Actions jobs.
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=8
    scene.cycles.use_denoising=False
    scene.render.resolution_x=384
    scene.render.resolution_y=1024
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.film_transparent=False
    scene.world=bpy.data.worlds.new('neutral_qa_world')
    scene.world.color=(0.08,0.08,0.08)
    scene.view_settings.view_transform='Standard'
    scene.view_settings.look='None'
    scene['task']='MORWEN-BLENDER-01'
    scene['approval_status']='FUTURE_CANON_PENDING_APPROVAL'
    scene['anatomical_depth']='INFERRED_NOT_MEASURED'
    collections={}
    for name in ('References_REFERENCE_ONLY','Candidate_armatures','Neutral_body_blockouts','QA_overlays'):
        c=bpy.data.collections.new(name)
        scene.collection.children.link(c)
        collections[name]=c
    mats={s:material(s,c) for s,c in [('L',(0.1,0.65,1.0)),('R',(1.0,0.4,0.06)),('C',(0.1,1.0,0.5)),('hidden',(0.9,0.15,0.8)),('ground',(1.0,0.15,0.15)),('proxy',(0.28,0.48,0.58))]}
    scale=data['common_pixel_scale']
    report={'status':'PASS','blender_version':bpy.app.version_string,
            'visual_approval':False,'production_use':False,
            'future_canon':'FUTURE_CANON_PENDING_APPROVAL','facings':{}}
    for index,(facing,entry) in enumerate(data['facings'].items()):
        offset=index*0.65
        ground=entry['measured_ground_y']
        origin=entry['origin_x']
        points=entry['rig_points_pixels']
        def position(pixel, side=None):
            depth=0
            if side and entry['near_side']:
                depth=(-1 if side==entry['near_side'] else 1)*entry['inferred_half_depth_px']*scale
            return Vector(((pixel[0]-origin)*scale,depth,(ground-pixel[1])*scale))
        pixel_bones={'root':([origin,ground],[origin,ground-30]),
                     'pelvis':(points['pelvis'],points['waist']),
                     'spine':(points['waist'],points['chest']),
                     'neck':(points['chest'],points['neck']),
                     'head':(points['neck'],points['head_top'])}
        for side in ('L','R'):
            for name,a,b in [('upper_arm','shoulder','elbow'),('forearm','elbow','wrist'),
                             ('hand','wrist','handtip'),('thigh','hip','knee'),
                             ('shin','knee','ankle'),('foot','ankle','toe')]:
                pixel_bones[name+'.'+side]=(points[a+'.'+side],points[b+'.'+side])
        assert set(pixel_bones)==set(parents)
        arm=bpy.data.armatures.new('Morwen_'+facing+'_17_candidate')
        rig=bpy.data.objects.new(arm.name,arm)
        collections['Candidate_armatures'].objects.link(rig)
        rig.location.x=offset
        rig['facing']=facing
        rig['candidate_status']='PIXEL_REFINED_VISUAL_ESTIMATE_UNREVIEWED'
        rig['source_sha256']=entry['source_sha256']
        rig.show_in_front=True
        arm.display_type='STICK'
        bpy.context.view_layer.objects.active=rig
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT')
        positions={}
        for name,(a,b) in pixel_bones.items():
            side=name[-1] if name.endswith(('.L','.R')) else None
            head,tail=position(a,side),position(b,side)
            assert (head-tail).length>1e-6
            bone=arm.edit_bones.new(name)
            bone.head=head
            bone.tail=tail
            bone.use_deform=name!='root'
            positions[name]=(head,tail)
        for name,parent in parents.items():
            if parent:
                arm.edit_bones[name].parent=arm.edit_bones[parent]
                arm.edit_bones[name].use_connect=False
        bpy.ops.object.mode_set(mode='OBJECT')
        # Neutral segmented mannequin: no costume/sexual detail, no claim of
        # multi-view 3D reconstruction or production topology/skin quality.
        verts=[];faces=[];groups={name:[] for name in parents}
        radii={'pelvis':(76,48),'spine':(64,42),'neck':(22,22),'head':(57,45),
               'upper_arm':(19,19),'forearm':(15,15),'hand':(12,12),
               'thigh':(34,32),'shin':(23,22),'foot':(21,19)}
        for name,(head,tail) in positions.items():
            if name=='root':
                continue
            key=name.split('.')[0]
            rx,ry=radii[key]
            # Width in profile is inferred body depth rather than shoulder width.
            if entry['near_side'] and key in ('pelvis','spine','head'):
                rx,ry=ry,rx
            direction=(tail-head).normalized()
            u=Vector((1,0,0))
            if abs(direction.dot(u))>0.95:
                u=Vector((0,1,0))
            u=(u-direction*u.dot(direction)).normalized()
            v=direction.cross(u).normalized()
            center=(head+tail)/2
            radius_z=(tail-head).length/2+8*scale
            start=len(verts)
            rings,segments=10,16
            verts.append(tuple(center+direction*radius_z))
            for lat in range(1,rings):
                theta=math.pi*lat/rings
                for lon in range(segments):
                    phi=2*math.pi*lon/segments
                    vertex=center+u*(math.sin(theta)*math.cos(phi)*rx*scale)+v*(math.sin(theta)*math.sin(phi)*ry*scale)+direction*(math.cos(theta)*radius_z)
                    verts.append(tuple(vertex))
            bottom=len(verts)
            verts.append(tuple(center-direction*radius_z))
            groups[name].extend(range(start,len(verts)))
            for lon in range(segments):
                faces.append((start,start+1+lon,start+1+(lon+1)%segments))
                last=start+1+(rings-2)*segments
                faces.append((bottom,last+(lon+1)%segments,last+lon))
            for lat in range(rings-2):
                for lon in range(segments):
                    a=start+1+lat*segments+lon;b=start+1+lat*segments+(lon+1)%segments
                    faces.append((a,b,b+segments,a+segments))
        mesh=bpy.data.meshes.new('Morwen_'+facing+'_blockout_mesh')
        mesh.from_pydata(verts,[],faces)
        mesh.update()
        body=bpy.data.objects.new('Morwen_'+facing+'_neutral_proxy',mesh)
        collections['Neutral_body_blockouts'].objects.link(body)
        body.location.x=offset
        body['status']='SEGMENTED_NEUTRAL_BLOCKOUT_NOT_FINAL_SKIN'
        body['facing']=facing
        body.display_type='WIRE'
        body.hide_render=True
        mesh.materials.append(mats['proxy'])
        for name,indices in groups.items():
            group=body.vertex_groups.new(name=name)
            if indices:
                group.add(indices,1.0,'REPLACE')
        modifier=body.modifiers.new('candidate_armature','ARMATURE')
        modifier.object=rig
        for polygon in mesh.polygons:
            polygon.use_smooth=True
        # Pack the exact source bytes; relative paths make the scene portable.
        image=bpy.data.images.load(str(ROOT/entry['source']),check_existing=True)
        image.pack()
        assert hashlib.sha256(bytes(image.packed_file.data)).hexdigest()==entry['source_sha256']
        image.filepath='//../../references/morwen/reference_20261112/'+Path(entry['source']).name
        image['status']='REFERENCE_ONLY'
        plane_mesh=bpy.data.meshes.new(facing+'_reference_plane')
        corners=[position(p) for p in ([0,1024],[384,1024],[384,0],[0,0])]
        plane_mesh.from_pydata([(p.x+offset,0.25,p.z) for p in corners],[],[(0,1,2,3)])
        uv=plane_mesh.uv_layers.new()
        for loop,coord in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):
            loop.uv=coord
        plane=bpy.data.objects.new(facing+'_REFERENCE_ONLY',plane_mesh)
        collections['References_REFERENCE_ONLY'].objects.link(plane)
        m=bpy.data.materials.new(facing+'_source')
        m.use_nodes=True
        nodes=m.node_tree.nodes;nodes.clear()
        tex=nodes.new('ShaderNodeTexImage');tex.image=image
        emit=nodes.new('ShaderNodeEmission')
        trans=nodes.new('ShaderNodeBsdfTransparent')
        mix=nodes.new('ShaderNodeMixShader')
        out=nodes.new('ShaderNodeOutputMaterial')
        links=m.node_tree.links
        links.new(tex.outputs['Color'],emit.inputs['Color'])
        links.new(tex.outputs['Alpha'],mix.inputs[0])
        links.new(trans.outputs[0],mix.inputs[1]);links.new(emit.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
        plane_mesh.materials.append(m)
        camera_data=bpy.data.cameras.new(facing+'_orthographic')
        camera_data.type='ORTHO';camera_data.ortho_scale=1024*scale
        camera=bpy.data.objects.new(facing+'_orthographic',camera_data)
        scene.collection.objects.link(camera)
        camera.location=(offset+(192-origin)*scale,-3,(ground-512)*scale)
        camera.rotation_euler=(math.pi/2,0,0)
        scene.camera=camera
        bpy.context.view_layer.update()
        max_projection_error=0
        for name,(head,tail) in positions.items():
            side=name[-1] if name.endswith(('.L','.R')) else None
            hidden=bool(side and entry['near_side'] and side!=entry['near_side'])
            color=mats['hidden'] if hidden else mats[side or 'C']
            a=head+Vector((offset,-0.3,0));b=tail+Vector((offset,-0.3,0))
            # Hidden chains remain coincident in XY, not fictitiously mirrored;
            # slight debug-only X offset makes inference visible in overlays.
            if hidden:
                a.x+=3*scale;b.x+=3*scale
            line(facing+'_'+name+'_QA',a,b,1.6*scale,color,collections['QA_overlays'])
            for point,pixel in zip((head,tail),pixel_bones[name]):
                projected=world_to_camera_view(scene,camera,point+Vector((offset,0,0)))
                error=math.hypot(projected.x*384-pixel[0],(1-projected.y)*1024-pixel[1])
                max_projection_error=max(max_projection_error,error)
        assert max_projection_error<0.01
        ground_a=Vector((offset+(0-origin)*scale,-0.3,0));ground_b=Vector((offset+(384-origin)*scale,-0.3,0))
        line(facing+'_measured_ground',ground_a,ground_b,0.8*scale,mats['ground'],collections['QA_overlays'])
        scene.render.filepath=str(output/(facing+'_overlay.png'))
        bpy.ops.render.render(write_still=True)
        report['facings'][facing]=dict(bones=len(arm.bones),parent_links=sum(b.parent is not None for b in arm.bones),
            proxy_vertices=len(mesh.vertices),proxy_vertex_groups=len(body.vertex_groups),source_image_sha256=entry['source_sha256'],
            max_projection_error_px=max_projection_error,measured_ground_y=ground,
            near_side=entry['near_side'],hidden_depth='INFERRED',anatomical_sides=True)
    # Additional neutral blockout plate makes the actual new geometry reviewable
    # without requiring a reviewer to open Blender. Source planes are excluded.
    collections['References_REFERENCE_ONLY'].hide_render=True
    collections['QA_overlays'].hide_render=True
    bodies=[obj for obj in collections['Neutral_body_blockouts'].objects]
    for body in bodies:
        body.hide_render=False
    mats['proxy'].node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=0.05
    for x,z,power in [(-1,2.8,80),(2.8,1.8,50)]:
        light=bpy.data.lights.new('blockout_area','AREA');light.energy=power;light.size=3
        obj=bpy.data.objects.new('blockout_area',light);scene.collection.objects.link(obj)
        obj.location=(x,-2,z)
        obj.rotation_euler=(Vector((0.975,0,0.5))-obj.location).to_track_quat('-Z','Y').to_euler()
    overview_data=bpy.data.cameras.new('neutral_blockout_overview')
    # For this landscape camera ortho_scale describes the horizontal span.
    overview_data.type='ORTHO';overview_data.ortho_scale=2.6
    overview=bpy.data.objects.new('neutral_blockout_overview',overview_data)
    scene.collection.objects.link(overview)
    overview.location=(0.975,-4,0.5);overview.rotation_euler=(math.pi/2,0,0)
    scene.camera=overview
    scene.render.resolution_x=2048;scene.render.resolution_y=1024
    bpy.context.view_layer.update()
    for body in bodies:
        for corner in body.bound_box:
            projected=world_to_camera_view(scene,overview,body.matrix_world@Vector(corner))
            assert 0 <= projected.x <= 1 and 0 <= projected.y <= 1, 'Blockout overview crops geometry'
    report['overview_camera_contains_all_proxies']=True
    scene.cycles.samples=32
    scene.render.filepath=str(output/'neutral_proxy_4views.png')
    bpy.ops.render.render(write_still=True)
    for body in bodies:
        body.hide_render=True
    collections['References_REFERENCE_ONLY'].hide_render=False
    collections['QA_overlays'].hide_render=False
    scene.render.resolution_x=384;scene.render.resolution_y=1024
    scene.camera=bpy.data.objects['front_orthographic']
    scene.render.filepath=str(output/'front_overlay.png')
    scene['source_images_packed']=4
    bpy.ops.wm.save_as_mainfile(filepath=str(output/'morwen_base_rig_candidate.blend'))
    (output/'blender_qa.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MORWEN_BLENDER_01_PASS')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=DEFAULT)
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    build(args.output.resolve())
