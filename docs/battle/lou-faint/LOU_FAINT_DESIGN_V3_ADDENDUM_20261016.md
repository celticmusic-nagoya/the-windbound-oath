# ルー気絶 設計 v3 追補（Codex予備レビュー指摘への対応／コード変更なし）
対象: v1=LOU_FAINT_DESIGN_FINAL_20261016.md, v2=LOU_FAINT_DESIGN_V2_REVIEW_20261016.md。基準 game repo a3f4bb8（読み取りのみ）。

## 0. setScript() の不具合（Codex未検証事項に先に回答）
- **不具合あり（v2資料の主張が誤り）**。プロトタイプの `reset()` が「消費済みの台本の残り」を複製していたため、v2の「reset後に台本は先頭から再開」が成立せず、再現テストで `[0.1,0.2,0.3]` を2つ消費→reset後の先頭値が 0.3 になった（期待 0.1）。
- 修正：原本 `scriptSrc` を保持し、`reset()` は常に原本から複製して再開。修正後 reset後の先頭値=0.1 を確認、既存の6検証（固定seed再現、Math.random呼出0回、フォールバック、一様性0.3297/0.4989、DEV外無効）も全て再PASS。ファイル: lou_faint_rng_proto.js / t_script.js（scratchpad、repo非接触）。
- テスト追加: T13d `setScript` を消費→reset→先頭から再開。T13e 台本使い切り→生成器フォールバック（draws継続）。

## 1. 指摘への回答（コード該当箇所を再確認済み）
### 指摘A：KOが勝利より優先され、気絶中のルーへの勝利ポーズが拒否される
- 事実：`BattleActorState.set()` に `if (battle.state==='ko' || (battle.state==='victory' && state!=='ko')) return false;` がある。気絶表示を `ko` 状態で出すと、finishRaider の `set('lou','victory')` が **無言で拒否**される。
- 設計：ルーの気絶は **`ko`状態を使うが、`battle.fainted=true` の専用フラグを持たせ**、set() のガードを「`ko` かつ `fainted` でない場合のみ拒否」に限定（他キャラのKO優先規則は不変）。`finishRaider` 側で勝利時に `BattleLouFaint.clearForVictory()` → `fainted=false` → victory。気絶中の勝利はこの順序を固定するテスト（T10拡張：勝利後 get('raider','lou')==='victory'、気絶アイコン/バッジ消去）。
- 代案（不採用理由）：専用状態 `faint` を新設する案は states/BATTLE_ASSETS/motion の拡張が必要で、新KO素材接続（別工程）と衝突するため後回し。

### 指摘B：既存 `recover()` は HP>0 が条件でルーに使えない
- 事実：`recover()` は `state==='ko' && health()[0]>0`。ルーは health()=[null,null] で常に偽。
- 設計：ルー専用の `wake(context,'lou')` を BattleActorState に追加（`fainted` を落として invalidate→`paint(resting)`）。既存 `recover()` は無変更。`resting()` の「hp===null→idle」特例は `fainted` 時のみ 'ko' を返すよう限定。テスト：T4拡張（復帰で idle 表示、ko 画像でない）、既存の他キャラ recover 挙動の回帰。

### 指摘C：最終祝福は演出前に使用済みになる → 保留・実行中・発動済みの区別が必要
- 事実：`finalBlessing()` は冒頭で `blessingUsed=true`。さらに演出が途中失敗(`token`不一致 / `BattlePresentation.action` 失敗)しても `enragePending` が戻らない経路がある。`enrageMoment()` は `blessingUsed||enragePending` なら即return。
- 設計：状態を4値化 `blessing: 'none' | 'pending' | 'running' | 'done'`。
  - none→(Phase3突入・ルー起きている) running→done
  - none→(Phase3突入・ルー気絶中) pending→(復帰) running→done
  - running中は enrageMoment/復帰/再入のいずれも新規発動しない（二重発動防止）。演出失敗(generation変更)時は戦闘リセットで none に戻る。
  - 既存の `blessingUsed`/`enragePending` は新状態からの派生（getter）にして外部参照互換を保つ。tests/battle で参照されている箇所は実装時に洗い出して回帰確認。
- 追加テスト：T6/T7拡張で4状態遷移を表で検証、復帰と同時にPhase3 tick、復帰演出中の再突入、generation変更で running から none への確実な復帰。

### 指摘D：復帰処理と通常支援が同ラウンドに重複しない制御
- 事実：支援は敵フェイズの `support()`、復帰はラウンド末(tick後)なので、通常は同ラウンドに重複しない。ただし復帰時の最終祝福はasync（バナー・演出に数秒）で、`rbBusy` 解除とラウンド進行より前に完了待ちが必要。
- 設計：`endOfRound` を `await LouFaint.endOfRound()` とし、復帰ログ→(pendingがあれば)最終祝福 の完了後に `rbRound++`/`rbBusy=false`/`updateRaider()`。復帰したラウンドは `LouFaint.wokeRound=rbRound` を持ち、`support()` は `rbRound===wokeRound` なら return false（二重ガード。通常は到達しないが、順序変更への保険）。祝福発動で `lastSupportRound` を更新（現行 finalBlessing と同じ）ので次ラウンドの通常支援が詰まらない。
- テスト：T5拡張（復帰ラウンドに通常支援の呼び出しが0回）、復帰＋最終祝福が同一ラウンド末に1回のみ、祝福演出中に次ラウンドコマンドが開かない(BattleCommandGate)。

## 2. 資料受け渡し（Codexが特定できない件）
- 原因：4資料は私の作業領域(scratchpad)にあり、GitHubにはありません。ブランチ名/SHAも存在しません。
- 提案（**承認が必要。現時点では実施しません**）：hub repo `celticmusic-nagoya/the-windbound-oath-handoff` に **docs専用の新規ブランチ** `handoff/lou-faint-design-review-20261016` を作成し、以下をコミット/プッシュ。game mainには触れない。
  - docs/lou-faint/LOU_FAINT_DESIGN_FINAL_20261016.md (v1)
  - docs/lou-faint/LOU_FAINT_DESIGN_V2_REVIEW_20261016.md (v2差分)
  - docs/lou-faint/LOU_FAINT_DESIGN_V3_ADDENDUM_20261016.md (本書)
  - docs/lou-faint/lou_faint_sim_v3.py
  - docs/lou-faint/lou_faint_rng_proto.js, t_script.js
  - docs/lou-faint/SHA256SUMS.txt
  承認後は固定SHAとファイルパスをお知らせします。代替案：ユーザーがこれらをそのままCodexへ添付。
- ご承認の際は、(1) hubへのブランチ作成・commit・push、(2) ブランチ名、の2点を明示してください。
