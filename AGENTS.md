## MORWEN-CANON-CLEANUP-02 — 2026-11-12 director visual override

- Issue #240 `issuecomment-6822050005` と `docs/design/MORWEN_CANONICAL_INDEX.md` をモルウェン制作参照の最新方針とする。受領ZIPのPNG12枚は `assets/references/morwen/reference_20261112/MANIFEST.json` でSHA保護する **REFERENCE_ONLY** セット。
- 将来の高品質Blender完成版は **FUTURE_CANON_PENDING_APPROVAL**。審査とディレクターの明示承認まで正式採用・本番差替えを行わない。旧v5.61/v3/3方向/HD画像は配置名だけで新正式版にしない。下記の旧ビジュアル正本ロックは、この後発指示が変更した制作参照・保存方針について履歴扱い。
- 設定・年齢・シナリオ・稼働中ゲーム/サイト・必要QA・共有ツールは保護。不要な旧派生物のみ検証して作業ブランチから削除する。mainマージ・公式サイト公開・自動採用・新規リグ生成は禁止。

# CURRENT CANON LOCK — 2026-11-12 (Claude / Codex / ChatGPT)

- **エイダン・フィオナ・モルウェンの公式年齢は全員18歳で固定。** 他人物の年齢は変更しない。過去の誤設定を再採用しない。
- **唯一の現行正典参照先**: private `celticmusic-nagoya/the-windbound-oath-handoff/reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md` の **main最新版**、`reference/lore/CANON_ADDENDUM.md`、`CANON_STATUS.md`。年齢は18歳、同一人物の他設定は後発の正式採用を優先する。
- Claudeを含むすべてのエージェントは**毎タスク開始時**に現行mainの `AGENTS.md` と本書を読み、正典のmain最新版と照合する。旧コミット・バックアップ・アーカイブ・PR・他ブランチ・過去会話・キャッシュの内容は**現行設定の根拠にしない**。履歴は差分調査・回帰確認に限って使用する。
- 作業ブランチが古い場合は最新mainの正典変更を取り込み、同じ設定の再導入を禁止。正典が参照不能なら `CANON_SOURCE_UNAVAILABLE` として設定依存作業をBLOCKEDにし、推測で補完しない。
- 既存画像のSHAロック、採用・未採用区分、他キャラクター設定は保護。年齢訂正だけで未承認アセットを採用しない。ゲーム本体・公式サイトへの公開は個別のQAゲートに従う。

## 2026-11-12 ディレクター正式訂正：モルウェンの年齢
- エイダン・フィオナ・モルウェンは全員**18歳**。旧年齢の記載は現行設定として使用しない。その他のキャラクター設定は変更しない。
- 既存の衣装・表現に関する品質基準、正本ロック、画像SHA保護は継続する。年齢変更は過去画像の自動採用・本体組込みを意味しない。

