# モスの森追加素材20種 配置結果 (2026-10-19)
- 登録: img/field/moss/manifest.json に node ルール20件 (gen=moss_additional_20261019、スタンドイン規則の直前)。既存ルールの解決結果は不変（変化は20ID＋既存プレースホルダー参照の rock_moss_01-03 / tree_ancient_* / tree_log_hollow_A3_01 のみ）。
- 配置: tools/moss/place_additional_assets.py。A1 38 / A2 34 / A3 22 の追加props（`p_add_*`, noCollision）＋装飾コライダー `cb_add_*`（scatterIgnore）。既存props/blockers/イベント/スポーン/遷移は不変（JSON差分で確認）。散布(RNG)出力は3マップとも配置前後で完全一致。
- 古代樹/センチネル/倒木 (A3既存配置): 実素材に差し替わり表示（既存の当たり判定プリセットは未変更）。
- 画像: 品質調整済み派生PNG (img/field/moss/art/)。原本は docs/art/delivered/moss_additional_20261019/originals。
- スクショ: PC/縦/横。Android実機 UNVERIFIED。
