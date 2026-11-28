"""Exact-byte, opt-in save observer adapter; does not launch or edit any native model."""
import argparse
import hashlib
import re
from pathlib import Path

OLD = b'''"$gui" click-label "evidence/$close_shot.png" 'Save as new item' 'Close Hairstyle Editor'
sleep 4
capture_state W110-save-return
'''
NEW = b'''"$py" -c 'import hashlib,sys; from pathlib import Path; sys.exit(0 if hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest()=="5cb371826a31ca9ec60c0755a9be7abed5f3e561ac3c5c4b594ca351adcbceb7" else 1)' "$W126_SAVE_OBSERVER"
"$gui" click-label "evidence/$close_shot.png" 'Save as new item' 'Close Hairstyle Editor'
"$py" "$W126_SAVE_OBSERVER" --gui "$gui" --evidence evidence
'''
POST = b'''grep -Fq 'Body' evidence/W110-save-return.txt
grep -Fq 'Outfit' evidence/W110-save-return.txt
if grep -Fq 'Close Hairstyle Editor' evidence/W110-save-return.txt || dialog_visible W110-save-return; then exit 1; fi
'''
OBSERVER_SHA256 = '5cb371826a31ca9ec60c0755a9be7abed5f3e561ac3c5c4b594ca351adcbceb7'

def adapt(raw, expected_sha256, observer):
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256) or hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError('worker identity')
    if hashlib.sha256(observer).hexdigest() != OBSERVER_SHA256:
        raise ValueError('observer identity')
    if raw.count(OLD) != 1 or raw.count(POST) != 1 or raw.count(NEW):
        raise ValueError('unexpected save anchors')
    start = raw.index(OLD)
    if raw[start + len(OLD):start + len(OLD) + len(POST)] != POST:
        raise ValueError('post-save guard changed')
    if any(raw.count(x) != 1 for x in (b'\nnative_save\n', b'\nreopen_copy\n')):
        raise ValueError('native checkpoint/reopen anchor missing or ambiguous')
    if not start < raw.index(b'\nnative_save\n') < raw.index(b'\nreopen_copy\n'):
        raise ValueError('native checkpoint sequence')
    return raw[:start] + NEW + raw[start + len(OLD):]

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('worker', type=Path)
    p.add_argument('expected_sha256')
    p.add_argument('observer', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    data = adapt(a.worker.read_bytes(), a.expected_sha256, a.observer.read_bytes())
    with a.output.open('xb') as f:
        f.write(data)