## モルウェン正本ロック（2026-11-08）
- 唯一の制作デザイン正本はユーザー添付のv5.61比較シート（SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`）。`docs/design/MORWEN_V561_CANONICAL_20261108.md` と `data/morwen-design-canonical.json` を参照。
- 他のv5.x画像・切り出し・清掃・リカラー試作品はすべてSUPERSEDED。ゲーム用RGBA PNGとして正式採用しない。添付はJPEG実体のため、画像シートを48×64透過PNGと誤認しない。

## 2026-11-08 優先変更：モルウェン公式原本HDドット制作
- 頭装備着せ替え用PNG制作は一時保留（設計・基盤は維持）。`docs/qa/MORWEN_PIXEL_MASTER_AUDIT_20261108.md` を参照し、モルウェンの正式v3原本に忠実なドット絵を優先。
- 原本の**短いぱっつんボブ＋大きな紫の魔女帽子**は必須。編み込みロングヘアや帽子なしの画像は不一致として不採用。ニーソックスはディレクターの後発指定。
- 原本照合がFAILの候補を「正式版」と呼ばず、本番スプライトへ登録しない。

## 2026-11-08 将来実装計画：RO風・頭装備着せ替え
- `docs/design/HEADGEAR_LAYER_SYSTEM_20261108.md` を設計正本とする。upper/middle/lowerの3スロット、4方向RGBA、ベースと同一anchor・親transform同期、戦闘/会話差分は将来の任意拡張。
- モルウェンの標準メガネはmiddle候補。正式髪型・ニーソックスと公式原本を保護。未照合のv5.3比較画像は本番採用しない。
- `js/field/field-headgear-layers.js` は**純粋な候補合成ロジック**。本番UI・SAVE・Androidは未接続。アセット未制作で本番切替禁止。

## 最新方針 2026-11-08: 公式デザイン準拠・HDピクセル制作
- `docs/design/FIELD_HD_PIXEL_OFFICIAL_PIPELINE.md` を新規フィールドキャラ素材の最優先制作規約とする。正式採用原本・年齢/役割・公式衣装を保護し、17歳キャラを性的に強調しない。
- 2.8–3.0頭身、現代高精細ピクセル、透明RGBA/方向別統一anchor、32/40/48px表示QA。制作前の比較シートや未検証候補を「正式合致済み」と記録しない。
- 原本を上書きせず `assets/candidates/field-hd-pixel/` に追加、`scripts/qa_field_hd_pixel.py` で候補技術QA。公式画像照合・Android実機は別ゲートで未実施を明示。

## 2026-11-08 ディレクター正式更新：全フィールドビジュアル刷新

**必読・優先:** [FIELD_VISUAL_OVERHAUL_20261108.md](docs/design/FIELD_VISUAL_OVERHAUL_20261108.md)。本規約はPC・同行者・NPC・敵・妖精・建物・地形の全フィールド要素に適用。フィールドキャラはRO風の独自ドット絵（人型約2.8頭身）、各方向の基本静止画＋JS/CSSバウンス/遅延揺れ/敵パルス。フィールドは25°〜30°のクォータービュー、重厚なペイント背景。高精細の戦闘・イベントCGと正式採用デザインは保護する。

**旧歩行アニメーション候補PR #139/#140/#144/#145/#153/#154は保留。** 新方式の品質・互換性検証が完了するまで、マージ・削除・正式採用への格上げをしない。不要になった場合のみ証跡と依存関係を確認して整理する。現行本番スプライトを即時撤去しない。

**実行方針:** 通常の実装・テスト・マージはAuto-Pilot。停止確認は不可逆データ損失・重大なセキュリティ問題・根幹仕様の重大な二択に限る。品質ゲートが未PASSなら自律修正またはBLOCKED報告とし、成功を偽らない。古い「3回で必ず停止」「mainへの個別承認」などの記載より、この最新ディレクター方針を優先する。

# AGENTS.md — THE WINDBOUND OATH / Mionn na Gaoithe

## 0. Official lore master (canon reference)
- The canon for world, story, characters and dialogue is 「THE WINDBOUND OATH 公式統合設定資料集 v5.0」(2026-10-19), (historical SHA no longer valid after director-authorized v5.0 correction). The full text is **not stored in this public repository**; it is kept in the private handoff repository (`celticmusic-nagoya/the-windbound-oath-handoff`, `reference/lore/`). Access must be granted by the user. See `docs/lore/README.md`.
- If you cannot read it, **do not reconstruct or guess it**: report `LORE_INACCESSIBLE` (what you tried and the error), ask the user to grant read access (how: `docs/lore/README.md`), and leave lore-dependent details unchanged.
- Priority: later explicit user adoption > formal addenda (`CANON_ADDENDUM.md`, private) > v5.0 latest addenda > the rest of v5.0 > archived older versions (history only) > proposals. Do not read the original alone: the addenda and status table are in the same private directory. Keep the labels 確定 / 脚本採用案 / 未決定 / 撤回 / 要コード照合 exactly; never promote candidates or undecided items to 確定 without the user.
- 設定確定 is not 実装済み: verify implementation with current main code, Git history and tests. Do not promote numbers found in code to official settings, and do not change existing scenario, dialogue, character design or balance on the strength of the lore text alone.
- Adopted changes are managed in the private canon repository. The director explicitly authorized correcting the original v5.0 age in place; use the latest main version plus addenda. Do not independently rewrite other original lore.
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
18, human swordsman, knight commander's son.
Brown tousled hair, green eyes, forest/deep green + ivory + antique gold armor/clothing.
Weapon: 誓いの剣.
Physical / TP-oriented.
Final battle art is the standalone transparent asset, not an old composite crop.

### Fiona / フィオナ
18, human healer from Rilde Village (リルド村).
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
18, top-ranked student at the Royal Magic Academy (王立魔法学院), and a reserved black mage.
Her officially approved v3.0 design is the academy uniform; preserve the existing character artwork and black/navy/purple + antique gold palette, long dark hair, and violet eyes.
The Royal Magic Research Institute (王立魔法研究院) is a separate research institution located alongside the academy. Morwen's admired mentor, Edric Vane (エドリック・ヴェイン), belongs to the institute; retain his existing story arc without inventing new details.
Highest MAG; Resonance system 0–3.
Canon: private handoff repository `reference/lore/CANON_ADDENDUM.md` ADD-002 (2026-11-06). Original v5.0 has been corrected by director instruction; use its latest main text and the later addenda.

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

## 🤖 Autonomous Execution & Auto-Merge Policy (自律実行・自動マージ規約)

本プロジェクトにおいて、Claude/Codexエージェントは、速度と効率を最大化するため、原則として**「事前承認なしの自律進行（Auto-Pilot）」**で作業を完結させます。

### 1. 基本原則（Default Autonomy）
- ユーザーからの指示・バグ報告・機能追加の依頼に対し、途中で「こう進めても良いですか？」といった**確認や許可を求める質問を禁止**します。
- 示された要件に基づき、思考・実装・コード修正・テストの実行までをワンストップで自律的にやり切ってください。

### 2. 自動マージのスコープ（Auto-Merge to Main）
- 実装が完了し、静的解析（TypeScriptコンパイル等）およびテスト（存在する場合）をパスした成果物は、ローカルでの検証を経て、**原則として `main` ブランチへのコミットおよびマージまでを自動的に完了**させてください。
- 作業完了時の報告は、「何を確認したか」の長い解説を省き、**「修正完了・mainマージ済み（変更ファイルの概要と次の推奨タスク1点）」**のみを簡潔に出力してください。

### 3. セルフリトライの義務（Self-Correction on Failure）
- ビルドエラー、テスト失敗、または採用品質に至らない不具合に直面した場合でも、**途中で作業を止めてユーザーに途中経過を報告せず、ログを解析して自律的に原因を修正・再試行**してください。
- 試行を重ねても解決しない場合や、次項の「例外」に該当する場合にのみ、作業を中断して質問を許可します。

### 4. 例外：確認を必須とするケース（Stop & Ask Triggers）
以下の「致命的な破壊リスク」に該当する場合のみ、自動進行をストップし、ユーザーに確認を求めてください。
1. **不可逆的なデータ損失のリスク:** データベースの破壊、既存データの消失、不可逆なファイル構造の全削除。
2. **セキュリティ上の重大な懸念:** APIキーや認証情報のハードコード、外部への意図しないデータ送信の危険性。
3. **仕様上の重大な二択:** アーキテクチャの根幹に関わるトレードオフが発生し、どちらを選ぶかでゲームの基本設計が完全に変わってしまう場合。

### 適用優先順位
- 本節はディレクターの最新の明示指示として、上記の旧「mainへの個別承認」「承認後マージ」「リトライ時の逐次報告」規定と抵触する場合に優先する。
- 既存の正式採用素材・確定シナリオ・SAVE互換性の保護義務は維持する。変更範囲外の破壊的操作を許可するものではない。

## 🤖 Autonomous Game Development Protocol v1.0 — 全領域統合参照（2026-11-11）

- **適用範囲:** シナリオ／世界観、ゲームシステム、UI/UX、演出、実装、アセット、QA。詳細正本: [AUTONOMOUS_GAME_DEVELOPMENT_PROTOCOL_v1.0.md](docs/policy/AUTONOMOUS_GAME_DEVELOPMENT_PROTOCOL_v1.0.md)。
- **シナリオ:** 会話・イベント・フラグを既存エンジンと互換なJSON/YAML等でモジュール化し、採用済み台詞・イベント順序・世界観の正本を保護する。非公開正本にアクセスできない場合は推測で補完しない。
- **システム:** コアループの最小検証可能単位を優先。既存設計を確認してからデータ駆動化し、SAVE互換性と既存のゲームバランスを守る。
- **UI/UX・演出:** レイアウト／グリッド／情報階層を先に固定し、視認性、スマホ操作、レスポンシブ、アクセシビリティを検証。カメラシェイク、ヒットストップ、音同期は設定可能な演出層として実装し、動きを減らす設定を尊重する。
- **アセット:** [CHARACTER_ASSET_GENERATION_GUIDE_v1.2.md](docs/policy/CHARACTER_ASSET_GENERATION_GUIDE_v1.2.md) を参照。素体とアンカー固定→全身マスターキャンバス→衣装レイヤリング→独立QA。原本を上書きしない。
- **タスクパケット:** TASK ID、対象Issue/PR、基準コミット、参照仕様ID、変更対象、成功条件、保護対象、検証方法、停止条件を短く記述。差分中心・小さな機能単位で実装し、実際のソースと仕様を必ず照合する。
- **自律QA:** テスト→原因分析→最小パッチ→再テスト。自己QAと独立QAを区別し、未実施をPASSと記録しない。失敗の無限反復は禁止。
- **既存規約との整合:** この節は既存のAuto-Pilot／Auto-Merge Policy、2026-11-08優先変更、Self-Retry Policyを上書きしない。マージ判断は既存の最新Auto-Merge Policyに従い、同ポリシーに列挙された停止条件および正式設定・素材・SAVE保護を守る。再試行は既存のソフトリミット（原則最大3回）を優先し、2回は推奨早期レビューの目安とする。タスク固有の明示的な禁止（例: PR #221の正式アセット採用・公開・本番統合保留）は維持する。
- **成果物:** 変更ファイル、検証証拠、既知のFAIL/BLOCKED/NOT_RUN、次の推奨タスクを記録。実際に実施していないpush・マージ・Android実機確認を完了と報告しない。


## Asset Generation Loop Prevention & Forward-Only Protocol (2026-11-11)

Scope: character/background/UI assets, sprites, masks, reference sheets, and image QA. This is a stricter asset-specific rule that complements the existing Self-Retry and Auto-Pilot policies.

1. **No blind repetition.** Every generation must be followed by an inspection of the actual result and a concise record of the delta from the canonical design. Never repeat a nearly identical prompt without an identified changed condition.
2. **Analyze after two failed attempts.** Before a third attempt on the same asset/defect, document the structural cause (orientation, occlusion, layers, anatomy, anchors, palette, or model limitations) and change the method rather than merely rewording the prompt.
3. **Three attempts maximum for the same defect.** Count the initial generation and subsequent corrections together. After three unsuccessful attempts, STOP that generation approach. Offer at least two alternatives such as component-level editing and manual retouching. This asset-specific cap is stricter than the general retry soft limit. Do not reset the counter through trivial prompt changes.
4. **Lock approved design decisions.** Explicit director approval marks the specified *design decision* DONE/LOCKED. A later explicit director change supersedes it. Design approval does not imply that the PNG has passed transparency, anchor, hash, independent QA, or device testing.
5. **Forward-only deliverables.** Prioritize the next real output (individual transparent PNG, comparison against original, QA evidence, integration) over recreating overview sheets. Fix minor visual discrepancies as part of the next production step without reopening accepted design decisions.
6. **Emergency recovery.** On detecting a loop, state STOP, show the expected-versus-actual delta and attempt count, identify the cause, provide two actionable alternative approaches, and proceed only with a changed method. Do not silently resume the same generation.
7. **Evidence.** Track asset ID, canonical reference, attempt count, structural analysis, observed delta, QA status, and next deliverable. Preserve originals. Report blocked/unrun work accurately.

Precedence: this section governs asset-generation attempt counting and forward progress. It does not waive repository safety rules, canonical asset protection, task-specific prohibitions on publishing or merging, or existing approval gates.
