# MORWEN PR419 — 局所surface造形01

## 実制作と方式

元はbody-fit-v02/MORWEN_BODY_FIT_V02_UNAPPROVED.blend。12,502頂点の全身原本を保持し、全身cage式は実行しない。肩・腋と膝・下腿の局所パッチだけにmesh隣接bi-Laplacian fairingと解剖位置handleを適用。外部境界はhard固定。Python著者指定の局所vertex-surface sculptであり、手動GUIスカルプト／retopologyを行ったとは主張しない。

実変更3,422頂点、範囲外9,080頂点のlocal座標は完全一致。最大world変位0.02367472（元正規化身長1）。12,500 quadの接続を維持。元v02と正式参照を上書きしない。参照再取得／SHA再照合／素体再download／参照scene再生成／旧全身before再renderなし。

## 局所操作と保護

肩端と腋–上腕の急な面変化を局所緩和し、deltoid幅を参照寸法へ近づけた。膝・下腿は局所centerline／断面とsurface遷移を修正。足・上腿境界は固定。

中央胸346頂点、腰／骨盤、頭、手、足は固定範囲に含む。ただし胸測定band104頂点中34は腋へ続く支持面として移動した。胸全体が不変とは言わない。中央主要胸面の座標、胸band bboxの全軸、腰・骨盤の改善寸法は維持された。

参照絵は校正済み正投影scanではなく関節中心は推定。幅は前工程と同じsource頂点bandを追跡した登録pxであり、厳密な解剖精度／silhouette IoUとは区別する。

|項目|参照target ±不確実性|v02前|局所後|絶対誤差 前→後|
|---|---:|---:|---:|---:|
|肩幅|180 ±10px|161.42|182.33|18.58→2.33|
|膝外幅|124 ±10px|150.94|128.27|26.94→4.27|
|胸幅|140 ±10px|149.47|149.47|9.47→9.47|
|腰幅|100 ±6px|104.04|104.04|4.04→4.04|
|骨盤幅|198 ±8px|187.22|187.22|10.78→10.78|

隣接1ring残差平均: 肩腋0.001508→0.000681、膝下腿0.000391→0.000373。これはfairing機械指標で、美術合格を証明しない。

## 保存済み成果物

assets/candidates/morwen-rebuild-01/body-local-v01/: 編集原本MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend、全身after4PNG、before/after肩正面・背面・右と膝正面・右の拡大10PNG、shoulder/knee frontのwireframe2PNG。全身512×768、frame内確認。拡大は意図的crop。原本初期cameraは全身正面。wire材質は診断render限定で、原本材質には保存していない。

docs/qa/morwen-rebuild-01/body-local-v01/: four-view-comparison.png（正式／既存v02／after）、local-before-after.png（同じ局所camera／照明）、local-topology.png（既存quad-flow検査）、JSON、CSV、vertex差分NPZ、実行log、独立QA。

## 独立QAと残存差

別AIレビュアーが元／変更原本をscripts無効で独立再openし、3,422変更、9,080固定完全一致、全face index lists一致・有限座標を確認。実局所編集と指定pinch／急な面変化の軽減は限定PASS。

G2局所正本解剖FAIL、全身G2 FAIL。外へ張る丸い肩cap、深い腋溝、膝profileの強い曲がりと平坦な前面、立ち姿が残る。胸全体不変や完成解剖面とは扱わない。

境界edge0、3面以上共有edge0、新規ゼロ面積first triangle0。ただしcage以前source法線に対する90°超flagは38→36（17解消／15新規）。新規は側胸・腋・上腕境界。単純な技術改善合格ではない。角度flagだけで反転／自己交差は確定しないが未解決懸念。自己交差・UV歪み・rig変形は未検証。

身体G1 PASS（既存結果維持）、G2 FAIL、G3全体NOT_RUN（法線診断FAIL）、G4 NOT_RUN。正式採用しない。v5.61未取得を身体工程の停止理由にしない。

## 失敗履歴・次工程

旧全身cageは2回FAILでSTOP維持。local differential surfaceは今回初回。目標幅と段差は改善したが、固定境界と既存腋接続を保持した曲率最小化だけでは解剖形状と法線懸念が解消しなかった。

fairing強度／回数を増やすだけの反復はしない。次は保護胸境界を維持した肩腋の解剖quad patch、deltoidから腋への意図的な流れ、膝蓋骨–腱–脛骨のsurface制御が必要。改善checkpointと固定torsoを引き継ぐ。顔・髪・衣装・rigへ進まない。正本変更・mainマージ・公開なし。
