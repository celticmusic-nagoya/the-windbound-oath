# ファイル担当・進捗索引

> 2026-10-12 main反映記録（Codex・作者G承認）: 機能merge `390f74aea90e449a50846e93496abc5b7be99632`、直前main `c4c536aad49bfa6d94ffbf79b951767627ee10ea`、rollbackタグ `rollback/before-quality-foundation-20261012`。全52対象合格確認（初回待機1件は修正/再実行）、最新m6_quest単独10連続合格。PLAYER QA待ち。戻し方: `git revert -m 1 390f74aea90e449a50846e93496abc5b7be99632`。詳細: `docs/handoff/codex-quality-main-integration-20261012.md`。

着手前にブランチと対象を追記する。別ブランチの記録もfetchして確認する。下記はCodex側の記録であり、Claudeの担当を予約しない。

| 担当 | ブランチ | 対象 | 状態 |
|---|---|---|---|
| Codex | work/codex-collaboration-rules | docs/handoff/COLLABORATION.md、CLAIMS.md、codex-collaboration-rules.md | READY: 運用資料のみ |
| Codex | work/codex-quality-foundation | 品質G: field-movement、tests、docs/art、docs/qa等（各branchの差分参照） | 開始基準でテスト合格、最新main再検証待ち |
| Codex | work/codex-loading-cg | docs/art/loading-cg/ | BLOCKED: 画像生成API利用上限、画像0枚 |
| Codex | work/codex-raider-mobile-layout | css/raider-mobile-layout.css、js/battle-party-layout.js、tests/battle/raider_mobile_layout.py、docs/qa/raider-mobile-layout/ | 開始基準でテスト合格、最新main再検証待ち |

Raiderブランチの既存index.html差分は、この新運用の受領前に作成済み（CSS link追加とscript cache query）。以降の直接編集は行わず、統合前にClaudeへ変更依頼として共有する。開始基準はe3565b6で、新main 0914263での再検証はまだ実施していない。
旧Codex Phase3は不採用。採用済みのClaude版へ旧素材・コードを戻さない。

## 承認済みRaider統合

Codex / `work/codex-raider-mobile-integration` / 基準main `0914263`。
対象: `8ac09e6` のCSS・BattlePartyLayout・テスト・QA資料、およびindexのCSS link／script cache queryだけ。作者がRaider修正を全承認済みのため、この限定index変更も統合する。Claudeのstory・field・納品motionは変更しない。
STATUS: READY — 最新main 0914263上で再検証完了。作者承認に基づきmainへ通常pushする。

## Claude: フィールド敵AI／シンボルエンカウント（PLAYER QA待ち）

Claude / `work/moss-slime-symbol-encounter` / 基準main `57dc6ae`。
対象: `js/field/field-monsters.js`（新規）、`moss-forest-runtime.js`（FieldMonsters接続・歩数エンカウント既定OFF）、`moss-forest-story.js`（onMonster）、`index.html`（script追加・撃破後resolve）、A1 JSON `monsters`（スライム2体）、`tests/moss/m15b_slime_symbol.py`。
STATUS: PLAYER QA待ち。作者承認までmainへmergeしない。モススライム／ゴブリンの速度等は `MONSTER_TYPES` の1か所で調整可能。

Claude / `work/forest-bat-symbol-encounter`（上記ブランチの上に積む）: フォレストバット（吸血・飛行シンボル、A2）。`work/leafy-boar-symbol-encounter`（さらにその上）: リーフィボア（突進シンボル、街道）。いずれもPLAYER QA待ち・main未merge。

## main反映記録


- 2026-10-12 Claude: フィールドモンスター一式（スライム/ゴブリン型AI・フォレストバット・リーフィボア）をmainへ `--no-ff` merge。ロールバック: タグ `rollback/before-field-monsters-20261012`（= 57dc6ae）、または該当マージコミットを `git revert -m 1`。PLAYER QA待ち。
- 2026-10-12 Claude: `work/battle-feel-and-monster-layout` — 戦闘演出（近接は選択敵位置へ飛び込み／フィオナは少し前進+魔弾／ルーの飛び回り+浮き沈み `js/battle-lou-flight.js`／カットイン `battle-presentation.js` durations 1250/2000ms・勝利ポーズ `VICTORY_POSE_MS=2400`）と、A1（スライム2・ボア2・ゴブリン2）／A2（スライム2・ボア2・バット2）配置、通常ゴブリンのフィールド戦闘接続（`fieldGobN`）。対象: index.html（WBActors v064/v066・finish）、js/battle-presentation.js、js/prologue-combat.js、js/field/moss-forest-story.js、css/battle-presentation.css、A1/A2 JSON、tests/moss/m16_battle_feel.py。
## 依頼G移植(Claude, 2026-10-11)

