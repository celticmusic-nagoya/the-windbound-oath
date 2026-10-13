# Codex 指示 GG〜KK (2026-10-13 夜) — BB〜FF / X〜Z 納品後の追加分
基準: 最新main(169f197以降)。standing-orders に従う。**js/・css/・index.html・採用素材は変更しない**(tests / tools / docs のみ)。不具合は直さず、再現手順つきで報告。
前提の新機能(本日main反映): (1)PCキーボード完全対応 `js/input-manager.js`(状態: FIELD/DIALOGUE/SCENE/MENU/BATTLE_COMMAND/BATTLE_SUBMENU/BATTLE_TARGET/BATTLE_ANIMATION/RESULT、`InputManager.state()`)と既存 `tests/input/kb_*.py` 5本 (2)フィールドのルー追従 `#forestLou`(`PartyManager.support.joined` 後のみ表示、`js/field/moss-forest-runtime.js` の `updateLou`)、`tests/moss/m32_lou_follower.py` (3)ルー戦闘待機ループが `prefers-reduced-motion` を無視する修正。

## GG: キーボード操作の独立QA(網羅と競合)
`tests/input/kb_audit.py` を新規。既存 kb_* が見ていない面を確認する。
- 画面網羅: クエスト手帳(Q / `#questMenu`)、ショップ(リルド/ドゥンヴァル)、宿屋、旧世界の `.npc/.door/.furn` の Enter 操作、各シーン(`#cinema,#returnScene,#escapeScene,#louIntroScene,#altarScene,#aftermathScene,#fortScene,#prologueEnd`)、マップ遷移フェード中、戦闘開始バナー中。
- ブラウザ既定動作の競合: Space でページがスクロールしない / Tab でフォーカスが画面外(アドレスバー等)へ逃げない(メニュー・戦闘中)/ 入力欄(`input,textarea`)にフォーカス中はショートカット(M,Q,E,Enter,Space)が発火しない。
- 二重実行監査: Enter/Space を連打・長押し(`keyboard.down` 連発)・同一フレーム2回で、戦闘行動・アイテム消費・宝箱・会話ページ・セーブが2回走らないこと(カウンタ/状態で検証)。
- スタック入力: キー押下中に blur / メニューを開く / 戦闘突入 / シーン開始 → キー解除後に移動が止まる(押しっぱなし移動が残らない)。
- 非退行: モバイル emulation(`is_mobile=True, has_touch=True`、390x844 と 844x390)で COMMAND が自動展開されない(従来のタップ展開)/ `body.kbNav` が付かない / タップ操作が従来通り。
- 成果: テスト、`docs/qa/keyboard-audit-20261013.md`(未対応の画面・再現手順・重大度)。

## HH: フィールドのルー追従の検品と軽量化案
- 表示条件: 合流前は非表示、合流後に表示、屋内マップ(`story.interior`)では非表示、マップ遷移・`FieldChoreo` 演出・戦闘突入/復帰・セーブ/ロード後に位置が飛ぶ/チラつく/Aidan・Fiona と重なって不自然にならないか。`?feature=heightSpecs` 有効時の持ち上げ(lift)も。
- 性能: 現状は 442x724 PNG ×6 を 52px 表示。`tools/field/make_lou_field_frames.py`(新規)で field 用の縮小版(例: 高さ 2 倍表示で ~120px、足元/胴体アンカーはバトルと同じ基準)を `/tmp` または `docs/art/proposals/lou_field/` に生成し、読込量(KB)・decode 時間・`m19_perf.py` 系フレーム時間を現状と比較。**採用はせず提案のみ**。
- 追従オフセット(後方 2.4 倍・浮遊 22px)の見た目スクショ(PC / 縦 / 横)を `docs/qa/lou-field-20261013/` に。
- 成果: テスト追加(m32 の拡張可)、`docs/qa/lou-field-review-20261013.md`。

## II: ルー戦闘待機が止まる件の実フロー切り分け
実機で「ルーが1枚絵のまま」との報告。端末のモーション軽減設定は修正済みだが、他経路の有無を確認する。
- `devJump('raider')` ではなく**自然な流れ**(祭壇シーン→`startRaiderBattle`)で、`BattleIdleMotion.status` と `document.body.className`(`dialogueOpen` / `battlePresentationBusy` / `actionCinematic`)、`canvas.dataset.frame` を 250ms 間隔で時系列ログ化。バトル開始〜最初のコマンド入力〜敵ターン〜被弾まで、ルーが「paused 扱いで固まる」区間がないか。
- 固まる区間があれば原因(どのクラスがいつ付きっぱなしか)を特定。コード修正はせず提案。
- 成果: `tests/battle/lou_idle_real_flow.py`、`docs/qa/lou-idle-real-flow-20261013.md`。

## JJ: テスト安定化(tests のみ)
- `tests/moss/m31_aidan_heading.py` が時々「straight up uses walk_up」で落ちる(直前の歩行からの停止待ちのタイミング依存)。原因を特定し、待機を状態ベース(歩行状態が IDLE になるまで)にして安定化。20回連続実行で確認。
- 開始直後の会話メッセージ(キーボード対応後は会話中に移動不可)に依存する既存テストがないか全テストを走査し、`closeDialogue()` 等の前置きが必要なものを修正。
- 成果: 修正と、20回連続結果のログ。

## KK: スマホで COMMAND を初期展開すべきかの判断材料
仕様は「COMMAND初期展開」だが、現状は PC(`hover:hover` かつ `pointer:fine`)のみ自動展開、スマホは従来のタップ展開。ユーザー判断用の資料を作る。
- 縦(390x844)・横(844x390)・小型(360x640)で通常戦闘・ボス戦の COMMAND 展開時/折りたたみ時のスクリーンショットを撮り、戦場(敵・味方スプライト)の可視面積が何%遮られるか、ボタンのタップ領域(44px 基準)を計測。
- 「展開」「折りたたみ+小さな常設ボタン」「縦は展開・横は折りたたみ」の3案を比較し推奨を1つ。
- 成果: `docs/qa/command-initial-open-mobile-20261013.md`(数値と画像つき)。js変更は不要(提案のみ)。

## 報告
各項目完了ごとに `codex-status.md` を更新して通常push(`work/codex-gg-kk`)。利用制限で止まったら wip コミット。最終コミット、テスト結果、未解決点を報告。
