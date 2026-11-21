# 風待ちの崖｜精密設計図と造形候補

Draft PR #421、基準 `9558af4bac2e605e616f6447fbdc8dd92c310588`。Blender 5.3.0、Z-up、海側 −Y、暫定BU。現行mainの正式CG `assets/approved/game/cliff/sunset_background.png` とSHAを照合した。

## 設計図と測定データ

[PDF](cliff-blueprint.pdf) は8ページ。[正面・背面・左右・上面](01-orthographic-views.svg)、[横6断面](02-transverse-sections.svg)、[縦6断面](03-longitudinal-sections.svg)、[境界・岩棚・谷・面法線・トポロジー](04-rock-topology.svg)、[写真PBRとUV](05-photo-pbr-and-uv.svg)、[可視面と遮蔽](06-visibility-and-occlusion.svg)、[道路・歩行・衝突](07-road-and-collision.svg)、[正式CGとの差分](08-official-cg-comparison.svg)。正投影の面塗りと比較写真は図面内の画像、輪郭・断面・注記はベクター。

- `structure.json` はBlender原本の旧キャリア、編集用ロフト、結合した候補、道路の頂点・辺・面構成・材質ID・面法線・傾斜角・UV・三角分割を収録。 `measured-sections.json` に三角形と平面の実測交線および材質境界の頂点IDを保存した。岩盤と草地の線は明示的な材質スロット境界で、旧地表のシェーダー内で混合される草色は材質IDからは分離できない。
- 正式CGの外郭・露岩は画像上で手計測。現況の固定夕景は418×235本の最前面レイで新しい頭部の岩材を計測し、旧536→候補3,596画素。CGとBlenderはカメラ未登録で、露岩の面積差は投影上の指標。正式CG内の見えない深度、世界寸法、配置は推定・暫定として区別した。

## 実造形

- カメラと既存の歩行面を固定し、主岩壁をその視線内に張り出す幅広い断面へ組み換えた。上段と下段の岩棚、張り出し、二つの岩肩と谷には別の奥行きと高さを与えた。高さ調整に加え、陸側斜面を段状に戻した。
- 新岩体と旧キャリアを陸側で結合し、ネイティブ原本には編集用の成形前メッシュも非表示で保存。結合メッシュの非多様体辺0。非隣接のBVHペア1件は精密分類で接触、真の交差0。
- Poly Haven *Rock Boulder Dry* のCC0写真PBR。検証済みbase color、normal、roughnessをパック。Blender結合後も新岩面の材質IDを転送し、GLBのUV0に該当面のUVと接線を整合させた。旧草地・道路・既存キャリアの材質とランタイム衝突を継承。
- 歩行11,372点と植生54点の描画面支持高さの差は0 BU。試遊では従来の衝突・レイキャストを使用し、同一出発点とカメラから移動・接地・風の停止再開を確認した。正式寸法・本編・Android実機は未検証。

レビューには `comparison.png` と6視点のBlender実レンダー、固定WebGLの出発・移動・風画像を使用。試遊の候補URLは `/dev/windwaiting-cliff/?cliff-blueprint=1&photo=1`。写真なしは `?cliff-blueprint=1`。写真PBRの取得元は [以前の手順](../composition-v1/README.md)。アーカイブ内の `SHA256SUMS` を確認してから使用する。

**独立美術QA G2 FAIL。** 固定夕景の主岩壁は露出したが、手前の草地が岩壁下端を隠す。二つの岩肩と谷の視覚的分離、規則的な岩肌、陸側の暗い接合は継続課題。最終原本と検視画像のハッシュおよび判断は `independent-art-qa.json`。

固定WebGLは252,582三角形・111 draw callsで、直前候補より1,036三角形減。造形原本とGLBは `tools/map_blender/lind/build_windwaiting_cliff_blueprint.py`、固定夕景の画素レイは `measure_windwaiting_cliff_projection.py`、PDF/SVGは `draw_windwaiting_cliff_blueprint.py` で再生成できる。前二つはBlender 5.3、図面はPythonのNumPy、Matplotlib、Pillowを使用する。図面生成には同じ出力先に `old-sunset.png` と `native-sunset.png` が必要。
