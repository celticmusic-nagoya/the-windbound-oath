# DIRECTIVE-19A material-adoption audit

Result: **BLOCKED — no verified formally adopted asset set for any of the three characters.**
This branch adds only the audit, not portraits, registration, gameplay or asset-status changes. No PR/main merge or Pages deployment for 19A.

Main baseline: `96edfb15a6466b0c2a54780253d43d0edff202b7` (PR #88 / existing DEV portrait lab).

## Available files and missing authorization

| Character | Normal | Expressions | Resolution | Formal adoption | Main registry | Conversation blink |
|---|---|---|---|---|---|---|
| Fiona | present | 8 total | 1024×1536 RGBA | UNKNOWN | absent | none found |
| Lou | present | 8 total | 1312×1199 RGBA | UNKNOWN | absent | none found |
| Emma | present | 8 total | 1024×1536 RGBA | UNKNOWN | absent | none found |

Each set has `normal / smile / angry / sad / surprised / worried / determined / relieved`.
Normal PNGs match the old source-master SHA declarations. Fiona and Emma alpha maximum is254; no transparency finishing was performed. Lou angry/sad/surprised/worried/determined carry explicit old visual-review concerns. Emma7 composites have source-copy/softness/face-line caveats. Clean technical compositing and previous registration do not establish user adoption.

## Evidence establishing the blocker

- [Main asset inventory](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/96edfb15a6466b0c2a54780253d43d0edff202b7/docs/ASSET_INVENTORY.md): old Fiona/Lou/Emma portraits are migration sources, including unadopted expressions; Phase4 requires per-expression adoption.
- [PR75](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/75): explicitly excludes Fiona/Lou/Emma images/registration until per-expression adoption.
- [Main generated registry](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/96edfb15a6466b0c2a54780253d43d0edff202b7/docs/assets/ASSET_REGISTRY.json): every inspected old-branch portrait record has approval_status UNKNOWN, qa_status CONDITIONAL. This audit does not overwrite those labels.
- [Issue16](https://github.com/celticmusic-nagoya/the-windbound-oath/issues/16): source/visual QA is CONDITIONAL and explicitly not formal adoption.
- [Issue19](https://github.com/celticmusic-nagoya/the-windbound-oath/issues/19): Emma normal/expressions QA does not grant formal adoption; originals unavailable/source-copy notes persist.
- [Fiona/Lou source doc](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/5d915ed9097a8d584d93ee28ee98b27fb62060cd/docs/portraits/FIONA_LOU_PORTRAITS.md).
- [Emma source doc](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/docs/portraits/EMMA.md).
- [Handoff Phase1 inventory](https://github.com/celticmusic-nagoya/the-windbound-oath-handoff/blob/64d95aa4c286e5024ca78b5b6be5b4bd284e6201/reports/TALK-PORTRAIT-BLINK-20261027/phase1/PHASE1_REPORT.md): explicitly lists adoption UNKNOWN for all3. Fiona battle-idle-v3 uses a different image and its approval does not cover conversation portraits/patches.
- Inspected handoff main0922430 and asset-title-emma-sword report32045c6: no newer adoption grant. Independent material review agrees: no adoptable set established.

## Exact inventory for review

No image was copied into production or modified. Source links are immutable; [JSON](PHASE4_ADOPTION_AUDIT.json) also records dimensions, alpha ranges, SHA256 and absent registration/blink state.

| Character / face | SHA256 | Source PNG |
|---|---|---|
| fiona / angry | `78f0e51745d60d645f4f4d62cc63310a8f954144871a4fe6050d67abeaec17d1` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_angry.png) |
| fiona / determined | `0f34319d42c6419147f6a0844021720a1e834c664a32fae76d59a7750608e6de` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_determined.png) |
| fiona / normal | `89efd67352ac7f03882242d2363a2a2c8762bc0489e447a7d6089745a227094a` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_normal.png) |
| fiona / relieved | `f4878f7823363a0d84ed2e6d5f8c17d78566425e5d1ada7fc94c7ffc94721cfc` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_relieved.png) |
| fiona / sad | `51d40c8b09439147965db114d5424b73bfdad5c9485a2486af75e632db0f4d92` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_sad.png) |
| fiona / smile | `7bf027597b7e2bc3f8d1e6fd9473e7a2e76dade3e32809fce5db876746823e95` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_smile.png) |
| fiona / surprised | `2702e0d406ed534ee613d75694bf7280d381024dd4d5faddc7f8709535aa0bd7` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_surprised.png) |
| fiona / worried | `b25d4aeffcb3f56df60070f599101b6b07e8186a77b59d75629cdb91f0b4f6fd` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/fiona/fiona_worried.png) |
| lou / angry | `d98d46e53a13473c8c7ee235076faa8a9e8be32e9ab626cbdabedf31e295a36d` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_angry.png) |
| lou / determined | `dc37f3c0a60dafcbdfee24fde1f45e873f2e04366b770bdd19ad75061905e226` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_determined.png) |
| lou / normal | `c2cc6d70614b18c685ef773e27bf4f50a7ed2947cb6e6b9367a5ba9e32e59e8f` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_normal.png) |
| lou / relieved | `acb2f46ec63379ff8c504ef65031cb64a356236f0a8e389d9da9278723ca78d4` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_relieved.png) |
| lou / sad | `824cb37beb9a0cce7f428b55313e381f4bcb97b1c00eac1428e9d60b66bd502a` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_sad.png) |
| lou / smile | `02099feb2c22fb6401d394a14e20be19d3fffe06d8d0e8a5a2a518d9d777a057` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_smile.png) |
| lou / surprised | `8f799e0f75f51e4e679ff401c9726c699afc09fecff95e5bf7443eb9ca184180` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_surprised.png) |
| lou / worried | `cb855929cd9c282d720316c0fa0057ef9c65dd0f0f80cf7fa02a32949001b846` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/2020e558447f05791fb0c514d8e3b58c991302c5/img/portraits/lou/lou_worried.png) |
| emma / angry | `2e72dd367673f5f7aa2e1776ef83bbff29b7b5b4e0fb65310b11a196b05aea33` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_angry.png) |
| emma / determined | `a0ca27839e56e74919029e65b98e65ded91f3c2881e42950857ac0c6059029fa` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_determined.png) |
| emma / normal | `f4dfd09d08e3bd333743f677afbe84e4e1771b295863e92a96a3b4c0904114b2` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_normal.png) |
| emma / relieved | `98cfd49e45864c73176c510c778771a7035be77ab9119e021246f544b3f42bb9` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_relieved.png) |
| emma / sad | `77c68198ae1eb76e2e19dfcfa7d51957726d300e91521be6c0c1a67cf52c8855` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_sad.png) |
| emma / smile | `e062d287e841ec86bce2310720cb63373a6eef9a51dda14e32f201887c4c183a` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_smile.png) |
| emma / surprised | `33207bf43223a8f5a28ace1bb22d3a638f8df2fd4d8a18a8e98a8264e407f2d0` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_surprised.png) |
| emma / worried | `d7a1de8fa59b2e4d288ae082c333de752bd34d295d60e87d746b95783564ae6a` | [PNG](https://github.com/celticmusic-nagoya/the-windbound-oath/blob/f4456a824adaa9add17204a8cd90385530f23619/img/portraits/emma/emma_worried.png) |

## Next actionable work

No new image production is yet required for a **static portrait** pilot: the existing files first need explicit adoption by character/face or an immutable adoption record. If only normal is adopted, register normal only and leave all other expressions unavailable. All3 can initially use still portraits; Emma is explicitly allowed to remain still.

Conversation-specific blink overlays are absent for all3. Do not reuse Fiona battle-idle-v3 patches: the source image is different. If blinking is later requested, produce and adopt four stages per left/right eye for each adopted open-eye expression (8 overlay PNG per such expression), matching the exact approved portrait coordinates. Lou smile/relieved and Emma smile/relieved are already closed-eye expressions and do not need blinking. Do not fabricate the total before the adopted expression set is fixed.

New gameplay/browser tests: **NOT_RUN**; no approved character was connected, so this report does not claim the requested registration/DEV/story QA PASS. Static integrity inventory:24PNG decode/hash checks completed. Existing Aidan54PNG, CG10, title, save and story code remain unchanged; main and Pages stay at the baseline.
