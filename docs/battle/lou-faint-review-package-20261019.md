# Lou-only faint (`lou_faint`) — Codex 独立レビュー用パッケージ（PR #36）

- 対象PR: https://github.com/celticmusic-nagoya/the-windbound-oath/pull/36（`feature/lou-faint-recovery`）
- 準拠仕様: 2026-10-16 確定仕様（`docs/battle/lou-faint/`）。一般状態異常 `general_stun` は **対象外**（将来候補・未採用）。
- ステータス: **レビュー待ち。main未マージ。VERIFIED宣言なし。Android実機 UNVERIFIED。** ロールバック先 = main `405111f838f50525c9de8107ca1037d275a048ec`。
- ゲーム仕様・数値・難易度の変更: **なし**（33% / 50% / 3R確定・戦闘数値はすべて確定仕様どおり）。

## 1. 変更範囲
| ファイル | 内容 |
|---|---|
| `js/battle-lou-faint.js`（新規） | 状態(fainted/count/justFainted)、独立RNG(mulberry32, crypto seed, Math.random不使用)、`judge()`<0.33、`advance()`（気絶R非加算／+2で<0.5／+3確定）、DEV限定 `fixSeed/setScript/clearFixed`、バッジclass切替 |
| `js/battle-actor-state.js` | `faint/wake/fainted`、`resting()`=気絶時のみko、勝利ポーズ優先の原子的解除、`begin()`でfainted初期化 |
| `js/prologue-combat.js` | 破砕斬ブロックで判定、気絶中の `support()` 無効（lastSupportRound非更新）、最終祝福の保留/復帰後1回、ラウンド末の回復処理（敗北判定の後）、`beginRaider` でreset、`enragePending` を祝福フロー終了時に必ず解除 |
| `index.html` / `css/style.css` | `<script>` 追加、バッジ要素「気絶中…💫」、勝利時 `BattleLouFaint.reset()` |
| テスト | `tests/battle/lou_faint.py`、`lou_faint_display.py`(T16)、`lou_faint_lifecycle.py`(T19)、`tools/qa/lou_faint_baseline.py`(T18計測・読み取り専用) |

## 2. 確定仕様との一致確認（最終祝福・保留・復帰後発動）
| 確定仕様 | 実装 | 状態 |
|---|---|---|
| 気絶中にPhase3へ入っても消費せず保留。`blessingUsed/enragePending/enrageFlow` を立てない | `enrageMoment()` は気絶中なら保留フラグのみ（`enragePending` は false のまま） | 一致（T6でassert） |
| 復帰時に一度だけ発動、ログ順「目を覚ました！」→祝福 | `louRoundEnd` で wake→ログ→保留があれば `finalBlessing()` を await | 一致（T7: ログ順と1回をassert） |
| 復帰ラウンドの通常支援なし、次ラウンドから再開 | 支援は敵フェイズ(復帰より前)に実行。復帰後は次ラウンドで `support()` 再開 | 一致 |
| 気絶中は支援（癒し/加護/祝福）なし、`lastSupportRound` 非更新 | `support()` 冒頭で気絶なら `false` | 一致（T5） |
| 敗北判定が先、敗北時に復帰演出なし | 復帰処理は敗北判定の後 | 一致（T19 b） |
| 世代変化で旧処理が新戦闘を更新しない | `louRoundEnd` は `token===generation` を返し、false なら `rbRound++` 等をスキップ | 一致（T19 c） |
| 祝福 running は常に done へ（finallyで enragePending 解除） | `finalBlessing()` を try/finally でラップ | 一致 |
| `blessingUsed/enragePending` を4値状態(none/pending/running/done)の派生getterに | **未実装**：既存booleanを維持し、`blessingDeferred` を追加 | **差異**（挙動同等、内部表現のみ。レビューで判断を求める） |
| `support()` の `wokeRound` 二重ガード（V3） | **未実装**：復帰はラウンド末のため同ラウンドで支援が重複する経路が無い | **差異**（到達不能のため省略） |
| 祝福実行中(running)に気絶した場合 | 仕様どおり done へ（バフなし）。実運用では気絶判定が敵フェイズ頭の別ラウンドのため到達しにくい | 仕様どおり・要レビュー |
| 一般状態異常 `stun` の追加 | **なし**（BattleStatus は4種のまま、`lou_ko_motion.py` が拒否を確認） | 一致 |

