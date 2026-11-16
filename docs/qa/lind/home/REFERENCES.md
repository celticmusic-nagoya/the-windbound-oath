# LIND-HOME-01 — reference register (Aidan's house)

Inspected with the Read tool on 2026-11-16 (downscaled copies only; originals untouched). SHA-256 computed on the worktree files at #338 head `c0223b5`.

## Approved (director-approved originals; SHA matches `docs/art/approved-rilde-story-20261107.json` / `approved-world-event-sha256.json`)
| Path | SHA-256 | Use for HOME |
|---|---|---|
| `assets/approved/world/rilde_village.png` (1672×941) | `c55af0770e0aa7c876575e57e4016df3280816459efd41f7200fa5ed3b51726a` | **Primary style base** (PR #309: base reference for Aidan house). Observed: cream/greige rounded snecked rubble with thin darker joints, larger squared quoins and window jambs, dark blue-gray slate roofs with visible courses and slightly ragged eaves, gable-apex stone chimneys with clay pots, small-pane timber windows with warm glow, plank doors, flower boxes, barrels, ivy, cobbled path. Which building is Aidan's is **not identified** in the CG. |
| `assets/approved/game/rilde_story/raid/attack_background_only.png` | `a19e782ec0927f9ef983cf896cf31a18ace0aca8bf2b165714342b1cfe528c3e` | burning-variant continuity only (same rubble/timber vocabulary) |
| `assets/approved/game/rilde_story/aftermath/ruins_background_only.png` | `78b0801f10b6a763c66aa44265ab381edc398f3b5adfb1b3d3dee0e6c6d917b2` | ruined-variant continuity only |
| `assets/approved/game/rilde_story/road/curve_reveal_APPROVED_user_reference.jpg` | `7989bca750f66ade1935c31fd1f15189505f7c8b481b3839d86cb5ab26c4c60b` | distant village only; no house detail |
| `assets/approved/game/rilde_story/recovery/relief_with_characters_APPROVED_user_reference.jpg` | `564bf45da05f9bc1d64a5e83986d1ce8eee0ab2e6dea82dd3d62d2a0cc15cda5` | aftermath; no house detail |
| `assets/approved/game/cliff/*` (4 files) | `db0b1f6a…4a07`, `f7e2c3a7…a9`, `a0a52220…b2`, `370b40af…1d` | not architectural; not used |

Roof canon: blue-gray slate (PR #307 `FIELD_VISUAL_OVERHAUL_20261108.md` line 44, director-approved 2026-11-14). Colour range HSV h200–215° s0.08–0.15 v0.32–0.45 is a **candidate** range from #309/#311, not canonical RGB.

## Reference-only / not in repo
| Item | Status |
|---|---|
| Aidan house visual target "V11" (`a_highly_detailed_cinematic_3d_rendered_scene_of.png`), SHA `bafade8ce4220bdbf1e09a4b9eeeb9b0fd168ce27fb7a910164e1538e86266a8` | User-approved quality target (#311 record). **Binary not in any repo → not inspected by this lane.** Characteristics used only via #311/#331 text. |
| 2026-11-16 world-map master `abbb3997b63ea5d86eea01f68bd220f0713baf4e90afaaa37684ec2687dc0620` | **Registered 2026-11-17** (repo dc17dd4 `assets/sources/lind-world-20261116/original.png`, 1536×1024; lead-verified). Inspected via local read-only copy `/home/claude/refs/lind_world_master_abbb3997.png` (SHA re-verified by `qa_aidan_house.py`; not copied into this branch). Composition master, not to scale. Village cluster: 1.5-storey side-gabled cottages, cream/greige rubble walls, gable-end chimneys with smoke, small dormers on some houses. **Roof colour observation:** foreground roofs read blue-gray slate, but several mid/back roofs in the master read warm brown/ochre. This lane keeps the director-approved blue-gray slate canon (#307); the mixed roof colour in the master is flagged to COORD, not resolved here. Which cottage is Aidan's is not labelled. |
| `data/maps/rilde_in_aidan.json` | current runtime **prototype** interior (single room; bed west near back wall, fireplace back wall east, window back wall, door bottom-centre, spawn `from_bed`). Used as layout hint only; not geometry authority; not modified. |

## Canon facts used (paraphrased, private bible v5.0 §8 + scenario canon, handoff `af0d068`)
- Aidan's house is a listed Rilde village structure; village is agricultural/pastoral and lived-in detail is strongly emphasised.
- Scenario canon step 1 and AGENTS.md §13/§15: the opening starts inside Aidan's house beside the bed; peaceful buildings are enterable; burning variant must keep layout continuity.
- No canon dimensions, storey count, door facing, chimney position or stone style exist → all such values in this lane are `CANDIDATE`.
