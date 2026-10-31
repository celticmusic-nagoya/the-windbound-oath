# DIRECTIVE-24A — production expression assignment QA

Base main2b2daa0c602bc4b8fe86a8b5df08a4469e33df0a. Scope: **PASS**, physical Android **NOT_RUN**. [Full per-page audit and manual reasons](evidence/directive-24a/dialogue-audit.json).

## Audit / implementation

388display-path pages (262FieldTalk,119cinematic,4training,3fieldinspection; sharedescape and legacyhill variants counted separately). 115eligible pages assigned: **102new,8updated,5retained**. Aidan41/Fiona48/Lou10/Emma16 portrait pages. Existing Aidan sunset smile/normal, Fiona bench normal and Emma first normal retained; Lou grief/recruitment8pages corrected from undifferentiatednormal. Manual decisions based on whole scenes, not keyword classification. Approved faces only; no Lou smile/relieved. Closed-eye Fiona/Emma smile/relieved remain static.

25intentional exclusions:22CG-owned pages keep existing exclusion;3mixed pages (forestarrival2speakers, aftermathAidan+narration, forestFiona+rune narration) retain original singlepage/no portrait. Remaining248pages are narration/otherNPCs. Eligible unhandled **0**. Whole-JS scan also found battle banter/logs and EventCG trigger markers: existing battle/CG presentation remains outside ordinary dialogue scope and untouched. Existing DRAFT scenario labels remain unchanged; expression assignment does not formally adopt new lore.

All original words/pages/order/choices/conditions/flags/rewards hash **4d9c203b00d45ac245a369350b8fe910bf4e2a1164e5cb492aa82bf7b1c10114** equals baseline. IndexHTML/controlflow with only explicitly allowed presentation/cache additions removed equals baseline hash **49479618b91079b9fcb423125f9938f1d7a793d17ef62959b125718fb3013bd5**. All259formalPNG/registry/draw/blink timing unchanged, registryaudit0errors. Lore checked against privatev5.0SHA e6f7331b867a7307017c7abb30bae7b6317363a33e5f9d831b80d34f0e51bf49 andaddenda/status; no lore text copied or rewritten.

Only required compatibility additions:3FieldTalklines accept explicit per-page char/face/side for sharedtextarrays (cannot overwrite text/effects); optional saymetadata follows existing talkText/ownership contract; existing cinematic text sinks forward data to existing TalkPortrait scene anchors. No auto-speaker/emotion inference, new renderer, new story, save schema or battle logic.

## Verification

**10unique regression files PASS; Node6/6PASS.** [Collected result/testSHA](evidence/directive-24a/results.json). m53 drives actualregistered NPC/quest/scene entries, realtraininghandlers, windstonehook and cinematicclickers at390×844/844×390, no injectedtalktables. All115page mappings match actualcanvas sourcepixels, correctsides, no sticky portraits on narration/other speakers, same-character switches have no blank hiddenframe; blink/staticfaces and cancel/LOAD/battle/CG cleanup verified. M44/Aidan andm46actualNPC/bench/Raideraftermath retain realflow/naturalblink pixel coverage. M7cliff/M12attack/M6quest/save lifecycle andM49/M51/M52formal protection/DEV/FieldTalk regressions PASS.

Visual inspection: [Emma concern portrait](evidence/directive-24a/24a_emma_worried_390.png), [Lou aftermath grief landscape](evidence/directive-24a/24a_lou_sad_844.png). Screenshots are state-seeded production dialogue, not new art. Other runtime captures retained inQA scratch. Fresh browser contexts isolate orientations from completed-prologue layers/toasts.

InitialQA found a real legacySay integration issue: plainmsg text lacked talkText required by existing ownership validity. Fixed only annotated saymarkup, unchangedwords, no lifecycle-rule weakening. Other retired test failures were existingmixed-page newline rendering, Liamstate carried acrossfixtures and the original650ms aftermath handoff racing the nextfixture; correctedverification/stateisolation/wait, no gameplaytimingchange. All retired FAIL results retained inraw scratch and excluded from PASS counts.

Passing evidence spans f8c1219 unchangedFieldTalk/renderer/portraits,50efeba finalruntime and7010bb5 finalm53; latercommits tests/docs only. Independent exact-head review must confirm code-path identity before merge. FinalPRrecords rollback, latestmain/head/conflict/checks andPagespublic/main equality.

## Android confirmation routes

- Fiona: training conversation and post-training light question → summitbench → sunset/stars/windstops (normal/smile/worried).
- Emma: village NPC, then repeat/questoffer/charmreport (normal/worried/surprised/relieved/smile); previousquest conditions preserved.
- Lou: actualRaider victory → aftermath conversation (sad/worried/determined/surprised/normal), thenfort (worried).
- Aidan: sunset smile/normal maintained; villageescape/forest/capitalgate introduce concern/surprise/grief according to originalcontext.

Physical Android final QA remains user action; no physical-device PASS claimed.