Claude / `work/claude-port-quality-foundation` / 基準main `9b17d06`。
対象: Codex `work/codex-quality-foundation` の3コミット(59d0ce4 dae453c e89a936)を cherry-pick(衝突なし)。`field-movement.js`(frameScale下限)、`tests/run_all.sh`、`tests/run_python.py`、m55_hz、m6_quest、素材棚卸し資料。
共存確認: 長押し移動(`moss-forest-runtime.js` の hold / `hooks.onTransition`)は `FieldMovement.frameScale` を直接参照せず、`FieldNavigation.follow` を使うため変更なし。m14_hold_move と m55_hz が両方合格。Raider修正・納品戦闘モーションも維持。
全回帰(`./tests/run_all.sh`, 最新main+移植): **47件中46件合格**。`tests/lind/walk_intake.py` は全件実行時のみ一度失敗(負荷時のタイミング依存)し、単独再実行で合格。m6_quest は合格(Codexの修正による)。
STATUS: READY — 作者承認後に main へ。

## Codex: 依頼G再検証・m6_quest安定化 (2026-10-12)

Codex / `work/codex-quality-revalidation` / G基準 `65bf6d8`、main基準 `57dc6ae`。
対象: `tests/moss/m6_quest.py`、必要な回帰テスト、`docs/handoff/CLAIMS.md`、専用検証報告・QA結果。
STATUS: WIP — 最新mainとの統合候補をこのブランチで検証。mainへのmergeは作者承認後。
Claude `work/moss-slime-symbol-encounter` (`f80019e`) → `work/forest-bat-symbol-encounter` (`3259741`) → `work/leafy-boar-symbol-encounter` (`8baa264`) は積み重ねたPLAYER QA待ちブランチ。既存field-monsters/runtime/story/indexの担当変更は行わず、Gとの共存だけを検証する。
素材候補は別 `work/codex-art-redelivery-20261012` の `docs/art/` に保存予定。正式採用素材の置換・ゲームへの組み込みなし。

共存実行検証用 `work/codex-quality-symbol-validation` を本検証ブランチから作成予定。`8baa264` を仮統合し、CLAIMSの追記を双方保持して解決する。ゲームコードは担当差分をそのまま保持し、長押し・速度・王都遷移ゲート・m6_quest・敵3種・Raiderの既存テストで確認する。main統合候補とは別ブランチで、PLAYER QA承認済みとは扱わない。

2026-10-12 checkpoint: `f6f08bd` でm6_questのテスト側待機を安定化。修正前4回は今回すべて合格（申告の確率は今回未再現）、修正後10回連続合格。最新main+Gの全回帰は進行中。画像はHTTP429利用上限で0枚（専用報告参照）。王都出口IDは作者回答により未確定/TBD維持。Android実機は未接続・未測定、計測手順を保存（`docs/qa/android-symbol-performance-20261012.md`）。

依頼Cの3出口のtoMap/toSpawnとJSON存在確認は `docs/handoff/codex-capital-exit-receivers-20261012.md`。取得済み全リモートrefで受け側JSON未作成を確認。TBD/nullを維持し、マップJSON作成後に接続する。

2026-10-12更新: fetchでmain `b75a805`（敵3種merge済み、新運用第6節）を確認。`work/codex-quality-symbol-validation` は未作成のまま取り止め、最新mainから `work/codex-quality-main-20261012` を作成してGと本検証差分をmergeし、全回帰を再実行する。対象は本行の担当範囲・CLAIMSの双方追記解決・検証記録。旧mainの結果も保持。作者の依頼は統合可否の判断であり、この段階でmain更新・タグ作成・deployはしない。PLAYER QAはmain反映後という新ルールを最終報告に反映する。

旧main `57dc6ae` + Gの全48対象を実行。初回45合格/依存不足3失敗、Pillow/NumPy追加後に3/3再実行合格。未説明の失敗なし。Raider・納品済みmotion・長押し・遷移ゲート・移動速度・クエストを確認。結果は `docs/qa/quality-revalidation-results/`。最新main `b75a805`候補の回帰へ継続。

Codex / `work/codex-quality-main-20261012` / 基準main `b75a805`。G・m6_questテスト修正・報告を `work/codex-quality-revalidation` からmerge。唯一の競合である本ファイルはClaude/main反映記録とCodex追記を双方保持。STATUS: WIP — 全回帰実行中。敵3種はmain反映済みのため旧「未merge」の記録は過去状態。今後のPLAYER QAはCOLLABORATION第6節に従いmain反映後。今回のGは作者による統合可否判断待ちでmainは更新しない。

## Codex最終結果 (2026-10-12)