## 3. テスト結果
（最新の実行結果は PR #36 本文と `docs/battle/qa/lou-faint-20261019/` を参照）
- `lou_faint.py`：T1/T1b(0.329/0.33)、T2〜T5(0.49/0.5、R+1/R+2/R+3)、T6/T7(保留→復帰後1回、ログ順)、T9、T10、T11、T13、T14/T15、T20、T21 — PASS
- `lou_faint_display.py`（T16）：PC 1280×720／縦 390×844／横 844×390 で、気絶バッジ表示・ビューポート内・HUD非重複、KO最終フレーム保持、復帰後バッジ非表示と通常ポーズ復帰 — PASS。スクリーンショット `docs/battle/qa/lou-faint-20261019/`。（初回、横画面でバッジがフィオナ近接HUDと重なったためCSS位置を調整。テスト緩和なし）
- `lou_faint_lifecycle.py`（T19）：a)やり直し b)復帰ラウンドでの全滅 c)復帰後祝福中のやり直し d)気絶中の勝利→次戦 — PASS。初回、勝利後にバッジ/フラグが残るバグを検出し、`finishRaider` に `BattleLouFaint.reset()` を追加して修正。
- 回帰（既存）：lou_ko_motion, lou_idle_real_flow, raider_motion_p5, kb_raider, hit_sync, battle_opening, raider_mobile_layout, asset_registry_audit — PASS（最終実行は PR 本文に記載）

## 4. T18 難易度影響（実フロー・固定seed・自動操作）
方法：`tools/qa/lou_faint_baseline.py`。実際の `startRaiderBattle`/敵フェイズを自動操作（時間はsetTimeout短縮のみ・ゲーム数値非変更）、`Math.random` をseed固定、同一ボットで **現行main(405111f)** と **PR #36** を50戦ずつ比較。
| 指標 | 現行main | PR #36 | 確定仕様のシミュレーション |
|---|---|---|---|
| 勝利/やり直し(全滅) | 50勝/0敗 | 26勝/24敗 | — |
| 支援回数/戦（癒し＋加護） | 6.0 | 4.72（−21%） | 5.5→4.3（−22%） |
| DEF付与/戦 | 3.0 | 2.9 | 61%→52% |
| 最終祝福の発動 | 1.0 | 1.0（全戦発動） | 全戦発動 |
| 気絶/戦（打切り含む） | 0 | 1.38 | — |
| ルー不在ラウンド率（打切り含む） | 0 | 13.6% | 不在 約29%（戦闘比） |

- 気絶回数別の全滅率（PR #36側）：0回=0/7、1回=10/22、2回=10/16、3回=4/5。
- **解釈上の注意**：このボットは現行mainでも20Rで辛勝する（余裕が薄い）ため、ルーの癒し(+12HP)喪失が全滅に直結しやすい。支援回数の減少率はシミュレーションと一致（−21%対−22%）。一方 **全滅(やり直し)率が 0%→48%** は想定より大きい。より慎重な操作ボット(`LF_POLICY=careful`)は現行mainでも30戦全敗（11R）で比較に使えなかった。
- 数値は変更していない。**難易度への影響が許容範囲かは仕様責任者の判断事項**（承認を仰ぐ項目）。
- 限界：プレイヤー操作・アイテム使用はモデル化していない。人間プレイでの検証は未実施。

## 5. 未解決事項・レビュー依頼
1. T18の全滅率上昇（ボット依存）を許容するか。許容しない場合の対処は **仕様変更になるため承認が必要**。
2. 4値状態(none/pending/running/done)への内部表現移行の要否（現状は挙動同等のboolean＋`blessingDeferred`）。
3. T17の回帰対象（PLAN記載の `ui_command_safety` 等は main に存在しない）は、存在する同等テストに読み替え済み。妥当性の確認。
4. T19系の追加ケース（BattleCommandGate等）、Android実機、人間プレイは未実施。
5. 既存 `lou_ko_motion.py` の assert は変更していない（`stun`/`faint` motion非登録、BattleStatus stun拒否は維持）。
