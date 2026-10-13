# LL 戦闘UI構造検証

初回mainf0fe968 / 最終追試maindeadf3d（source f9136bf） / work/codex-ll-pp。
10シナリオ・70状態を完了、FAILS0/pageerror0。仕様差84観測を別記、ゲームは未修正。
新規tests/battle/ui_structure.pyと本報告・50画像/JSON/log。

PC1280×720/1920×1080、縦390×844、横844×390、小型360×640の通常forestGob1（3敵）/ボスを検査。各7状態: 初期/COMMAND展開/items/表示中log/実busy/復元/CSS actionCinematic probe。

## 仕様差

| 観測 | 件数 |
|---|---:|
| ui_visible_during_presentation | 40 |
| overlap | 44 |

COMMAND/itemsの矩形がviewport外へ出る観測0。一方、味方との重なりと実battlePresentationBusy中のtoggle/log/近接HUDの可視を記録。84は状態ごとの反復であり独立不具合84件ではない。スマホ次ターンの折りたたみは今回の決定仕様と区別する。

## PC配置・拡大率

| view | 戦闘 | Aidan x/viewport幅 | box幅×高さ | idle fit |
|---|---|---:|---:|---:|
| pc | normal | 0.285 | 154.4×194.6 | 0.1005 |
| pc | raider | 0.108 | 158.2×197.7 | 0.1030 |
| pc-large | normal | 0.305 | 154.4×194.6 | 0.1005 |
| pc-large | raider | 0.129 | 158.2×197.7 | 0.1030 |

両戦闘とも味方は左半分。1280→1920でboxサイズは不変、viewport比では小さくなる。「右戦場で味方を拡大」とは配置/サイズに差がある。fitは元idle画像に対する描画率、未定義の拡大倍率を勝手に決めない。

## 画面別の重なり

矩形重なり÷2番目の領域面積。透明余白を含む参考値、完全遮蔽率ではない。

| view | 戦闘 | 状態 | 領域 | overlap % |
|---|---|---|---|---:|
| pc | raider | initial | commands / aidan | 100.0 |
| pc | raider | initial | commands / fiona | 2.1 |
| pc | raider | open | commands / aidan | 100.0 |
| pc | raider | open | commands / fiona | 2.1 |
| pc | raider | items | items / aidan | 43.9 |
| pc | raider | active-log | commands / aidan | 100.0 |
| pc | raider | active-log | commands / fiona | 2.1 |
| pc | raider | restored | commands / aidan | 100.0 |
| pc | raider | restored | commands / fiona | 2.1 |
| pc-large | raider | initial | commands / aidan | 61.1 |
| pc-large | raider | open | commands / aidan | 61.1 |
| pc-large | raider | active-log | commands / aidan | 61.1 |
| pc-large | raider | restored | commands / aidan | 61.1 |
| portrait | normal | open | commands / aidan | 22.2 |
| portrait | normal | open | commands / fiona | 22.6 |
| portrait | normal | items | items / aidan | 26.5 |
| portrait | normal | items | items / fiona | 27.3 |
| portrait | normal | active-log | commands / aidan | 22.2 |
| portrait | normal | active-log | commands / fiona | 22.6 |
| portrait | raider | open | commands / aidan | 98.1 |
| portrait | raider | open | commands / fiona | 100.0 |
| portrait | raider | items | items / aidan | 91.9 |
| portrait | raider | items | items / fiona | 100.0 |
| portrait | raider | active-log | commands / aidan | 98.1 |
| portrait | raider | active-log | commands / fiona | 100.0 |
| landscape | normal | open | commands / aidan | 88.9 |
| landscape | normal | active-log | commands / aidan | 88.9 |
| landscape | raider | open | commands / aidan | 100.0 |
| landscape | raider | open | commands / fiona | 90.4 |
| landscape | raider | items | items / aidan | 100.0 |
| landscape | raider | active-log | log / enemy | 1.8 |
| landscape | raider | active-log | commands / aidan | 100.0 |
| landscape | raider | active-log | commands / fiona | 90.4 |
| landscape | raider | real-busy | log / enemy | 1.8 |
| landscape | raider | restored | log / enemy | 1.8 |
| landscape | raider | css-actionCinematic-probe | log / enemy | 1.8 |
| small | normal | items | items / aidan | 20.4 |
| small | normal | items | items / fiona | 21.8 |
| small | raider | open | commands / aidan | 97.3 |
| small | raider | open | commands / fiona | 100.0 |
| small | raider | items | items / aidan | 91.9 |
| small | raider | items | items / fiona | 100.0 |
| small | raider | active-log | commands / aidan | 97.3 |
| small | raider | active-log | commands / fiona | 100.0 |

## actionCinematic CSSゲート

以下のUIがCSS probeの保存矩形で表示された。実プレイで必ずこのclassを通ったという意味ではない。実busyの可視判定とは別の条件検査。

| 条件 | 非表示にならないUI |
|---|---|
| pc/normal | commands |
| pc/raider | log |
| pc-large/normal | commands |
| pc-large/raider | log |
| portrait/raider | log |
| landscape/raider | log |
| small/raider | log |

通常には#battleFieldがあるが、ボス測定stageはCOMMAND/HUDを含む#raiderBattle全体。両者で独立した右戦場へ構造を統一済みとは言えない。mode/is-visibleのCSSルールがactionCinematicの非表示指定を上書きしないかClaude側で検討する提案、CSS未編集。

画像では横ボスのログは敵HUDとも重なる（敵HUDは自動矩形比較集合に入れていない）。

## 方法と限界

タイマーで開始ログが消えた状態だけにならないよう、既存showBattleBanner/showRaiderBattleLogで「行動を選択。」を2500ms表示する準備を追加。スタイル/ゲームコードは変えない。実engine skill→guard→敵ターンを通しbusyを計測、終了後にCOMMAND toggle/展開windowが復元。actionCinematicは独立CSS gate probeと明記した。全技/全アイテムの演出ではない。

[50画像/生データ/ログ](battle-ui-structure-20261013/) に保存。再実行python tests/battle/ui_structure.py、自身の8831 server終了。Android実機未測定。仕様の適用はClaude/作者判断。main未統合、将来戻し方git revert -m 1 <merge>。