`work/codex-quality-main-20261012` / 基準main `b75a805582f076c6a8ceb67fd1bf9d5c75769e53` / 検証用merge `c5c3da2`。STATUS: READY — 最新main+Gの全回帰 **51/51合格**、最新候補でm6_quest単独 **10回連続合格**。敵3枝とのcode競合なし（CLAIMS追記のみ双方保持）、長押し・onTransition・速度・Raider・納品済みmotion・ストーリー/クエスト/セーブを維持。最終fetchでもmainの更新なし。

依頼Gは品質修正として新ルールの統合対象にできると判断。統合推奨は元の `65bf6d8` 単独でなく、m6安定化と最新mainを含む本候補。今回mainへmerge/pushは行っておらず、タグも未作成。作者の統合判断待ち。報告と戻し方は `docs/handoff/codex-quality-revalidation-20261012.md`、試験結果は `docs/qa/quality-revalidation-results/`。

残項目: 画像API HTTP429利用上限で生成0枚。王都3出口の受け側JSONなし/TBD維持。Android実機未測定（計測手順・静的バット素材サイズを保存）。PLAYER QAはmain反映後に、敵の探知/追跡、ボア0.6秒予備動作/1.4秒硬直の回避、バット吸血60%、スマホ負荷、長押し/高Hz移動、Raider/motion、クエストを確認。ゲーム側の数値調整・素材置換なし。

## Codex: 依頼G承認後の統合 (2026-10-12)

作者が依頼Gを承認。Codex / `work/codex-quality-approved-20261012` / 基準main `c4c536aad49bfa6d94ffbf79b951767627ee10ea`。
対象: 承認済み `work/codex-quality-main-20261012` (`8465915`) のG/m6_quest修正・CLAIMS/報告/QA結果。CLAIMSの競合は双方の記録を保持。新しい戦闘演出・A1/A2配置・納品素材はそのまま保持。
STATUS: WIP — 最新mainとの統合後に全52本を再検証し、rollbackタグを直前mainへ付けて `--no-ff` でmainへ通常pushする。force pushなし。

全52本の初回は51合格・`tests/moss/m8_town_maps.py` の街道→王都待機が1件失敗。main未更新。担当追加: 同テストの待機・失敗時診断（assertion/ゲーム仕様は維持）。短い専用ゲート検証は合格し、長距離経路の固定30秒待機を負荷再現で診断中。原因を確認して該当回帰を再実行後に反映する。

統合前最終結果: CPU負荷模擬で30秒時点の正常歩行継続・約51秒後の正常王都遷移を確認し、待機不足を再現。m8の実遷移待機を90秒/操作可能状態までとし、期限超過は明示的に失敗、診断を出す。ゲーム側変更なし。m8/王都加入ゲート/新戦闘演出の再実行3/3合格、最終m8再実行+最新候補のm6_quest単独10回で11/11合格。全52対象に合格結果が揃い、mainへの反映準備完了。ロールバックタグ予定名 `rollback/before-quality-foundation-20261012`、直前main `c4c536a`。

- 2026-10-12 Claude: bat layout / DEV monster arena (`map:dev_monster_arena`, monsters x3, A1/A2 goblins, A3 bat/slime/boar) / Aidan+Fiona new walk art merged to main. Rollbacks: `rollback/before-bat-layout-20261012`, `rollback/before-new-walk-20261012`, `rollback/before-dev-arena-20261012`.

## Codex: 納品モス素材の統合後検証 (2026-10-12)

ブランチ: `work/codex-moss-delivered-art-verification`。基準main `ce2b366`（素材merge済み）。対象: `docs/field/moss-forest-asset-requests.md`、本CLAIMS、専用報告・QA記録。指定8テストを順次実行、外部スクリプトで9座標/結界4状態を確認。画像差し替え・ゲーム仕様変更なし。STATUS: WIP。既存merge `ce2b366` と退避branch `rollback/pre-moss-delivered-art` (`0372ef6`) を確認。

納品検証checkpoint: 指定8本の初回7合格/スライム逃走距離1失敗。納品前mainのスライムは合格、納品後単独再実行でも逃走距離が不足したため未解決として調査中。コンソールエラーは各browserテスト0。m14_hold_moveとwalk_a1は -u 実行で出力/合格を確認。素材やゲーム仕様の変更なし。mainへの資料統合は原因解決後。

担当追加: `tests/moss/m15b_slime_symbol.py`。外部診断で徘徊座標由来の退避先がblocked-destination、goFeet=false、移動0のまま接触を再現。テスト側のみ、衝突なし/到達可能な退避地点と移動受付の明示確認へ修正する。距離/無接触のassertionを維持。ゲームAI/速度/衝突/素材は変更しない。最新mainの当たり判定/横歩行/文言変更を取り込んで指定8本を再検証する。

