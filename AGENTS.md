# AGENTS.md — THE WINDBOUND OATH / Mionn na Gaoithe

## 0. Official lore master (canon reference)
- The canon for world, story, characters and dialogue is 「THE WINDBOUND OATH 公式統合設定資料集 v5.0」(2026-10-19), SHA-256 `e6f7331b867a7307017c7abb30bae7b6317363a33e5f9d831b80d34f0e51bf49`. The full text is **not stored in this public repository**; it is kept in the private handoff repository (`celticmusic-nagoya/the-windbound-oath-handoff`, `reference/lore/`). Access must be granted by the user. See `docs/lore/README.md`.
- If you cannot read it, **do not reconstruct or guess it**: report `LORE_INACCESSIBLE` (what you tried and the error), ask the user to grant read access (how: `docs/lore/README.md`), and leave lore-dependent details unchanged.
- Priority: later explicit user adoption > formal addenda (`CANON_ADDENDUM.md`, private) > v5.0 latest addenda > the rest of v5.0 > archived older versions (history only) > proposals. Do not read the original alone: the addenda and status table are in the same private directory. Keep the labels 確定 / 脚本採用案 / 未決定 / 撤回 / 要コード照合 exactly; never promote candidates or undecided items to 確定 without the user.
- 設定確定 is not 実装済み: verify implementation with current main code, Git history and tests. Do not promote numbers found in code to official settings, and do not change existing scenario, dialogue, character design or balance on the strength of the lore text alone.
- Adopted changes are managed as addenda in the private repository, never by editing the original.
- Do not make copies of the full lore text (one master, kept private). Refer to it by version and section instead. Early-game dialogue and NPC lines may only use what the characters know at that point. Spoilers in development docs are tolerated before release (2026-10-20 policy), but credentials, keys, tokens and personal data must never be committed.
- Open item kept as-is: the timing of Fiona's 風の舞 acquisition is 要確認 (current code gate: story stage 13).
- Superseded: `docs/story/WORLD_STORY_BIBLE_v1.1.txt` (history only; not canon).

## 1. Mission
You are implementing an existing original 2D browser JRPG, not redesigning it from scratch.
Preserve confirmed behavior unless the user explicitly requests a change. Prefer root-cause fixes and maintainable systems over layers of CSS/JS patches.

Current development baseline: v0.66 "Impact Effects".
Primary target: PC browser. Secondary target: responsive Android Chrome.
Deployment target: GitHub Pages.

## 2. Canonical title
- THE WINDBOUND OATH
- Gaelic subtitle: Mionn na Gaoithe
- Do NOT use obsolete titles "THE OATH OF WIND" or "THE JOURNEY OF THE WIND".
- Aidan's weapon is 「誓いの剣」. Never call it 「誓いのダガー」.

## 3. Technology / repository policy
- HTML / CSS / vanilla JavaScript.
- Assets should live in `img/`, not Base64 in HTML.
- Keep paths GitHub Pages compatible and relative to the repository.
- Prefer semantic modules/files as the project is refactored; do not make a giant monolithic patch pile.
- Preserve mobile touch support; no virtual D-pad/controller.
- Suppress accidental text selection/long-press UI where appropriate for game surfaces.
- Do not depend on `file://` or Android `content://` behavior for production. Production is GitHub Pages/HTTPS.
- Development-only tools must be clearly gated and removable from release builds.

## 4. Non-negotiable confirmed game rules
### Battle resources
- TP = personal combat resource, max 100.
- Battle starts at TP 0.
- Normal attack: +15 TP.
- Defend: +10 TP.
- 「一閃」 costs TP 30 and is disabled/dimmed below 30.
- 「一閃」 is an ordinary personal sword technique.
- Future 「風の一閃」 is a separate Oathblade/RUNE special.
- RUNE = shared party resource, max 100.

