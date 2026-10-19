# ルー気絶 設計 v4 追補（Codex独立レビュー P1×3 / P2 への対応／コード変更なし）
v3追補の該当箇所を本書で置換する。基準 game repo a3f4bb8（読み取りのみ）。

## P1-1 勝利指定が拒否される（fainted=false にしてもKO状態が残る）→ **受容。原子的な勝利遷移に変更**
- 原因：v3は「先に fainted=false → set('victory')」としたが、set() 冒頭ガード `battle.state==='ko'` は状態文字列で判定するため、fainted を落とした時点で通常のKOと区別できず拒否される。
- 設計（BattleActorState.set の1箇所のみ改修）：
  ```
  const faintedLou = battle.fainted === true && state === 'victory';
  if ((battle.state==='ko' && !faintedLou) || (battle.state==='victory' && state!=='ko')) return false;
  if (faintedLou) { battle.fainted = false; }   // ガード通過後、同一呼び出し内で解除（原子的）
  ```
  → 以降の paint('victory') まで同一呼び出し。他キャラ（HPで ko になる者）は fainted を持たないため従来どおり KO優先。
- 呼び出し側に先行解除コードを置かない（finishRaider は従来どおり `set('lou','victory')` のみ）。
- テスト：T10-a 気絶中に勝利→`get('raider','lou')==='victory'`・fainted=false・気絶バッジ消去／T10-b エイダン/フィオナがKO中の勝利は従来どおり拒否（回帰）／T10-c 勝利後に復帰タイマー・endOfRoundが走らない／T10-d 勝利後の `wake()` は no-op。

## P1-2 祝福が同一世代内で失敗した場合の running からの復旧 → **定義**
- 現行挙動（維持）：`finalBlessing()` は冒頭で `blessingUsed=true`、演出失敗（`BattlePresentation.action` が偽）でも再試行しない＝消費済み。バフ付与(`buffParty`)は演出成功後のみ。
- 新方針：`running` は **必ず finally で `done` に遷移**。
  - 演出成功：バフ付与→ログ→done
  - 演出失敗（同一世代）：バフなし・done（再試行しない＝現行互換）。ログ「祝福の光は届かなかった」等は出さず内部のみ（UI変更なし）
  - 世代変化（やり直し/中断/新戦闘）：状態は戦闘リセットで `none`
- `enragePending` は finally で必ず false にする（現行は成功経路のみ false で、失敗時に残留し得る既存の弱点。派生getter化で解消）。
- 状態表（確定）：
  | 状態 | 遷移 |
  |---|---|
  | none | Phase3突入×ルー起きている→running／Phase3突入×気絶中→pending |
  | pending | 復帰→running（一度だけ）／勝利・世代変化→none |
  | running | finally→done／世代変化→none（新戦闘で再初期化） |
  | done | 以後すべての発動要求は無視（二重発動なし） |
- テスト：T7a 成功→done・バフ1回／T7b 同一世代で演出失敗→done・バフなし・再試行されない・enragePending=false／T7c 世代変化→次戦で none／T7d running 中の再突入(enrageMoment・復帰)で新規発動ゼロ。

## P1-3 復帰演出の await 後に世代を再確認しないと旧処理が次戦を更新する → **採用**
- 設計：`endOfRound` は先頭で `const token=PrologueCombat.generation` を取得。**各 await の直後に `if(token!==generation) return false`**（復帰ログ後、祝福前、祝福後）。戻り値 false なら呼び出し側 `enemyRaider` は即 return し、`rbRound++` / `rbActor='aidan'` / `rbActs=[]` / `rbBusy=false` / `updateRaider()` を **実行しない**。
  ```
  if(!(await BattleLouFaint.endOfRound(token))) return;   // 旧世代: 何も触らない
  rbRound++; ... rbBusy=false; updateRaider();
  ```
- 呼び出し位置：既存の `BattleStatus.tick` の後、敗北判定(`rbHP<=0||rbFHP<=0`)の**前**。敗北時はやり直しに移るため復帰演出を出さない（`if(rbHP<=0||rbFHP<=0)` を先に判定するか、endOfRound内でゲームオーバー相当なら即return）。→ **確定：敗北判定を先に行い、敗北時は endOfRound を実行しない**（演出の無駄打ちと世代競合を避ける）。
- テスト：T19 復帰演出中に `startRaiderBattle`（やり直し/新戦闘）→ 旧処理が rbRound/rbBusy/rbActor/ログ/UIを一切更新しない（新戦闘値を保持）／T19b 祝福演出中に世代変化→同様／T19c 敗北判定が先に走り復帰演出が出ない。

## P2 DEV解除後に固定台本が残る／初期reset前の台本枯渇で例外 → **修正済み（プロトタイプ）**
- `reset()` は DEV 有効時のみ fixedSeed/script を採用。`next()` は (a) `gen` 未初期化なら遅延初期化（例外なし）、(b) DEV が無効になっていたら fixedSeed/scriptSrc を**破棄**して通常のエントロピー初期化に戻す（DEVを再度ONにしても復活しない）。`clearFixed()` は DEV に関係なく常に可能。
- 検証（t_p2.js）：リセット前の draw で例外なし／台本枯渇でPRNGにフォールバック／DEV off で台本は無視／DEV off→on でも台本は復活しない。既存検証（setScript先頭復帰、Math.random呼出0、一様性0.3297/0.4989、DEV外fixSeed/setScript無効）も全てPASS。

## テスト一覧の更新（v2のT1〜T18に追加）
T7a–d、T10-a–d、T13d/T13e（v3）、T19/T19b/T19c、**T20 DEV off 後に固定seed/台本が無効**、**T21 初期reset前の draw が例外にならない**。合計 T1–T21（T12系はv2の修正済み版）。

## 次の資料授受
Codexの報告では v1・v2・sim v3・t_script.js が未添付とのこと。今回、v1/v2/v3追補/v4追補/sim_v3/rng_proto/t_script/t_p2 とSHA256SUMSをすべて添付する。GitHubへのブランチ作成・commit・pushは未承認のため実施しない（希望される場合は `handoff/lou-faint-design-review-20261016` で承認ください）。実装着手は引き続き保留。製品・テストコード、既存証跡、GitHubは未変更。
