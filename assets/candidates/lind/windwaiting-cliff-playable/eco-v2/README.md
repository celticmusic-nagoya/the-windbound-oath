# 風待ちの崖｜ECO v2 試験統合

PR #357 の `1c8d0ebf69022f83806a837669ce57156b0dbb68`、Actions run 44730162099、artifact 14626605689 を入力に使用。ZIP SHAと全99エントリーを再照合した。採用した7つのLOD1 GLBと苔PBRの元ファイルは `source.json` にSHAを固定した。草地LOD2は収録・ロード・配置の対象外。原本とナビゲーションのバイト一致はテストが検証する。

## 配置と描画

- 草地LOD1は近景3タイルと夕景の要所14タイル。適地は支持面、傾斜、縁の周辺サンプル、路面・既存障害物の除外で絞った。
- 中遠景は草地の地表PBRと疎な低木・広葉樹。広葉樹の根元と回転は既存の位置を継承。花は白と紫の計4群生で、各群2〜3株。路面を空けた。
- 苔のbase color、normal／微細な凹凸、roughnessを既存岩材のシェーディングへ混合した。Blenderは法線と凹部、WebGLは法線と凹部の近似マスクを使う。既存の106メッシュは形状SHA一致。地形、衝突、道路のデータは従来のGLBとJSONを使用する。
- 各植生を役割別の距離帯と視錐台で絞り、可視インスタンスを共有ジオメトリ・マテリアルのバッチへ詰める。初回の区画別バッチは静止視点で123 draw callsだったため、区画ごとの描画をやめ、アセットごとに集約した。
- 揺れはECO GLBの `_WIND_WEIGHT` と `eco_wind` を使用。共有の `lind_wind_strength` が0の場合は頂点変形をスキップする。試遊では同名の制御を `lind-wind-strength` イベントの数値 `detail` から受け取れる。

## 前後比較

| 視点 | 統合前 | 統合後 |
| --- | --- | --- |
| Blender 夕景 | [前](render-before-sunset.png) | [後](render-after-sunset.png) |
| Blender 試遊方向 | [前](render-before-gameplay.png) | [後](render-after-gameplay.png) |
| WebGL 出発点 | [前](web-legacy.png) | [後](web-v2.png) |

Blenderは同じカメラ・照明・770×434・Cycles 12サンプル。WebGLは同じ出発点・カメラ・960×560、風0と水面位相固定。ブラウザの最初の4フレームを除外した12フレームを記録。タイミングはソフトウェア描画環境の計測値。詳細は [比較JSON](comparison.json) と [移動・接地・カメラ回帰QA](browser-qa.json) を参照。

| WebGL計測 | 統合前 | 統合後 |
| --- | ---: | ---: |
| 三角形数 | 447,825 | 255,920 |
| Draw calls | 106 | 108 |
| フレーム時間 中央値 (ms) | 1,700 | 1,150 |
| フレーム時間 p90 (ms) | 3,417 | 2,133 |

風を動かした2フレームの画像差と、停止連続フレームのPNGバイト一致を検証した。風停止後は開始時のゼロ姿勢に完全一致。

旧G2判定を引き継ぐ。ECO v2統合シーンの独立美術レビュー、Android実機、本編への統合、正式採用は未実施。

## 村・森林への再利用

`tools/map_blender/shared/vegetation_placement.py` は、シーン側が地表の高さ・法線と、道路・水・建物などの除外判定を渡す仕組み。配置範囲、密度、役割、群生の中心はシーン別。生成した配置データとGLBカタログを `dev/shared/vegetation.mjs` に渡すと、描画と風を共用できる。村・森林では配置ルールとローカル尺度を各シーン側で与える。

再生成はBlender 5.3.0で `tools/map_blender/lind/build_windwaiting_eco_v2.py` を実行する。編集原本は `cliff_eco_v2_UNAPPROVED.blend`、試遊のGLBは変更前の地形とECOオーバーレイを別ファイルからロードする。
