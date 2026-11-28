"""Stage only already-public upstream CC0 files; never read TWO scores or recordings."""
import hashlib, json, pathlib, sys
from probe_button_accordion import REV, ROOT, SAMPLES, fetch

META = [('LICENSE.txt', '0e259d42c996742e9e3cba14c677129b2c1b6311'),
        ('README.txt', '2f7b811c0273d47c9a2c7391f7150c2cee02166c'),
        ('PRESET Button Accordion HN tuned.sfz', 'd366eaaee8c1fcde7c61500af2c8d27c3f1a6ddb')]
SHA256 = ('c3a8c7305e61a8aacb310e99cb37c2cb42c89313e05687a833991a560e61180e',
          'd250bec14ee45c881561df7bf243a97487bb7dc0184fc3603075ca0c8b932fd0',
          '0c1acd40d37acaad3e69364173f684e69ac29dfb0d78c2d0cbe16e7303df1919',
          '5bd803db3e141a53b306490692981070681bc47c05db9e95aca411d7a320118e',
          '62ab39cbfd471b97ad0505231f72d9f2ae164eda75ecdb20b9c69efe3592e1c6',
          'a57a68c42ae1bfe59335d79944d35be3a9af0f52123035436f694c6bd08a61bb',
          '5ed816a960b2d9abc9dc6e18ec35105ec725055e882da1b16a1d9dc859a7fbea',
          '20f3c0f9266f0ee7deb7e77f840557c659b7e764b0ca1523b0f0c4a7ecd6dfa7')

def stage(out):
    out.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, blob in META:
        files[name] = fetch(name, blob)
    if b'CC0 1.0 Universal' not in files['LICENSE.txt'] or b'CC0' not in files['README.txt']:
        raise ValueError('license evidence mismatch')
    for (label, key, cents, blob), digest in zip(SAMPLES, SHA256, strict=True):
        name = 'Button Accordion HN ' + label + '.flac'
        data = fetch(name, blob)
        if hashlib.sha256(data).hexdigest() != digest or not data.startswith(b'fLaC'):
            raise ValueError('source mismatch: ' + name)
        files[name] = data
    if len(files) != 11 or sum(map(len, files.values())) > 4_000_000:
        raise ValueError('unexpected payload')
    for name, data in files.items():
        (out / name).write_bytes(data)
    receipt = dict(revision=REV, source=ROOT, license='CC0-1.0', scope='public upstream subset only; no TWO inputs', files={n:dict(sha256=hashlib.sha256(b).hexdigest(),size=len(b)) for n,b in files.items()})
    (out / 'transport.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(receipt))

if __name__ == '__main__':
    stage(pathlib.Path(sys.argv[1]))
