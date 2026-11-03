# DIRECTIVE-ART-08F — Codex independent QA

**PASS（QA観点）。推奨周期72。PR #112は未マージ。**

対象HEAD: `42509215520ac129cf14c83d436f448d1487dd83`。
比較main: `693995082bbb10e017ee25af34476a910acb440b`、merge-base: `85fa7770c61ac20f093390c038ab2d8dcb4191e8`。
26C監査を先に完了（連続到達9/11のPARTIAL、リアム加入不能を別P1として確定）した後に着手した。

## 結果

| 確認 | 結果・根拠 |
|---|---|
| 左右6コマ | 全12PNGのSHA・2048×1280 RGBA一致。01/04で前脚が交互、02/03と05/06は奥・手前の役割を交換。既存stripを目視し、明らかな足の切断・アンカーずれなし |
| 実描画 | 50/72/90 × PC1920×1080・縦390×844・横844×390、9/9ケースPASS。実DOM画像の全6状態、左右とも6→1を最低2回観測。画像decode成功、実移動量>250、停止時idle・bob終了を検査。`live/results.json`と各ケースright/left.json・PNG・WebM |
| 停止・再開・方向 | 左右、down/up、同一contextでの画面サイズ反転後も実画像と移動を確認。歩ける・相互作用zone外の床へtrusted touchを送り、目標へ到達（約113world移動）。Fionaも既存画像で追従 |
| 周期比較 | 距離駆動の位相を観測。50の周期推定は約50、72は約70～75、90は約87.5～90world（フレーム境界の量子化を含む）。50は接地に近いが速く、90は読みやすいが滑りが増す。72は折衷として妥当。滑りゼロとは判定しない |
| PCの録画負荷 | PC72は録画ありrAF約26.3/s、なし約57.4/s（rightの観測窓）。録画なし追加1/1ケースPASS、左右の観測コマ飛び0。左向きの実速度は録画なし約300world/s。録画ありのコマ飛びを端末性能の不具合と断定しない |
| 正面・背面・Fiona・旧画像 | 向き判定JSとFiona registryはmainと同一。既存mainのimg1000ファイルすべてバイト不変。元の左右4コマも保持。回帰m9/m31/m10/m12/m11_dev_lazy/m8の6/6 PASS |
| 正式259PNG | 259/259固定SHA一致。`independent-static.json`、26Cの固定SHA一覧と照合 |
| console/Promise/HTTP | 最終live9ケースのpageerror/console error/HTTP4xx5xxは0。requestfailed全件の専用監視やOS性能測定ではない |

右向き直線測定の終盤には河川境界で停止するサンプルも含む。周期評価はwalkフレーム区間、速度の比較は障害物のない左向き区間を使用した。全区間を等速・無衝突と主張しない。録画の時刻とpage performance時刻は厳密同期を保証しないため、`actual-72-contact-sheet.png`は実表示の抜粋であり、キャプションから各コマIDを断定しない。コマID・6→1の根拠はrAFの実DOM観測とPNG照合。

## m31の間欠FAIL

原版・未変更テストを直列、main/PR交互に各5回。**main5/5、PR6/6（回帰1回＋追加5回）PASS**。`regression-summary.json`と各結果JSON/原ログ。元の間欠FAILは再現せず、消失・解決とも断定しない。

別診断ではArrowLeft→ArrowDownの間隔を0/30/120msで与え、180ms間の実移動・実DOMを取得。main/PR双方で入力直後のleft→down過渡を再現（`input-probe.json`）。向き判定はEMA+ヒステリシスを描画フレームごとに更新する既存処理で、原版m31は順次keydownと壁時計60ms後の採取を組み合わせる。負荷時に横向きを拾う原因候補として整合する。ただし歴史的な1件のFAILを直接再現した証明ではない。推奨は別QA案件で入力時刻と描画フレームを記録し、対角入力成立前／平滑化の過渡／成立後の継続表示を区別すること。期待方向まで待ってから採取して不具合を隠す修正は避ける。

## QA helperの失敗と限界

ゲームや正式画像は修正していない。最初はPlaywright用FFmpeg不足でブラウザ生成前に失敗し、scratchへ公式FFmpegを導入。旧測定の失敗はすべて保存した。

- `live-attempt1`: 高速周期で01を観測し損ねると、次の観測01まで複数周期になる。全間隔を1周期とする検査を修正。位相の1コマ幅に起因する距離の量子化も扱った。
- `live-attempt2/3/4`: 固定タップ先が石碑／NPC相互作用範囲に重なり、会話が始まって移動しない試行。最終版は歩行可能・NPC zone外の床を選び、目標座標への到達も保存値から照合した。
- `live-mixed-road-attempt5`: 石碑回避で実際にdownへ向きを変え、位相がリセットされた。これを1本の直線周期として扱った検査が不適切。比較地点をx1100,y640へ統一し、旧試行とは別に9ケースを完走。
- `input-probe-invalid-idle`: 遅延したarrival会話により入力が動いていない無効試行。PASSには使わず、修正版は会話終了後に実移動>10を必須にして再実行。

ARTは独立した描画fixture（DEV forest、stage=1、enterMap、通常経路goFeet）であり、26Cの同一履歴や通常到達性の証明には一切使っていない。26Cの永続profileは触っていない。Androidはviewport/touch相当のみで実機は未実施。

## 重大な問題・マージ可否

PR #112固有の重大問題は検出なし。残る滑り、腕・マントの追加モーションは既知の範囲。26Cで確認したリアム加入不能は別のP1であり、このPRの歩行変更による回帰ではない。

QA上は周期72で進行可。GitHubではPRはDraft、mergeable/mergeStateStatusはUNKNOWN、必須チェックを満たすという最終判定は未実施。ユーザーの承認なしにmain変更・PRマージは行わない。PR #109/#111の個別マージも行っていない。Pages公開・本番反映は実施せず。

全成果物は`/workspace/work/art08f/`。PRと比較mainのworktreeはともにclean。26C監査のローカルHEADは`5913d1a4fc86449d3f7bffe22ce4a03c4354b9ca`で維持。

最終独立証拠監査: **PASS**（`independent-final.md`）。自己照合: `validation.json`、成果物SHA: `SHA256.json`。
