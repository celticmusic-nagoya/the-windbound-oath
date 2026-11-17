# LIND CONTINUOUS CLIFF 02 — Independent art QA (2026-11-17)

## Evidence
GitHub Actions run https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43989381659
Artifact https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43989381659/artifacts/14286054623
Actual six-file ZIP downloaded and inspected: front.png, oblique.png, top_contact.png, continuous_cliff_study.blend, manifest.json, blender.log.
Manifest: Blender 4.0.2; 11,300 vertices; 11,202 faces; 0 nonmanifold/boundary edges by edge-incidence test; PNG SHA and .blend SHA verified in CI; .blend reopened in CI.

## Independent visual QA: G2 FAIL
1. Frontal rock face consists of broad, nearly parallel sinusoidal bands, reading as smoothed stacked strata rather than authored weathered Irish coastal cliff geology.
2. The cliff cap reads as a smooth, generic hill/terrain slab; insufficient exposed bedrock/soil transition.
3. Crest has dark open-looking notches and folded/smeared patches. A watertight topology result does not prove a visually sound surface or no self-intersection.
4. Oblique view exposes vertical rectangular cut end and horizontal flat base. Candidate remains a laboratory slab, not a production coastal formation.
5. No broken scarps, scree, fracture hierarchy, coast/river contact, convincing scale cues, or approved game-size visual proof.

## Gate decisions
G1 BLOCKED: approved scale/placement/official CG match not validated.
G2 FAIL: observed three actual PNGs.
G3 LIMITED PASS: Blender run, 3 PNGs, hashes, closed edge incidence and .blend reopen. Self-intersections, normals, realistic geology, nav/collision NOT_RUN.
G4 NOT_RUN: no game/WebGL/Android integration.

## Stop condition and different production method
This is a first attempt in the continuous sinusoidal displacement family, but previous PR #346 A/B already exhausted smooth-heightfield/striped-rock geology. Do **not** repeat the smooth wave bands under another name or tune parameters without structural change. Move to reference-driven geological blockout/sculpt with manually authored strata/joint masks and sculpt/voxel remesh, or properly licensed high-quality photogrammetry/3D rock assets, maintaining original world design. Record rights and provenance before asset adoption. Perform clay G2 before PBR.
No changes to approved CG, bridge PR, runtime or main.
