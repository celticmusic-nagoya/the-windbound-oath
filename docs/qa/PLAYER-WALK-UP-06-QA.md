# PLAYER-WALK-UP-06-QA — PR153 最終独立QA

対象固定HEAD `c15a715fe450e76820153e71ea7b04e70e258d6d`。基準main `6e28466751f124fc5a483be3d89c65f35a320b5c`。専用branch `feature/player-walk-up-06-qa`。本番採用・mainマージ・Pages公開は行わない。Claude自己QAは根拠資料として読み、独立計測／実際のDEV描画で再検証した。

## 画像の独立検査

候補 `assets/candidates/player-walk-polish01/up-06-left-boot-outline/aidan_walk_up_pushoff_candidate_v2.png`、SHA256 `1bde96684c85739e821e8c7e5e8f07831b8819414569d07d6a3bbb3613e80dfd`。

- RGBA2048×1280。正式03との差18,549px。元マスク37,699px＋記録された29px拡張の外のRGBA差分0。PR152との差248px＝輪郭216px＋透けの補修32px。既存原本／候補を加工せず独自NumPy/SciPy/Pillowスクリプトで再計算。
- 拡張29pxは包含矩形[1123,973,1135,996]、全座標は独立metrics.jsonへ記録。完全不透明alpha255の正式画素はこの拡張部で変更なし。**元alphaの実範囲は26〜200**（200が1px）。元資料の26〜67という記載は訂正が必要。
- 実PNGの左ブーツ輪郭は25行閉処理の独立測定で最大段差8→1画像px。作者の目標輪郭0pxとは計測対象が違う。残差は等倍0.0625CSSpxであり、明確な画像破綻ではない。
- 編集脚部の閉じた穴はalpha24/128/200基準すべて0。全画像のalpha24基準では正式03から存在する20pxが編集範囲外に残り、候補で増えていない。「全域0」と「編集部0」を区別する。
- 最下行は正式03と同じ（alpha>0は1229、>128は1227、>200は1225）。PNG自体にゲームアンカーは格納されていないため、DEV実描画で(1024,1230)・scale.0625・全2048×1280表示を別途検証。

黒／白背景・原寸／拡大で、左ブーツの板装甲・輪郭・膝から靴のつながりを独立目視。216pxの補間は既存装甲の連続として馴染み、膝の分断や分離した靴は未検出。新しい右靴底は正式装甲より少し滑らかな陰影と薄い帯が残るが、本編等倍で再修正を要する重大な画風差は未検出。29pxの拡張は狭い境界部の透けを埋める処置として妥当。ただし正式原本の境界画素も候補内では変わるので「全て元どおり」と表現しない。

## 実際のDEV比較

|条件|順序|bob|周期|
|---|---|---|---|
|A|03→04→01→06|25%|90world|
|B|新規→03→04→01→06|25%|90world|
|C 参考|現行01→02→03→04→05→06|25%|90world|
|D 本番参考|現行01→02→03→04→05→06|100%|90world|

通常NEW GAME→自宅会話終了→既存DEV歩行テストで、等倍／拡大を比較。DEVを閉じて通常キー入力で上直進・左上・右上へ移動し、実際のPNG読込・currentSrc・naturalWidth・コマ順・周期・bob・停止／復帰・保護状態を記録。移動やフラグの直接代入、teleport、DEVジャンプは使わない。

QA専用Python `tests/moss/m66_up06_independent.py` と `tests/helpers/up06_fixture.py` がブラウザメモリ内だけに比較用descriptorを設定する。既存JS／bankファイルを変更せず、共有FieldWalkMotionの位相計算・bob・既存DEV／フィールド描画を使う。`?dev=1&up06QA=1`＋WINDBOUND_DEVを満たすテストcontextだけ有効。負のゲート検査も実施。

フィールド描画は起動時に既存キーをMapへ固定するため、Bだけ**使わないup02の描画DOMスロット**へ候補URLを一時割当する。Bの比較descriptorもその既存キーを使い、実際に候補URLと復号画像が出ることを検査する。元AidanFieldAssets・bankは書き換えない。A/C/D・LOADで元up02のsrc/data-srcへ復帰。これはQA限定の可逆的な描画fixtureで、本番統合に持ち込まない。

