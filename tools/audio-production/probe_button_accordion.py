"""Read-only CC0 recording qualification: no publication or game binding."""
import array, hashlib, json, math, pathlib, subprocess, sys, urllib.parse, urllib.request, wave

REV = 'd70d16456fd99305d1c24c612b205ab38846eb0f'
ROOT = 'https://raw.githubusercontent.com/freepats/button-accordion-HN/' + REV + '/'
# Exact upstream Git blob SHA and SFZ keycenter/tune, not guessed pitch names.
SAMPLES = [
    ('D5', 62, -26, 'b192d15d4e4bf8dd8e13915d822db39055e839b9'),
    ('E5', 64, -30, 'a652d2cbf0502527ecd843df0e5c33e2aa85b184'),
    ('F#5', 66, -26, '5ddf0732df2fed83add3f6100157eb87775d0fca'),
    ('G5', 67, -29, '07f97732c2c0dfaf36e823489c842f272b26f4f8'),
    ('A5', 69, -20, 'bf1562eeac2ed8cd80a5b541be00a24ecc380ec6'),
    ('B5', 71, -7, 'dbde5326dbdf646bc32729b1d445159aa97fbb22'),
    ('C6', 72, -26, 'cb312fb40be2d12f3063fba909b76577c70d2518'),
    ('D6', 74, -16, '8432ee64e6c7fcd3a84d862ddadd8ba1aa885d64'),
]
RATE = 48000

def git_hash(data):
    return hashlib.sha1(('blob %d\0' % len(data)).encode() + data).hexdigest()

def fetch(name, expected):
    with urllib.request.urlopen(ROOT + urllib.parse.quote(name), timeout=20) as response:
        data = response.read(2_000_001)
    if not data or len(data) > 2_000_000 or git_hash(data) != expected:
        raise ValueError('upstream bytes mismatch: ' + name)
    return data

def phrase(out):
    out.mkdir(parents=True, exist_ok=False)
    license_bytes = fetch('LICENSE.txt', '0e259d42c996742e9e3cba14c677129b2c1b6311')
    assert b'CC0 1.0 Universal' in license_bytes
    parts = []; receipt = []
    for label, key, cents, expected in SAMPLES:
        data = fetch('Button Accordion HN ' + label + '.flac', expected)
        pcm = subprocess.check_output(['ffmpeg','-v','error','-f','flac','-i','pipe:0','-ac','1','-ar',str(RATE),'-f','f32le','pipe:1'], input=data)
        a = array.array('f'); a.frombytes(pcm)
        if sys.byteorder != 'little': a.byteswap()
        assert len(a) >= RATE and all(math.isfinite(x) for x in a)
        ratio = 2 ** (cents/1200)
        n = int(RATE * .36); b = []
        for i in range(n):
            j = i*ratio; k = int(j); f = j-k
            gain = min(1, i/(RATE*.008), (n-1-i)/(RATE*.035))
            b.append((a[k]*(1-f)+a[k+1]*f)*gain)
        peak = max(map(abs,b)); assert peak > .0001
        parts.extend(b + [0.] * int(RATE*.04))
        receipt.append(dict(label=label,keycenter=key,tune_cents=cents,git_blob_sha=expected,sha256=hashlib.sha256(data).hexdigest(),decoded_frames=len(a),probe_peak=peak))
    peak = max(map(abs,parts)); scale = .5/peak
    pcm = array.array('h',(round(x*scale*32767) for x in parts))
    if sys.byteorder != 'little': pcm.byteswap()
    path = out/'button_probe.wav'
    with wave.open(str(path),'wb') as w:
        w.setparams((1,2,RATE,0,'NONE','not compressed')); w.writeframes(pcm.tobytes())
    with wave.open(str(path),'rb') as w: assert w.getnframes()==len(parts) and w.getframerate()==RATE
    print(json.dumps(dict(candidate='CC0 button accordion technical probe',revision=REV,license='CC0-1.0',sources=receipt,frames=len(parts),seconds=len(parts)/RATE,pcm_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),peak_dbfs=20*math.log10(max(map(abs,parts))*scale),status='PASS',limits='short-note sample decoding only; no release layer, sustain loop, pitch/listening, full B01 or game QA; no audio uploaded')))

if __name__ == '__main__':
    phrase(pathlib.Path(sys.argv[1]))
