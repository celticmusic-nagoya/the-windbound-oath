# Aidan Battle Idle Animation Prototype — PLAYER QA

FINAL RESULT: **PASS WITH WARNINGS** (prototype visual approval / physical mobile pending).

- START commit: `92e77b94aee6277df7b045a7edf97e543fc345ec` (latest main inspected).
- SOURCE BRANCH: `work/battle-aidan-idle-prototype`.
- Implementation commit: `d4580786e54505c5217c18ceea45bbeda527e6db`.
- QA / FINAL commit: the commit containing this report.
- Main is not merged or deployed. Lind Village STEP B remains on its separate source branch.

## Actual assets inspected

All four actual files are **1536×1024 PNG / RGBA**, alpha range **0–254**. Files and source pixels are unchanged. [Full audit + SHA-256](assets.json), [source contact](source-contact.jpg), [white-background composite](source-on-white.jpg).

| File in `img/battle/characters/aidan/idle/` | Fully transparent pixels | Transparent % | Strong-content margins L/T/R/B (alpha≥64) | Draw offset X/Y (source px) |
|---|---:|---:|---|---|
| aidan_idle_00.png | 716,534 | 45.56% | 10 / 11 / 8 / 10 | -1.25 / 0 |
| aidan_idle_01.png | 710,182 | 45.15% | 9 / 7 / 7 / 9 | -3 / -1 |
| aidan_idle_02.png | 676,053 | 42.98% | 11 / 8 / 5 / 9 | -5 / -1 |
| aidan_idle_03.png | 670,581 | 42.63% | 11 / 7 / 8 / 13 | -3.25 / +3 |

These margins describe the substantial visible outline, **not wholly transparent strips**. At alpha>0, faint edge/glow pixels reach all canvas edges in 00–02; 03 has nine fully transparent bottom rows. Low-alpha components were retained. Visual inspection on dark green and white found no baked checkerboard, white/black rectangular background, major character loss or sword loss. Each pose has one sword. No PNG cropping, rewriting, renaming or generation was performed.

The source poses are closely related: modest chest/cloth/stance changes in 01/02 and a stronger cloth/gaze adjustment in 03. They suit a slow breathing cycle, rather than a rapid four-frame loop.

## Implementation

`BattleIdleMotion` provides shared profile registration (`defineType`) and actor/context registration (`register`). Only Aidan is registered, for normal and Raider battles. Future hover/flap/squish/sway/etc profiles can supply their own frame/hold sequences; none were added or applied to other actors.

- One reusable, small DPR-capped canvas per actor/context, drawn inside the existing image host. Motion roots, layout and HUDs are untouched.
- Four decoded images are cached **once per page**, shared by normal and Raider contexts; no per-frame loads. `ready(selector)` exposes the preload completion boundary.
- One shared RAF while idle is animating. Static holds reuse the last canvas drawing; redraw occurs on transitions/resize. No added interval/timeout per actor.
- `BattleActorState` adds only optional begin/paint/end notifications. Existing sequence IDs, timer cancellation, guard and KO/Victory logic remain identical.
- Canvas appears only in `idle`. ATTACK / SKILL / WIND / DAMAGE / GUARD / LOW_HP / KO / VICTORY use the original engine-owned image. State change hides the idle canvas synchronously; return to idle starts at **00** with a fresh hold.
- Dialogue/cut-in/cinematic ownership pauses the idle clock. Field exit and KO/Victory stop its RAF. Async preload completion checks current eligibility, so it cannot resurrect a terminal pose.
- Reduced motion shows static 00 with no idle RAF. Visibility changes and resize are handled.
- Cosmetic pause variation uses a private PRNG seeded with Web Crypto, **not the battle's Math.random**.
- Existing `BattleFacing` controls both the base image and canvas; BACK ATTACK reflection was verified.

## Adopted sequence / timing

Normal cycle: **00 → 01 → 00 → 02 → 00**.

| Frame | Hold |
|---|---|
| 00 | 1.3–1.9 s |
| 01 | 0.85–1.15 s |
| 00 | 1.1–1.6 s |
| 02 | 0.85–1.15 s |
| 00 | 1.3–2.1 s |

A breathing cycle is 5.4–7.9 seconds; different holds prevent a fixed metronomic rhythm. Frame changes crossfade for **220 ms**, with no new whole-body translate/scale/bob animation.

After **3–5 breathing cycles**, add a 00 pause **2–4 s**, special **03 for 1.2–1.9 s**, then **00 for 1.8–2.4 s** before normal breathing resumes. Actions reset the cycle and return to 00.

## Anchor correction

Inspected both boot soles, ground contact, foot midpoint and sword position. The reference `(888.5,1014)` is the **existing static battle idle's** boot midpoint / main-foot ground line, not an invented center of the PNG. New frame anchors are `(889.75,1014)`, `(891.5,1015)`, `(893.5,1015)`, `(891.75,1011)`.

