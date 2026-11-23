"""Blender-side native measurement (run inside Blender 5.3.0 / bpy 5.3.0).

Usage: <python-with-bpy> measure_blender.py NATIVE.blend SPEC.json OUT.json
       blender -b --factory-startup --python measure_blender.py -- NATIVE SPEC OUT
Read-only: opens the file, never saves. Coordinates are world-space mesh data
(pre-modifier) unless spec["evaluated"] is true.
"""
import hashlib
import json
import sys

import bpy


def fingerprint(obj, evaluated, depsgraph):
    digest = hashlib.sha256()
    digest.update(repr((obj.name, obj.type, tuple(tuple(r) for r in obj.matrix_world),
                        obj.hide_render, obj.parent.name if obj.parent else None)).encode())
    if obj.type == "MESH":
        mesh = obj.evaluated_get(depsgraph).to_mesh() if evaluated else obj.data
        digest.update(repr((tuple(tuple(v.co) for v in mesh.vertices),
                            tuple(tuple(p.vertices) for p in mesh.polygons),
                            tuple(p.material_index for p in mesh.polygons),
                            tuple(s.material.name if s.material else None
                                  for s in obj.material_slots),
                            tuple(tuple(tuple(d.uv) for d in layer.data)
                                  for layer in mesh.uv_layers))).encode())
        if evaluated:
            obj.evaluated_get(depsgraph).to_mesh_clear()
    return digest.hexdigest()


def main(argv):
    native, spec_path, out = argv
    spec = json.load(open(spec_path))
    bpy.ops.wm.open_mainfile(filepath=native, load_ui=False)
    evaluated = bool(spec.get("evaluated"))
    depsgraph = bpy.context.evaluated_depsgraph_get()
    objects = {}
    for obj in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        record = dict(type=obj.type, location=list(obj.matrix_world.translation),
                      fingerprint=fingerprint(obj, evaluated, depsgraph))
        if obj.type == "MESH":
            mesh = obj.evaluated_get(depsgraph).to_mesh() if evaluated else obj.data
            points = [obj.matrix_world @ v.co for v in mesh.vertices]
            if points:
                record["bbox_min"] = [min(p[i] for p in points) for i in range(3)]
                record["bbox_max"] = [max(p[i] for p in points) for i in range(3)]
            record.update(vertices=len(mesh.vertices), faces=len(mesh.polygons))
            if evaluated:
                obj.evaluated_get(depsgraph).to_mesh_clear()
        objects[obj.name] = record
    result = dict(bpy_version=bpy.app.version_string,
                  build_hash=bpy.app.build_hash.decode() if isinstance(bpy.app.build_hash, bytes)
                  else str(bpy.app.build_hash),
                  file_version=list(bpy.data.version), evaluated=evaluated,
                  is_dirty=bpy.data.is_dirty, objects=objects)
    with open(out, "w") as stream:
        json.dump(result, stream, sort_keys=True, indent=1)


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(args)
