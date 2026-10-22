# THE WINDBOUND OATH — PROJECT MASTER

Status: **PROPOSED — Claude-reviewed revision of the ChatGPT draft (2026-10-22 JST). Not author-approved; not authoritative until it is merged under `docs/handoff/AI_HANDOFF_PROTOCOL.md`.**
Scope: shared entry point for ChatGPT / Claude Code / Codex. This is an **index and operational summary**. It does not replace official canon, `AGENTS.md`, the handoff protocol or the code, and it grants no permission.
Base checked: game repository `main` = `081111ed848a54e4c0b70894a1c41205cf6642f3` (2026-10-22). **Always fetch `main` again before work.**

## 0. Status vocabulary used in these three documents
| Tag | Meaning |
|---|---|
| `CONFIRMED` | Official canon or an explicit, evidenced user/author decision |
| `IMPLEMENTED` | Seen in current `main` code, data or merged history |
| `IN_PROGRESS` | Work exists on a branch or backup but is not integrated |
| `PROPOSED` | Not approved. Never treat as a rule |
| `UNKNOWN` | Could not be verified from the sources named |
| `SUPERSEDED` | Old, withdrawn or replaced. History only |

Lore labels stay exactly as the original uses them: 確定 / 脚本採用案 / 未決定 / 撤回 / 要コード照合. **設定確定 ≠ 実装済み ≠ 統合承認** (canon adopted ≠ implemented ≠ approved to merge).

## 1. Project identity
- Title: **THE WINDBOUND OATH** (Japanese reading ウィンドバウンド・オース), Gaelic subtitle *Mionn na Gaoithe*. `CONFIRMED` (`AGENTS.md` §2, lore v5.0 §1). Obsolete titles "THE OATH OF WIND" / "THE JOURNEY OF THE WIND" must not be used. Aidan's weapon is 「誓いの剣」, never 「誓いのダガー」.
- Original Celtic-influenced 2D browser JRPG: HTML, CSS, vanilla JavaScript; GitHub Pages (HTTPS). Primary target PC browser, secondary responsive Android Chrome. `CONFIRMED` (`AGENTS.md` §1, §3).
- Game repository `celticmusic-nagoya/the-windbound-oath` (public). Private handoff repository `celticmusic-nagoya/the-windbound-oath-handoff` (official lore, QA reports, handoff records).

## 2. Authority and precedence
**A. Lore, story, characters, world** (this order is the one in `AGENTS.md` §0 and `docs/lore/README.md`; it is not re-ranked here):
1. A **later explicit user adoption** whose date and source can be checked.
2. Formal addenda in private `reference/lore/CANON_ADDENDUM.md`.
3. The latest addenda inside the v5.0 master (its §§1–6).
4. The rest of the v5.0 master (including the v4.0 text kept as its appendix A).
5. Archived older versions: history only.
6. Proposals and drafts: not implementable.

The v5.0 master (SHA-256 `e6f7331b867a7307017c7abb30bae7b6317363a33e5f9d831b80d34f0e51bf49`) is edited by nobody. `CANON_STATUS.md` is a **status table, not an adoption record**, and `CANON_CHANGELOG.md` is a history. Do not read the master alone; read the addenda and the status table with it. Do not reproduce the master here or anywhere in the public repository. If the private files cannot be read, report `LORE_INACCESSIBLE` (what was tried, the error) and leave lore-dependent details unchanged.

**B. Process, permissions, merge gates**: current user decisions, then `AGENTS.md`, `docs/handoff/AI_HANDOFF_PROTOCOL.md`, `docs/handoff/COLLABORATION.md`, `docs/handoff/codex-standing-orders.md`. If they conflict, stop and ask (Protocol §1); do not pick the permissive reading.

**C. Evidence of implementation**: current `main` code, history and tests show what is *implemented*. They are not proof of canon (`AGENTS.md` §0). Numbers found in code are not promoted to official settings.

Roadmaps, archived scripts, unapproved proposals and draft branches are history only.

