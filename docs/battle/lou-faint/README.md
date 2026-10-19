# ルー専用「気絶」確定仕様（2026-10-16）— 正の資料

ルーの「気絶」は一般状態異常ではなく、**ルー専用の KO 代替状態**です。本ディレクトリは確定資料の**逐語コピー**（原本は handoff リポジトリ `celticmusic-nagoya/the-windbound-oath-handoff` のブランチ `backup/uncommitted-20261017-docs`、コミット `6992849…`、`backup/docs/scratchpad_docs/`）。内容は変更していない。

| ファイル | 役割 | SHA-256 |
|---|---|---|
| `LOU_FAINT_PLAN_FINAL_20261016.md` | 確定仕様・既存攻撃との対応・接続点・難易度評価・実装計画 | 1a3cf6d3556a1599555d2cd494c0c437ba7f58a2b4e35895d00ca0acf892e6e5 |
| `LOU_FAINT_DESIGN_FINAL_20261016.md` | 最終実装設計（v1）・テスト T1〜T18 | 3fe3e836e4d6353988f627108b2451125939aeec41772db6f761fef0e1cfa63f |
| `LOU_FAINT_DESIGN_V2_REVIEW_20261016.md` | v2: ルー専用の独立乱数（mulberry32）、T12 の修正 | 81ceee0b6f9e0c62d6a2107499f662154d87c8870d1e8e04986b9b10ee9635ba |
| `LOU_FAINT_DESIGN_V3_ADDENDUM_20261016.md` | v3: 勝利優先・`wake`・最終祝福4値化・復帰の重複防止 | e4cf86b252ea628b87e601778cce6cdccc0a9116728e80e8f1435156bf7996e3 |
| `LOU_FAINT_DESIGN_V4_ADDENDUM_20261016.md` | v4: 原子的な勝利遷移・祝福失敗時の復旧・復帰演出の世代再確認（T1〜T21） | 621adc077a6e4b47b74cbdaf6556054bec57c6c072f1f37f44816affeb0de76c |
| `LOU_FAINT_PLAN_20261016.md` | 旧計画（PLAN_FINAL に置換済み。参考） | ad5d67bffba99a1bb07f798476cec34b11e44f4f729b273f89ec76370791edc2 |
| `LOU_FAINT_SHA256SUMS.txt` | 原本の添付ファイルのSHA（sim/proto スクリプトは handoff 側） | – |

## 確定仕様（2026-10-19 19:58 再確認）
1. ルーにHPは新設しない。 2. ルーは通常のKOにならず、専用の気絶状態になる。
3. ゴブリン・レイダーの「破砕斬」実行時、ルーが非気絶なら **33%** で気絶。
4. 気絶したラウンドを0とし、**2ラウンド後に50%で復帰、3ラウンド後は必ず復帰**（気絶ラウンド自身の終了では加算しない）。
5. 気絶中はルーの通常支援を停止し、`lastSupportRound` は更新しない。 6. 復帰した次のラウンドから通常支援を再開。
7. ルーの気絶は敗北判定に影響させない。 8. 表示は既存の Lou KO 素材・経路を暫定利用してよい。勝利時は勝利ポーズを優先。
確定資料が追加で定めるもの: 気絶中の再被弾は無効（カウント不変）／気絶中に Phase 3 へ入ったら最終祝福は保留し復帰時に一度だけ／30%の HP 復帰案は破棄／残りターンは UI に出さない／乱数はルー専用で他の判定に影響しない／戦闘ロジック変更は Codex 独立レビュー必須。

## 旧案（SUPERSEDED）
`docs/battle/faint-state-design.md` / `faint-state-proposal.md` / `faint-motion-asset-spec.md`（2026-10-19 作成の一般stun案）は本仕様と異なるため非採用。
