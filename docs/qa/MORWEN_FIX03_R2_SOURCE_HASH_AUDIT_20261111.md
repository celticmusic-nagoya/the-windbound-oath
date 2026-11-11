# MORWEN FIX-03 R2 — historical-source hash audit

## Scope
Compared the **local** `MORWEN_REAL_CANON_FINAL_ALIGN_01.zip` four-direction PNGs with the local FIX-03 R2 PNG. This is NOT an independent comparison against the current GitHub original binary.

| Item | Historical back final | FIX-03 back R2 |
|---|---:|---:|
| Canvas | 1200x1600 | 1200x1600 |
| Alpha>32 content width | 793px | 703px |
| Alpha=255 pixels | 612,528 | 1,340 |
| Ground row y1540 | occupied | occupied |

Historical back SHA-256: `4c4f10586cf80a38` (prefix only; computed from archive).
GitHub FIX-03 `BASE_BODY_SPEC.json` references a different back source SHA-256: `9aca3a79ad62cb1c37a998a0e48f333988287527ec422fb9d1b29f7fa9459d2a`.

**Result:** Hash mismatch. Historical archive is a provisional visual reference only; not the current canonical source. The R2 candidate remains **NOT_APPROVED**. No new art was generated and no official assets were overwritten.

## Next step
Acquire original PNGs matching the GitHub canonical SHA-256 in the same processing environment, then perform the shoulder/arm/hair and garment comparison. Do not make speculative geometry edits or restart reference-sheet generation.
