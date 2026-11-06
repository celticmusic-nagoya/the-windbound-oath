# THE WINDBOUND OATH — 4 companions delivery

Review staging only. No runtime integration, deployment, or merge is authorized.

## Storage and adoption

| Character | Original PNG directory | Status from source MANIFEST | Supplied WebP |
| --- | --- | --- | --- |
| Serena | `serena/master/`, `serena/reference/` | Full-body v1 approved; sheets reference | `../../web/companions/serena.webp` |
| Morwen | `morwen/master/`, `morwen/reference/` | Full-body v3.0 approved; sheet approved_reference | `../../web/companions/morwen.webp` |
| Bram | `bram/master/`, `bram/reference/` | Full-body candidate_pending_explicit_approval; sheet reference | Not supplied |
| Liam | `liam/source/` | All supplied_original_unverified; canonical selection pending | Not supplied |

Paths above are relative to this README. WebP paths are review derivatives only.
The directory name `master` does not approve Bram. No Liam file is promoted by delivery.
Do not replace Morwen v3.0 or Serena approved artwork with reference sheets or candidates.
Bram and Liam WebP were absent from the source ZIP; no substitute or derivative was generated.

## Source and verification

Reassembled source ZIP: 94,655,871 bytes; SHA-256
`83a06b81b0bd8199ed062120ce34bc267b2e4ea9b27a6c12741e0ae2efc85bb0`.
`MANIFEST.json` is the exact source manifest, relocated from the archive root.
Its asset paths resolve from the repository root. Its historical staging status is retained.
`SOURCE_ARCHIVE_README.md` is the untouched archive README preserved as source material.
Its instruction to create a NEW branch is superseded by the user's recovery request:
this delivery reuses `feature/four-companions-asset-delivery-20261106`.
The repository root README and all existing tracked files are unchanged.

All 31 manifest records (30 PNGs and one supplied text file) match SHA-256 and byte size.
Both supplied WebPs are byte-identical to the archive and decode successfully.
See `DELIVERY_VERIFICATION.json` for per-file hashes, checks, and pending review.

The source contains two identical-content filename pairs in Liam's bundle:
`liam_action_run.png` / `liam_entry.png`, and
`liam_bow_cutin.png` / `liam_skill_cutin.png`.
Names and original bytes are preserved for manifest fidelity; each pair shares one Git blob.
These names do not establish distinct motions or approved canonical art.
No existing repository PNG/WebP had matching content before this delivery.

## Review usage

Open original PNGs or the two WebPs directly from a checkout for visual review.
Use full-body originals for design inspection; reference sheets remain references.
Do not wire these staging paths into game code or publish them.
From the repository root, verify source records with:

```sh
python - <<'PYVERIFY'
import hashlib, json
from pathlib import Path
m = json.loads(Path('assets/companions/MANIFEST.json').read_text())
for a in m['assets']:
    data = Path(a['path']).read_bytes()
    assert len(data) == a['bytes'], a['path']
    assert hashlib.sha256(data).hexdigest() == a['sha256'], a['path']
print('PASS:', len(m['assets']), 'records')
PYVERIFY
```

Delivery self-check is not independent QA or director approval.
After the Draft PR is created, stop for ChatGPT independent QA and director approval.
