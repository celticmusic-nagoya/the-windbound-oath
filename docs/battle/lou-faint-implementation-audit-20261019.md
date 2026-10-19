# ルー専用「気絶」— 確定仕様と現在の main の照合（2026-10-19）

**調査のみ。戦闘ロジック・テスト・素材は変更していない。** 基準: main `f6120bb`（PR #33 統合後）。正の仕様: [`lou-faint/`](lou-faint/README.md)（2026-10-16 確定、`PLAN_FINAL` / `DESIGN_FINAL` / v2〜v4）。
訂正: 2026-10-19 に作成・統合した「一般状態異常 stun」案（`faint-state-design.md` 等）は確定仕様と別物のため SUPERSEDED（旧案・非採用）。

## 1. 総括
| 区分 | 結果 |
|---|---|
| ルー専用気絶のゲーム内ロジック | **未実装**（`LouFaint` / `battle-lou-faint.js` / `fainted` フラグ / `wake` / 保留祝福のいずれも main に存在しない。作業ブランチ `feature/lou-faint-recovery` も未作成） |
| 表示素材 | **あり**: Lou KO 6コマ（PR #30、`lou/ko`、hold last）。`BattleActorState.set('lou','ko')` で再生できる。ゲーム内でこれを呼ぶ処理は無い（DEV/テストのみ） |
| 実装の前提（接続点） | 下表のとおり、いずれも**そのままでは使えない**箇所がある（§3） |
| テスト | 確定資料の T1〜T21 は**1本も存在しない**（§4） |
| 承認状態 | 仕様は承認済み。**実装着手・ブランチ作成・テスト追加は個別承認待ち**（PLAN_FINAL §7）。戦闘ロジック変更のため Codex 独立レビュー必須 |

## 2. 仕様項目ごとの実装状況
| # | 確定仕様 | main の現状 | 状況 |
|---|---|---|---|
| 1 | ルーに HP を新設しない | `raider:lou` の `health` は `[null, null]` のまま | ✅ 既に満たす（維持） |
| 2 | ルーは通常の KO にならず専用の気絶状態になる | ルーは `ko` に入る経路が無い。HP0 でも KO にならないことを `lou_ko_motion.py` が確認 | ❌ 未実装（気絶状態そのものが無い） |
| 3 | 破砕斬の実行時、非気絶なら 33% で気絶 | 破砕斬ブロック（`prologue-combat.js` `if(rbQueued)`、約266行）にルー判定なし | ❌ 未実装 |
| 4 | 気絶ラウンド=0、2R後 50% で復帰、3R後は必ず復帰（気絶ラウンド自身の終了は加算しない） | カウンタ・復帰判定なし。ラウンド末は `BattleStatus.tick`（約281行）→敗北判定（282行）→`rbRound++` | ❌ 未実装 |
| 5 | 気絶中は通常支援を停止、`lastSupportRound` は更新しない | `support()`（288行）に気絶ガードなし | ❌ 未実装 |
| 6 | 復帰した次のラウンドから通常支援を再開 | 復帰処理なし（設計上は、復帰がラウンド末＝支援枠通過後のため特例不要） | ❌ 未実装 |
| 7 | ルーの気絶は敗北判定に影響させない | 敗北は `rbHP<=0||rbFHP<=0` のみ（282行） | ✅ 現状は満たす（実装後も維持が必要: T9） |
| 8 | 表示は既存 Lou KO を暫定利用、勝利時は勝利ポーズ優先 | KO 素材・経路あり。**勝利優先は不可**: `BattleActorState.set()` の `battle.state==='ko'` ガードが勝利を拒否する | ⚠️ 素材は接続可能、勝利優先は未実装 |
| 9 | 気絶中の再被弾は無効（カウント不変・乱数を引かない） | – | ❌ 未実装 |
| 10 | 気絶中に Phase 3 へ入ったら最終祝福を保留、復帰時に一度だけ発動（none→pending→running→done の4値） | `finalBlessing()` は冒頭で `blessingUsed=true`、`enrageMoment()` は `updateRaider`（index.html 1270行）から Phase 3 突入時に呼ばれる。保留の概念なし。成功経路でしか `enragePending=false` にならない既存の弱点も残る | ❌ 未実装 |
| 11 | ルー専用の独立乱数（mulberry32、crypto シード、DEV 限定の `fixSeed`/`setScript`/`clearFixed`、`draws`） | 無し。回避(`BattleStatus.dodges`)・会心は別系統で未変更 | ❌ 未実装 |
| 12 | UI: 「気絶」バッジのみ。残りターン・確率・カウントは DOM/title/aria/ログ/コンソールに出さない（`BattleStatus.render` は使わない） | バッジなし | ❌ 未実装 |
| 13 | 復帰演出の `await` 後に世代(generation)を再確認、旧世代なら `rbRound++` 等を実行しない（v4 P1-3）。敗北判定を先に行う | `enemyRaider` はこの構造にしていない | ❌ 未実装 |

