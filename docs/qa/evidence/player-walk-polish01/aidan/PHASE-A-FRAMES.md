# Phase A — Aidan current-frame audit and candidate acceptance

Read-only audit at e63780543d7ba1719a39a2f68b9924dc6d5b3933. This supplements REVIEW.md under the user's narrowed v2 scope. **No cadence or art adoption is recommended for immediate runtime application.**150 remains an unadopted comparison proposal. Phase A delivers inspection/specification; Phase B creates candidates through Claude's assigned creative role; Phase C integrates only director-approved assets. No new assets or browser tests were produced by this reviewer.

“Image-left/right” below always means the viewer's screen, not anatomical left/right. A forward/backward foot cannot be reliably identified from apparent boot height alone because foreshortening, lifted soles, bent knees and cloak occlusion change the projection. Contact labels are observations or explicitly marked uncertainties, not ground-truth animation metadata.

## Straight vertical production bank

All rows use existing img/field/characters/aidan/aidan_walk_{direction}_{NN}.png,2048x1280,anchor1024/1230,scale.0625, production stride90. Numeric order01→06→01 comes from suffix sorting and uniform distance sampling; no heel-strike labels or phase-duration metadata are stored. Current frontal/back paintings entered the straight banks in b706afcf03325fdfd2d1d1380bcf501b074c903b; prior3/4 art remains separately named dl/ul. Delivered front.png/back.png are existing provenance references, not authorization to repaint or recut.

|frame|visible foot/contact evidence|phase certainty / concern|
|---|---|---|
|down01|Image-right boot extends lower toward viewer; image-left boot sits higher behind.|Contact-like separation; planted vs descending foot unproven.|
|down02|Image-left boot has a broad dark sole toward viewer; image-right is narrower/upright.|Lift/forward-swing-like sole exposure; toe/heel contact cannot be certified.|
|down03|Image-right boot now presents a dark underside/forward toe; opposite leg partly hidden.|Opposite-side exposure directly after02; a distinct neutral pass is not clearly documented.|
|down04|Image-right toe reaches the lower baseline; image-left boot sits higher.|Contact-like pose close in leg emphasis to01.|
|down05|Image-right boot again dominant at bottom; other foot tucked behind.|Another similar-side emphasis; a new left-contact phase is not established.|
|down06|Image-left boot reaches lower; image-right boot raised behind.|Opposite contact-like separation;06→01 side swap deserves animated inspection.|
|up01|Image-left shin/boot hangs to lower baseline; opposite boot is partly cloaked.|Contact-like; heel/sole relation obscured.|
|up02|Image-left broad underside/heel is exposed while image-right boot reaches lower.|One lift and one support-like leg, but anatomical side identity not proven.|
|up03|Image-right boot reaches bottom; image-left leg is bent/hidden.|Contact-like continuation; no explicit pass label.|
|up04|Image-right dark sole faces viewer while other foot is more tucked/raised.|Lift-like opposite exposure; planted-contact assignment uncertain.|
|up05|Image-right boot reaches lower; opposite foot barely visible.|Contact-like emphasis resembles03; cloak hides the distinguishing motion.|
|up06|Image-left shin/boot reaches lower; image-right boot sits above/behind.|Return-side contact-like separation;06→01 may be visually similar.|

These six image files per direction are distinct drawings, **not proof of six biomechanically correct phases or a complete alternating gait**. Static inspection found no obvious missing toe or impossible disconnected leg requiring an immediate patch. Uneven sole exposure, repeated same-side visual emphasis, cloak concealment and body/arm/cape shape changes remain potential sequence/art defects. Timing alone cannot supply a missing passing pose, switch occlusion order, or make anatomical legs remain consistent.

## Side production bank — protect adopted runtime

Left/right remains180 and the existing six slots/paths must stay unchanged in this task's audit/candidate phases. Side source intent is recorded by tools/art/make_art08e_aidan_side6.py:01/04 contact,02/03 first passing pair,05/06 derived second pair. Its own predecessor documentation warns that the03 swinging leg is painted in front when its far-leg role should pass behind: shading does not fix overlap. This is a documented historical limitation, not a newly verified runtime regression.

