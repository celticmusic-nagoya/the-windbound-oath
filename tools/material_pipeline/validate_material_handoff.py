#!/usr/bin/env python3
"""Read-only validation of an image-to-3D material handoff manifest."""
import argparse
import hashlib
import json
from pathlib import Path

MAP_TYPES = {'base_color', 'roughness', 'normal', 'height', 'alpha', 'emissive', 'metallic'}

def validate(manifest_path, root):
    manifest_path, root = Path(manifest_path), Path(root).resolve()
    data = json.loads(manifest_path.read_text(encoding='utf-8'))
    errors = []
    if data.get('schema') != 'lind.material-handoff.v1':
        errors.append('schema: expected lind.material-handoff.v1')
    for field in ('asset_id', 'reference_sha256', 'producer', 'tool_version', 'seed', 'license'):
        if not data.get(field) and data.get(field) != 0:
            errors.append(f'missing {field}')
    maps = data.get('maps')
    if not isinstance(maps, list) or not maps:
        errors.append('maps must be a nonempty list')
        maps = []
    for i, item in enumerate(maps):
        label = f'maps[{i}]'
        if not isinstance(item, dict):
            errors.append(f'{label}: not an object'); continue
        if item.get('type') not in MAP_TYPES:
            errors.append(f'{label}: invalid type')
        if item.get('color_space') != ('sRGB' if item.get('type') in ('base_color','emissive') else 'Non-Color'):
            errors.append(f'{label}: invalid color_space')
        sha = item.get('sha256', '')
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in '0123456789abcdef' for c in sha):
            errors.append(f'{label}: invalid sha256'); continue
        rel = item.get('path')
        if not isinstance(rel, str) or not rel:
            errors.append(f'{label}: missing path'); continue
        candidate = (root / rel).resolve()
        if not candidate.is_relative_to(root):
            errors.append(f'{label}: path escapes root'); continue
        if not candidate.is_file():
            errors.append(f'{label}: file missing'); continue
        actual = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if actual != sha:
            errors.append(f'{label}: SHA mismatch')
    return errors

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('manifest')
    ap.add_argument('--root', default='.')
    args = ap.parse_args()
    errors = validate(args.manifest, args.root)
    print(json.dumps({'status':'FAIL' if errors else 'PASS','errors':errors}, ensure_ascii=False, indent=2))
    raise SystemExit(bool(errors))

if __name__ == '__main__':
    main()
