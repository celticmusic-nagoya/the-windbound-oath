# DIRECTIVE-21A — Phase4 formal adoption and immutable PNG protection

**APPROVED / 正式採用** (2026-10-30, adopter: user).

Adoption basis: **「ユーザーAndroid実機QA全4項目PASS」** for PR91. The user explicitly adopted the exact bytes actually published and used at PR91 merge, not files chosen from older handoffs. Immutable reference: PR [#91](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/91), merge `bdf6a6dd50a26183daa181342d1fa546f5873418`.

| Character | Expressions including normal | Blink PNGs | Exact runtime version |
|---|---:|---:|---|
| Fiona |8 (normal +7) |8 (normal,L/R,stages1–4) | normal original +provisional-20e |
| Lou |6 (normal +5) |8 (normal,L/R,stages1–4) | normal original +provisional-20e |
| Emma |8 (normal +7) |8 (normal,L/R,stages1–4) | normal original +provisional-20c |
| Total |**22** |**24** |**46 PNGs** |

The3 normal PNGs were already formally adopted under19B; that original adoption evidence/date remains intact. This decision confirms all46 and newly promotes43 files (19expression differences +24blink overlays). Lou smile/relieved are excluded. The old Fiona/Lou20C files, other unapproved branch expressions, whole imagegen donors, reference sheets and masks are not newly adopted.

## Authoritative current record

- [Per-file SHA/source/approval basis and excluded-status snapshot](PHASE4_FORMAL_ADOPTION_21A.json).
- [Canonical46-file SHA lock](PHASE4_ADOPTED_SHA256SUMS), SHA-256 `f6c497673372365f986b0a4456796d8f6abf98521d3299a1a2c992de8dfe9b02`.
- [Central asset registry](../assets/ASSET_REGISTRY.json): exactly46 current records APPROVED, QA/Android PASS; no other material's adoption status changed. Source-path SHA matched directly against the PR91 commit and current files.

The20C/20E JSON documents and earlier QA reports are retained as historical snapshots of the provisional phase. Their then-current provisional fields do not override21A for these46 exact paths. They continue to document unchanged source bytes and generation provenance.19A audit and19B original normal-adoption records are also retained.

## Protection and runtime scope

`tests/moss/m49_phase4_formal_adoption.py` pins the46-file lock digest in code, checks all actual PNG hashes and the live PortraitRegistry path/face set, and checks the formal central ledger and all100 excluded portrait statuses. Regenerating a PNG and updating the JSON alone cannot silently pass this guard. It independently pins the64 Aidan/eventCG files, for110 protected formally adopted PNGs in total.

No PNG, registry/runtime JavaScript, CSS, index, dialogue/story/flags, save data or display logic changes are made by21A. Existing paths named `provisional-*` stay unchanged to preserve the deployed bytes/URLs. The DEV's legacy QA-candidate labels/metadata also remain unchanged under the explicit no-display-logic-change scope; authoritative adoption status is this record and the central registry. Renaming folders or removing UI labels is a separate display change, not required to adopt these bytes.

Never overwrite formally adopted PNGs by rerunning an asset build. A future revision requires a new version path and explicit user adoption. Shape approval, technical QA, Android QA and formal adoption are separate decisions; this is the explicit final adoption decision for these files.