The table's source-pixel offsets are applied only in canvas drawing; original root transforms, scale, lunge distance, duration/easing and HUD position are unchanged. The visible sword/body stay inside the drawing area. Independent rendered-canvas alpha measurements at PC 1920×1080 show the main sole at **193.596 CSS px in all four frames** and the other sole at **188.606–189.604 CSS px** (under 1px variation). [Actual pixel measurements](anchor-qa.json).

## QA evidence

| Test | Result |
|---|---|
| 120s idle per normal/Raider context, all four requested viewports | PASS — [idle-qa.json](idle-qa.json) |
| All four frames; 03 low-frequency; no per-frame DOM growth; four shared image requests | PASS |
| ATTACK / SKILL / WIND / DAMAGE → idle00; guard; pause and reduced motion | PASS |
| Old attack/damage timer followed by HP0: KO fixed | PASS |
| DEV kill during attack: Victory fixed, canvas stopped | PASS |
| Actual COMMAND attack, forced Critical, 820ms lunge + 100ms hit-stop | PASS — [actions-qa.json](actions-qa.json) |
| Actual 一閃/Cut-in → idle; TP30 consumption; actual enemy damage → idle | PASS |
| COMMAND open/close, DEV kill, normal/Raider KO/Victory, independent Boss HUD | PASS — [battle-regression.json](battle-regression.json) |
| Original doors, attacks, skill, Fiona guard | PASS — [live-input-qa.json](live-input-qa.json) |
| Baseline actor/enemy sizes, root transforms, HUDs, HP/MP/TP/RUNE, facing | Exact match — [baseline-comparison.json](baseline-comparison.json) |
| Final private-PRNG 60s native RAF sequence; battle Math.random calls | PASS / **0** — [final-sequence.json](final-sequence.json) |
| Original image bytes, engine logic, motion/cut-in/critical/CSS sources | Protected — [protection.json](protection.json) |

PC **1280×720 / 1920×1080**, mobile emulation **844×390 / 390×844**: PASS. Two permanent Aidan canvases maximum after visiting both contexts; one decoded four-image cache. No idle load outside battle, no idle RAF after battle exit or terminal state. Rare idle frame appears only through the real clock; tests do not force frame changes.

**Raider HP 1250**, giant scale and Boss HUD: preserved. Fiona, Lou, Goblin, Tainted Goblin and Raider artwork/state/motion: unchanged. Skill/Critical/Battle Dialogue modules and existing resources/turn/balance logic: unchanged.

**Image 404 = 0 · JS exceptions = 0 · Console errors = 0 · Legacy asset references = 0** in final functional tests. Source PNGs are unchanged. Syntax and git diff checks passed.

The long viewport suite began before the cosmetic RNG was separated; its action/lifecycle/anchor code did not change. Both mobile pages ran with the private PRNG, and the final implementation commit additionally passed a native 60s PC trace and verified zero gameplay RNG consumption. The actual critical/cut-in and baseline layout suites are separate evidence for their respective checks.

## Modified / added files

- `index.html`: two external include lines only; inline engine code unchanged.
- `js/assets.js`: verified idle frame registry appended; existing asset maps unchanged.
- `js/battle-actor-state.js`: three optional visual lifecycle notifications only.
- New `js/battle-idle-motion.js`, `css/battle-idle-motion.css`.
- This QA directory. JPEGs are review screenshots/composites, not production assets.

## Warnings / PLAYER QA

1. This is an **Aidan-only prototype**, requiring visual approval of the breathing pace, special pose frequency and 220ms crossfade. A crossfade blends existing illustrations; it does not synthesize intermediate limb/sword poses. Please review temporary outline overlap and feel.
2. The other sole retains approximately 1px of source-pose variation. Main ground contact is fixed; no destructive PNG normalization was used.
3. Physical mobile / low-end-device performance remains PLAYER QA; completed mobile tests are Chromium touch emulation.
4. Main/Pages publication is unchanged. Run this source branch, use existing DEV Event Jump to a normal battle (Moss encounter) and Raider, and wait roughly 20–45 seconds for a special idle. Execute attack/一閃/guard/DEV kill to review state boundaries. Reduced-motion preference shows 00 only.

[Aidan normal](idle-normal-1280.jpg) · [Raider scale](idle-raider-1280.jpg) · [PC 1920](idle-normal-1920.jpg) · [Mobile landscape](idle-normal-844.jpg) · [Mobile portrait](idle-normal-390.jpg) · [Critical](critical-raider-1280.jpg) · [Cut-in](cutin-normal-1280.jpg).

Gate scripts are retained here. Start the existing static application server on port 8015; use the installed Playwright/Chromium and `NODE_PATH=/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules`. Set `AIDAN_IDLE_QA_OUT` to write rerun output outside the repository. Baseline comparison expects a separate read-only baseline server on 8016; its data identifies the exact start commit.

**AIDAN IDLE ANIMATION — PLAYER QA READY**
