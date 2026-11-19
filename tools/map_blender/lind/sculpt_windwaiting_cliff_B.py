"""Windwaiting Cliff B: connected voxel-sculpted bedrock, noncanonical art candidate.
Distinct from stopped cross-section extrusion. No external assets.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, noise

def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()

def mat(name,rgb):
    m=bpy.data.materials.new(name);m.diffuse_color=(*rgb,1);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb,1);p.inputs['Roughness'].default_value=0.9
    tex=m.node_tree.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=8
    tex.inputs['Detail'].default_value=5
    bump=m.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=0.24
    bump.inputs['Distance'].default_value=0.06
    m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
    m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
    return m

def aim(obj,target):
    obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def main():
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    out=Path(argv[argv.index('--out')+1] if '--out' in argv else 'out/cliff-b')
    out.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    for k,v in {
        'coordinate_space':'asset-local-provisional','unit_scale_status':'UNAPPROVED',
        'origin_convention':'XY center of rock assembly, Z=0 provisional ground',
        'ground_contact_convention':'rock base at provisional Z=0, game placement BLOCKED',
        'source_manifest_sha256':'NO_EXTERNAL_SOURCE; ORIGINAL_GEOMETRY',
        'source_license':'original in-repository Blender authored source',
        'producer_commit':'UNSET_AT_GENERATION',
        'canonical_world_placement':'BLOCKED_FOR_INTEGRATION',
        'up_axis':'Z','forward_axis':'-Y',
        'art_status':'UNAPPROVED_G2_REVIEW_REQUIRED',
        'production_method':'overlapping volumes -> voxel fusion -> localized vertex sculpt',
    }.items():s[k]=v
    rockmat=mat('Weathered limestone - provisional',(0.30,0.295,0.265))
    # Directed geological masses, each (x,y,z,sx,sy,sz,yaw,tilt).
    # Inputs are fused and sculpted into one continuous rock mesh.
    blocks=[
      (-2.70,0.23,1.45,1.25,1.17,1.90,-0.22,0.15),
      (-1.80,0.10,2.00,1.35,1.24,2.32,0.16,-0.08),
      (-0.68,-0.12,2.05,1.42,1.38,2.44,-0.15,0.12),
      (0.45,-0.20,2.28,1.30,1.51,2.60,0.11,-0.11),
      (1.63,0.03,1.96,1.48,1.35,2.37,-0.12,0.06),
      (2.78,0.17,1.52,1.19,1.12,1.95,0.24,-0.13),
      (-0.70,-0.72,3.26,1.42,1.24,0.68,-0.10,0.14),
      (0.72,-0.83,3.53,1.36,1.24,0.69,0.17,-0.10),
    ]
    parts=[]
    for i,(x,y,z,sx,sy,sz,yaw,tilt) in enumerate(blocks):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1,location=(x,y,z))
        o=bpy.context.object;o.name='FUSION_INPUT_%02d'%i
        o.scale=(sx,sy,sz);o.rotation_euler=(tilt,0,yaw)
        bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
        parts.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:p.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join()
    rock=bpy.context.object;rock.name='WINDBOUND_SCULPTED_CLIFF_B_UNAPPROVED'
    rock.data.remesh_voxel_size=0.085
    bpy.ops.object.voxel_remesh()
    # Geometry-level sculpt: multiscale relief and tapered recessed fault channels.
    faults=[(-2.15,-0.92,0.45,0.28),(-0.20,-1.24,-0.30,0.21),(1.95,-1.08,0.54,0.24)]
    for v in rock.data.vertices:
        p=v.co.copy();n=v.normal.copy()
        q=Vector((p.x*1.19,p.y*1.04,p.z*0.88))
        broad=noise.noise_vector(q*0.73).dot(Vector((0.3,0.6,0.7)))
        middle=noise.noise(q*2.15);fine=noise.noise(q*6.20)
        relief=(0.17*broad+0.075*middle+0.025*fine)*(0.48 if p.z<0.32 else 1)
        fault_depth=0.0
        for x,y,slope,width in faults:
            distance=abs(p.x-(x+slope*(p.z-2.0)))
            visibility=max(0,min(1,(p.z-0.35)/0.6,(4.0-p.z)/0.7))
            if p.y<0.45:
                fault_depth+=0.19*math.exp(-((distance/width)**2))*visibility
        v.co=p+n*(relief-fault_depth)
    rock.data.update()
    rock.data.materials.append(rockmat)
    uv=rock.data.uv_layers.new(name='PROVISIONAL_TRI_PLANAR_PREVIEW')
    for poly in rock.data.polygons:
        for li in poly.loop_indices:
            p=rock.data.vertices[rock.data.loops[li].vertex_index].co
            uv.data[li].uv=((p.x+4.5)/9.0,p.z/5.5)
        poly.use_smooth=True
    smooth=rock.modifiers.new('Mineral relief preservation smooth','SMOOTH')
    smooth.factor=0.24;smooth.iterations=2
    w=bpy.data.worlds.new('Neutral studio');s.world=w;w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.23,0.25,0.29,1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.7
    for name,loc,power,size in [('Key',(-4,-6,9),1800,5),('Fill',(4,-5,6),900,4),('Rim',(1,5,8),2100,5)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
        o=bpy.data.objects.new(name,data);s.collection.objects.link(o);o.location=loc;aim(o,(0,0,2))
    camdata=bpy.data.cameras.new('Art review orthographic')
    cam=bpy.data.objects.new('Art review orthographic',camdata)
    s.collection.objects.link(cam);s.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=10.5
    s.render.engine='CYCLES';s.cycles.samples=20
    s.render.resolution_x=1100;s.render.resolution_y=780;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG'
    bpy.ops.file.pack_all()
    blend=out/'windwaiting_sculpted_cliff_B_UNAPPROVED.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    views={'front':(0,-13,5.5),'left':(-10,-8,5.5),'right':(10,-8,5.5),'elevated':(8,-10,11)}
    for name,pos in views.items():
        cam.location=pos;aim(cam,(0,0,2.1));s.render.filepath=str(out/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    files=[blend]+[out/(n+'.png') for n in views]
    manifest={
        'asset':'Windwaiting Cliff / connected bedrock B',
        'status':'UNAPPROVED_ART_CANDIDATE',
        'method':'fused-volume voxel sculpt; geometric fault carving',
        'blender':bpy.app.version_string,
        'mesh_vertices':len(rock.data.vertices),'mesh_polygons':len(rock.data.polygons),
        'coordinate_space':'asset-local-provisional','unit_scale_status':'UNAPPROVED',
        'G1':'NOT_RUN','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN',
        'integration':'BLOCKED_FOR_INTEGRATION',
        'files':{p.name:digest(p) for p in files},
    }
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('SCULPTED_CLIFF_B_GENERATED',json.dumps(manifest),flush=True)

if __name__=='__main__':main()
