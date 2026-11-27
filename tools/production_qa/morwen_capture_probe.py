#!/usr/bin/env python3
"""Read-only macOS capture probe; archive audit works on Linux. No native edits."""
import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
import zipfile
import io
from PIL import Image

SWIFT = r'''
import AppKit
import CoreGraphics
import Foundation
let display = CGMainDisplayID()
guard let mode = CGDisplayCopyDisplayMode(display) else { exit(2) }
let bounds = CGDisplayBounds(display)
let apps = NSRunningApplication.runningApplications(withBundleIdentifier: "net.pixiv.vroid.macosx")
guard apps.count == 1, let app = apps.first else { exit(3) }
let all = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
let windows = all.filter { w in
    guard let pid = w[kCGWindowOwnerPID as String] as? NSNumber,
          pid.int32Value == app.processIdentifier,
          let layer = w[kCGWindowLayer as String] as? NSNumber, layer.intValue == 0,
          let b = w[kCGWindowBounds as String] as? [String: Any],
          let width = b["Width"] as? NSNumber, let height = b["Height"] as? NSNumber else { return false }
    return width.doubleValue >= 200 && height.doubleValue >= 200
}
guard windows.count == 1, let window = windows.first,
      let id = window[kCGWindowNumber as String] as? NSNumber,
      let wb = window[kCGWindowBounds as String] as? [String: Any] else { exit(4) }
let result: [String: Any] = ["logical_mode": [mode.width, mode.height],
 "pixel_mode": [mode.pixelWidth, mode.pixelHeight],
 "display_bounds": [bounds.origin.x, bounds.origin.y, bounds.width, bounds.height],
 "display_pixels": [CGDisplayPixelsWide(display), CGDisplayPixelsHigh(display)],
 "window_id": id, "window_bounds": wb, "pid": app.processIdentifier]
let data = try JSONSerialization.data(withJSONObject: result, options: [.sortedKeys])
print(String(decoding: data, as: UTF8.self))
'''

def sha(data):
    return hashlib.sha256(data).hexdigest()


def image_info(data):
    with Image.open(io.BytesIO(data)) as image:
        if image.format != 'PNG':
            raise ValueError('not PNG')
        image.load()
        return {'size': list(image.size), 'sha256': sha(data)}


def read_json(data):
    return json.loads(data)


def historical(path, expected):
    data = path.read_bytes()
    if sha(data) != expected:
        raise ValueError('archive SHA mismatch')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if z.testzip() is not None or len(set(z.namelist())) != len(z.namelist()):
            raise ValueError('invalid archive')
        receipt = read_json(z.read('module-receipt.json'))
        if not receipt['files']:
            raise ValueError('empty receipt')
        for name, digest in receipt['files'].items():
            if sha(z.read(name)) != digest:
                raise ValueError('receipt mismatch: ' + name)
        names = sorted(n for n in receipt['files'] if n.startswith('skirt-hd-') and n.endswith('.png'))
        if not names:
            raise ValueError('no historical capture evidence')
        return {'scope': 'HISTORICAL_SCREENSHOT_AUDIT', 'archive_sha256': expected,
                'receipt_count': len(receipt['files']), 'mode_log': z.read('skirt-display-modes.txt').decode().strip(),
                'window_log': z.read('skirt-hd-window.txt').decode().strip(),
                'images': {n: image_info(z.read(n)) for n in names}}


def capture(out):
    if sys.platform != 'darwin':
        raise RuntimeError('macOS runtime required; use --archive on other platforms')
    out.mkdir(parents=True, exist_ok=False)
    meta = read_json(subprocess.check_output(['/usr/bin/swift', '-e', SWIFT], timeout=45))
    (out / 'geometry.json').write_text(json.dumps(meta, indent=2) + '\n')
    subprocess.run(['/usr/sbin/screencapture', '-x', str(out / 'display.png')], check=True, timeout=20)
    subprocess.run(['/usr/sbin/screencapture', '-x', '-o', '-l', str(int(meta['window_id'])), str(out / 'window.png')], check=True, timeout=20)
    after = read_json(subprocess.check_output(['/usr/bin/swift', '-e', SWIFT], timeout=45))
    if meta != after:
        raise RuntimeError('display/window geometry changed during capture; preserve evidence, do not compare')
    images = {n: image_info((out/n).read_bytes()) for n in ('display.png', 'window.png')}
    result = {'scope': 'READ_ONLY_MACOS_CAPTURE_NOT_NATIVE_EDIT', 'geometry': meta, 'images': images,
              'display_matches_pixel_mode': images['display.png']['size'] == meta['pixel_mode'],
              'limits': 'No claim of full skirt framing, overlay cause, or model QA. Inspect actual pixels.'}
    (out / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--archive', type=pathlib.Path)
    group.add_argument('--capture', type=pathlib.Path)
    p.add_argument('--sha256')
    a = p.parse_args()
    if a.archive and not a.sha256:
        p.error('--archive requires exact --sha256')
    result = historical(a.archive, a.sha256) if a.archive else capture(a.capture)
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
