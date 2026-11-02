# Goblin20 independent static / Node review

Reviewed exact HEAD `bb9477fdc57e725cf57e2740a28d17d387a29f91`, baseline `2276c3c693cce9ea215dd68d51e1725bfb4e51fb`. Read current branch AGENTS.md; branch candidate authorization is not formal adoption or main/merge permission.

**Static and direct Node QA: PASS. Browser QA is pending root collection.**

Independently executed tests/goblin_field_animation.test.cjs:10/10 actual cases PASS, covering four directional banks, idle clock, blocked movement, freeze/resume/clear, and three legacy monster types. Candidate20 PNG manifest hashes and320×320RGBA geometry match. All259 adopted PNG hashes match26C protection; all1298 pre-existing img/assets files from baseline are byte-identical. audit_registry reports1202assets/0errors. No browser or product changes performed by this reviewer.

Visual comparison of packed-contact.png to official goblin_battle_idle.png: green long-eared goblin, yellow eyes, patched brown hood/leather wraps, belt and curved rusted blade align with reference. Directional right/left/back views are distinct rather than runtime mirroring. Four walk stages visibly vary leg contacts/poses. No obvious crop clipping in the contact. These are candidate generated interpretations, not pixel-identical approved art, and final aesthetic acceptance remains user-owned. Static review cannot certify in-game speed/contact or small-screen readability.

FieldMonsters adds only goblin art metadata and a conditional directional animation path. Facing derives from actual collision-constrained displacement; walk phase derives from distance, idle from the existing update loop (no extra timer). Blocked goblins select idle. Heading changes reset travel; entering movement resets phase. Existing think/chase/engage/state/balance parameters are unchanged. Legacy file templates, pose clock, mirroring and flyer behavior remain on their prior branch, with direct regression coverage.

Registry coverage change correctly permits locally-existing BRANCH_ONLY registered candidate files without falsely labelling them MAIN. MAIN existence/SHA/runtime-reference, duplicate IDs, enums, frame numbering, unregistered-image and freshness checks remain. Limitation: BRANCH_ONLY paths counted for coverage do not receive the MAIN-only per-file hash/runtime-reference checks in this audit; candidate manifest20SHA verification and freshness are therefore separate gates and must remain. No formal status upgrade is inferred.

No blocker found for candidate-branch integration within the reviewed scope. Do not report final browser PASS or deployment before root results. No main/PR/merge authorization is implied. Only this scratch review file was written.
