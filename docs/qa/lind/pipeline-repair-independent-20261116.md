# Pipeline repair independent QA — 2026-11-16

Reviewer `/root/qa`, separate from implementation author. Worktree `/workspace/lind-pipeline-repair`; baseline `993c75fb64be67680982f7096be3f3743495fb53`. Review covers the uncommitted repair diff, not full world acceptance. Raw command outputs and checks are embedded in adjacent JSON.

## Executed checks

- Independently reran startup race 20, SAVE compatibility 34, CONTINUE restore 37 assertions: all PASS. These execute shipped product blocks with simulated DOM/network/timers; browser/Android were not rerun for this repair.
- Source/legacy Python unit tests: 5 PASS. Existing render guard unit tests: 8 PASS.
- Legacy implementation is byte-for-byte identical to baseline assembler: SHA-256 `54e3f49d92b62965517f5d9822a76244086561a098499823b6d536343241506e`. New gateway rejects default new-world use before importing Blender and refuses existing output. Legacy use now requires explicit flag; old pixel map contract remains historical only.
- Independently computed SHA-256 of both downloaded Ubuntu packages under `/workspace/lind-package-check`: both exactly match committed checksum manifest. Workflow selects package version `4.0.2+dfsg-1ubuntu8`, checks binary/data hashes, checks installed package versions and Blender `4.0.2` runtime string.
- Independently exercised source registration transaction in a temporary fake repository with synthetic bytes and mocked hash verification: main branch refusal creates no directory; feature branch preserves exact bytes; a second registration refuses overwrite. These controls do **not** register the approved image or establish its SHA. Actual mismatch/non-PNG rejection is covered by rerun unit tests.
- Return-scene extraction includes shipped `rildeReturnActive` lexical state and actual scene functions. Four independent negative controls (missing declaration, missing ending boundary, missing start function, missing advance function) all reject. Reviewer initially mistyped state name as `rildeReturnRunning`; that QA harness assertion failed and was corrected against actual source, with no product changes.

## Review result and limits

No blocking defect found in this repair scope. The former SAVE fixture failure is resolved without replacing the real scene state with a permissive stub. Source registration fails closed on mismatched bytes, uses an exclusive new directory and exclusive image creation, and does not alter the input image. Legacy geometry cannot run by default through the supported entry point.

Pinned Blender **actual CI install/render remains NOT_RUN by this reviewer**; package hash verification is not execution evidence. Exact adopted-image registration remains **BLOCKED** until original bytes are available to the runtime. G1 full concordance stays BLOCKED, G2/full-world G3/G4 and Android remain unapproved. No runtime or accepted assets modified, no main merge or publication performed by reviewer.
