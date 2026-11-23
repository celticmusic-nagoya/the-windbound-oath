import bpy, hashlib, json, math, sys
from mathutils import Vector
from pathlib import Path
mode, filename, value = sys.argv[sys.argv.index('--')+1:]
p=Path(filename)
if mode == 'create':
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for name,loc in [('target',(0,0,0)),('protected',(0,5,0))]:
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        bpy.context.object.name=name
    bpy.ops.object.camera_add(location=(4,-6,3))
    cam=bpy.context.object
    cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler()
    bpy.context.scene.camera=cam
    bpy.ops.wm.save_as_mainfile(filepath=filename)
else:
    bpy.ops.wm.open_mainfile(filepath=filename)
    obj=bpy.data.objects['target']
    if mode in ('edit','correct'):
        desired=float(value) if mode=='edit' else obj.dimensions.x+float(value)
        obj.scale.x*=desired/obj.dimensions.x
        bpy.context.view_layer.update()
        bpy.context.preferences.filepaths.save_version=0
        bpy.ops.wm.save_as_mainfile(filepath=filename)
    elif mode=='measure':
        protected=bpy.data.objects['protected']
        payload=json.dumps({'matrix':[list(r) for r in protected.matrix_world],
                            'vertices':[list(v.co) for v in protected.data.vertices]})
        print('NATIVE_JSON',json.dumps({'length':obj.dimensions.x,'width':obj.dimensions.y,
                                        'protected':hashlib.sha256(payload.encode()).hexdigest(),
                                        'topology':[len(obj.data.vertices),len(obj.data.polygons)]}))
    elif mode=='preview':
        scene=bpy.context.scene
        scene.render.engine='CYCLES'
        scene.cycles.samples=1
        scene.world=bpy.data.worlds.new('preview')
        scene.world.color=(.6,.6,.6)
        scene.render.resolution_x=128
        scene.render.resolution_y=128
        scene.render.resolution_percentage=100
        scene.render.filepath=value
        bpy.ops.render.render(write_still=True)

