# LL 戦闘UI構造検証

基準mainf0fe968 / work/codex-ll-pp。tests/battle/ui_structure.pyと本報告・40画像/JSON/ログのみ。ゲーム未修正。

5画面×2戦闘の実シナリオを完了、各6状態（初期/展開/items/実busy/復元/CSS actionCinematic probe）を取得。FAILS0、pageerror0。仕様差60観測を別記し、これをテストFAILにはしない。

## 仕様差

| 観測 | 件数 | 解釈・再現 |
|---|---:|---|
| ui_visible_during_presentation | 30 | 詳細はresults.jsonのspecDifferences |
| overlap | 30 | 詳細はresults.jsonのspecDifferences |

COMMAND/itemsの矩形がviewportから外れる観測は0。一方、展開/itemsが味方スプライトの矩形と重なる条件がある。battlePresentationBusy中にtoggle/log/近接HUD等が表示された観測を記録。actionCinematicのCSS gateは別probeで確認し、自然な演出でそのclassを必ず通ったとは扱わない。

## PCの味方配置と拡大率

| 表示 | 戦闘 | Aidan x / viewport幅 | 表示box幅×高さ | idle fit |
|---|---|---:|---:|---:|
| pc | normal | 0.285 | 154.4×194.6 | 0.1005 |
| pc | raider | 0.108 | 158.2×197.7 | 0.1030 |
| pc-large | normal | 0.305 | 154.4×194.6 | 0.1005 |
| pc-large | raider | 0.129 | 158.2×197.7 | 0.1030 |

両戦闘とも味方は左半分。1280→1920でAidan boxの幅/高さは変わらず（約154×195通常、158×198ボス）、viewport比では小さくなる。「右戦場で味方を拡大」とは配置/サイズに差がある。fitは元idle資産に対する実描画率であり、未定義の「拡大すべき倍率」を勝手に決めない。

## 画面別の重なり

矩形の重なり面積÷2番目の領域面積を百分率にした参考値（透明余白も含む）。同じ種類の観測が複数状態で起きるため60は独立不具合60件という意味ではない。

| 画面 | 戦闘 | 状態 | 領域 | 重なり% |
|---|---|---|---|---:|
| pc | raider | initial | commands / aidan | 100.0 |
| pc | raider | initial | commands / fiona | 2.1 |
| pc | raider | open | commands / aidan | 100.0 |
| pc | raider | open | commands / fiona | 2.1 |
| pc | raider | items | items / aidan | 43.9 |
| pc | raider | restored | commands / aidan | 100.0 |
| pc | raider | restored | commands / fiona | 2.1 |
| pc-large | raider | initial | commands / aidan | 61.1 |
| pc-large | raider | open | commands / aidan | 61.1 |
| pc-large | raider | restored | commands / aidan | 61.1 |
| portrait | normal | open | commands / aidan | 22.2 |
| portrait | normal | open | commands / fiona | 22.6 |
| portrait | normal | items | items / aidan | 26.5 |
| portrait | normal | items | items / fiona | 27.3 |
| portrait | raider | open | commands / aidan | 98.1 |
| portrait | raider | open | commands / fiona | 100.0 |
| portrait | raider | items | items / aidan | 91.9 |
| portrait | raider | items | items / fiona | 100.0 |
| landscape | normal | open | commands / aidan | 88.9 |
| landscape | raider | open | commands / aidan | 100.0 |
| landscape | raider | open | commands / fiona | 90.4 |
| landscape | raider | items | items / aidan | 100.0 |
| landscape | raider | restored | log / enemy | 1.8 |
| landscape | raider | css-actionCinematic-probe | log / enemy | 1.8 |
| small | normal | items | items / aidan | 20.4 |
| small | normal | items | items / fiona | 21.8 |
| small | raider | open | commands / aidan | 97.3 |
| small | raider | open | commands / fiona | 100.0 |
| small | raider | items | items / aidan | 91.9 |
| small | raider | items | items / fiona | 100.0 |

ログが空ならdisplayが存在しても内容のない領域の見え方に注意が必要。測定は実開始ログを含む状態を記録。演出中は実engine skill→guard→敵ターンを通し、終了後にCOMMANDのtoggleまたは展開windowが復元することを確認。スマホの初回/次ターン折りたたみは今回決定した仕様として扱う。

[画像/生データ](battle-ui-structure-20261013/) に各画面のinitial/open/items/busyを保存。通常はforestGob1/3敵、ボスはDEVジャンプ開始。実engine roundを使用したが、全技・全アイテム演出は未実施。Android実機未測定。

再現: 各viewportで戦闘を開き、COMMAND展開/items→Aidan skill+Fiona guardの実roundでbusyクラス中のHUD/log/toggleを比較。仕様差の採用・本体修正はClaude/ユーザー判断。次MM。main未統合、戻し方（将来統合後）git revert -m 1 <merge>。
