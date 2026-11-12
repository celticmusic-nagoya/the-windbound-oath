# MORWEN-ASSET-FIX-03 納品・受入手順（技術QA：Claude）

編集を始める前に、修正してよい範囲を宣言した（`morwen.layer-template.json` の `correctionTargets[].zonesCanonPx`。座標は正本の画素、推定値）。枠だけを描いた透過PNGは `edit_zones_back.png` と `edit_zones_right.png`。

| 方向 | 編集元（SHA-256） | 修正範囲 | 納品の条件 |
|---|---|---|---|
| 背面 | `back.png` `15c9d452…` 1152×1536 | Z1 スカートの裾からガーター上端（480,785〜690,835）、Z2 太もも帯・両脚（470,835〜740,920） | 1152×1536、RGBA、背景は α=0、局所編集のみ |
| 右向き | `right.png` `f5b5787c…` 1200×1600 | Z1 帽子の花・リボン・飾り（320,90〜560,515）、Z2 手前の腰のバッグと背後（410,690〜630,935）、Z3 手前の胴のストラップ（600,540〜690,760）、Z4 ガーター（600,860〜700,975） | 1200×1600、RGBA、背景は α=0、局所編集のみ |

納品する場所: `assets/candidates/morwen/fix-candidates/<view>-fix03-<n>/`。PNG と、SHA-256・制作者・編集元のSHA・編集方法・変更範囲を書いた `MANIFEST.json` を一緒に置く。

受入の確認（`--provenance` には MANIFEST の制作元を渡す）:
```sh
python3 tools/character-asset-studio/layer-template/verify_fix_candidate.py \
  tools/character-asset-studio/layer-template/morwen.layer-template.json back <PNG> --provenance "<制作元>"
```
自動で判定する項目: 寸法、RGBA、外周の画素、体の部分の不透明度、背景の透過（99.5% 以上）、修正範囲内の変化、範囲外の変化（2% 以下）、正本 SHA の保護。

人間が確認する項目（NOT_RUN）: デザインの一致、非対称デザインの位置。

同じ方法で2回失敗したら再生成をやめ、手動のレイヤー編集に切り替える。失敗の回数は `attemptPolicy` に記録する。背面は、全体を再生成する方法ですでに1回失敗している（7776.png）。
