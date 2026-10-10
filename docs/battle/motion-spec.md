# 戦闘モーション規格（多コマ攻撃など）

## 納品規格
- 1コマ = 1枚の透過RGBA PNG。命名 `<actor>_<state>_NN.png`（NN=01..）。例 `aidan_attack_01.png`〜`_06.png`。
- キャンバスは**そのstateの既存静止画と同寸**（aidan_attack = 1312×1199、idle = 1536×1024 など。stateごとに違う）。足元の基準線は静止画と±48px以内。
- 枠に触れるのは警告のみ（既存画も触れている）。コマ数 2〜12。
- 切り出し: 連結シートなら `tools/lind/extract_walk_sheet.py <sheet> --suffix attack --anchor X,Y`（出力 `<id>_attack_NN.png`）、そのまま `tools/battle/install_motion_frames.py <dir> [--variant wooden] [--hit 4] [--ms 80,80,100,100,110,110] [--dry-run]`。

## データ構造（キャラ別・コマ数別・ヒット位置別）
`img/battle/motion-manifest.json`
```
motions: { "<actor>[:<variant>]": { "<state>": { dir, pattern:"{n}", frames, ms:[…]|数値, hitFrame:1始まり, hold:"last" } } }
```
- 剣士 `aidan.attack = {frames:6, hitFrame:4}` / 魔法使い `{frames:4, hitFrame:3}` のように**アセットごと**に持つ。コードは固定値を持たない。
- `ms` は配列でコマごとの表示時間（＝ticksPerFrame相当）。合計がstate時間（aidan 820ms / 他 attack 680ms / スキル 1100–1200ms）に収まらないと設置ツールが警告。
- variant（`aidan:wooden` = 少年剣士の木剣）は `BattleMotion.setVariant` で切替。未納品のstate/variantは**静止画へ自動フォールバック**。
- `hitFrame` に到達した瞬間に `battle-motion-hit {actor,state,frame,at}` を発火。ヒットフラッシュ・揺れ・数字ポップはこのイベントに結び付ける。

## 所見（要判断・今回は未変更）
現行は**攻撃開始と同時にダメージを適用**（prologue-combat.js）し、アニメの特定コマには依存しない。6コマ中4コマ目で当たって見せたい場合は、計算は触らず**表示側だけ**を `hitFrame` まで遅らせる（`BattleMotion.hitDelay(actor,state)` が遅延ms=hitFrameまでの累積msを返す）。一閃 TP30・HP/フェーズ等のバランスは不変。

## 検証
`python3 tests/battle/motion_intake.py` — 仮コマを作成→設置→順序/ヒットイベント(4コマ目≒300ms)/idle復帰/静止画・variantフォールバックを確認し、manifestと仮ファイルを自分で元に戻す。
