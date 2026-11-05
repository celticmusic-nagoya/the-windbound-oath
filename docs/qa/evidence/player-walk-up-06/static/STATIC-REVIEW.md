# PLAYER-WALK-UP-06-QA — independent initial static review

PR153 fixed `c15a715fe450e76820153e71ea7b04e70e258d6d`; read AGENTS and candidate README/tools/qa. No source edits or browser/GitHub operations by reviewer. Runtime harness/final-head review pending.

## Protection / execution

Own all17 available Node files PASS via direct sequential node execution (18th historical up-DEV test is absent from this branch; not fabricated or skipped). All1833 main-baseline PNG blobs unchanged, canonical259 formally adopted SHA match, all17 immutable PR153 files unchanged. Fixed PR changes only candidate material/evidence/scripts, no JS/index/CSS/productionIMG/data change. Clean fixed candidate head. Logs/scripts/JSON are outside repository in independent-review.

## Independent mask/threshold findings

Actual candidate SHA `1bde96684c85739e821e8c7e5e8f07831b8819414569d07d6a3bbb3613e80dfd`,2048x1280RGBA.18549RGBA changes versus official03. Exactly29 changed pixels outside original proposed_mask, matching recorded extension coordinates and bitmap;0 outside mask+extension.248changes versus PR152, inclusive bbox[1055,973,1135,1108]. Claimed local scope is upheld.

Factual reporting caveats must accompany immutable author README rather than editing its history:

- It states original alpha26–67 for the29 extension pixels; independent original03 values actually range26–200 across24 distinct values. No alpha255 fully opaque original pixel is in the extension, but do not call all29 extremely low-alpha26–67.
- Lowest row1227 uses alpha>128. At alpha>200 lowest1225; anynonzero/alpha>24 lowest1229; both original03 and candidate agree at each threshold. This is appearance-bound preservation, not physical foot contact.
- close_speckles_info globally reports20 alpha24 enclosed pixels while qa scopes zero alpha24 holes to inside-mask. Do not conflate scoped zero with whole-image zero without independently measuring.

No source-quality verdict follows solely from these metadata imprecisions.29 recorded edits remain localized and no outside-union or fullyopaque-original escape is established. Detailed mask numbers in mask-independent.json.

## Harness review requirements

A4[03,04,01,06],B5[new,03,04,01,06],Cproduction6 must be explicitly labelled with90world stride and bob settings; use real shared animation/renderer only. Temporary page policy must be installed before cached consumers, or actualdecodedURL assertions must prove bothpreview andfield consume it. Candidate/index changes alone are insufficient. Normal inputs only for straight/diagonal motion, no position/flags/SAVE writes. Preserve strict phase/cadence assertions and raw failed attempts. Native recording and physical Android remain separate. Completed anatomical gait/contact cannot be inferred from pixelbounds or timers.

## QA-only fixture at4e67b63

Accessor is registered by Playwright add_init_script before FieldWalkMotion assignment/consumers, addressing late-descriptor capture risk. Double URL opt-in plus WINDBOUND_DEV at shared-policy assignment; no sourceJS/bank change. Only frozen descriptor/frame URL/order/bob clones are created; actual frameAt/bob/renderers remain shared. New candidate frame copies03 geometry, with no generated pose/independent locomotion clock. D baseline identity, other-direction/Fiona/idle identity and LOADreset verified by own outside-repo VM7case contract. Initial falseDEV reviewer fixture mistakenly assumed gated Aidan source exists; corrected contract expects null source under existing source module gate, without relaxing QA policy conditions. Both logs retained.

Suggested runtime robustness: field OBS should store actualcurrentSrc as well as dataset.src and assert decoded equality, so source-label changes alone cannot pass. Preview CAP already checks currentSrc. No blocking source issue found; final runtime remains pending.

Own actual holes check confirms alpha>24 global20 enclosedpixels but0inside originalmask; alpha>128 and>200 global0. Thus any unconditional wholeimage alpha24 zero claim is inaccurate; scoped QAjson is consistent. Alpha bounds/holes are visual transparency measurements, not contact proofs.

## Reversible mounted-slot fixture atfce7b0e

Existing field renderer mounts a closed registry-key→DOM map, so an invented candidatekey does not actually display merely because shared descriptor changes. Earlier field assertion correctly caught this fixture integration limitation; not a PR153 image defect. QA-only revision aliases new Bpose to existing up02 mounted DOM slot while assigning candidate URL and03geometry in the cloned Bdescriptor. B5 excludes original02, so no duplicate-key collision inside B. A/C/D/LOAD restore original slot02src/data-src; production registry source is untouched. This is permissible ephemeral test setup, not a production integration design. Future adoption must register a distinct new frame key/slot rather than copy this alias technique.

Own connected fakeDOM test:6alternating B→C/A/D switches plus B→LOADreset allPASS; original URL/src/dataset restored, candidate onlyB, original asset JSON and other descriptor identities preserved. Evidence fixture-slot-contract.cjs/log. Actual m66 now checks currentSrc against dataset and decodedimage state, closing initial metadata-only concern. Runtime final verification still pending browser handoff. Border-box native-size fixture correction150px is separate from pose/material behavior.
