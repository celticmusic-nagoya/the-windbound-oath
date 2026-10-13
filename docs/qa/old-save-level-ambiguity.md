# EE: 旧セーブ座標と高さの曖昧さ

基準game main3208079。新規validatorはheight付きmap/overlay全件を読み、integer>=0かつ宣言floor存在を確認し、実FieldCollision/FieldHeightでspawnの22×10足元と入口からの到達を検査する。bool/文字列/小数/負/未定義floorのspawn.level負例をself-testで拒否。

旧saveのx/yはactor左上、map spawnはfeetである（feet=actor+[17,42]）。levelなし復元は座標の事前衝突判定→最高階derive→connector commitの順。表は全上階walk矩形に対し5代表点を調べた曖昧領域であり、連続座標の全pixelを列挙したものではない。blockerと接続端では候補/補正が異なるのでJSONの各exampleを確認。フラグOFFの通常mapには変化なし。

|map/spec|上階矩形|feet矩形|actor XY代表点|合法floor|derive→commit|事前衝突判定|
|---|---:|---|---|---|---|---|
|dev_height_proto|0|[1500, 480, 120, 640]|[1543, 758]|[0, 1]|1→1|True|

## 名前付きspawnの旧座標解釈

|map|spawn|現在declared/derived floor|old XY actor|old derive→commit|old XY事前受入|
|---|---|---:|---|---|---|
|dev_height_proto|start|0|[283, 1208]|0→0|True|
|dev_height_proto|deck|1|[1543, 558]|1→1|True|
|dev_height_proto|plateau|1|[1983, 208]|1→1|False|
|dev_height_proto|under|1|[1543, 858]|1→1|True|

## 要判断

同じXYに下層と上層が存在すれば、levelなしでは元の意図を復元できない。highest deriveは地上を橋面へ変更する場合がある。自動移行を採用せず、領域ごとの作者判断/安全spawnへの誘導案を別レビューする。runtimeのfinite検査だけでは負/小数/未定義floorを防げないため、schema検査に加えload側の防御をClaudeへ提案する。コード/セーブ構造は変更していない。AA cliff draftは別branchで未採用なのでこのmain監査には含まない。heightの本編有効化とAndroid実機確認は未実施。旧XYの事前受入がfalseなら実restoreはspawnへ退避するため、derive→commitは座標を保持できた場合の参考値である。
