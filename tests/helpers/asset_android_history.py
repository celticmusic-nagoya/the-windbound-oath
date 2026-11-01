"""Read-only test oracle for the current formal, user-confirmed Android records."""
import hashlib
import json

LEDGERS = ('PHASE4_FORMAL_ADOPTION_21A.json',
           'PHASE4_EXPRESSION_BLINK_FORMAL_22A.json', 'PHASE4_FIONA_22BR4.json')

def android_history_errors(records, root):
    expected, errors = {}, []
    for name in LEDGERS:
        ledger = json.loads((root / 'docs/portraits' / name).read_text())
        basis = ledger.get('adoption_basis', '')
        if ledger['status'] != 'APPROVED' or 'Android' not in basis or not any(s in basis for s in ('PASS', '合格')):
            errors.append('no formal Android evidence: ' + name)
            continue
        manifest = (root / ledger['manifest']).read_bytes()
        locked = {f: h for h, f in (s.split(maxsplit=1) for s in manifest.decode().splitlines())}
        assets = {a['file']: a['sha256'] for a in ledger['assets']}
        if hashlib.sha256(manifest).hexdigest() != ledger['manifest_sha256'] or assets != locked:
            errors.append('formal manifest mismatch: ' + name)
        for file, digest in assets.items():
            if hashlib.sha256((root / file).read_bytes()).hexdigest() != digest:
                errors.append('formal PNG mismatch: ' + file)
            expected[file] = digest
    present = {a['source_path'] for a in records}
    for file in expected.keys() - present:
        errors.append('Android evidence record missing: ' + file)
    for a in records:
        file = a['source_path']
        if file in expected:
            if (a['android_status'], a['qa_status'], a['approval_status'], a['source_sha256']) != ('PASS', 'PASS', 'APPROVED', expected[file]):
                errors.append('Android history mismatch: ' + file)
        elif a['android_status'] != 'UNVERIFIED':
            errors.append('undocumented Android claim: ' + file)
    return errors
