# MORWEN-HD-CANONICAL-V2 QA（2026-11-10、Claudeによる自己QA）

基準：main `1de4f90c374ca0799d6c80a29a1d2ad1d4e4f410`。ブランチ：`feature/morwen-hd-canonical-v2-registration`（Draft PR #221）。
独立QA・ディレクターの視覚確認・Android実機での確認は**未実施**。モバイルの結果は、Chromiumでスマホの画面を再現したもの。

## 技術QA — PASS（74項目・失敗0）
`python scripts/qa_morwen_hd_v2.py`（結果：`evidence/morwen-hd-v2/qa_morwen_hd_v2_report.json`）
- 配布されたMANIFESTの13点のSHA-256：13/13一致（portrait.webpは既存ファイルで照合）
- データに登録した全件：SHA・RGBA・寸法が一致し、廃止した素材を参照していない
- 表示用派生4点：原本から完全に同じ画像を再現できる。接地行はy=1539。ブーツの計測値と補正値（anchor_dx）が整合している
- index.htmlに新しい素材への参照がないこと（本番に接続していない）
- 新しく追加したファイルに、旧左向き（`35a0820989`・`d858c428`）への参照がないこと

`node --test tests/field/morwen_hd_canonical.test.js`：5/5 PASS（4方向の配置、補正後の足元の位置、縮小したときの足元、廃止素材を拒否すること、不正な入力を拒否すること）

## 4方向の表示QA — 技術的にはPASS、要判断が2点
DEVプレビュー `dev/morwen-hd-v2-preview/` を、PC 1280×900・縦390×844・横844×390 の3画面と、4つの組み合わせ（表示用派生、表示用派生＋補正、ドット絵原本、イラスト原本）で撮影し、計12回確認した（`evidence/morwen-hd-v2/preview_qa_results.json`）。
- 4方向の画像がすべて読み込まれ、描画されている（各枠で背景と異なる画素が3%以上）：12/12
- 足元が計算上の接地点に一致する：12/12
- 横方向のはみ出し・コンソールエラー・旧左向きの読み込み：いずれも0
- 目視の確認：帽子・メガネ・花・肩の紋章・ケープ・ポーチ・ニーソックス・ブーツは、4方向で整合している

**要判断（画像は加工していない）**
1. 派生は外接矩形を中央に置いているため、ブーツの中心が前611.5／左499／右712.5／背面600.5になっている。補正なしのまま向きを切り替えると、左右で約210px横に跳ぶ。補正値はデータに記録し、プレビューでオン・オフを切り替えられる（`preview_pc_display.png` と `preview_pc_display_anchorfix.png` を比較）。
2. 縮尺：目の高さが前330／左290／右368で、左と右の大きさが約6〜7%違う。

その他の注意：原本の体の部分はα253（約1%透けている）。

## 既存機能の回帰
- ゲームのコード（index.html・js・css）は変更していない。追加したのは独立したファイルだけ。
- Nodeのテスト（tests/*.cjs と tests/field/*.js）：28件中20件PASS、8件FAIL。FAILした8件は、**変更前のmain 1de4f90でも同じ内容で失敗する**（`rildeReturnActive is not defined`、`fixture: product DEV block end not found`、`WALKER_FPS`）。今回の変更による新しい失敗はない。
- 頭装備のテスト 5/5 PASS、HDドット絵候補QAの単体テスト PASS。
- 起動の簡易確認（ヘッドレスChrome、PCとスマホ縦でindex.htmlを開く）：コンソールエラー0件、モルウェン関連のリクエスト0件で、mainと同じ結果。