### Party
Long-term roster: six controllable characters + Lou as support.
- Normal battle: 4 active + 2 reserve + Lou SUPPORT.
- Reserve recruited members receive 100% EXP.
- Lou does not take normal command turns and does not use normal levels.
- Story events may require/restrict members.
- Architecture must be able to grow into Party A / Party B / Party C for multi-party story battles.

### Growth
- Level cap 50.
- Natural story clear target roughly LV35–40.
- Completionist target LV50.
- Basic skills may unlock by level; signature skills should come from story/exploration/character events.

## 5. Canonical characters
### Aidan / エイダン
17, human swordsman, knight commander's son.
Brown tousled hair, green eyes, forest/deep green + ivory + antique gold armor/clothing.
Weapon: 誓いの剣.
Physical / TP-oriented.
Final battle art is the standalone transparent asset, not an old composite crop.

### Fiona / フィオナ
~16, human healer from Rilde Village (リルド村).
IMPORTANT:
- ordinary HUMAN ears
- NO elf ears
- NO wings
Light chestnut/beige long wavy hair, green eyes, floral/leaf ornamentation, ivory/pale-green/deep-green + antique gold.
Healing/life/plants/wind motifs.

### Lou / ルー
Tiny palm-sized fairy, always hovering.
Silver-blue hair, pointed fairy ears, aqua eyes, translucent blue/gold wings.
White/teal/aqua/gold clothing.
SUPPORT-only in normal battle.
Her progression is FAIRY BLESSING through finding/rescuing named fairy survivors; no normal LV system.

### Liam / リアム
~20, thief/treasure hunter, former royal ruins surveyor.
Fastest party member; CRI/steal identity.
Russet/red patterned bandana, goggles, agile dark leather equipment.

### Morwen / モルウェン
17, top-ranked student at the Royal Magic Academy (王立魔法学院), and a reserved black mage.
Her officially approved v3.0 design is the academy uniform; preserve the existing character artwork and black/navy/purple + antique gold palette, long dark hair, and violet eyes.
The Royal Magic Research Institute (王立魔法研究院) is a separate research institution located alongside the academy. Morwen's admired mentor, Edric Vane (エドリック・ヴェイン), belongs to the institute; retain his existing story arc without inventing new details.
Highest MAG; Resonance system 0–3.
Canon: private handoff repository `reference/lore/CANON_ADDENDUM.md` ADD-002 (2026-11-06). Original v5.0 remains immutable; clean up outdated references only after game-main integration and formal scenario revision.

### Future dwarf
Blacksmith/tank. High DEF, provoke, cover, iron wall, shield bash/BREAK.
Joining can unlock forging/equipment upgrades.
Name/design not finalized.

### Future dancer
Buff/debuff/action-order specialist.
Distinctive proposed mechanic: DANCE CHAIN.
Name/design not finalized.

## 6. Battle presentation — confirmed baseline
- Allies on left facing right; enemies on right facing left.
- Normal / PREEMPTIVE STRIKE / BACK ATTACK.
- Bosses do not randomly back-attack.
- Command UI is a compact `COMMAND` tab while closed; expands only when needed.
- Command window is translucent so battlefield remains visible.
- Empty battle-log boxes must never remain visible.
- Dialogue/event layers have priority over utility HUDs.
- Lou appears as a small SUPPORT element, not as a full-size party member.
- Close-range attackers make a large, readable lunge toward the target.
- Ranged/magic characters only step forward modestly.
- Enemy melee attacks similarly lunge toward the party.
- Impact presentation may use slash/magic effects, hit-stop, damage numbers, and restrained screen shake.
- Keep responsive layout clean in desktop, mobile landscape, and portrait.