## 3. Lou KO モーションとの接続状況と、そのままでは使えない点
- 接続できるもの: `lou/ko` の 6コマ（manifest、hold last）、`BATTLE_ASSETS.lou.ko`（静止画フォールバック）、`BattleActorState.set('lou','ko',{battle:'raider'})`、`updateRaider()` 内の `sync('raider','lou')` は ko を巻き戻さない（`lou_ko_motion.py` で確認済み）。
- **v3/v4 が指摘した 3 つの障害は、main では未対応**:
  1. **勝利が拒否される**: `set()` 冒頭の `battle.state==='ko'` ガードで、`finishRaider`（index.html 1348行）の `set('lou','victory')` が無言で失敗する。v4 の「`fainted` を持たせ、勝利時のみ同一呼び出し内で原子的に解除」が必要。
  2. **復帰できない**: `recover()` は `health()[0]>0` が条件で、HP が `null` のルーには使えない。ルー専用 `wake` が必要。
  3. **`resting()` が常に `idle`**（`hp===null`）: `fainted` 中は `ko` を返す限定が必要。
- 表示素材は「暫定」でよい（確定仕様 8）。専用の気絶モーション素材（3人分）は**制作しない**（旧案を取り下げ）。
- 参考: 先に統合した資料（`ally-motion-asset-spec.md`・台帳メモ）にあった「ルーは HP を持たず本編では KO しない／気絶は別状態の提案」という記述は、**気絶＝ルーの KO 代替状態**という確定仕様に合わせて訂正が必要（本 PR で台帳メモを訂正）。また「最終祝福＝時間巻き戻し」とした記述は誤りで、実際の `finalBlessing` は Phase 3 で味方全員に ATK/DEF +15%（3ターン）を与える強化（時間巻き戻しは全滅時のやり直し演出）。

## 4. テスト不足
- 確定資料の T1〜T21（トリガー、カウンタ境界 0.329/0.33・0.49/0.5・3R必復帰、支援停止、復帰ラウンド、最終祝福4値、勝利優先（原子的遷移）、世代競合、乱数独立と `draws`、DEV外での固定seed無効、UI非表示の文字列走査、モバイル幅）は**すべて未作成**。
- 現存の関連テスト: `lou_ko_motion.py`（KO 6コマ再生・HP0でもルーはKOしない・stun 状態/型が登録されていない）、`lou_idle_real_flow.py`、`raider_mobile_layout.py`、`raider_motion_p5.py`。
- **実装時に必ず衝突するテスト**: `lou_ko_motion.py` の「通常戦ラウンドでルーが ko にならない」系は、破砕斬で気絶が起き得るようになると意図が変わる。確定仕様に沿った更新（理由と根拠の明記）が必要で、緩めるだけの変更はしない。
- PLAN_FINAL T17 が挙げる `ui_command_safety` / `int02_routes_real_adapter` / `int02_p0_start_failure` / `battle_admission_adapter` は、**現在の main に存在しない**（未統合の P0-D / INT-02 側）。回帰対象の読み替えが必要。
- 難易度再検証（T18）: 実装前の「現行」実機ベースライン（固定seed 50〜100戦）が未取得。シミュレーション（33%: ルー不在率29%、支援 5.5→4.3回/戦）との乖離確認が残る。

## 5. 実装に着手する場合の手順（承認後・参考）
`PLAN_FINAL §5` / `DESIGN_FINAL §5` のとおり: ① `feature/lou-faint-recovery` 作成 ② テスト先行（赤→緑） ③ `js/battle-lou-faint.js` ＋ 接続点（破砕斬・`support()`・`enrageMoment`・ラウンド末・`finishRaider`・リセット・`BattleActorState` の `fainted`/`wake`/勝利遷移） ④ UI バッジ ⑤ T1〜T21 ⑥ T18 難易度再検証 ⑦ 報告→Codex 独立レビュー。`main` への直接変更・merge は個別承認まで行わない。

## 6. 承認いただきたい点
1. 実装着手の可否と作業ブランチ名（`feature/lou-faint-recovery` でよいか）。
2. 実装前に「現行」実機ベースライン（T18）を取得してよいか（読み取り実行のみ）。
3. PLAN_FINAL T17 の回帰対象を、現在の main に存在するテストへ読み替えてよいか。