最新main `35834dd` を取り込み。m15bは明確なblocked-destinationを修正したテスト入力で単独合格（5秒後gap693、console0）。修正commit `9dbb274`。元5秒/350px/接触0を維持し、追加assertionは退避経路/追跡/受付。現在指定8本を順番どおり再実行中。任意4本は旧基準ce2b366で合格。新mainのFiona台詞変更とm4旧期待値の不一致を発見し、作業3指定に従い期待値更新を作者へ確認中（まだ変更なし）。

最終結果: `9dbb274` / 基準main `35834dd` で指定8本を順に実行、8/8合格・失敗0・browser console0。m15bの5秒後gap701。テスト入力の衝突問題を解決しゲーム変更なし。素材依頼一覧は未納品3点のみ。9座標の納品前後比較と結界4状態を保存。STATUS: READY — 退避branch作成後に資料/テスト修正をno-ffでmainへ統合。任意m4の新台詞期待値更新は未回答/未修正。

最終mainは `499f781`（35834ddから追加シナリオ資料のみ）を取り込み、検証時のアプリ/tests treeと同一を確認。結界は画像3種と開放後node0を再撮影/console0。正面の石/紋様との重なりで違いが読みづらい点を追記。追加統合の退避先は `rollback/pre-moss-delivered-art-verification`（直前499f781）。素材退避branch `rollback/pre-moss-delivered-art`（0372ef6）は保持。mainへno-ff統合後PLAYER QA。

2026-10-12 main反映記録: 機能merge件名 `Merge delivered moss art verification and pending asset list`。基準main499f781、指定8/8・console0。m15b入力修正と未納品一覧/証跡をno-ffで反映、PLAYER QA待ち。追加分の退避branch `rollback/pre-moss-delivered-art-verification` は499f781。素材本体の既存mergece2b366/退避0372ef6は保持。追加分だけは本mergeをrevert、素材全体は本merge→ce2b366の順でrevert。force pushなし。

## Codex: 剣設定の影響調査・差分案 (2026-10-12)

ブランチ `work/codex-sword-setting`、基準main `0d48324`、引継 `docs/codex-sword-handoff` (`1b3b248`)。担当は本CLAIMSと `docs/handoff/codex-sword-proposal-20261012.md`、同差分 `.patch`。Gは調査のみ、Hは未適用の差分案として提示。Claude所有のindex.htmlは直接編集せず差分で共有。高さ・採用素材・シナリオ・セーブ形式は変更しない。mainへマージしない。STATUS: WIP。

剣設定checkpoint: G影響表とHの未適用patchを完成。対象6ファイルの案をリポジトリ外で展開し、装備テスト2/2合格・console0、旧木剣セーブ移行/原本維持/再保存冪等性/v30維持を確認。git apply --checkとNode移行検証合格。仮IDfather_sword、補正0、物語/高さ/採用素材/セーブ形式は変更なし。main 0d48324は維持。STATUS: READY（差分案のレビュー待ち、未適用・未統合）。

## Codex: 常設運用と高さ設計 (2026-10-13)

`work/codex-standing-orders`、基準main058cfc8。本status初回作成、既存CLAIMS追記、新規height-contact-review-20261013.md/map-height-plan-20261013.mdのみ。優先1/2の調査と設計まで、実装はClaude。担当宣言はcodex-status.mdに記録。ゲーム/マップ/テスト/素材未編集・mainマージなし。STATUS: WIP。

常設運用checkpoint: status初回2f4367aをpush。優先1の接触レベル設計/14テスト案と優先2の30JSON高さ計画を完成。最新mainでDEV map追加を確認、本編28はheight無し。敵移動のplayer-level依存、pending発火前commit、once/latch副作用前再確認、connector中間の面契約を要判断として共有。コード/マップ/テストは未変更、全30JSON parse/ID重複/DEVのみheight検査合格。STATUS: READY（資料納品、実装/動的回帰/Android未実施）。mainマージなし。本statusのmain反映はClaudeへ引継ぐ。

追加承認checkpoint: ユーザーの「GitHubのClaude指示を取得して積極着手」をstatusへ記録しecfcb7aでpush。remote再取得・main058cfc8を確認。優先3の文面短縮案と新規QA画像/JSONを追加。3ページの案を実DOMだけでpreviewし縦3→2行・横1行、pageerror0、原altarLines/誓い不変を確認。index等未変更/未適用、全回帰/Android未実施。STATUS: READY（提案納品、採用は要判断）。

Codex N着手: work/codex-wind-dance-sim / main53180f3。status宣言の新規simと報告のみ。L/M/接触設計の再作業なし、ゲーム数値未適用。STATUS WIP。

Codex Q: work/codex-q / main88ae6c0。上記statusの1部屋spawn小修正/生成元/新規回帰を担当。sy以外のmap再レイアウトなし。STATUS WIP。
