# Lind PLAYER QA main integration

Approved source branch: `work/lind-step9-11-prep`.
Source: `599a4c0fcaebef2e8d5a168803b48b411c2d2249`.
Main before: `51cf09258b36c47ba1b9dc8954f385cbeaf018d9`.
Integration: fast-forward to source commit; no history rewrite or conflicts.

Scope audit found only approved STEP9 villagers, STEP10 Emma, STEP11 birds, navigation/bridge movement improvements, Aidan A1 and DEV PLAYER QA UI plus their QA documentation. Battle modules, CSS and images have no changes. Index changes are field navigation and DEV module inclusion only.

Before push main QA passed at 1280×720, 844×390 and 390×844: Aidan idle 4/4 and walk 16/16, exact source PNG SHA/RGBA/alpha 20/20; NPC placement/interaction/collisions, Emma, bird takeoff/flock/wind stop, Wind Stone three states, water continues with wind OFF, actual click/tap destinations and keyboard/bridge/corner/wall handling. Normal attacks, 一閃, defend, enemy turns, COMMAND, instant kill, KO/Victory race protection passed. Raider HP is 1250 and sprite/HUD geometry is exactly equal to the prior stable baseline.

Pre-publication QA exposed a landscape toolbar wrap that let the wind-stone notice overlap the monument. The DEV display button was shortened (current actor → alternate actor); compact landscape-only toolbar widths/padding now keep the stone unobstructed. Stone re-test passed all three sizes. This does not move any world actor or landmark.

A four-times-CPU-throttled long detour exceeded the test budget once under concurrent browser suites (481.7 ms). Isolated portrait re-test passed (281.4 ms); no movement/planner code was changed for this integration. Desktop/landscape navigation and portrait bridge/click/key tests passed.

All measured local browser runs: image 404 0, JS exceptions 0, console errors 0. Literal image paths and legacy asset references: 0 invalid. Evidence: `qa/lind-main-integration/`.

Public Pages verification follows the main push; no A2/Fiona/Lou/STEP12 work is included.
