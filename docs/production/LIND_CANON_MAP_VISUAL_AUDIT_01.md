# LIND official village map — visual audit 01
Date: 2026-11-16. Source: docs/art/reference/lind/リルド村RPGアセット全体マップ.png (1536x1024 RGBA); SHA-256 83dd4ad1eb10103fdb7eb569e8b1b22cc92920d4c94d4eae85735125de87fe6c.
Evidence: GitHub Actions 43828092892, artifact 14207437553; downloaded ZIP and independently computed source SHA-256 locally, MATCH. Original image directly visually inspected. Source is a **composite**: left upper village map and separate right/bottom asset catalogue; catalogue illustrations must not be misread as additional village locations.

## Observed map layout (relative, NOT metric coordinates)
- Map is an illustrated isometric/oblique village overview. It does not explicitly label north orientation, metric scale, world origin, elevations or camera angle. Do not infer them from page pixel coordinates.
- Waterfall and elder's home: upper-left / northwest visual sector; waterfall upstream among cliffs.
- Inn: upper middle-left; Aidan's home: upper middle-right; training ground: upper right / east side.
- Central village plaza: glowing wind stone and well, near the centre; shop on left/west side; storage/warehouse east-southeast of plaza.
- Livestock enclosures: below/right of plaza, with cattle and pigs; fields and orchard: lower/right of central village.
- Main river visible along lower edge and right-hand side of village; crossing bridge toward the training area; fishing dock at lower-right. Secondary creek/watercourse and a smaller bridge near the left/lower village entry are visible. Distinguish each crossing before establishing gameplay collision.
- Village entry and dwellings: lower-left; houses and fenced plots on the western/southwestern approach.
- Image's accompanying asset catalogue includes building front/oblique views, training objects, nature tiles, bridges, barrels, signs and weather particles; this is reference content, not evidence that every shown asset is deployed at a second map position.

## Canon reconciliation and blockers
- Confirmed spatial **relationships**: Aidan house near inn, upper half of overview; central square windstone+well; training east of river crossing; elder home toward waterfall; southern/southeastern farmland.
- Still **BLOCKED**: map's true cardinal north (page-up not proven north), exact distances, 3D elevations, entry-door directions, bridge crossing counts/identifiers in runtime, collision, CG camera match and building footprints. The map is not a dimensioned architectural plan.
- Preserve current DOM 2200x1550 prototype coordinates as legacy integration references only, not official map coordinates.
- Spatial contract remains DRAFT; no director spatial lock. Aidan house master may progress on modular shape/material design but cannot finalize world-space transform.

## Suggested authoring zones (proposals, NOT canon coordinates)
ZONE_WEST_ENTRY; ZONE_CENTRAL_PLAZA; ZONE_NW_WATERFALL_ELDER; ZONE_NORTH_INN_AIDAN; ZONE_EAST_TRAINING; ZONE_SOUTHEAST_FARMS; ZONE_RIVER_CROSSINGS; ZONE_FISHING_DOCK. Each requires a canonical source-image evidence reference and reviewed camera-space footprint before approved coordinates are written.

QA: original file SHA PASS; map visual inspection PASS; qualitative relative-layout audit PASS; metric spatial contract G1 BLOCKED; G2/G4 NOT_RUN.
