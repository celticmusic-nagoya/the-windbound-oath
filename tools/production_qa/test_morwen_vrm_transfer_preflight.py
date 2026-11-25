"""Independent negative probes; no real character data. Run against reviewed module.
Usage: python test_morwen_vrm_transfer_preflight.py /path/to/import_vrm_transfer.py
Synthetic control is only a parser-shape fixture, not a conformant VRM or an import test.
"""
import copy
import hashlib
import importlib.util
import json
import pathlib
import struct
import sys


def glb(model, tail=b''):
    payload = json.dumps(model, separators=(',', ':')).encode()
    payload += b' ' * (-len(payload) % 4)
    return struct.pack('<4sII', b'glTF', 2, 20 + len(payload) + len(tail)) + struct.pack('<I4s', len(payload), b'JSON') + payload + tail


def fixture():
    return {'asset': {'version': '2.0'}, 'extensions': {'VRMC_vrm': {'specVersion': '1.0', 'meta': {'name': 'synthetic fixture'}, 'humanoid': {'humanBones': {'hips': {'node': 0}}}, 'expressions': {'preset': {'blink': {}}}}}, 'nodes': [{}], 'skins': [{'joints': [0]}], 'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'TEXCOORD_0': 0, 'JOINTS_0': 0, 'WEIGHTS_0': 0}}]}], 'materials': [{}], 'images': [{'bufferView': 0, 'mimeType': 'image/png'}], 'accessors': [{'bufferView': 0, 'componentType': 5126, 'type': 'VEC3', 'count': 1}], 'bufferViews': [{'buffer': 0, 'byteOffset': 0, 'byteLength': 12}], 'buffers': [{'byteLength': 12}]}


def probes(inspect):
    base = fixture()
    tail = struct.pack('<I4s', 12, b'BIN\0') + bytes(12)
    normal = glb(base, tail)
    cases = [('category_control_only', normal, True), ('wrong_magic', b'BAD!' + normal[4:], False), ('wrong_total_length', normal[:-1], False), ('missing_bin_chunk', glb(base), False), ('truncated_bin_payload', glb(base, tail[:-4]), False), ('garbage_trailing_bytes', glb(base, b'garbage!'), False)]
    def modify(name, mutate):
        model = copy.deepcopy(base)
        mutate(model)
        cases.append((name, glb(model, tail), False))
    modify('external_image_uri', lambda m: m['images'][0].update(uri='external.png'))
    modify('invalid_joint_node_index', lambda m: m['skins'][0].update(joints=[999]))
    modify('invalid_humanoid_node_index', lambda m: m['extensions']['VRMC_vrm']['humanoid']['humanBones']['hips'].update(node=999))
    modify('invalid_accessor_index', lambda m: m['meshes'][0]['primitives'][0]['attributes'].update(POSITION=999))
    modify('buffer_view_overrun', lambda m: m['bufferViews'][0].update(byteLength=999))
    modify('image_buffer_view_index_invalid', lambda m: m['images'][0].update(bufferView=999))
    modify('missing_vrm_extension', lambda m: m.update(extensions={}))
    modify('missing_required_category', lambda m: m.update(skins=[]))
    result = []
    for name, raw, expected in cases:
        try:
            inspect(raw)
            accepted, error = True, None
        except Exception as exc:
            accepted, error = False, type(exc).__name__
        result.append(dict(case=name, expected_accept=expected, observed_accept=accepted, pass_=expected == accepted, error=error, input_sha256=hashlib.sha256(raw).hexdigest()))
    return result


def main():
    path = pathlib.Path(sys.argv[1])
    spec = importlib.util.spec_from_file_location('reviewed_importer', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = probes(module.inspect_vrm)
    print(json.dumps({'scope': 'SYNTHETIC_PARSER_PROBES_NOT_MODEL_QA', 'module_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'cases': results, 'pass_count': sum(r['pass_'] for r in results), 'total': len(results)}, indent=2))
    return int(not all(r['pass_'] for r in results))


if __name__ == '__main__':
    raise SystemExit(main())
