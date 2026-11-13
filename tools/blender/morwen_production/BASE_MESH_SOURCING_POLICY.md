# MORWEN-BASE-SOURCING-01 — Third-party base mesh sourcing policy

Status: APPROVED WORKFLOW / NO NEW THIRD-PARTY ASSET APPROVED

## Goal
Use an existing professionally built topology/rig as a lawful *production base* and transform it to the canonical THE WINDBOUND OATH design. Never substitute an unmodified downloaded character for an original game character.

## Candidate classes
1. Current pinned VRoid old-beta Base_Female.vrm: existing isolated evaluation candidate. Its CC0 provenance and the exact asset's redistribution rights must be documented before production acceptance.
2. VRoid Studio independently generated original base: evaluate license terms of software outputs, included clothing/hair/materials, and third-party presets separately.
3. MakeHuman/MPFB: existing import trial did not pass Morwen artistic G2; use only if an improved topology/workflow can address the recorded root cause, not as a repeated primitive experiment.
4. Blender-compatible game/VTuber bases: evaluate original author, topology, deformation, shader portability, UVs, source license and restrictions.
5. Vocaloid or branded fan models: do not import without verified model rights, character/IP permission, derivative-game permission and redistribution rights. Default status: REJECT/UNVERIFIED.

## Intake gate
Record for each candidate: name, original creator, original URL, asset version, downloaded SHA-256, exact license text/URL and retrieval date, commercial use, derivative modification, embedded game distribution, redistribution of source, attribution, trademark/character restrictions, texture/rig/motion licenses, model polycount, topology, rig format, Blender version, and evidence links.

Keep third-party downloads in isolated candidate folders, never overwrite canonical refs. Do not ship or publish candidate assets until rights are checked.

## Art production
- Compare the immutable four-view Morwen Layer 0 references with the candidate from consistent orthographic cameras.
- Establish explicit front/profile landmarks by manual review; do not infer landmarks from bounding boxes or material names.
- Sculpt/retopologize facial silhouette and eyes; create independent hair, thin gold glasses, hat, outfit, asymmetrical accessories, cape, boots and skin material.
- Preserve anatomical right (+X) garter and approved asymmetries.
- Apply four gates: G1 canonical fidelity; G2 visual/artistic quality; G3 render/alpha/topology/rig technical quality; G4 in-game appearance and performance.
- After two failed attempts with the same method, stop and change the method based on root-cause evidence.

## Safety
Only a feature branch and Draft PR for changes; no main merge, production asset replacement, or release without explicit authorization.
