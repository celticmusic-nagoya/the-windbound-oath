# Rilde architecture: approved CG first, rural Irish vernacular second
Director instruction 2026-11-26. Applies to BUILD #356 and scenic integration #364; existing original assets protected. This records production direction, not formal asset adoption.

## Source priority
1. Approved event/world CG exact bytes, current main cb0c880d1e638bad1f8855a8bedbe17d11a8c16f. Day: assets/approved/world/rilde_village.png SHA256 c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a. Raid: assets/approved/game/rilde_story/raid/attack_background_only.png SHA256 a19e782ec0927f9ef983cf896cf31a18ace0aca8bf2b165714342b1cfe528c3e. Aftermath: assets/approved/game/rilde_story/aftermath/ruins_background_only.png SHA256 78b0801f10b6a763c66aa44265ab381edc398f3b5adfb1b3d3dee0e6c6d917b2 (raid/aftermath hashes from BUILD programme; verify actual bytes). Current connector returned empty base64 for images. Fresh visual source inspection pending readback. The existing BUILD programme records earlier visual observations; do not treat them as fresh inspection.
2. Irish vernacular reference, not canon, no automatic adoption of modern features or photo pixels:
- National Inventory of Architectural Heritage, Finnea (natural slate, modest street-fronted dwelling): https://www.buildingsofireland.ie/buildings-search/building/15301002/main-street-finnea-finnea-westmeath
- NIAH Lisball (slated porch, limewashed rubble stone, irregularity, farm context): https://www.buildingsofireland.ie/buildings-search/building/40402814/lisball-co-cavan
- NIAH Slane (stone houses, continuous street frontage): https://www.buildingsofireland.ie/buildings-search/building/14315024/main-street-slane-slane-co-meath
- Heritage Council, Traditional Farm Buildings Grant Scheme (Clare outbuildings, Mayo boundary wall/bridge, Cork stone/slate, Kerry local sandstone/Valentia slate): https://www.heritagecouncil.ie/projects/traditional-farm-buildings-grant-scheme
- Visual reference Doolin road bend and low stone boundary walls; Bunratty Folk Park historic street composition; modern painted shopfronts, asphalt, road markings, utilities, cars, modern lettering excluded. No third-party imagery embedded or copied to textures without rights clearance.

## Next actual model tasks
- Compare same-camera actual building render to day CG, prioritize proportions, roof silhouette, scale hierarchy, exposed irregular stonework, openings and lived-in props. Keep established dark blue-gray slate rather than copying thatch or brightly painted tourist buildings.
- Preserve actual HOME/BUILD geometry and state interfaces; edit isolated candidate only. Residential massing should be modest and varied; inn/shop recognizable by roles, not a generic identical building kit.
- Streetscape: asymmetrical clustered frontages, irregular courtyards, low stone boundaries, ground contours, narrow lanes with wider meeting spaces; retain traversability and portal access. Do not invent canonical coordinates or dimensions from perspective image. Evaluate matched player-eye and overhead views.
- Peaceful/raid/aftermath: same footprint, masonry shell, chimney and opening positions, controlled roof/wood/prop state change. Do not introduce actual fire damage to protected originals.
- D0 source SHA, D1 parent scene/interfaces, D2 elevation/sections and comparison, D3 measured tolerance/uncertainty, D4 separate review before precision edits. G2 HOLD until actual model visuals reviewed; G4 not implied.
- Android reporting: RGB JPEG preview alongside links to original native/PNG evidence, no new public distribution. Existing V11 run must not be duplicated.