## 3. Baseline summary (reference table — not a restatement of the sources)
| Topic | Statement | Tag | Source |
|---|---|---|---|
| Party | 6 playable characters; normal battle 4 active + 2 reserve; Lou is the support slot, not a normal-level member; level cap 50 | `CONFIRMED` | `AGENTS.md` §4–5; lore v5.0 §4 |
| Resources | TP personal, max 100; RUNE shared, max 100; the main costs are in `AGENTS.md` §4 | `CONFIRMED`; `IMPLEMENTED` per `CANON_STATUS.md` (2026-10-20, not re-verified for this document) | `AGENTS.md` §4; `CANON_STATUS.md` |
| Goblin Raider | Difficulty was explicitly approved. **No casual rebalancing.** Do not copy the numbers; read `AGENTS.md` §7 | `CONFIRMED` | `AGENTS.md` §7 |
| Prologue route | The canonical route is `AGENTS.md` §15 (Moss Forest → stone/Fiona → Lou → altar, where the Raider appears and the father's sword breaks → Raider battle → aftermath → Dunvar Fortress → prologue end). The ordering in `docs/GAME_DESIGN.md` "Prologue" (weapon lost before Lou appears; altar before Raider) is older | `CONFIRMED` (§15 and lore v5.0 §2); `docs/GAME_DESIGN.md` prologue list is `SUPERSEDED` in part | `AGENTS.md` §15; lore v5.0 §2 |
| Sword | Aidan carries his father's sword from the start; it breaks at the Raider encounter; after the altar contract 誓いの剣 is his fixed weapon and can be strengthened by smithing. Smithing recipes and numbers are 未決定 | `CONFIRMED` / 未決定 | lore v5.0 §2; `AGENTS.md` §15 |
| Fiona 風の舞 | Narratively first manifests at the Raider encounter. Cost, multiplier and duration are not approved. The code gate is story stage 13, and whether the two match is **未確認** | `CONFIRMED` (narrative) / 要コード照合 (timing) | lore v5.0 §2; `CANON_STATUS.md` #4, #7 |
| Moss Forest | A1 Sunlit Path → A2 Mossy Ravine → A3 Ancient Grove. Maps `moss_forest_01/02/03` exist in `data/maps` | `CONFIRMED`; `IMPLEMENTED` (maps exist; story completeness not verified here) | lore v5.0 §2–3; `data/maps` |
| Battle UI | Battlefield, log, COMMAND, expanded commands and item selection are separate in the DOM; compact closed COMMAND; portrait: controls below, landscape: controls left and field right; shared by normal and boss battles | `CONFIRMED`; implementation state 要コード照合 | lore v5.0 §4; `AGENTS.md` §6 |
| Field height Phase 1 | 56 world px per level, `unitScale=2.5` (not applied twice), level-aware collision, connectors. Inert on maps without a height spec | `IMPLEMENTED` (`js/field/field-height.js`, `data/maps/dev_height_proto.json`, `cliff_moher_01_spiral_ascent` spec) | code; `docs/art/height_phase2_render_spec.md` §1 |
| Field height Phase 2 | Design documents merged by PR #44 (docs only). Runtime pieces, manifest, maps and assets are **not** approved. The spec's own header records author approval of the basic design and D1–D5 on 2026-10-21 23:10 | design `CONFIRMED` per spec header; implementation not approved | `docs/art/height_phase2_*.md`; PR #44 |
| Height on story maps | Enabling it needs real-device Android performance verification, which is `NOT_RUN` | not authorized | `docs/handoff/codex-standing-orders.md` §1 |
| Lou-only faint | Three separate things. (1) **Canon**: adopted (ADD-001, 2026-10-16, narrowed to Lou on 2026-10-19). (2) **Difficulty**: the author explicitly accepted the difficulty rise on 2026-10-20 ("難易度上昇を許容", a lower win rate is not itself a reason to block the merge; the confirmed spec — 33% faint, 2–3 rounds to recover, support stopped while fainted, final blessing held and fired once — stays and no unauthorised tuning), as a **conditional** merge approval for PR #36 only. Source: [PR #36 comment of 2026-10-20 JST (2026-10-19T15:40Z)](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/36#issuecomment-6271128948). The statement that the effect "is unapproved" in the [PR #36 tidy-up comment of 2026-10-22](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/36#issuecomment-6332388215) conflicts with it; that comment is a tidy-up note, not an author decision, and no later author record withdrawing the acceptance was found (`UNKNOWN` whether one exists). (3) **Code/integration**: PR #36 was **closed unmerged on 2026-10-22** as tidy-up, which the same comment says is not a merge approval, not a rejection of the spec and not a branch deletion; Codex independent QA was not completed; it is to be re-proposed as a new PR on the current `main` with independent QA. The 2026-10-20 acceptance is **not** an approval to integrate: it was tied to PR #36's head and to the QA gates, and covers neither a new PR nor a changed head. Past 50-battle comparison (main 50 wins / 0 losses, PR 26 / 24) is a measurement, not a verdict | canon `CONFIRMED`; difficulty acceptance `CONFIRMED` (conditional, 2026-10-20); code `IN_PROGRESS` (branch `feature/lou-faint-recovery` kept, not integrated) | `CANON_ADDENDUM.md` ADD-001; PR #36 comments |
| General faint / stun for other characters | Not adopted; a future candidate only. Character growth system v0.1 is also not adopted | `PROPOSED` | `CANON_STATUS.md` #3, #5 |
| Field camera | Adjustable 1.00×–2.10×; default 1.80× is temporary | `CONFIRMED` per `docs/GAME_DESIGN.md` (Oct 2026) | `docs/GAME_DESIGN.md` |
| Save | Format v30, **additive changes only**; never destroy an older save | `CONFIRMED` | `docs/handoff/codex-standing-orders.md` §8; `AGENTS.md` §17 |

## 4. Source index
| Domain | Current source |
|---|---|
| AI instructions | `AGENTS.md` |
| Process and merge gates | `docs/handoff/AI_HANDOFF_PROTOCOL.md`, `COLLABORATION.md`, `codex-standing-orders.md`, `CLAIMS.md` |
| Official lore | private `reference/lore/`: v5.0 master, `CANON_ADDENDUM.md`, `CANON_STATUS.md`, `CANON_CHANGELOG.md`, `SHA256SUMS` |
| Public lore access policy | `docs/lore/README.md` |
| Core gameplay | `docs/GAME_DESIGN.md` (partly dated; see §6), code and tests |
| Roadmap | `docs/ROADMAP.md` — historical v0.66 baseline, not the current sprint |
| Art, battle, field, height | `docs/art/`, `docs/battle/`, `docs/field/`, `docs/qa/` |
| Scenario | private lore plus `docs/story/` (`WORLD_STORY_BIBLE_v1.1.txt` is `SUPERSEDED`) |
| Live work and blockers | `DEVELOPMENT_STATUS.md` (a dated snapshot) and the GitHub Issues / PRs it links |

## 5. Document hygiene
- A confirmed change records, separately: decision date, author evidence, canon status, implementation status, target branch/SHA, QA status and rollout permission.
- Keep old files for audit; add a superseded notice instead of overwriting approved source material.
- No credentials, tokens, personal data, unapproved final art or private lore text in public documents.
- A status snapshot shows its as-of date and can never authorize a merge or a deletion.

## 6. Known reconciliation work (`PROPOSED` — none of it is done by this document)
Each item is a separately reviewed docs-only change; this document edits none of these files.
1. **v0.66 baseline wording.** `AGENTS.md` §1, `README.md`, `CODEX_START_PROMPT.md` and `docs/ROADMAP.md` all name v0.66 "Impact Effects" as the handoff baseline (last changed 2026-10-07 to 2026-10-20 per git history). Later work (Rilde village, Moss Forest, battle motions, height Phase 1, protocol v1) is not reflected. No newer baseline label was found in the sources reviewed (`UNKNOWN`). Treat v0.66 as the historical handoff baseline, and refresh the entry links without rewriting history.
2. **`docs/GAME_DESIGN.md` "Prologue" list** predates `AGENTS.md` §15 and lore v5.0 §2 (see §3). Add a superseded notice that points to them.
3. **`docs/lore/README.md` and private `CANON_STATUS.md`/`CANON_ADDENDUM.md`** still describe PR #36 as "review pending", name `main 405111f` as the implementation baseline, and say the lore files are "not on `main` until PR #1/#2 merge". PR #36 is now closed, and the private PRs #1/#2 were merged on 2026-10-20 (`CANON_CHANGELOG.md`). Update them in a reviewed change; the private files belong to the handoff repository.
4. **Protocol title.** `docs/handoff/AI_HANDOFF_PROTOCOL.md` is titled "v1" and is ACTIVE (user decision 2026-10-20; PR #43). The v2 proposal in PR #14 was closed unmerged on 2026-10-22 (it changed permissions and automation gates; manual approval is required) and is not in force.
5. Branch inventory must be recomputed against the current `main` (see `DEVELOPMENT_STATUS.md`).
