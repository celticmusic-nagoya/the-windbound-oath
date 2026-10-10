# Field life / movement audit

Actual main code, unchanged. The accelerated stress run calls actual NPC/animal
update functions at 0.1s steps for 3600s, wind ON and OFF in separate isolated
browser contexts. It is not a claim of a physical device running for an hour.
Browser clock and live-input suites independently exercise RAF/input/cleanup.

## Emma CURRENT

EMMA kind, speed1.2 world px/s, goals origin+(4,-2) and origin, rests24/36s.
Mount phase adds20.4s: initial44.4s rest; first movement44.5s. Arrival tolerance
0.5px makes measured max radius4.08px, not the theoretical4.472px goal distance.
A later one-way leg is about3.6px/3s. One idle image only: no walk pose exists.
`workTime=1.4` is assigned on arrival but WORK is only allowed for WORKER kind;
Emma never displays WORK. This is an implementation limitation, not a timer hang.

|Duration|WAIT/IDLE|MOVE/WALK|WORK|Move episodes|Mean distance/episode|Max distance|
|---|---|---|---|---|---|---|
|10分|91.43%|8.57%|0%|17|3.628px|4.080px|
|30分|90.98%|9.02%|0%|54|3.609px|4.080px|
|60分|90.99%|9.01%|0%|108|3.604px|4.080px|

30min total194.88px travel,54 episodes;60min389.28px,108 episodes. Identical
first-move/route behavior with Wind OFF and normal DEV focus proximity. At camera
1/1.5/1.8/2.1 the maximum displacement is4.08/6.12/7.34/8.57 screen px. In broad
PC views this is easily missed. She cannot move if the player's feet are placed
within the32px exclusion range: intentionally waits and retries after3s blocked
plus5s rest, with no force displacement. Direct blocking fixture remains still;
normal focus placement is outside the exclusion range and has0 blocked samples.
Interaction pauses for2s; this is short compared with the routine waits. No
camera-visibility freeze branch exists in this routine.

## PLAYER QA options only — NOT IMPLEMENTED

All distances are world px and require future swept-collision/anchor QA. WORK
below means a proposed gentle inspection/sewing pause; current source has none.
No final frequency decision or new images are made in this audit.

|Profile|Initial wait|Rest per stop|Speed|One-way distance|Move duration|Work pause|
|---|---|---|---|---|---|---|
|CURRENT|44.4s|24/36s|1.2|~3.6px actual|~3s|0s visible|
|OPTION A: slightly active|16–24s|18–26s|1.2|6–8px|5–6.7s|2s|
|OPTION B: readable village life|10–16s|12–20s|1.4|10–14px|7.1–10s|3–5s|
|OPTION C: active|8–12s|8–14s|1.6|16–20px|10–12.5s|4–6s|

## Coordinated 30/60min stress

13 NPCs retained; no invalid/NaN/out-of-map positions or newly penetrated static
solids. Every moving villager/child/Emma has travel, every livestock species
stays inside its configured pen, no persistent child overlap. DOM797→797,
NPC13→13. Farmer has3686px travel in60min, caretaker2151px, both ordinary workers
and children continue with Wind OFF. Children are still a single-pose visual
limitation. They yield to the player; input suite checks destination retention
and resumption around pig/children/villagers/multiple dynamic obstacles.

Fisherman:30min11catches,WAIT88.83%;60min26catches,WAIT88.00%. Formal sequence
FISH_IDLE→WAIT→BITE→REEL→CATCH→INSPECT→RESET→FISH_IDLE remains, with unsuccessful
waits going through ROD_ADJUST.18% eligible bites and minimum60s cooldown unchanged.
No new fishing mechanic or loot.

Timer leak claims are bounded: these long simulations do not advance every
browser timer for an hour. Separate repeated-scene and idle-clock suites measure
pending timers/RAF/DOM; no increasing counts were observed. This does not replace
long real-device soak profiling.

## Input / collision / camera QA

camera-qa.json:4views×4representative scales, each10pointer bridge roundtrips
and10keyboard roundtrips (160each). Real mouse/touch/keys,22.5 keyboard increment,
5pointer step, wall slide/corner assist/blocked destination/actor retry maintained.
All17 camera choices separately measured. Initial1.00 remains intentional WARNING;
no default was selected on the user's behalf. Player collider22×10 unchanged.

Aidan A1:actual four idle directions/16walk frames, last-facing idle, click/tap/
keyboard, stable44world-px body and foot anchor. Review exit protects story/save.
Wind Stone NORMAL/GLOW/OFF and river continue independently. Bird QA uses actual
approach→TAKEOFF→WAITING, overhead flock and wind OFF60s no spawn, water running,
wind ON resume and reduced motion. No environmental source changes.

Building front QA evidence is collected separately. Ground-contact metadata,
facade depths and front props are used, never whole-image bounding boxes.

Final durable building run:4viewports, all14buildings at1.00, representative5
(shop/house02/barn/pigsty/training shed) at1.50/1.80/2.10:116cases total. Each
checks4manual ground contacts,20keyboard approaches, front stops,3pointer door
approaches, blocked props, behind-corner navigation, depth/overlay alignment,
state/save restore and error listeners. No penetrations. Broad original runner
also completed both PC viewports at all4scales, but was interrupted before its
final combined JSON; it is not used as the durable complete-run claim.
