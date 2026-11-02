# Phase 2 furniture — final QA (Claude QA; not Codex independent QA)

Date: 2026-11-02. Branch `feature/phase2-furniture-assets`. No change to main, maps, manifest or adopted assets.

## GitHub Actions
- #4 (6d78a9c) SUCCESS: log shows Pillow 11.3.0 installed, 9 PNGs CHECKED (7 redraws + fireplace body/fire) with size/RGBA/binary alpha/transparent RGB, `PASS: fireplace pixel-exact alpha composite`, 0 errors.
- #3 (b2f3dfe) FAIL: `Pillow missing` — the validator failed closed before checking. Fixed in #4 by the install step.
- This commit extends the validator to all 13 items (+2 fireplace parts) and adds stand-item grounding. A negative test (stool lifted 3 px, barrel RGB residue) fails as expected.

## Item sources
| item | file | source |
|---|---|---|
| fireplace, body, fire | `fireplace/` | Delivery 2 (ChatGPT redraw, split by Claude) |
| bed, bed_small, rug, window, tapestry, spinning wheel | `new_drawings/` | Delivery 2 |
| table, stool, jar, chair | `claude_repair/` | **Claude repair** re-cropped from the Delivery 1 `reference_sheet.png` (`tools/recrop_small.py`). These are NOT the Delivery 3 final files. |
| doormat, barrel | `delivery1/` | Delivery 1 output, unchanged |

Delivery 3 PNGs were never received by Claude (no ZIP in the chat, none on GitHub). `delivery3/` is left empty; the validator prefers `delivery3/` automatically once it exists.

## Results
| check | result |
|---|---|
| Numeric (size per repair_plan, RGBA, binary alpha, transparent RGB 0, grounding, fireplace composite 0 px diff) — `tools/accept_h01.py` and `validate_delivery2.py` | PASS 15/15 |
| 300% visual (`qa/final/small_items_x3_magenta_before_after.png`, `qa/delivery2/delivery2_x3_magenta.png`) | PASS |
| In-game render, rilde_in_house_01 via browser interception (PC / Android landscape / portrait **emulation**) | PASS: 13/13 loaded, 0 page errors |

Repairs: table — white panel between legs removed; stool — seat no longer clipped; jar — white shadow removed (handle holes now transparent); chair — grey line under seat removed.

## Open
- Android real device: 未検証.
- Rug content height 193/240 and spinning wheel 112×112 are proportion-preserving; widen only if the director asks.
- Small items come from a ~60–190 px reference infographic: edges are softer than the Delivery 2 redraws. Replace with Delivery 3 when uploaded.
- Formal adoption, manifest/map wiring and main merge need explicit director approval.
