"""Package the image-tool edit into 20 PNGs; no repainting or resampling.

Equal atlas cells are cropped and padded to a shared sole anchor. Original
uploaded PNGs and the generated atlas are kept separately for provenance.
"""
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'docs/art/candidates/goblin-field-20f/generated-sheet.png'
DEST = ROOT / 'img/field/monsters/goblin'
ROWS = ['idle', 'walk_down', 'walk_right', 'walk_up', 'walk_left']


def main():
    sheet = Image.open(SOURCE).convert('RGBA')
    DEST.mkdir(parents=True, exist_ok=True)
    entries = []
    for row, name in enumerate(ROWS):
        for col in range(4):
            rect = [round(col * sheet.width / 4), round(row * sheet.height / 5),
                    round((col + 1) * sheet.width / 4), round((row + 1) * sheet.height / 5)]
            cell = sheet.crop(rect)
            alpha = cell.getchannel('A')
            box = alpha.point(lambda a: 255 if a > 32 else 0).getbbox()
            assert box, (row, col)
            # Both soles/ankles define the horizontal anchor, not the cleaver.
            bottom = max(box[1], box[3] - round((box[3] - box[1]) * .18))
            feet = alpha.crop((0, bottom, cell.width, box[3])).point(lambda a: 255 if a > 128 else 0).getbbox()
            assert feet
            ax, ay = round((feet[0] + feet[2]) / 2), box[3]
            dx, dy = 160 - ax, 288 - ay
            # The transparent edit has low-alpha matte noise across empty cells.
            # Keep the entire >32-alpha figure plus a two-pixel antialias gutter.
            hull = (max(0, box[0] - 2), max(0, box[1] - 2),
                    min(cell.width, box[2] + 2), min(cell.height, box[3] + 2))
            assert hull[0] + dx >= 0 and hull[2] + dx <= 320, (name, col, hull)
            assert hull[1] + dy >= 0 and hull[3] + dy <= 320, (name, col, hull)
            frame = Image.new('RGBA', (320, 320))
            frame.paste(cell.crop(hull), (hull[0] + dx, hull[1] + dy))
            # Discard invisible matte RGB, preserving every visible RGBA pixel.
            frame.putdata([p if p[3] else (0, 0, 0, 0) for p in frame.getdata()])
            path = DEST / f'goblin_{name}_{col + 1:02d}.png'
            frame.save(path, optimize=True)
            entries.append({'path': str(path.relative_to(ROOT)), 'row': name,
                            'frame': col + 1, 'source_rect': rect, 'translation': [dx, dy],
                            'anchor': [160, 288], 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = {'status': 'CANDIDATE_NOT_APPROVED', 'frame_count': 20,
                'canvas': [320, 320], 'scale': .25, 'anchor': [160, 288],
                'reference': 'img/battle/enemies/goblin/goblin_battle_idle.png',
                'reference_sha256': hashlib.sha256((ROOT / 'img/battle/enemies/goblin/goblin_battle_idle.png').read_bytes()).hexdigest(),
                'sheet_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'frames': entries}
    (DEST / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
