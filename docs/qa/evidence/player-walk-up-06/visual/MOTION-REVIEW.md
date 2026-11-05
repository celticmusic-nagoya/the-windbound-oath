# Independent actual-motion review — PR153

**Visual quality verdict: PASS. Formal-adoption recommendation: YES for the inspected five-pose bank NEW→03→04→01→06, cycle90, bob25%, with the minor residuals disclosed below. No material image/continuity defect requiring another art revision was identified. This is a recommendation, not adoption or main-merge authorization; director/Android final decision remains pending.**

Evidence: parent actual native1280×720 browser recording `../preliminary-pc1280.webm`; raw telemetry `../screens3/up-runs.json.gz`. I independently decoded chronological moving-field frames for4/5 poses and UL/UR, inspected native source edges and black/white plates, and generated matched temporal1× excerpts. This is independent visual analysis of root capture, not a separate browser session or physical Android run.

| Criterion | Result |
|---|---|
| Planted left boot contour | PASS. Existing notch visibly reduced; no detached plate/ankle or whole-foot size change evident. Actual measured residual1nativepx remains and is not a field-size blocker. |
| Right knee/cuff/sole | PASS with minor style residual. New rear sole is connected to the plated shin; no clear horizontal knee severing or stray frill fragment. Sole is smoother/more uniform than original armor and faint tread bands remain, subtle at field size. |
| NEW→03 | PASS at inspected field size. Raised right sole becomes the small forward/passing right boot while left remains stance-like. The right silhouette changes briskly; no severe discontinuity or vanished boot demonstrated in sampled moving frames. This is not proof of biomechanically exact support. |
| 06→NEW wrap | PASS with retained source-body motion. Small left passing boot becomes planted-left, and right stance-like boot becomes rear sole. Unlike4frame06→03, this adds a right rearward phase. It is a pose swap, not a generated in-between; source cape/root changes still exist, but no conspicuous new field-size foot teleport is demonstrated. |
| Alternation / 4 versus5 | Prefer5: both left and right rear soles are now represented. Four-pose sequence privileges repeated left toe-off exposures. The fifth pose addresses the previously identified missing right phase; it does not by itself guarantee equal anatomical stance durations. |
| Speed / bob | Keep90/.25 for comparison. Both loops remain90world/300world-per-second=0.300s. Four holds75ms; **five holds60ms**. More silhouette updates may appear busier, but cycle/travel speed is not increased. Bob25 avoids exaggerated vertical bounce. Zero foot sliding is not inferred from unchanged scalar speed. |
| Straight / UL / UR | Actual chronological route samples show normal directional travel and no obvious new clipping. UL/UR use the same unmirrored up bank; not independent diagonal-specific drawings. Tiny-foot details in reduced overview rely on native straight/source evidence as well. |

## Art-scope and disclosed corrections

See `STATIC-REVIEW.md`/`metrics.json`: SHA exact,18,549vsformal03,248vsPR152,0difference outside originalmask+29px extension. Extension formalalpha range26–200, not26–67; global20alpha24 enclosed pixels persist outside legs exactly as formal. No new leg holes at24/128/200. These are documentation/measurement corrections rather than a reason to fabricate an art defect.

## Deliverables / reproduction

- `own-edge-06-NEW.png`, `own-edge-NEW-03.png`: independently generated native leg boundary crops plus DPR2.625 fullcanvas views. No alignment/warp.
- `own-actual-4vs5-chronology.png`: same fixed native crop,40ms chronological samples across >one cycle. No body recentering.
- `own-diagonal-chronology.png`: actual UL/UR at+.25/+.75s, reduced overview only.
- `own-actual-4vs5-temporal1x.mp4`: A/B side-by-side at unchanged temporal rate. `...spatial3x.mp4` enlarges only spatially, not temporally.
- `motion-seeks.json` documents exact starts/crop/duration. `motion_review.py --repo ... --video ... --telemetry ... --out ...` reproduces straight clips/plates/edges with Pillow/ffmpeg; outputs only to supplied directory. Archive source video and telemetry.

Native video25fps cannot show every browser RAF; chronological sampling can miss an intermediate60ms pose. It is evidence for observed appearance, not a zero-frame-drop certificate. The original production-six/bob100 capture failed a100msRAF gap in the same preliminary run and must remain FAIL, even though A/B/C routes passed before it. This visual PASS does not erase that capture-performance issue. Full protection/SAVE/other-character tests belong to runtime QA owner. Android device visual adoption is NOT_RUN here.
