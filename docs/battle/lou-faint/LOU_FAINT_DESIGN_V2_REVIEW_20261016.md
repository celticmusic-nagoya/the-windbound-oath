# ルー気絶・ランダム復帰 設計 v2 差分とCodex設計レビュー用資料（コード変更なし）
前版: LOU_FAINT_DESIGN_FINAL_20261016.md（v1）。本書はv1からの差分と、レビュー対象・テスト手順。製品コード/テストコード変更・commit/push/PR/merge は未実施。実装着手は次の承認待ち。

## 差分1：ルー専用の独立疑似乱数生成器（v1「既定 Math.random」を撤回）
### 設計
- 生成器: **mulberry32**（32bit状態、約10行、外部依存なし、`Math.random`を一切呼ばない）。
- 乱数源は `js/battle-lou-faint.js` 内部に閉じ、**唯一の引き口 `next()`**（[0,1)）のみ。回避(`BattleStatus.dodges`)・会心(`BattleCritical`)・ルー飛行(`battle-lou-flight.js`)とは状態を共有しない。
- **初期化/シード**: 戦闘開始ごとに `reset()` が `crypto.getRandomValues(Uint32Array(1))` で新シードを得て生成器を作る（crypto不可時は `Date.now()^performance.now()` のハッシュにフォールバック。いずれも `Math.random` 不使用）。
- **戦闘再開始時**: `startRaiderBattle`/`beginRaider` から必ず `reset()`。時間巻き戻しによるやり直しも同じ経路なので、毎回**新しいシード**（同じ運命の繰り返しを避ける）。ゲーム状態として保存しない（セーブ形式不変）。draws カウンタも0に戻す。
- **テスト時の固定（`WINDBOUND_DEV` のときのみ有効。製品では no-op で false を返す）**:
  - `fixSeed(n)`: 固定シード。以後**戦闘開始のたびに同じシードで再初期化**＝再開始後も同一列が再現される。
  - `setScript([v1,v2,…])`: 値を順に返す台本（境界値 0.329/0.33/0.49/0.5/0.999 の検証用）。台本を使い切ったら生成器に戻る。`reset()`で台本はコピーから再開。
  - `clearFixed()`: 解除。
  - `draws`: 現戦闘での引いた回数（読み取り専用。T12/T12bの検証用）。
- 公開APIは `Object.freeze`。判定式は `next() < 0.33`（気絶）/`next() < 0.5`（カウント2復帰）。定数は1箇所。
### プロトタイプ検証（scratchpad、ゲームrepo非接触）: `lou_faint_rng_proto.js`
- 固定seedは `reset()`（再開始相当）後も同一列を再現 ✔ ／ 固定なしは戦闘ごとに別列 ✔
- **faint側で1000回引いても `Math.random` 呼び出し0回** ✔（回避・会心の乱数列に影響しない）
- 台本 `[0.1,0.9]` → 使い切り後は生成器へフォールバック ✔
- 一様性: seed99・20万回で P(<0.33)=0.3297 / P(<0.5)=0.4989 ✔
- DEV外では `fixSeed`/`setScript` は false を返し無効 ✔
### 影響範囲
既存の回避・会心・ルー飛行のコード、呼び出し順、乱数列は不変（ルーの新規消費が Math.random に1回も入らない）。

## 差分2：T12の修正（乱数を引く条件の厳密化）
v1の「気絶していない経路では引かない」を撤回し、以下に置換。**専用乱数を引くのは次の2経路のみ**:
| 経路 | 条件 | 引く回数 |
|---|---|---|
| ① 破砕斬の実行 | その時点でルーが**起きている**（気絶中でない） | **1回**（33%判定） |
| ② ラウンド終了時の復帰判定 | 気絶カウントが**ちょうど2**に到達した時 | 1回（50%判定） |
引かない経路（draws が増えないことをテスト）: 破砕斬以外の全攻撃（通常攻撃/狂爪連撃/腐蝕の波動/穢れの供給/角笛）、**破砕斬だが既にルーが気絶中**、気絶カウント1・3、気絶していないラウンド末、戦闘開始/終了処理、Phase3移行、支援処理。
- T12（修正）: 起きている状態で破砕斬を実行→`draws` がちょうど+1。
- T12b: 破砕斬以外の攻撃を全種実行→`draws` 不変（0）。
- T12c: 気絶中に破砕斬を実行→`draws` 不変、カウント不変。
- T12d: 1回の気絶〜復帰（3R復帰）で draws=1(気絶)+1(カウント2判定)=2、4R復帰でも同じ2（カウント3は必ず復帰のため引かない）。
- T12e: 33%が不成立（気絶せず）の場合 draws=+1 のみ、以後ラウンド末で引かない。

## 前版からのその他の差異
なし（気絶条件、カウント定義、最終祝福保留、復帰ラウンドの扱い、勝利優先、非表示要件、UI、変更しない範囲はv1と同一）。T11/T13は次のように具体化: T11 回避/会心は固定seedでも変わらない（`Math.random`スタブ列を同一に与え、faint有効/無効で回避・会心結果が一致）、T13 `fixSeed/setScript` はDEV外で無効。

## Codex独立設計レビュー依頼（確認観点）
1. 専用PRNGの分離が実際にMath.random消費ゼロであること、reset経路の網羅（startRaiderBattle、beginRaider、時間巻き戻し、generation変更）。
2. カウンタ定義（気絶ラウンドを数えない）と、同一関数内の「気絶→ラウンド末tick」順序の安全性（justFaintedフラグ）。
3. enrageMoment/finalBlessingの保留と復帰時発動、二重発動防止、enrageFlow/enragePending残留の有無。
4. 勝利優先（BattleActorState「KO outranks victory」との整合）と気絶専用経路の分離。
5. 非表示要件（BattleStatus.render非流用、title/aria-label）。
6. 難度評価の妥当性（シミュレーション前提の限界。T18実機再検証計画）。
レビュー対象ファイル: LOU_FAINT_DESIGN_FINAL_20261016.md（v1）+ 本書（v2差分）、lou_faint_sim_v3.py、lou_faint_rng_proto.js、調査根拠は game repo a3f4bb8 の js/prologue-combat.js(L249-304)、js/battle-actor-state.js、js/battle-status.js、js/battle-critical.js。
Claudeは完了/VERIFIEDを自己判定しません。

## 最終テスト手順（v1のT1〜T18にv2修正を反映）
A トリガー: T1/T1b(0.329→気絶,0.33→しない)/T1c
B カウンタ: T2/T3/T4/T5
C 最終祝福: T6/T7/T8/T8b
D 敗北・進行: T9/T10
E 乱数: T11、**T12(修正)/T12b/T12c/T12d/T12e**、T13、**T13b 固定seedが戦闘再開始後も同一列／固定なしは再開始ごとに別列／台本は reset 後に先頭から再開**、**T13c 同一seedの2戦闘で気絶/復帰タイミングが再現**
F UI: T14/T15/T16
G 回帰: T17
H 難易度: T18（実機フロー固定seed 50〜100戦、現行ベースラインと比較）
実行: tests/run_python.py + Playwright(PW_CHROMIUM_EXECUTABLE=/opt/pw-browsers/chromium)、実開始関数経由、生成世代バイパス不使用。乱数は `fixSeed`/`setScript` で固定。未実行テストはPASSに数えない。