## 7. Goblin Raider — stable gameplay
Do NOT casually rebalance this boss. User explicitly approved its difficulty.
- HP 1250.
- 3 phases: >820, >400, <=400.
- Normal damage: phase1 21, phase2 27, phase3 32, plus +3 per add.
- Adds on rounds 2, 5, 8; max 4.
- Queued 「破砕斬」: phase3 base 48, otherwise 42; hits both current heroes; Fiona base -6; defend halves.
- Queued every third round, or even rounds in phase 3.
- RUNE starts at 25.
- 「風の一閃」 conceptually clears minions and damages/breaks queued boss action.
- Raider should look genuinely huge on desktop.
- Raider HUD must be independent from the image, not overlap the face/body, and must remain fixed while the sprite lunges.
- KO art must replace live art on defeat.

## 8. Goblin behavior
- Normal goblin: telegraphed 「仲間を呼ぶ」; once per individual; enemy cap about 4.
- Tainted Goblin: aggressive black-purple rune attacks.
- Goblin Raider: large war horn / 増援召集.
- KO graphics must be applied correctly to both Tainted Goblin and Raider.
- Use standalone transparent monster assets. Never return to ugly crops from composite reference sheets.

## 9. Current visual asset rule
This is critical:
- DO NOT crop final battle characters/monsters out of composite design sheets.
- Use individually generated standalone transparent PNG assets.
- Verify actual alpha transparency; do not mistake checkerboard pixels for transparency.
- Avoid background fragments, duplicated sprites, or overlapping Fiona/Lou.
- Use `object-fit: contain` and responsive wrappers where appropriate.

## 10. Battle systems architecture direction
Avoid bespoke logic per battle. Move toward:
- centralized `PartyManager`
- centralized battle actor model
- reusable action definitions
- target selection
- KO/revive state
- action queue with eventual SPD ordering
- encounter metadata
- reusable result/EXP handling
- support actor system for Lou
- future BREAK gauge support
- future party split state: Party A / B / C / Reserve / Lou Support

Do not prematurely rewrite stable gameplay in one giant refactor. Migrate incrementally with regression checks.

## 11. Quest/UI rules
Permanent OBJECTIVE/subquest HUDs are obsolete.
- On objective update: transient notice, then disappear.
- Menu contains メインクエスト / サブクエスト tabs.
- Main journal: title, synopsis, current objective.
- Subquest journal: active/completed/objective/reward.
- Dialogue must be frontmost.
- Hide quest/fullscreen/transient notices during dialogue.
- `closeDialogue()` or equivalent cleanup must occur before battle/transitions.

## 12. Field rules
- Top-down/slightly angled classic JRPG field.
- Scrolling maps larger than viewport; camera follows player.
- PC: arrows/WASD + click; Enter for dialogue/interact where applicable.
- Smartphone: tap destination / NPC / object / choice / dialogue.
- No virtual controller.
- OBJECTIVE means the player actually moves/interacts; do not auto-progress objectives.

## 13. Rilde Village (リルド村)
Peaceful Lind is a real explorable place before destruction.
Important locations: Aidan house, inn, shop, elder, training ground, river/bridges.
Opening starts inside Aidan's house beside the bed.
Confirmed side quests:
1. 風に飛ばされた風船 → きずぐすり×2
2. 迷子の猫「ミル」 → 毒消し×2
Peaceful buildings are enterable.
During the attack, main buildings are destroyed/burning/inaccessible and peaceful NPCs must not remain reachable.
Peaceful and burning versions should preserve recognizable layout continuity.

## 14. Moss Forest
Compact ~10-minute dungeon.
- branches/dead ends
- 3 chests
- Lou hidden wind path
- 3 field-symbol goblins
- ancient wind barrier requires 3 abnormal-goblin wins before Lou progression
- barrier must not incorrectly trigger conversation before requirements are met

## 15. Prologue canonical route
「風が止んだ夜」, roughly 15–25 minute vertical slice:
Title → peaceful Rilde → Aidan house → training → Fiona → tutorials → wooden dummy → Fiona joins/heals → sunset hill → wind stops → village attack → Fiona reunion → burning village → 2 abnormal goblins → royal knights → north escape → river fall → Moss Forest → ancient stone/Fiona → Lou appears → altar (goblins surround → Goblin Raider appears → Aidan's father's sword is broken → Lou's support + Fiona's wind dance stall the Raider for a moment → the stone answers and Aidan binds 誓いの剣) → Goblin Raider battle → aftermath/Lou joins → dawn → Dunvar Fortress (starter gear issued, EQUIP menu unlocked) → PROLOGUE END.

