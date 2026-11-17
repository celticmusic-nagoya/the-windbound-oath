import bpy,json,hashlib,sys
from pathlib import Path
args=sys.argv[sys.argv.index('--')+1:];out=Path(args[0]); rows=[]
for im in bpy.data.images:
 if im.packed_file:
  data=bytes(im.packed_file.data);rows.append({'name':im.name,'size':list(im.size),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
result={'blender_version':bpy.app.version_string,'blend':bpy.data.filepath,'scene_properties':dict(bpy.context.scene.items()),'collections':[{'name':c.name,'properties':dict(c.items()),'objects':len(c.objects)} for c in bpy.data.collections],'packed_images':rows,'objects':[{'name':o.name,'type':o.type,'location':list(o.location),'properties':dict(o.items()),'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'vertices':len(o.data.vertices) if o.type=='MESH' else None,'polygons':len(o.data.polygons) if o.type=='MESH' else None} for o in bpy.data.objects]}
out.write_text(json.dumps(result,indent=2,default=str)+'\n');print('INDEPENDENT_BLEND_INSPECTION',out)
