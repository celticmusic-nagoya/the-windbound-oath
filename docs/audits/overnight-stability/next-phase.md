# Next-phase readiness — proposals, not implementation

|Phase|Verdict|Reason / required gate|
|---|---|---|
|Aidan Battle Motion|READY WITH WARNINGS|Main state/race/Idle stable; separate motion prototype needs PLAYER QA. Sequential attack PNG pack is absent; no frame attack can be approved yet.|
|Forest Bat Idle|READY WITH WARNINGS|4 true-alpha source frames exist; anatomical center/wing margins need approval before flight preview. No enemy implementation implied.|
|Character HD upgrade|READY WITH WARNINGS|Rendering comparison can proceed; source enlargement is not justified on PC. True HD production requires memory/device gate and visual approval.|
|Emma Motion tuning|READY WITH WARNINGS|Numeric CURRENT/A/B/C proposals available; select after PLAYER QA, then collision-test new route.|
|Lind Interiors|NOT READY|Lind exterior is DEV review; formal interior art/entry wiring remains a later approved phase. Existing legacy rooms are not finalized new Lind interiors.|
|Aidan House / NEW GAME opening|NOT READY|Requires formal house/interior/story integration; preserve existing opening meanwhile.|
|Fiona Field Sprite|NOT READY|No formal production field PNG in current main; HUMAN design/source review required.|
|Party Follow|NOT READY|No approved field-follow contract or complete actor assets; needs follower/collision/transition design first.|
|Location Card|READY WITH WARNINGS|Presentation can be isolated; approve location labels/duration and dialogue priority before implementation.|
|Cinematic Camera|READY WITH WARNINGS|Coordinates/pointer conversion tested, but current camera must stay unchanged; design an opt-in presentation API and reduced-motion policy first.|
|Moss Forest implementation|READY WITH WARNINGS|Legacy progression/3corruption fights and event persistence exist; production layered map/assets/collision and layout approval are still needed.|

## PLAYER QA required

1. Rendering comparison for PC coarse edges; no automatic bulk HD conversion.
2. Emma CURRENT / A / B / C activity preference; age/style preserved.
3. Main's Idle subtlety versus the separate tuning prototype; do not mix branches.
4. Forest Bat chest registration / full wing silhouette and5future Aidan-background
   assets if those states are ever enabled.
5. Real phone performance/temperature/memory. Mobile emulation cannot certify these.

## Recommended next3tasks

1. Opt-in PC character rendering comparison with current PNGs, then choose smoothing
   policy based on PLAYER QA, before considering HD sources.
2. Emma routine preview profiles A/B/C on a separate branch, preserving ground
   contact and slow elderly movement; approve one before replacing CURRENT.
3. Existing Aidan/Bat motion prototype PLAYER QA and source readiness gate, then
   scoped integration. Wait for actual attack frame assets instead of inventing paths.

No subjective tuning, formal map/story integration, new NPC/enemy art or production
deployment was performed in the stability-audit branch.