Weapon/equipment rules (2026-10-13): Aidan holds his father's sword (the knight commander's) from the start; the wooden sword is used only by the boy swordsman at the training ground. After the contract, Aidan's weapon is fixed to 誓いの剣 (cannot be unequipped/replaced; upgraded later at a smith with special materials). The equipment system is hidden until the prologue ends. Slots: weapon, head, body, accessory x2.

## 16. Development-only tools
Keep an obvious DEV gate.
Current useful dev features include:
- Event Jump
- one-hit kill command for fast battle verification
Do not expose these in final public release.

Canonical Event Jump destinations:
1 Aidan house
2 training/Fiona
3 sunset hill
4 Lind attack
5 Fiona reunion
6 royal knight/north route
7 river escape
8 Moss Forest
9 Lou before
10 altar
11 Raider
12 aftermath/Lou join
13 Dunvar Fortress
14 PROLOGUE END

## 17. Save
Current historical implementation only partially saved growth state.
Target: robust localStorage save for story state, party/growth, inventory, quests, event flags, settings, treasure/one-time states.
Version save data and provide migration/default handling. Never silently destroy an older save during development.

## 18. Known historical hazards
Before changing battle UI, inspect existing source. There have been conflicting accumulated CSS overrides and duplicate/legacy battle elements.
Historical IDs include:
`#aaPanel`, `#ggPanel`, `#battleActors`, `#normalPartyHud`, `#normalActor`, `#normalBattleCmd`, `#battleMsg2` and Raider equivalents.
Do not blindly add another override.
A previous `transform: none !important` blocked attack motion. Root-cause fixes are preferred.
Do not use `nth-child` hacks to hide commands; this previously hid Guard/Item.
Do not reintroduce empty battle log overlays.
Do not let result overlays reveal the wrong field (e.g. peaceful Lind behind a battle result).
Keep destination-first scene transitions.

## 19. Working method
For every implementation request:
1. Inspect current source and identify the real active DOM/CSS/JS path.
2. State a small implementation plan.
3. Change the smallest coherent subsystem.
4. Preserve stable mechanics.
5. Run syntax/basic smoke checks.
6. Test both normal Tainted Goblin and Raider paths when battle code changes.
7. Check desktop + responsive layout.
8. Report changed files and concrete test steps.
9. Do not claim something is fixed unless the code path was actually changed/tested.
10. Prefer commits that are easy to review/revert.

## 20. Product direction
The goal is a polished original indie JRPG portfolio piece, not a school HTML exercise.
Visual identity: ancient Celtic stone tablet × parchment × deep green × antique gold; high-detail anime/painterly battle art; polished pixel-art field; cinematic but readable effects.
Theme: 「守れなかった者たちが、今度こそ誰かを守る」
Tagline: 「失った故郷。残された仲間。そして、風だけが知っていた真実。」

## 21. Agent workflow — GitHub-first, branch-only (2026-11-02 director directive)
This section applies to ChatGPT, Claude, Codex and other agents when working on this repository. Preserve all existing canon, gameplay, visual, and QA requirements above. If a prior workflow instruction conflicts with this section about candidate-branch commits, this later director directive takes precedence **only for nonproduction working branches**.

### Artifact delivery
- Deliver work through commits to the designated `feature/*` branch and purpose-specific directories, not chat ZIPs, binary attachments, or text archives.
- For Phase 2 furniture use `feature/phase2-furniture-assets` and `assets/candidates/phase2/`. Keep original drawings, candidate PNGs, source references, scripts, manifests, and QA evidence clearly separated.
- Report actual branch, full commit SHA, changed paths, test results and remaining blockers concisely. Never claim a push, binary upload, test, or QA result unless verified.
- If the available agent connector cannot upload binary files, report the specific blocker. Do not silently substitute chat ZIP distribution or pretend the file was committed.

