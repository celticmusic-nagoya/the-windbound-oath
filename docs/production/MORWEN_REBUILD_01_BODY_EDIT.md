# MORWEN PR419 — 実全身造形 v02

## 実行範囲

既存編集原本 `assets/candidates/morwen-rebuild-01/body-workspace/MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED.blend` を使用。正式PNG再取得／SHA再照合／素体再download／参照シーン再生成なし。新PRなし。旧before PNG4枚を再利用し、afterだけ正面・背面・右・左を実レンダーした。

## 実形状変更

正式Layer0の足底、顎、肩、胸、腰、骨盤、膝、足首、手首／手先の位置をpixel座標で選択し、source上の対応高さ・断面と比較。直接見える輪郭と、衣類で隠れた皮膚／骨格joint／髪で隠れた頭蓋頂の推定をmesh-edit.jsonで分けた。
登録は前面中心x213.5、足底y1003、推定頭蓋頂y57（±20px）。正規化高946pxは画面上の比較尺度でメートルではない。7.5079頭身はこの推定頭蓋頂を使った設計値であり、イラストの頭蓋頂を直接測定して7.5頭身と証明した値ではない。

全身の単調cubic高さcageと幅／厚み／中心曲線、腕の解剖centerlineに基づき、実meshデータの12,502頂点すべてを変更。表示transformだけの変更ではない。面数12,500と接続を保持。頂点world差分の最大0.07817015、平均0.04034859（元身長1）。顎高は約0.8254→0.8668、股輪郭高0.4887→0.5328へ移動。胴長（肩–股station）は約0.2863→0.2896。脚長（足底–股輪郭station）は約0.4887→0.5328。これらのstation一致は輪郭全体の合格や骨格joint確定ではない。

## 数値比較

単位は登録画像px。断面bandに属する同じsource頂点を追跡した幅／奥行きであり、未校正の絵を正投影scanとしてIoU比較していない。各targetの不確実性はJSONに±6〜12pxで保存。

|項目|参照target|修正前|v02|絶対誤差の前→後|
|---|---:|---:|---:|---:|
|肩幅|180|188.2|161.4|8.2→18.6（悪化）|
|腰幅|100|123.8|104.0|23.8→4.0|
|骨盤幅|198|173.1|187.2|24.9→10.8|
|胸幅|140|183.4|149.5|43.4→9.5|
|膝外幅|124|137.2|150.9|13.2→26.9（悪化）|
|左右足の外幅|116|146.0|142.8|30.0→26.8|
|腰の奥行き|110|91.5|120.5|18.5→10.5|
|骨盤奥行き|140|103.6|134.5|36.4→5.5|
|胸の奥行き|142|94.0|117.1|48.0→24.9|

手首領域の横位置は194.9→125.1px（target143、身体側へ約17.9px行き過ぎ）。手先領域は198.0→134.5px（target143）。領域重心であり厳密な関節中心ではない。姿勢差と左右viewの非校正を残存制約として明示する。

## 成果物と独立QA

- `assets/candidates/morwen-rebuild-01/body-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend`：実編集mesh。原本／v01を上書きしない。
- 同directoryのfront/back/right/left.png：変更後4方向、既存beforeと同じcamera・照明・framing。
- `docs/qa/morwen-rebuild-01/body-fit-v02/four-view-comparison.png`：正式画像／既存before／afterを並列表示。キャンバス比率差があるので重なり率と誤認しない。
- landmark-height-comparison.png、measurement-table.csv、mesh-edit.json、measured-residuals.json、vertex-delta.npz、Blender実行log、再open技術QA。
- `INDEPENDENT_ART_QA.md`：別AIレビュアーが正式4画像・before・after4PNG・comparisonを見て、両.blendを独立再open。12,502頂点の変更と接続保持を確認。

独立G2 **FAIL**。v02で初版の上腕pinchは改善したが、肩端／腋、上腕–前腕、膝下腿、臀部の面band、足の形・stanceが未合格。新しいゼロ面積first triangleは0、有限座標／保存差分一致はPASS。ただし法線変化>90°のfirst triangle38面があり局所screen FAIL、交差・UV歪み・変形未検証。face-normal角度だけで自己交差／反転確定とはしない。

身体G1 PASS（既存結果維持、再照合なし）。最終衣装・外観G1は別課題。G2 FAIL、G3全体NOT_RUN（局所screen FAIL）、G4 NOT_RUN。今回の「変更mesh保存と4viewで確認」の完了条件は満たしたが、正式採用／高品質素体合格ではない。

同cagefamilyはv01/v02の2回失敗で停止。3回目のthreshold微調整はしない。次は肩腋と膝下腿の局所quad-flow／解剖surface sculptへ方式を変更する。全身G2が未PASSのまま精密顔・髪・衣装・rigへ進まない。v5.61未取得を身体作業の停止理由にしていない。mainmerge／正本置換／公開なし。
