"""Windwaiting Cliff C: art-directed CC0 scan assembly (unapproved).
Inputs: PR #415 packed source artifact. Preserves original scan geometry/materials.
Unlike A/B, this creates no procedural primary cliff geometry: all rock masses
and the seam backing are derived from actual CC0 scan meshes.
"""
import argparse, bpy, hashlib, json, math, sys
from pathlib import Path
from mathutils import Vector

def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda:f.read(1048576),b''):h.update(c)
    return h.hexdigest()

def bounds(objs):
    points=[o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    if not points:raise RuntimeError('SOURCE_HAS_NO_MESH_BOUNDS')
    return (Vector([min(v[i] for v in points) for i in range(3)]),
            Vector([max(v[i] for v in points) for i in range(3)]))

def append_scan(blend,name):
    with bpy.data.libraries.load(str(blend),link=False) as (source,target):
        target.objects=[n for n in source.objects if n]
    col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col)
    meshes=[]
    for obj in target.objects:
        if obj and obj.type=='MESH':
            col.objects.link(obj);meshes.append(obj)
    if not meshes:raise RuntimeError('NO_SCAN_MESHES:'+str(blend))
    return col,meshes

def look_at(obj,point):
    obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--source',required=True);a.add_argument('--out',required=True)
    args=a.parse_args(sys.argv[sys.argv.index('--')+1:])
    src=Path(args.source);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((src/'editable_source_manifest.json').read_text())
    candidates=manifest['candidates']
    if len(candidates)<2:raise RuntimeError('NEED_TWO_VERIFIED_CC0_SOURCES')
    for item in candidates:
        if sha(src/item['blend'])!=item['blend_sha256']:
            raise RuntimeError('SOURCE_SHA_MISMATCH:'+item['id'])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    s['coordinate_space']='asset-local-provisional'
    s['unit_scale_status']='UNAPPROVED'
    s['up_axis']='Z';s['forward_axis']='-Y'
    s['origin_convention']='X0 center, Y negative viewing front, Z0 contact plane'
    s['ground_contact_convention']='all CC0 source instances bottom at Z0 (local)'
    s['canonical_world_placement']='BLOCKED_FOR_INTEGRATION'
    s['art_status']='UNAPPROVED_SCAN_ASSEMBLY_C'
    s['source_manifest_sha256']=sha(src/'editable_source_manifest.json')
    s['source_license']='CC0_CANDIDATE_FROM_PR415_REVERIFY_BEFORE_ADOPTION'
    s['producer_commit']=__import__('os').environ.get('GITHUB_SHA','LOCAL_UNVERIFIED')
    s['design_reference']='PR344 LIND official CG; visual silhouette QA REQUIRED'
    s['spatial_unit']='WINDWAITING_CLIFF_LOCAL_SPACE_01'
    s['production_stage']='STEP_1_SPATIAL_SKELETON_ONLY'
    s['world_integration']='BLOCKED'
    s['lod_export']='NOT_RUN'
    # Deliberate arrangement: 3 lower supporting rock masses, 2 upper interlocking
    # masses, and one scan-derived rear buttress. NOT random scatter.
    layout=[
        (0,(-2.2,0.0,0.0),1.78,-0.18),
        (1,(-0.70,0.17,0.0),1.95,0.23),
        (0,(0.90,0.15,0.0),1.94,-0.35),
        (1,(2.22,0.32,0.0),1.66,0.11),
        (0,(-0.86,0.45,1.20),1.72,0.38),
        (1,(0.95,0.40,1.26),1.77,-0.29),
        (0,(0.05,0.88,0.65),2.12,0.08),
    ]
    placements=[];visible=[]
    for i,(which,target,scale,yaw) in enumerate(layout):
        item=candidates[which]
        col,objs=append_scan(src/item['blend'],'SCAN_%02d_%s'%(i,item['id']))
        low,high=bounds(objs);center=(low+high)*0.5
        extent=max((high-low).length,1e-8)
        factor=scale/extent
        root=bpy.data.objects.new('ART_DIRECTED_SCAN_ROOT_%02d'%i,None)
        col.objects.link(root)
        for obj in objs:
            world=obj.matrix_world.copy();obj.parent=root;obj.matrix_parent_inverse.identity()
            obj.matrix_world=world
            visible.append(obj)
        root.rotation_euler.z=yaw
        root.scale=(factor,)*3
        # Convert source geometry bounds to the desired provisional local contact plane.
        # Evaluate actual transformed corners after parenting, scaling and yaw.
        bpy.context.view_layer.update()
        instance_low,instance_high=bounds(objs)
        root.location.x += target[0]-(instance_low.x+instance_high.x)*0.5
        root.location.y += target[1]-(instance_low.y+instance_high.y)*0.5
        bpy.context.view_layer.update()
        instance_low,instance_high=bounds(objs)
        root.location.z += (0.0 if i<4 else target[2])-instance_low.z
        bpy.context.view_layer.update()
        root['source_sha256']=item['blend_sha256']
        root['source_id']=item['id']
        placements.append({'source_id':item['id'],'source_sha256':item['blend_sha256'],
                           'position':list(root.location),'rotation_z':yaw,'scale':factor,
                           'lower_support':i<4})
    # Source objects remain in separate editable local collections for future LOD splits.
    # No invented cube, plane, heightfield or procedural cliff primary geometry.
    # Keep scans editable and separate to preserve their PBR/scan detail.
    # The seam and geological cohesion must pass visual QA, not presumed by code.
    w=bpy.data.worlds.new('Neutral art QA');w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.18,0.20,0.23,1)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.8;s.world=w
    for name,pos,power,size in [('Key',(-5,-6,10),1800,6),('Fill',(6,-3,7),900,5),('Rim',(1,5,9),1800,5)]:
        d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
        o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=pos;look_at(o,(0,0,0.6))
    cd=bpy.data.cameras.new('Art QA ortho');camera=bpy.data.objects.new('Art QA ortho',cd)
    s.collection.objects.link(camera);s.camera=camera;cd.type='ORTHO';cd.ortho_scale=8.8
    camera.location=(0,-10,4.2);look_at(camera,(0,0,0.6))
    s.render.engine='CYCLES';s.cycles.samples=24
    s.render.resolution_x=1024;s.render.resolution_y=768
    s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
    for layer in s.view_layers:layer.cycles.use_denoising=False
    bpy.ops.file.pack_all()
    blend=out/'windwaiting_cc0_scan_assembly_C_UNAPPROVED.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    views={'front':(0,-10,4.2),'left':(-9,-6,4.2),'right':(9,-6,4.2),'elevated':(7,-8,10)}
    for name,pos in views.items():
        camera.location=pos;look_at(camera,(0,0,0.6))
        s.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True)
    files=[blend]+[out/(name+'.png') for name in views]
    result={'asset':'Windwaiting Cliff scan assembly C',
            'status':'UNAPPROVED_ART_CANDIDATE','source_manifest_sha256':sha(src/'editable_source_manifest.json'),
            'source_candidates':candidates,'placements':placements,
            'source_mesh_count':len(visible),'blender_version':bpy.app.version_string,
            'spatial_unit':s['spatial_unit'],'production_stage':s['production_stage'],
            'script_sha256':sha(Path(__file__)),
            'G1':'BLOCKED','G2':'NOT_RUN','G3':'NOT_RUN','G4':'NOT_RUN',
            'qa_notes':'G2 must inspect overlaps, seam visibility, source scan repetition, geological layering, overhang and PR344 visual reference. This is not a fused sculpt.',
            'files':{p.name:sha(p) for p in files}}
    (out/'manifest_C.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('SCAN_ASSEMBLY_C_ARTIFACTS',json.dumps({'files':result['files']}),flush=True)

if __name__=='__main__':main()