### Preapproved working-branch actions
- Agents may independently create/revise candidate PNG assets, scripts, manifests, QA data, in-scope bug fixes, refactors and small layout adjustments **on the assigned working branch**, and commit/push them without asking for each change.
- Inspect active code and scope first; keep changes minimal and reversible. Test relevant desktop and mobile views. Do not overwrite other agents' recent work or approved assets without verification.
- Candidate branch commit permission is not formal asset adoption, production deployment or merge authorization.

### Protected changes requiring explicit director approval
- Never directly modify or commit to `main`; never merge to `main` without explicit authorization.
- Do not alter production map files (including `data/maps/rilde_in_house_01.json`), deployed production assets, or already-approved shared assets without separate explicit authorization, even on a feature branch.
- Do not make fundamental destructive changes to approved lore, worldbuilding, design direction, or gameplay without director approval.
- Formal adoption and production application require human director review and approval after QA. A Claude PASS or automated PASS is necessary evidence, **not by itself adoption authorization**, unless the director expressly delegates that specific adoption decision.

### Communication
- Start implementation immediately when requirements are clear. Avoid greetings, repetitive policy recitations, and approval questions for preapproved actions.
- Use concise evidence-based reports. Explicitly distinguish self-QA, Claude QA, Codex independent QA, emulated mobile layouts and actual Android device checks.
- Do not imply autonomous background work or cross-session memory: agents must read this file at the start of each repository session.

### Scope and rollout
- This file is versioned in the feature branch. Other sessions must open the same branch to inherit this revision.
- Propagating these instructions to `main` or other branches requires separate director authorization and an approved change process; this directive does not authorize a `main` update.

## 🤖 AI Token & Workflow Policy (トークン効率・タスクパケット方式)
1. **タスクパケット方式の徹底:** ワーカー（Claude/Codex）への指示および報告は、挨拶や長文説明を排した極小のメタ情報と指示のみで行う。
2. **トークン極小化:** 挨拶、前置き、過度な解説、まとめの文章（「お疲れ様です」「何か質問は〜」等）は一切禁止。
3. **差分ベースのやり取り:** コード全体の送受信を禁止し、変更対象のファイルパスと該当スニペット（または git diff）のみを扱う。
4. **回答フォーマットの固定:**
   ■ 診断・修正理由（1〜2行で簡潔に）
   - [理由]
   ■ 修正コード（該当部分のみ）

## 自律リトライ原則（Self-Retry Policy）— ソフトリミット版（2026-11-03 ディレクター承認）
- 対象：全ワーカー（Claude/Codex等）およびディレクター補佐（ChatGPT）。アセット制作・コード実装・検証などでエラーや品質未達が発生した場合、報告のみで直ちに停止せず、原因分析・修正・再検証を自律的に行い、採用水準の成果物を目指す。
- **内部リトライのソフトリミットは原則最大3回。** 同一問題に対する初回試行後の再試行を数え、各回で原因・修正・検証結果を確認する。無意味な同一操作の反復は禁止。
- 3回のリトライでも解決しない場合は、無理に継続せず、発生している問題の具体内容・試した対処・残る障害・次の選択肢を簡潔に報告し、人間の判断を仰ぐ。未達の成果をPASSや完了と偽らない。
- **仕様判断不能・承認必須事項・権限不足・安全上の問題がある場合は、リトライ回数にかかわらず直ちに停止し、必要事項のみピンポイントで質問する。**
- 既存の承認範囲・正式採用素材／確定シナリオの保護・main変更／マージの個別承認・FAST-TRACK方針を厳守する。リトライは権限拡張や作業範囲の無断変更を認めない。
- 今後のClaude/Codex向け全タスクパケットおよびChatGPTによる実作業に本原則を適用する。
