# Morwen skirt — independent art QA + launch audit (Claude, 2026-11-26)

Scope: read-only independent QA. No native write, no dispatch, no merge, no adoption. Self-QA by producers is not counted here.

## 0. Prework receipt
- main `6fa24485b1c1c64430a505303732ac6a11ee69cb`; AGENTS.md blob read at this HEAD (Production-First v6.0 section).
- Owner #427 HEAD `df986c7e0549871940deb26f65f7a54f58658211`; material #540 parent `20c60aa867679b0c5734d2cda24734698f9b0780`.
- Handoff: #427 comment 7174960775 (2026-11-25T21:21Z).
- References re-downloaded: clothed archive 14683737147 ZIP SHA256 `a290131b16f8c61ee32d30125e438782ab59e36ffa2ce9c132685cefa71016bc`; Layer0 archive 14602858760 ZIP SHA256 `d7e006a37dbc739a68d3a409c6ceafd038306d856bb445c8c8c60d4e18c3d29d` (both match recorded values).
- Actual native evidence re-downloaded, digest = local SHA256:
  - A: run 45634559551, artifact 15034545779, `0cbed45868e3e16824c3c3d855070565581f7f6df72f338e89beb63262344e57`
  - B: run 45637701817, artifact 15033184697, `8fa256a51eae314d70cc6ac31ad5ab98e445acaba2c55d0859e718454dd3af1b`
  - Flat control: run 45646771070, artifact 15038608976, `01d44d12d305a430a1e22071c3bbeb09ae71b047f6f8ffda3d62360a1c4d62ae`
  - Latest capture (zoom30/41/46, "298/292px"): run 45666549093, artifact 15048511508, `263206fa773017b8cdb691dffc41fd2981cfebf5850b23cbca1f4d8ad42e6188`
- V3 (`MORWEN_PLAID_PALETTE_V3_20261126.json`, RGBA `cff14a10…`) has no native application → 3D judgement NOT_RUN; only atlas values were compared.
- Comparison image (kept private, not committed, because new VRoid screenshots are not in the approved public set): `MORWEN_SKIRT_QA_CLAUDE_20261126_comparison.png` SHA256 `8b51f0fd9145caabec568a847569770074a043790ecbff5c21dff43dd63551ed`.

## 1. Evidence limitation (important)
The latest ≥292px capture (run 45666549093, `capture-stock-close-41.png`) shows the **stock grey preset plaid skirt**, not A/B/V3. A/B were only captured at low resolution: A zoom12 skirt height ≈ 83 px (y462→545), B front ≈ 63 px. **No ≥292px native capture of any candidate exists.** All A/B measurements below carry ±2–3 px edge uncertainty.

## 2. Measurements (screen pixels, sRGB; illustration vs VRoid render, not physical reflectance)
| Item | Reference | A (actual) | B (actual) | Verdict |
|---|---|---|---|---|
| Plaid width / visible skirt width, front | 0.14 median (p90 0.27), sheet front | ≈0.60 (x358–445 of 330–475 @y500, zoom12) | ≈0.69 (front) | OUTSIDE |
| Plaid horizontal centroid (0=screen-left) | 0.37 (= her right front, above right garter) | 0.49 (centred) | ≈0.50 | OUTSIDE |
| Plaid median RGB / S | 136,65,167 / S .60 (master); sheet S .46 | 139,78,153 / S .51 | 133,77,151 / S .51 | within range (A palette OK) |
| V3 atlas | — | atlas S .457 (more muted than A .503) | — | not preferred: moves away from reference |
| Dark cloth median RGB | 34,22,38 (V≈.15) | 52,37,59 (V≈.23), lilac-grey, almost flat | same | major: too light / too flat |
| Gold rule RGB | 205–227,155–177,119–134 | 205,158,108 | same | PASS-range |
| Paired gold hem rules height above hem (centre front) | ≈5–12 % of visible skirt height | 20–30 % (rules y520/528, hem y545) | similar | OUTSIDE |
| Hem shape | short front, longer/layered sides & back, second dark under-tier visible | symmetric stock hem, single layer | same | FAIL (geometry) |
| Pleats | deep crisp knife pleats with strong light/dark alternation | stock shallow pleats, almost no shade; plaid verticals broken/jagged across pleat islands | same | FAIL |
| Waist / overlap | fitted purple-black vest + gold-trimmed waist yoke over skirt | stock navy school blazer covers upper ~40 % of skirt | same | FAIL (outfit-level, outside skirt module) |

Four-view (A, from `skirt-uv-*`): plaid only in atlas C3–C4 → visible front only; left4 (her right side) shows a sliver, right4 (her left) none. B adds a sliver in right4. Reference wants the plaid on **her right front**, readable from front and from her right side, not from her left/back. Rear: not inferred (occluded by cape in canon).

Game-size readability: at full-body ~300 px height the centred wide panel reads as "a purple plaid skirt"; reference reads as "a dark pleated skirt with a narrow purple accent". This is the most visible G2 error.

## 3. Grey line / lower-centre seam
- Flat control zoom42: centre-front feature at x≈392, y616→696 widens 0→5 px toward the hem. Pixel (392,685) = 141,136,141 next to cloth 51,36,58; backdrop under hem 214,214,214. Per-channel blend fraction = 0.55/0.56/0.53 — consistent with **≈55 % backdrop coverage, i.e. a sub-pixel geometric opening between centre-front pleat edges** (or a neutral untextured inner face). A texture edit cannot fix either. Status HOLD until the discriminating test below.
- Grey dotted chain (RGB≈145,140,145): only seen in Texture Editor captures, where the editor grid/guide toggle is ON (blue icon, top-right). Hypothesis: editor guide overlay. Not yet proven.
- Thin dark-red lines on pleat folds and on the blazer edges in normal preview (zoom41): appear on jacket too → MToon outline, not a skirt seam. Minor.