90world÷300world/s＝1周0.300秒。4コマは75ms／22.5world、5コマは60ms／18world、6コマは50ms／15world。5コマ化で周期や移動速度は増えないが、姿勢変化の頻度は増える。一定速度だけで無滑り・生体力学的接地を証明しない。

## 画像・動作品質の独立結論

**視覚品質PASS、5コマ・周期90・bob25%の正式採用を推奨。** 最終の技術回帰と公開成果物照合は別項に記録する。今回の判定はディレクターの採用／マージ権限ではない。

右の靴底／蹴り出しが追加され、4コマ案の右脚相不足を改善。06→新規で左脚通過から左接地寄り、新規→03で右靴底から前方へ運ばれる形が視認できる。直進・左右斜め上で明確な足の消失・膝の切断・重大な新規ジャンプは未検出。右の輪郭変化は速く、外套の元々の動きも残るが、等倍では追加制作を要する破綻ではない。bob25%は全身の浮き感を抑え、周期90を変更する独立根拠は見つからない。滑りゼロ・支持力・全端末性能を保証する判定ではない。

## 失敗と検証条件を保持

初回はQAの等倍表示幅が既存CSSのborder-boxを考慮せず78.75pxになり、幅を150pxへ修正して80px表示を回復。次の試行では新規キーがフィールド内部の固定Mapに存在せず、5コマの候補が描画されないことを厳密検査が検出。上記のQA限定既存スロット方式へ修正した。PR153の画像やゲーム本編を修正したものではない。

PC1280×720の原寸録画ではA/B/Cの実移動を通過後、D本番参考6コマの拡大検査で最大RAF間隔100msとなりコマ落ちFAIL。候補BのFAILへ転記せず、Dの成功とも扱わない。録画負荷が原因候補。PC960×540の原寸録画へ下げ、CSS画像サイズと全ての厳密assertは維持して検証を継続。Android相当は縦390×844／横844×390、DPR1。Android実機は未実施。動画25fpsは全RAFの完全記録ではなく、raw観測と独立した目視の両方で判断する。

## 本番統合時の注意

1. 採用決定後に別案件で、上記SHAの無加工PNGを別の正式パス／独立したフレームキーへ登録する。既存正式03やup02は上書きしない。**QAのup02エイリアスは禁止。**
2. bankは新規→03→04→01→06、周期90、上だけbob.25、アンカー(1024,1230)、scale.0625、全身補正なし。下ARM-02・左右周期180・Fiona・移動速度・衝突・SAVEは維持。
3. 別途承認された統合PRで台帳・SHA・キャッシュ参照・既存SAVE・全方向回帰を確認する。今回のPythonfixture、比較用DOM操作、試作一式を本番へ取り込まない。
4. 元資料のalpha範囲／穴の範囲／輪郭計測値は上記の独立訂正値を採用根拠へ引き継ぐ。過去の自己QA資料は履歴として上書きしない。
5. Android実機の採用最終判断は、本番公開後にディレクターが実施する。今回main／Pages／採用状態は変更しない。


## 最終技術回帰・保護

**最終判定：PASS。新規右足ポーズを含む5コマ・周期90・bob25%の正式採用を推奨する。** 採用登録・mainマージ・Pages公開は行っていない。

|検査|独立結果|
|---|---|
|m66実DEV／実フィールド比較|246/246 PASS、24プレビュー＋36経路、3ビューポート|
|m62下方向ARM-02|88項目PASS|
|m58左右周期180|62項目PASS|
|m55味方・敵・NPC共通DEV|PASS|
|SAVE/CONTINUE|25項目PASS|
|素材台帳監査／m49正式保護SHA|PASS／PASS|
|既存Node|17ファイルPASS|

独立7スクリプトすべてexit0、ログ中FAIL行／非ゼロFAILSなし。各スクリプトの実行前後SHA不変を記録。実行時HEADは `bb99a12efa8302d4d190cebd62ea1b3ca49bc85a`（引継ぎ9fa14ab以降はQA資料追加だけで、アプリ／テスト／素材入力一致）。実装者実行247項目と独立246項目の差は、起動時の既知Raider画像差替abortを検査する任意の1件であり、必須検査のskipではない。未処理console／Promise／HTTPエラーなし。プレビューのbob／アンカー登録誤差最大0.002768world。

