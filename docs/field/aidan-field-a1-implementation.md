# Aidan A1 DEV integration checkpoint

Asset checkpoint: `0f148389e9c0a8e5733da6a9811e9473403c0788`.
Only peaceful Lind DEV art review uses the new sprite. Open DEV → リルド村 · 素材仮配置. Aidan 正式 / Aidan 仮表示 toggles comparison without changing position. The original field/story placeholder is restored on close. No main merge or STEP12 integration.

`AidanFieldAssets` centralizes all20 actual paths and original canvas foot registration. `AidanFieldActor` observes actual field coordinate displacement, selects DOWN/LEFT/RIGHT/UP, cycles WALK01..04 at100ms, settles into matching IDLE after110ms without displacement. Keyboard22.5px/input and pointer5px/frame are unchanged. Focus jumps do not animate as walks; blocked movement settles to idle. Field collider remains x+6..28/y+32..42 and navigation anchor(17,42); visual foot registration maps to that anchor. Character visible height44px matches villagers39–46px and remains taller than Emma38px. No Battle transform/state/timer/motion change.

PNG pixel bytes are unchanged copies. Different original padding/pose scale is registered explicitly at display time, not cropped/painted. Images are decoded together on first DEV review entry, rather than downloaded during ordinary game startup; a loading label is shown until ready. Pending readiness cannot reactivate the sprite after review closes. Own RAF is cancelled on exit. No save, story, map, PartyManager, BattleActorState or battle asset modification.

Implementation changes: index.html adds3 DEV field load lines; lind-review.js adds2 actor lifecycle calls; new css/aidan-field.css and js/field/aidan-field-actor.js. All179 existing protected image/CSS/JS files remain byte-identical to the continuation baseline. Movement/navigation/rivers/NPCs/Emma/birds sources unchanged.

QA: actual field RAF plays all16 WALK frames and all4 matching IDLE states in1280×720,844×390 and390×844; rendered PNG registration and foot collider/navigation anchor align; mouse/touch comparison toggles, arrows/WASD, lifecycle/position/save restoration pass. All20 textures load. Other final field/Battle and full bridge-loop evidence is in the final report and JSON files.

Warnings: four-frame simple walking with slight cloak/embroidery differences; PLAYER QA for rhythm/foot sliding. Source PNGs are high-resolution1536×1024 (about30MB total); future production-size export optimization should follow PLAYER QA, not redesign these assets. No RUN/TALK/ATTACK, Fiona/Lou production, A2 or STEP12 work.
