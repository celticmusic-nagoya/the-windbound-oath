# 主人公(エイダン/フィオナ)の戦闘攻撃モーション 設計 + 手描き素材の受入

## 1. 既存の仕組み（そのまま使う）
`js/battle-motion.js` + `img/battle/motion-manifest.json` + `tools/battle/install_motion_frames.py`（仕様は `motion-spec.md`）。
コードに固定値は無く、**キャラ×state×variant ごとに {frames, hitFrame, ms[], hold}** をデータで持つ。未納品は静止画へ自動フォールバック。`battle-motion-hit` イベントで演出を結べる。

## 2. 納品計画（データ）— `docs/battle/hero-motion-plan.json`
| キャラ | state | コマ | hit | 合計ms(上限) | 踏み込み |
|---|---|---|---|---|---|
| エイダン | attack | 6 | 4 | 720 (820) | 大きく |
| エイダン | skill(一閃) / wind(風の一閃) | 8 | 5 | 1100 (1200) | 大きく |
| エイダン | charge | 4 | — | 560 | なし |
| フィオナ | attack(杖) | 5 | 3 | 610 (680) | 控えめ |
| フィオナ | heal | 6 | 4(発動) | 760 (760) | なし |
| フィオナ | prayer(風の祈り) | 8 | 5(発動) | 1100 (1100) | なし |
| フィオナ | charge | 4 | — | 560 | なし |
- エイダンの attack は **武器 variant**（`wooden` 木剣 / `iron` / `steel`。装備の `motionVariant` で自動切替）ごとに同じ命名で納品。誓いの剣取得後は variant 無し。
- 各コマのポーズ指示（予備動作→踏み込み→HIT→振り抜き→残心）も plan に入っている。
- **ブリーフ出力**: `python3 tools/battle/hero_motion_brief.py`（正確なファイル名・キャンバス寸法・ms・ポーズ一覧を表示）/ `--check` で計画を検証。
- 納品→設置: `python3 tools/battle/install_motion_frames.py <dir> [--variant wooden]`。

## 3. ダメージ表示の命中コマ同期（実装済み・承認済み）
`js/prologue-combat.js`: ダメージ・HP・KO・ターン進行・TP/RUNE は**従来どおり即時（ロジック）**。**表示だけ**（被弾ポーズ/KO、フラッシュ、敵HPバー・テキスト、バナーのダメージ数値、会心演出、HUD更新）を
`BattleMotion.hitDelay(actor,'attack')`（0〜600msに制限）だけ遅らせる。
- 適用: エイダン/フィオナの**通常攻撃**（カットイン演出を持つ一閃・風の一閃などは既存の演出タイミングに従うので対象外）。通常戦闘・レイダー戦の両方。
- モーション未納品なら遅延0＝従来と完全に同じ。戦闘終了/再開(`generation`)で保留中の表示は破棄。
- 保留中は敵のバーを被弾前の値に保つ（`shown`/`pend`）。
- テスト: `python3 tests/battle/hit_sync.py`（ダミー6コマ・hit=300msで、ロジックHPは即減少・バーは300ms後に減少、未納品時は即時を確認）。

## 4. 注意（既存の戦闘静止画）
現在の `img/battle/characters/*` の静止画は **αが全面不透明（背景込み）**。新コマは必ず本当の透過PNG（インストーラは透過を要求）で、既存の背景付き静止画とは見た目が変わる点に注意。

## 5. フィールド素材（フィオナ/エイダン）の受入 — `tools/field/install_hero_frames.py`
```
python3 tools/field/install_hero_frames.py <src_dir> --hero fiona|aidan [--height-world 46] [--dot 2] [--dry-run]
```
- 入力（キャンバスサイズ自由・1コマ=1透過RGBA PNG）: `<hero>_idle_<down|left|right|up>.png`, `<hero>_walk_<dir>_01..06.png`（4〜6コマ、全方向で同数）。
- 正規化: 全体で**単一スケール**（idle_down の身長 → 世界 46/44px）、**足元の最下行→アンカー行**、方向ごとに idle の足元中心→アンカー列（歩行コマ間のブレ防止）。`--dot 2` で「1ドット=2px」へスナップ（ドット絵納品用）。
- 検証: 透過率15%未満(背景込み)・四隅の不透明・欠番・方向間のコマ数不一致を拒否。出力は `img/field/moss/real/fiona/`・`img/field/characters/aidan/` と各 `*-field-assets.js`。ランタイムはコマ数を自動認識（エイダン4→6コマ等）。
- テスト: `python3 tests/moss/m9_hero_intake.py`（リポジトリ素材には触れない）。
