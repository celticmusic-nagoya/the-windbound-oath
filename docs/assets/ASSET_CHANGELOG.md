# ASSET CHANGELOG（納品・採用・修正・実装・main統合・差し戻し）

形式: `日付 | 素材 | 事象 | SHA / PR / Issue`。新しい行は上に追記。

- 2026-10-19 | Phase 5 ゴブリン・レイダー | 採用5シート（attack/damage/enrage/call/idle 各6コマ）を切り出し・実装（表示倍率補正・idleループ）。候補2種（powered_attack / ko_dissolve）は未実装のまま PENDING | main 6a99f2bd70bc32ccd111f05effed2ebdb1ac0bd5 / PR #28 / handoff phase5-raider-20261019.md
- 2026-10-19 | Lou KO | lou_new_ko（10/16納品・採用）を6コマで実装（lou/ko, hold last）。ルーはHPを持たず本編ではKOしない。「気絶」は別状態として仕様案 docs/battle/faint-state-proposal.md（承認待ち・未実装） | main 記録は PR 後 / handoff lou-ko-20261019.md
- 2026-10-19 | UNKNOWN照合 第1回 | テンプレート参照の検出を修正（参照なし 170→20）、Lind動物の参照元を明記、レポート作成。採用済み・未実装 0件。候補（BG-02/03・BG-01前景・モスFX12・斜め歩行プール・リルド屋内v1）はオーナー判断待ち | docs/assets/reports/unknown_reconciliation_20261019.md
- 2026-10-19 | 台帳初期構築 | ASSET-REGISTRY-01 Step 1〜3（台帳・バックログ・監査ツール） | 本PR
- 2026-10-19 | 少年剣士10歳版（公式6コマ 288×256） | 台帳登録。Codex再QA CONDITIONAL (64a104d9…)、main統合済み | 実装 8084c9d4… / main 7b124ab9… / PR #22 / #18
- 2026-10-19 | モスの森追加素材20種 | 派生PNG採用・manifest登録・A1/A2/A3配置・main統合 | main 8c61b328842f7cedaf1af5334dee6cecde1eb680 / PR #26
- 2026-10-19 | ARENA-MOTION-01 | アリーナ「モーションテスト」追加（本編 BattleMotion 共用、読取専用 frames()/states() 追加） | main a8ab7771202fbf2dfeda3babe066bd0e525f06d2 / PR #25
- 2026-10-19 | Phase 3 味方モーション | Aidan damage/low_hp/ko、Fiona attack/damage/heal/ko/winddance、Lou damage/blessing（各6コマ）を実装・main統合。Lou KO は気絶仕様待ちで保留 | main 07f25528586683a22c1eb33e2b0d5166efa81ca7 / PR #24
- 2026-10-19 | 味方原本の保存 | 10/16 ZIP（10枚, ZIP SHA-256 af0c79c3…）と 10/17 改訂版4枚を handoff `assets-originals/` に登録 | handoff 861fe10374edbaa5ea2d12239cf41118944772da
- 2026-10-19 | Phase 4 ゴブリンKO消滅 | goblin / tainted_goblin KO（hold hide）を main 統合 | Issue #7
- 2026-10-19 | モスの森追加素材 | 7シートを20素材に分離（原本維持、原本SHA記録）、ブッシュ01=左/03=右を維持 | docs/art/delivered/moss_additional_20261019
- 2026-10-17 | BATTLE-ANIM4 | aidan hit/lowhp/ko 改訂版、fiona winddance 改訂版 納品（10/16の hplow/ko/danceofthewind は置換） | handoff assets-originals/battle_anim4_20261017
- 2026-10-16 | aidan_fiona_lou_new_asset.zip | 10 PNG（Aidan 2 / Fiona 5 / Lou 3）納品。ブランチ assets/aidan-fiona-lou-* / assets/party-motion-originals-* は実在せず、原本は handoff のみ | ZIP SHA-256 af0c79c3bc95b337edc8b4b52c9005127a1db5cfbe9d957bde4d04eef931c5b0
- 2026-10-16 | ゴブリン・レイダー 6コマ7シート | 納品（5シート採用・未切り出し、powered_attack/ko_dissolve は候補で採用待ち）。ブランチ assets/goblin-raider-ko-from-dissolve-f1 のみ、未実装 | Phase 5 予定
