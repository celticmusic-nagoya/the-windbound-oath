# モルウェン Layer 0 マスター素体候補 v0.8（MORWEN-LAYER0-01）

**状態: 未承認の候補（UNAPPROVED_CANDIDATE）。デザインと骨格の最終的な採用判定は NOT_RUN のまま。** 正式採用はディレクターが判断する。

1つの3D骨格（`joints3d`）を4方向に投影した、中立的なマネキン型の構造ガイド。キャンバスは 1200×1600、接地点は (600, 1540)。正面と背面は左右対称の骨格で、側面は同じ骨格を横から投影したもの。モルウェンは17歳のため `minor_neutral_structure` を使う（頭・胸郭・骨盤・手足の単純な形だけで、解剖学的な細部は描かない）。

作り方: `python3 tools/character-asset-studio/pipeline/cas.py master-body --character morwen --observations <このフォルダ>/observations_v0.8.json --layer0-evidence tools/character-asset-studio/layer0/morwen-v0.7/landmark_evidence.json --transforms tools/character-asset-studio/normalized/morwen-final-canon-20261111/view_transforms.json --out-dir <このフォルダ> [--overwrite]`

## ファイル
| ファイル | 内容 |
|---|---|
| `MASTER_BODY_SPEC.candidate.json` | 共通骨格のパラメータ（値・状態・導き方）、3D関節、方向ごとの投影座標。BASE_BODY_SPEC v2.0 互換のランドマーク（`baseBodySpecV2`）も含む |
| `front／back／left／right_structure_guide.png` | 独立したガイドPNG（RGBA、透明背景）。正本の画素は含まない |
| `*_structure_overlay.png` | 正本（正規化した作業用コピー）に半透明で重ねた比較画像。衣装の外にはみ出した構造は赤で示す |
| `BODY_CONSISTENCY_QA.json` | 寸法・整合のQA |
| `production_brief.json` | 画像を作るAI（ChatGPT）への制作指示。各点の状態（VERIFIED／ESTIMATED／DESIGNED_CANDIDATE）を記録している |
| `observations_v0.8.json` | 正規化した画像を AI（Claude）が目で見て記録した観察値（ESTIMATED） |
| `MANIFEST.json` | このフォルダの SHA-256 |

## パラメータの状態
| 状態 | 項目 |
|---|---|
| VERIFIED（正本から自動で計測） | 接地 y=1540、中心 x=600 |
| ESTIMATED（AIの目視、人間の確認なし） | 顎 y=335、正面の手首（y=772、中心からの幅 219） |
| DESIGNED_CANDIDATE（新しい設計値。実測値ではない） | 頭頂 y=175（帽子に隠れているため設計。確認用の範囲 167〜186）、頭の高さ 160・幅 125・奥行き 144、首の付け根 y=395、肩 y=430（中心から ±115）、腕の長さ 357、胸郭の下端 y=600、骨盤 y=744（股関節 ±50、骨盤ブロック ±78）、膝 y=1076（±37）、足首 y=1470（奥行き −36）、足の幅 ±37、身長（靴を含む）1365＝8.53頭身 |

- 設計値はそれぞれ、導き方を JSON の `derivation` に書いている。衣装（帽子・ケープ・スカートの帯）の輪郭は、関節の上限・下限の目安にだけ使い、体の寸法としては使っていない。
- v0.7 で方向ごとに観測した膝の位置（1059〜1093px）は、未承認の観測値として `unapprovedObservationsKept` に残した。共通の膝の高さ y=1076 も未承認の設計候補のまま。
- 正面の顔の中心は x≈605 だった。v0.6 の首の推定（x=580）とずれているが、v0.6 のデータは変更していない（`observations_v0.8.json` に記録）。

## QA（`BODY_CONSISTENCY_QA.json`：PASS 57／FAIL 0／BLOCKED 0／NOT_RUN 16、採用不可）
- PASS:
  - 4方向のキャンバス（1200×1600 RGBA）、透明領域、接地点 (600, 1540)、頭頂の線 y=175
  - 正面と背面で、頭身・肩幅・骨盤幅・脚の長さが一致する
  - 正面の骨格が左右対称で、左右の側面が鏡像になっている
  - 3Dで左右の手足の長さが一致する
  - 頭頂・骨盤・膝・接地の基準線が4方向で一致する
  - VERIFIED の接地点と一致し、正面・背面の足の接地点は靴底の幅の範囲内（10px 以内）
  - 構造が衣装の内側に収まる割合（front 99.8%、back 99.8%、left 98.2%、right 99.1%）
  - 正本17件の SHA-256 が変わっていない
- NOT_RUN（人間の確認待ち）:
  - デザイン保護の12項目
  - 側面の手首の観測値との差（−15px）
  - 独立した目視QA
  - デザインと骨格の最終的な採用

## 画像生成の後
画像生成AIの出力に1pxの精度は期待しない。生成した画像は次のコマンドで頭頂・接地・接地点の x を数値で測る。ずれている場合は、均等な拡大縮小と整数ピクセルの平行移動で、新しいファイルに補正する（描き直しはしない）。

`cas.py master-body-fit --spec MASTER_BODY_SPEC.candidate.json --view <方向> --image <生成画像> --out <新しいファイル>`

テストでは、わざと縮小・移動した画像を補正し、誤差 2px 以内に戻ることと、同じ結果が再現されることを確認した。