## 4. Repair instructions (Codex-executable)
Atlas 1024×512, 8 columns × 128 px (C0…C7); front centre = x512; her right = lower x (coarse correspondence, ±32 px).

**Critical**
1. C1 plaid placement: panel x[395,495) (width 100, range 72–138), plaid repeat and paired gold rules as A, A palette (not V3). Targets in front native capture: width fraction 0.20 ± 0.06, centroid 0.37 ± 0.05; left4 (her right) plaid visible, right4 (her left) ≤ 0.03. If off, move panel by measured response (do one 32-px shift trial, measure screen shift, then correct). Do not widen to fix side coverage.
2. Capture A/C1 at ≥292 px skirt height in normal preview (editor closed, cursor outside model), same camera as zoom41, front + left4 + right4 + left8.
3. Centre-front opening test: same pose, two captures with yaw ±10° (or a different backdrop if VRoid allows). If the wedge colour follows the backdrop → geometry gap confirmed → VRoid: try "Skirt (Tighter)" small steps and record wedge width; if not closable → Blender stage (overlap/lining plane, weld). Texture Editor grid toggle OFF vs ON pair to settle the dotted chain.

**Major**
4. Hem rules: move both rules down so lower rule bottom sits 4–8 % of visible skirt height above hem (≈4–7 px at 83 px; ≈15–25 px at 292 px). Measure control response with one shift trial first.
5. Dark cloth: lower base value ~30–35 % toward 34,22,38 (keep scan microdetail, no baked highlight); re-measure V ≤ .18 in matched capture.
6. Pleat read: in VRoid only via Shade Color/texture fold lines aligned to actual pleat edges (no directional highlight in Base Color). Real pleat depth, front-short/back-long hem, second under-tier → **Blender stage** (after VRoid native reaches its limit; per VRoid-first policy).

**Minor**
7. Plaid gold verticals broken across pleat islands: align repeat phase to pleat UV islands after C1 position is fixed.
8. Outline colour to dark violet or thinner width.

Outside skirt module (record only): blazer → canon vest/jacket, stockings + right garter, waist yoke. These dominate overlap and must be scheduled in the wardrobe module.

VRoid-native: 1, 2, 3 (test), 4, 5, 7, 8. Blender later: 6 geometry, gap closure if confirmed. HairHarpy: not applicable to skirt.

Re-verification: same camera/zoom, actual PNG SHA, native pre/post SHA, then save unique native + reopen for G3.

## 5. Launch system audit (`.github/workflows/morwen-request-launch.yml`, blob `2e19ae757f48a4cdc735704f4854a12c5a73f1d2`)
Actual ChatGPT probe: comment 7175012014 → run 45703908180, job `probe` success, log `READ_ONLY_CONNECTOR_RECEIVED 7175012014`; `accept` skipped. Handoff comment 7174960775 → run 45703546750 skipped (correct). Connector receipt PASS; **no production dispatch was attempted.**

| Check | Result |
|---|---|
| Identity (repo id, PR 427 open, sender/user id, OWNER, unedited, attempt 1, ≤10 min, live re-read) | PASS |
| Shell injection (body read from event JSON in node; not interpolated) | PASS |
| Least privilege (top-level `{}`, probe PR read only, accept actions:write) | PASS (actions:write unavoidable) |
| Ambiguous POST (no retry, poll for run by request id, fail closed) | PASS |
| Target guard (expected_main = GITHUB_SHA, request id regex, attempt 1, main-only job) | PASS |
| Native original protection (inputs from immutable artifacts + SHA, ephemeral runner) | PASS; retention risk: required artifact 15003297779 expires 2026-12-02T08:10Z → all modes except hair_candidate fail after that |
| Stage authorization | FAIL: hard-coded historic run ids/blobs; `priorBlob===blob` rejects unchanged workflow; owner HEAD pinned to df986c7e |
| Current launchability | BLOCKED: `runs[0]` must be the prior main run, but latest run is codex-branch 45666549093 → every start is rejected today |
| Durable idempotency | PARTIAL: dedupe only by display title in last 10 runs (backed by 10-min age + attempt 1) |
| CAS / lease / fencing | FAIL: only a snapshot count of active runs; no lease token |
| Manual/other-AI exclusion | FAIL: branch `workflow_dispatch` bypasses launcher; shared concurrency group with pending-replacement can silently cancel an approved queued run |

Fix (reuse, no new engine): replace `eligible()` transitions with a reviewed stage-authorization record on main (stage id, mode, owner HEAD, workflow blob, spec/input/checkpoint SHA, predecessor run+artifact digest, attempt budget, expiry). Acquire `tools/production_qa/shared_asset_lease.py` CAS lease (create-only tag ref, unique object = fencing token) in the launcher **and** as the first step of the target workflow for both launched and manual runs; assert ownership before upload; release on completion. Use `shared_dispatch_reservation.py` for the reservation/receipt. Negative tests required: stale, replay, edited comment, source drift, active manual writer, lost lease, ambiguous POST, expired artifact.

## 6. Gates (this QA)
- G1 canon/provenance: references and artifacts provenance PASS; design conformance of A/B FAIL (plaid placement/width).
- G2 art: **FAIL** (A, B). V3: NOT_RUN (no native application).
- G3 technical/save-reopen: NOT_RUN (volatile, no save); centre-front opening HOLD.
- G4 game: NOT_RUN.
