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

Delivery 3 received 2026-11-02 21:29 and registered byte-identical in `delivery3/` (commit 1384410).

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

## Cleanup (AGENTS.md §21 lifecycle)
Removed as superseded: `qa/delivery2/render_delivery2_{pc,land,port,pc_zoom2x}.png` (showed Delivery 1 small items, replaced by `qa/final/`), `qa/delivery2/accept.json` (covered by `qa/final/accept.json`), `qa/final/render_phase2final_pc.png` (duplicate of `_pc_zoom2x`). Added `source/ref_sheet_delivery1.png` so `claude_repair/` is reproducible. No candidate PNG changed; QA unaffected.

## Delivery 3 QA (2026-11-02)
Numeric: all 4 PASS (size, RGBA, binary alpha, transparent RGB 0, grounding). Visual 300% (`qa/final/delivery3_x3_magenta_delivered_vs_selected.png`, top = delivered, bottom = selected):
| item | result |
|---|---|
| table_small | PASS — gap between legs clean |
| chair_back | PASS — grey line removed |
| jar | FAIL (minor) — white background inside both handle holes (107 px cleared). Fixed copy: `delivery3_fix/furn_h01_jar.png` (holes made transparent, nothing else changed). Fixed copy PASS |
| stool | FAIL — new seat is flat drawn ellipses with a green cushion layered over the old clipped seat (double seat, style mismatch). Use `claude_repair/furn_h01_stool.png` (PASS) or request a redraw |

Final selection: `selection.json`. In-game render with the selection (`qa/final/render_d3select_*`, PC / Android landscape / portrait emulation): 13/13 loaded, 0 page errors, grounding and scale OK.
Cleanup: `qa/final/render_phase2final_*` replaced by `render_d3select_*`. `claude_repair/` table/jar/chair kept as provenance (superseded, listed in selection.json `rejected`); remove on director confirmation.
