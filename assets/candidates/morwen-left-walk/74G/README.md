# MORWEN-ASSET-74G 左向き歩行 最終品質調整（候補・本番未反映）

ベース: ART-74F-C（`cd5525c`）。動き・周期・接地・デザインは74F-Cと同じで、画質だけを調整した版。
74A〜74F・右向き72・公式設定画・本番素材は変更していない（SHA-256一致をQAで確認）。

## 変更点（74F-C → 74G）

1. **1px孤立点の削減**: 周囲と色が繋がらない単独ピクセルを近傍色に統合（全24枚で241点）。顔・目・耳飾りとブーツの金の鳩目は保護し、輪郭は触っていない。
2. **金装飾のちらつき抑制**: 上下動のずれを切り替える行を、金の装飾や横エッジが最も少ない行（首56／腰81）に固定。装飾の途中でずれが入らない。
3. **48pxの安定化**: 48px版を「ずらす前の96px」から同じ格子で縮小し、そのあとで整数ずらしを適用。コマごとに縮小の位相が変わって模様が崩れる問題を解消。

## 比較（QA_REPORT_74G.json）

| 指標 | 74E | 74F-C | **74G** |
|---|---|---|---|
| 1px孤立点 96（平均/コマ） | 18.6 | 20.5 | **4.3** |
| 1px孤立点 48 | 3.42 | 3.50 | **0.67** |
| 金のちらつき（画素数CV）96 | 0.0092 | 0.0215 | **0.0178** |
| 金のちらつき 48 | 0.0348 | 0.0484 | **0.0331** |
| 色数 96／48 | 2488／735 | 2475／735 | 2467／724 |
| 穴（最大） | 2 | 2 | 2 |
| 足滑り（96、px） | — | 0.53 | **0.53**（悪化なし） |
| 周期 | — | 840 ms | 840 ms |
| F11→F00の差分／他コマ間の最大 | 4200／4147 | 2072／4218 | 2075／4250 |

シルエット差（74F-C比）: 96pxは55行目と81–82行目のみ1〜6px。48pxは14〜53px差（48pxで出ていた1pxの腰の上下を、安定縮小で出さなくなったため）。

## 採用判断

**74Gは74F-Cより正式採用に値する。** 動き・デザインが同じまま、孤立点が約1/5、48pxの金のちらつきが約3割減で、悪化した指標はない。
ただし正式化の前に以下が必要:
- 第三者美術QA（`qa_preview_74G.html`）: NOT_RUN
- Android実機QA: NOT_RUN
- 歩行速度の扱いの決定（`SPEED_AUDIT_74G.md`）。300 px/sでは素材どおりの歩きは約12倍速く、距離連動でも足滑りは消えない。
- 96pxの金のちらつきは、74E（0.0092）にはまだ及ばない（上半身の位相差によるもの）。

## ファイル

| ファイル | 内容 |
|---|---|
| `morwen_left_walk_74G_12f_{00..11}_{96x128,48x64}.png` | 12コマ |
| `morwen_left_walk_74G_12f_sheet_{96x128,48x64}.png` | シート |
| `morwen_left_walk_74G_12f.gif`／`_48native.gif`／`_48x3.gif` | 単体GIF |
| `COMPARE_74FC_vs_74G_96x2.gif`／`_48x3.gif`／`_48native.gif` | 同期比較GIF |
| `COMPARE_74FC_vs_74G_x3.png` | 偶数コマ比較 |
| `COMPARE_OFFICIAL_74FC_74G.png` | 公式設定画との比較 |
| `BACKGROUNDS_74G.png` | 苔の森／草原／洞窟（暗・模擬）／夜（模擬） |
| `qa_preview_74G.html` | 第三者・Android QA用プレビュー |
| `QA_REPORT_74G.json`／`SHA256SUMS_74G.txt` | 技術QA／ハッシュ |
| `SPEED_AUDIT_74G.md`／`audit/` | 速度調査と測定スクリプト |
| `build_morwen74g.py` ほか | 再生成スクリプト |

## 再生成

```
MORWEN72_PIPELINE=<build_morwen66..71 のあるdir> python3 build_morwen74g.py \
  --ref74c ../74C/REFERENCE_left_side_edit_right_coords.png --source ../74A/source_65B_F00 --out .
python3 qa_morwen74g.py ...   # 引数は --help
python3 make_sheets74g.py --art . --f74 ../74F --repo ../../../.. --official <公式左向きPNG>
python3 make_qa_preview74g.py --art . --f74 ../74F --ground ../../../../img/field/moss/art --out qa_preview_74G.html
```

QA区分: 技術QA PASS／自己美術確認 済／第三者美術QA NOT_RUN／Android実機 NOT_RUN。