正式259SHA・既存1833PNG・PR153候補17ファイルは一致。PR153固定HEADから既存JS／index／CSS／img／data／assetsへ変更なし。新規ファイルはQA用Pythonと報告／証拠だけ。元編集マスクはPR150 `d8708f75aa7dcffb3aa1715284ff60eb83b89f66` のZIP内 `PLAYER-WALK-UP-03/02_masks/proposed_mask.png` とバイト一致、SHA `14dc4e2c3edf6774497cba79db4ba9abf69d8cc1bf40ee4caea1530aae085601`。自己QA側のマスクを無条件に信用せず、元の公開資料まで照合した。

素材監査の直接実行が既存の生成レポートの素材件数だけ1212→1215へ更新した（エラー0は不変）。差分を保存し、共有3パスそれぞれのHEAD原本が同じバイト列と確認した上で全て復元。復元SHA `8f5136aea8717d49c05e37eacf6bf45dbda93e816dff53ee0446d0b36e8db369`、各パス読戻し・最終cleanを独立確認した。これをゲーム変更やテストFAILと混同せず、生成副作用も記録する。通常の既存runnerならアーカイブ内で処理するが、今回は容量節約のためcleanな共有worktreeから直接実行し、SAVEには所有するloopback serverを用意した。検査を省略したものではない。

### 納品資料

- [独立視覚評価](evidence/player-walk-up-06/visual/MOTION-REVIEW.md)／[最終ネイティブ補足](evidence/player-walk-up-06/visual/NATIVE-SUPPLEMENT.md)／[独立技術QA](evidence/player-walk-up-06/runtime/REVIEW.md)
- [4コマ／5コマ・時間1倍](evidence/player-walk-up-06/visual/own-actual-4vs5-temporal1x.mp4)／[同じ映像の空間3倍](evidence/player-walk-up-06/visual/own-actual-4vs5-temporal1x-spatial3x.mp4)
- [右脚・左ブーツの黒白拡大](evidence/player-walk-up-06/visual/own-legs-black-white.png)／[輪郭・膝](evidence/player-walk-up-06/visual/own-outline-knee-black-white.png)
- [06→新規境界](evidence/player-walk-up-06/visual/own-edge-06-NEW.png)／[新規→03境界](evidence/player-walk-up-06/visual/own-edge-NEW-03.png)
- 原寸全操作動画：[PC960×540](evidence/player-walk-up-06/native/pc-four-conditions.webm)／[縦390×844](evidence/player-walk-up-06/native/portrait-four-conditions.webm)／[横844×390](evidence/player-walk-up-06/native/landscape-four-conditions.webm)。A→B→C→D、各条件で拡大→等倍→上直進→左右斜め上の順、時間倍率1。
- 生テレメトリ・RGBA差分・座標・SHA・失敗履歴・全回帰ログは同じ証拠フォルダ。25fps録画と時系列静止画は全RAF／物理的接地の保証ではない。未実施Android実機をPASSにしない。

### 再検証

Chromium／Playwright／ffmpegを用意し、`QA_OUT=<保存先> PW_CHROMIUM_EXECUTABLE=<Chromium実行パス> python tests/moss/m66_up06_independent.py`。必要ならPLAYWRIGHT_BROWSERS_PATHでffmpegを含む既存cacheを選ぶ。テストだけがQA用init_scriptを挿入するため、通常indexを開いただけでは比較fixtureはインストールされない。既存本編のコード／bankへ比較用登録を追加していない。

画像検査は `python docs/qa/evidence/player-walk-up-06/visual/analyze.py --repo . --out <新規保存先>`。動作比較の切出しは同フォルダのmotion_review.pyへ `--repo . --video <証拠/preliminary-pc1280.webm> --telemetry <証拠/screens3/up-runs.json.gz> --out <新規保存先>`。モバイル時系列はmobile_review.pyへ `--screens <証拠/native> --view portrait` または `landscape` と `--out <新規保存先>` を渡す。全て出力先だけへ書き、既存候補を修復しない。