|direction/frame|installed source / intent|what is actually established|
|---|---|---|
|left01|side6 original01; near leg forward/contact intent|Painted separation; anatomical identification depends on convention.|
|left02|fix01 replacement02; base02 far/rear leg shaded|Complete recovered forward toe; old visible pixels preserved.|
|left03|side6 original03; far swing shaded|Swing/support overlap remains a painting limitation.|
|left04|fix01 replacement04; base04 front region shaded|Complete recovered toe; opposite-contact intent, not measured force/contact.|
|left05|fix01 replacement05; base02 with near/far shading swapped|Same geometry/alpha as02, not a separately drawn opposite-leg pose.|
|left06|side6 original06; base03 with near/far shading swapped|Same geometry/alpha as03; second passing role is inferred through tone.|
|right01|fix01 replacement01; base01 rear region shaded|Complete recovered toe; contact intent.|
|right02|side6 original02; rear leg shaded|First passing/weight shift intent.|
|right03|side6 original03; swing leg shaded|Known foreground-overlap limitation remains.|
|right04|side6 original04; front region shaded|Opposite-contact intent.|
|right05|side6 original05; base02 with near/far roles swapped|Same geometry/alpha as02, not independent opposite-leg articulation.|
|right06|side6 original06; base03 with near/far roles swapped|Same geometry/alpha as03; tone changes establish intended role only.|

PR127 adopted cadence180; it did not turn these shaded derivations into new full-gait geometry. Prior FIX01 repaired four cut toes through registered original-source pixels and retained originals/provisional art status. Preserve its four sparse replacement files and all original-side PNGs. Do not silently replace them during an up/down candidate task.

## Historical gaps and what remains uncertain

`docs/art/redelivery_requests.md` (2026-10-11) explicitly reported that opposite-leg phases could not be distinguished, with step/standing alternation; back walk then had only two alternating poses, and right-side work was still older delivery. This predates current Oct13 straight drawings and later side6, so it cannot alone prove today's exact banks are still two-pose loops. It does establish why counting filenames is insufficient and why candidate delivery must explicitly identify both legs and contacts. Current metadata supplies no adoption record certifying every present image's anatomical leg/contact identity.

## Candidate pose acceptance for Claude/director review

1. Deliver six genuinely articulated phases per requested direction, with explicit intended anatomical left/right support/swing labels: A contact, A loading/opposite toe-off, opposite leg passing, B contact, B loading/opposite toe-off, opposite passing→A. A six-frame sketch may combine loading/pass details, but both alternate contacts and both passes must remain visible. Labels are proposed candidate requirements, not a claim about present images.
2. Show anatomical leg tracking/temporary annotation on QA sheets so the director can follow each same leg through the entire loop. No05=02/06=03 geometry duplicate disguised by shading; far-leg overlap must remain anatomically behind when appropriate.
3. Preserve Aidan identity, face/hair, costume/armor/sword design, scale, common ground/foot anchor and camera angle. Candidate variants must be separate files outside adopted production paths. Real transparent alpha, complete boots/soles, clean edges, no glow fragments or checkerboard paint.
4. Include original candidate PNGs and full loop/boots contact comparisons against current protected art at identical ground/scale. Review01→06 plus06→01; no unexplained leg swaps, contour jumps, body-size jitter, floating support foot, missing toe or clipped blade/cape.
5. Demonstrate fixed-view candidate loops at comparable .4/.5/.6-second cycles (120/150/180 at300world/s) without changing world speed; cadence remains a director decision after anatomy/phase validity passes. Rate changes cannot substitute for missing poses.
6. Gate Phase C on explicit director approval of named candidate files/hashes and selected cadence. Then obtain independent exact-head artifact/product QA appropriate to the approved phase. During Phase A/B preserve production side180, existingup/down90, all original PNGs,259 portraits, SAVE/story/battle/movement and approved asset status.
