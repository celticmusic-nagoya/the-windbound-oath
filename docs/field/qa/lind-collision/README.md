# Lind collision audit — 2026-10-09

Baseline: `308e9c68c7b7a7a85601bfdd77e7af26728f1c45`. Fix: `7bac843c8a53fee096c38e2270cb093e9de72655`.

## Root cause

Buildings used one generic rectangle at 18% X / 62% Y, 64% width / 27% height. Normalized visible-content sizing preserved that narrow footprint and omitted attached ground fences, flowerbeds and stores. The camera was not the cause: at all four scales the same world point was incorrectly allowed.

Representative house1: world origin (140,810), visible size 270×212, old local rect [49,131,173,57]. Right ground fence now extends to local X261.9 rather than old X222: about39.9 missing world pixels (83.8 screen pixels at2.10). Actor origin (366,943.96) was allowed before and blocked after at every tested scale. This is an independently reproduced example, not identification of a supplied screenshot.

Feet remain x+6,y+32,22×10 with anchor x+17,y+42. Sprite origin, camera conversion, motion, corner assist and navigation remain unchanged. Rect parts follow ground walls/props, not roof/canopy or transparent PNG bounds. Ten door approach points remain walkable; chicken-coop front gate remains open. Laundry right-post and training-flag pole footprints corrected.

## River and debug

Water rendering and bridge/fishing lanes unchanged. Existing bank margins (2px west/6px east) are made explicit in collisionEnvelope for shared feet/debug; 361,221 legal-position samples match the old predicate. SVG uses the same world data as movement; 130 shapes independently compared with DOM geometry at1.00/1.50/1.80/2.10. Debug OFF schedules no render RAF; repeated toggles do not grow listeners or overlays.

## QA

Collision runner covers 13 village buildings plus training shed, eight approach directions, doors, blocked destinations, mouse/touch, navigation routes, bridge10 round trips per scale/view, lifecycle and saved/live-state preservation. Local primary13 coverage has160 total bridge round trips; training shed was additionally tested in all16 combinations. Camera regression includes Arrow/WASD and corrected open-ground speed fixtures (old1100,900 is beside now-solid pigsty). Aidan A1, villagers/Emma, birds/wind/water, normal and Raider battles, command/attack/skill/KO/Victory tested separately. Browser clock advances are used for deterministic navigation/state sweeps; Aidan animation also tested with live RAF.

See geometry-audit.json and local-collision-results.json for numerical evidence. Run with NODE_PATH pointing to Playwright: `node docs/field/qa/lind-collision/collision-qa.cjs`. Override LIND_QA_URL, COLLISION_QA_OUT, COLLISION_VIEWS; public proxy mode COLLISION_PUBLIC=1. Data audit output: COLLISION_DATA_OUT (default /tmp/lind-geometry-audit.json).

## Scope and warnings

Legacy prototype well is hidden in this DEV review; no standalone well is registered. Its legacy story interaction was not replaced or finalized. Roof/canopy foreground depth may occlude upper sprites while feet remain outside solids; current depth design retained. Exact art contours still merit player review. No PNG, Battle logic/motion, field movement speed, save/story, A2 or STEP12 changes.

Official future player camera MIN1.00 / MAX2.10 / DEFAULT1.80 TEMPORARY is documented; public default1.00 unchanged. SETTINGS/storage/cinematic implementation deferred.

## Complete current manifest audit

| Object | Category | Parts | Decision |
|---|---|---:|---|
| cliff | prop | 1 | Audited ground footprint |
| lind_elder_house | building | 5 | Audited ground footprint |
| lind_inn | building | 4 | Audited ground footprint |
| lind_aidan_house | building | 5 | Audited ground footprint |
| lind_item_shop | building | 5 | Audited ground footprint |
| lind_house_01 | building | 5 | Audited ground footprint |
| lind_house_02 | building | 5 | Audited ground footprint |
| lind_house_03 | building | 5 | Audited ground footprint |
| lind_house_04 | building | 5 | Audited ground footprint |
| lind_barn | building | 5 | Audited ground footprint |
| lind_storage | building | 4 | Audited ground footprint |
| lind_cowshed | building | 4 | Audited ground footprint |
| lind_pigsty | building | 4 | Audited ground footprint |
| lind_chicken_coop | building | 4 | Audited ground footprint |
| lind_field_wheat | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_field_vegetables | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_field_flower | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_orchard_apple | prop | 2 | Audited ground footprint |
| lind_haystack | prop | 1 | Audited ground footprint |
| lind_hay_bale | prop | 1 | Audited ground footprint |
| lind_cart | prop | 3 | Audited ground footprint |
| lind_farm_tools | prop | 2 | Audited ground footprint |
| lind_tree_01 | prop | 1 | Audited ground footprint |
| lind_bush | prop | 1 | Audited ground footprint |
| lind_flower_patch | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_grass_tuft | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_rock_small | prop | 1 | Audited ground footprint |
| lind_rock_large | prop | 1 | Audited ground footprint |
| lind_stump | prop | 1 | Audited ground footprint |
| lind_fence | prop | 6 | Audited ground footprint |
| pig_fence | prop | 6 | Audited ground footprint |
| chicken_fence | prop | 6 | Audited ground footprint |
| lind_crate | prop | 2 | Audited ground footprint |
| lind_barrel | prop | 1 | Audited ground footprint |
| lind_feed_sack | prop | 1 | Audited ground footprint |
| lind_water_bucket | prop | 3 | Audited ground footprint |
| lind_laundry | prop | 2 | Audited ground footprint |
| lind_sign | prop | 1 | Audited ground footprint |
| lind_bridge | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_fishing_pier | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_fishing_rod | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_fish_basket | prop | 1 | Audited ground footprint |
| lind_reeds | decoration / non-solid | 0 | Intentional non-solid decoration |
| lind_river_rocks | decoration / non-solid | 0 | Intentional non-solid decoration |
| fishing_crate | prop | 2 | Audited ground footprint |
| train_ground | decoration / non-solid | 0 | Intentional non-solid decoration |
| train_shed | prop | 3 | Audited ground footprint |
| train_weapon_rack | prop | 2 | Audited ground footprint |
| train_target | prop | 1 | Audited ground footprint |
| train_dummy | prop | 1 | Audited ground footprint |
| train_post | prop | 1 | Audited ground footprint |
| train_gate | prop | 2 | Audited ground footprint |
| train_flag_green | prop | 1 | Audited ground footprint |
| train_fence_west | prop | 6 | Audited ground footprint |
| train_fence_east | prop | 6 | Audited ground footprint |
| lind_wind_stone | prop | 1 | Audited ground footprint |
