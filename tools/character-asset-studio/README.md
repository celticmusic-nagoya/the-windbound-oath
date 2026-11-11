# Character Asset Studio v0.9

> **v0.5 の方針（CHARACTER-ASSET-STUDIO-06）:** 人間向けの画面の改善より、ChatGPT と Claude のあいだでアセットの制作・検証・データの受け渡しを自動化することを優先する。中心は `pipeline/`（コマンドライン、[pipeline/README.md](pipeline/README.md)）。画面の v0.4 の機能はそのまま残す。自動位置合わせなどの画面の改善は保留する（内部処理としての座標の正規化・位置合わせは `pipeline/` にある）。

THE WINDBOUND OATH のキャラクター素材を確認するためのローカルブラウザツール。正本画像を変更することはない。
ChatGPT から納品された v0.1 MVP（コミット f5088ae に、受け取ったままの状態で取り込み済み）を、`docs/CLAUDE_HANDOFF.md`（CHARACTER-ASSET-STUDIO-02）に従って強化した。

## 起動方法
リポジトリのルートで HTTP サーバーを起動し、ブラウザで開く。

```sh
python3 -m http.server 8000
# http://localhost:8000/tools/character-asset-studio/
```

- ルートから配信するのは、「正本を参照表示」で `assets/candidates/morwen/final-visual-canon-20261111/` を読むため。
- 外部ライブラリは使っていない。
- `file://` で開いた場合、プリセットは 1200×1600 だけになり、同梱候補の表示と正本の参照表示は使えない。

## できること
| 機能 | 内容 |
|---|---|
| 4方向の表示と切り替え | 正面・背面・左・右 |
| PNG のレイヤー読み込み | 部位とフレームごとに読み込む。フレーム数はプリセットごとに決まる（12または6） |
| 再生 | 1〜24 fps |
| 同梱候補の表示 | `demo/` にある派生候補で、正本ではない。画面上では［候補］と表示する |
| 正本の参照表示 | 正式な4方向画像を読み取り専用で表示する。読み込んだ時点で MANIFEST と SHA-256 を照合する。画面上では［正本・読取専用］と表示する。書き出す合成PNGやシルエットPNGには、正本の画素を含めない |
| プリセット | `profiles/presets.json` に定義。1200×1600（モルウェン）、1024×1280（HDフィールド）、96×128（ピクセル） |
| 関節アンカー | 正規化座標（0〜1）で記録し、キャンバスの大きさに合わせて換算する。ドラッグで移動でき（タッチ操作にも対応）、点ごとに信頼度（provisional / low / medium / high）と出どころ（template_default / manual_edit / imported_spec / measured_reference）を持つ |
| 画像の配置 | キャンバスと同じ大きさの画像は等倍で置く。大きさが違う画像は縦横同じ比率で縮小・拡大し、下端を中央に合わせて置く（縦横比を変えて引き伸ばすことはしない） |
| 構造チェックリスト | `profiles/morwen_constraints.json` に定義。目視で確認する項目（ローブ左右の裾、後ろのスリット、紐、ソックスとガーター、チェック柄など）。自動で PASS にはせず、確認した印は REVIEWER_MARKED として記録する |
| BASE_BODY_SPEC v2.0 | スキーマは `docs/BASE_BODY_SPEC.schema.json`。キーを並べ替えて書き出すので、同じ状態なら毎回同じ内容になる。読み込みは v1.0（ピクセル座標）にも対応 |
| QA | SHA-256（正本は MANIFEST と照合）、寸法、本当に透過しているか、外周のα、αの外接矩形、4方向そろっているかを確認する。解剖とデザインの確認は常に NOT_RUN |
| 書き出し | ガイドPNG（背景とガイド線あり）、合成PNG（ガイドなし・透過）、シルエットPNG |

## v0.3 モーション参考スタジオ（07 / CHARACTER-ASSET-STUDIO-03）
参考動画（MP4/WebM）を見ながら歩行の目安を記録する。**記録した値はすべて「未承認の参考値」（`UNAPPROVED_REFERENCE`）として扱う。** 素体仕様（BASE_BODY_SPEC）、正本、キャラクターのデザインには自動で反映しない（`autoApply: false`。読み込んだJSONに別の値が書かれていても上書きして戻す）。

| 機能 | 内容 |
|---|---|
| 動画 | 端末内のファイルを読み込み、再生・一時停止・±1／±10コマ送り・スライダー・タイムラインのタップで移動する（キーボードでは `,` と `.` でコマ送り）。FPSは入力値を使い、各コマの中央の時刻へシークする。SHA-256はブラウザ内で計算する |
| 計測範囲 | 全体／左半分／右半分。分割画面の動画（Grid Overlay は左半分が側面）に使う |
| 比較表示 | 左右に並べる表示と重ねる表示。スプライトの不透明度・拡大率・横位置を調整できる。スタジオの ground 線を表示する。周期内の位置に合わせてスプライトのフレームを切り替えられる |
| 歩行フェーズ | contact / down / passing / up / push_off。側は L / R / A / B / unknown（A・B は交互だが解剖学的な左右を特定していない）。同じ側の contact から次の contact までを1周期とする |
| 関節アンカー | head・shoulder・elbow・wrist・hip・左右の knee・ankle・toe。動画をタップしてコマごとに記録する。軌跡を表示し、記録のないコマは補間位置を点線で表示する |
| 周期比較 | 選んだ周期を 6・8・12 コマに等間隔で分け、動画のコマとスプライトのフレームを並べる |
| JSON | `motion-reference/1.0`。キーを並べ替えて書き出すので、同じ状態なら毎回同じ内容になる。動画の画素は含めず、ファイル名・SHA-256・寸法・FPSだけを記録する。別の動画用（SHA-256不一致）のJSONは適用しない |

`motion/grid_overlay_walk.reference.json` は、添付の Grid Overlay 動画（640×360、25fps、618コマ）の側面を解析した結果（接地9回、通過8回、7周期、1歩 平均53.25コマ、1周期 平均106.3コマ）。動画fpsで換算すると1歩 約28歩/分となり、通常の歩行よりかなり遅い。動画がスロー再生かどうかは確認していないため、値はコマ数で扱う。関節アンカーは計測していない。

参考動画そのもの、動画から切り出したフレーム、動画が写ったスクリーンショットはリポジトリに入れない。

## v0.4 視覚QA修正（CHARACTER-ASSET-STUDIO-04）
- **未登録フレーム:** 比較画面と周期比較で、スプライトが登録されていないフレームは「未登録」と表示する。周期比較では「比較枠 N · 登録済みスプライト X / 12 フレーム · 未登録 · 仮表示」の枠数を明示する。
- **再利用プレビュー（任意）:** 「未登録フレームに既存フレームを再利用（仮表示）」をオンにすると、直前の登録済みフレームを表示する。枠は橙の破線、ラベルは「仮表示 f3←f0」で、アニメーション素材とは区別する。スタジオのレイヤーには追加しない。画像の自動生成・自動補完はしない。
- **比較画面:** スプライトは登録済みフレーム全体の不透明部分＋ground で切り抜き、縦横比を保って表示領域いっぱいに拡大する（全フレーム同じ切り抜きなので縮尺はそろう）。動画は計測範囲を縦横比を保って拡大する。動画（拡大率・上下位置・足元ライン）とスプライト（拡大率・上下位置・横位置）を別々に調整できる。「足元を揃える」で、スプライトの ground（橙）を動画の足元ライン（水色）の高さに合わせる。表示だけの調整で、計測値や素体仕様は変えない。
- **390px:** 比較画面のキャンバスを縦長（720×640）にし、比較画面と再生操作を画面上部に固定する（操作パネルをスクロールしても見える）。再生ボタンは5列で並べる。
- **歩行フェーズ:** 「脚の開き幅の極大・極小」は解析マーカー（`candidates`）として、接地（`phases` の contact）とは別に記録する。接地は登録時点では「候補（未確定）」で、動画を見て確認したものだけ「目視確定」（`verification: "visual_confirmed"`）にする。確定してもファイル全体は未承認の参考値のまま。
- **Grid Overlay 参考JSON:** ファイルは変更していない（バイト単位で同一）。中の contact は脚の開き幅の極大から求めた値で、目視確定はしていないため、読み込むと9件すべて「候補（未確定）」と表示される。

## v0.5 AI Collaboration Pipeline（CHARACTER-ASSET-STUDIO-06）
| 優先事項 | 実装 |
|---|---|
| 1. 共通JSONスキーマ | `pipeline/schemas/`。対象は asset-set（素体・衣装レイヤー・歩行フレーム）、anchor-set、motion-reference、manifest、production-brief、qa-report。BASE_BODY_SPEC 2.0 は既存の `docs/BASE_BODY_SPEC.schema.json` を使う |
| 2. SHA-256 MANIFEST と正本保護 | `cas.py manifest-build／manifest-verify／protect-verify／protect-diff`、`pipeline/protected_assets.json`（17件）。すべての書き込み処理は、保護対象のパスへの書き込みと既存ファイルの上書きを拒否する |
| 3. 画像の自動QA | `cas.py qa`。寸法、アルファ、外周の透明、接地とアンカー、フレームの欠落・重複、フレーム間の整合、同じ画像の連続 |
| 4. ガイドPNGと制作指示JSON | `cas.py brief`。方向ごとの透明ガイドとプレビュー、`cas/production-brief/0.5`（`autoAdopt: false`） |
| 5. PASS／FAIL／BLOCKED／NOT_RUN | `cas/qa-report/0.5`。人間の検査項目は記録がなければ NOT_RUN |
| 6. Draft PR への集約 | `cas.py pr-summary` と `cas.py pr-append`（開いた Draft PR だけを編集し、マージはしない） |

この版の MANIFEST.json は `cas/manifest/0.5` 形式（各ファイルの SHA-256 と状態）。

**v0.5.1（CHARACTER-ASSET-STUDIO-07）:** パイプラインの信頼性を修正した。
- `pr-append` は、同じ key の範囲を置き換えるだけになった（冪等）。
- QA の判定（`overall`、`adoptionReady`）と終了コードを分けた。
- `--overwrite` で置き換えられるのは、パイプラインが作ったファイルだけになった。
- 旧形式の `docs/BASE_BODY_SPEC.example.json` は原本のまま残し、2.0 に変換した例を `docs/BASE_BODY_SPEC.example.v2.json` として追加した。

詳しくは [pipeline/README.md](pipeline/README.md)。

## v0.9 Layer 0 関節構造の改善と Layer 1 基本インナーウェア候補（MORWEN-LAYER0-02）
- `layer0/morwen-master-v0.9/`: v0.8 の関節を1つも変えずに、関節構造を区別できるようにした（12関節を追加し、理由を記録した）。歩行用の回転軸も定義した。
- `layer1/morwen-base-v0.9/`: Layer 0 から作った、不透明で露出の少ない基本インナーウェアの候補。
- Layer 0／1 の ON/OFF 合成と、正本（Layer 2・3）との位置関係を自動で検査した。最終採用と独立した目視レビューは NOT_RUN。

## v0.8 モルウェン Layer 0 マスター素体候補（MORWEN-LAYER0-01）
`layer0/morwen-master-v0.8/`（未承認）。1つの3D骨格を4方向に投影した、中立的なマネキン型の構造ガイド。
- 接地と中心は VERIFIED、顎と手首は ESTIMATED、頭頂・肩・骨盤などは DESIGNED_CANDIDATE（新しい設計値。実測値ではない）。
- 寸法と整合の自動検査はすべて PASS。デザインと骨格の最終的な採用、独立した目視QA、デザイン保護12項目は NOT_RUN。
- 詳しくは [そのフォルダの README](layer0/morwen-master-v0.8/README.md)。

## v0.7 4階層モジュラー基盤とモルウェン Layer 0 候補（CHARACTER-ASSET-STUDIO-10）
- **A 作業座標の正規化:** `normalized/morwen-final-canon-20261111/`。v0.6 の実測した接地点から変換量を計算し、4方向の接地点を (600, 1540) にそろえた（PASS）。骨格の整合は評価していない（NOT_RUN）。
- **B 4階層の共通スキーマ:** L0 BASE_BODY／L1 UNDERWEAR／L2 BASE_OUTFIT／L3 OUTER_ACCESSORIES（`profiles/layer_catalog.json`、`cas/modular-part/0.7`、`cas/modular-character/0.7`）。計測状態（VERIFIED／ESTIMATED／UNKNOWN／TEMPLATE／DESIGNED_CANDIDATE）と採用状態は別の項目にした。
- **C モルウェン Layer 0 候補:** `layer0/morwen-v0.7/`（未承認）。測定不能の23点は計測値として登録していない。
- **D レイヤー検証:** MANIFEST、SHA-256、PNG の検査、アンカー、ON/OFF 合成、4方向比較、フレームの整合、PR への集約。
- **デザイン保護:** `profiles/morwen_design_protection.json` の12項目は、人間が確認するまで常に NOT_RUN。
- v0.7 の実装が終わっても、モルウェンのマスター素体を正式に採用したことにはならない。

## v0.6 モルウェン最終正本の骨格計測（CHARACTER-ASSET-STUDIO-08）
最終正本4方向を読み取り専用で計測し、未承認の候補を `measurements/morwen-final-canon-20261111/` に置いた。概要は [そのフォルダの README](measurements/morwen-final-canon-20261111/README.md) を参照。

- 40点のうち 可視14・推定3・測定不能23。頭頂・肩・骨盤は帽子とケープ、スカートに隠れているため、すべての方向で測定不能。測定不能の点を計測値や PASS として扱うことはない。
- 接地の高さは4方向で最大12px違い、left の画像は接地点がアンカーから108px左にずれていた。どちらも QA で FAIL として報告した（正本は変更していない）。
- R2.1 は BLOCKED のまま。

## Android 実機での起動（CHARACTER-ASSET-STUDIO-05）
**実機QA: 4/4 PASS**（ディレクター報告、2026-11-11。`qa/android_device_qa_20261111.json`）。PASS した4項目は、下の「実機チェック手順」の4つの確認点。

ターミナルは不要。Android の Chrome で次のURLを開く（このリポジトリは公開リポジトリで、raw.githack.com はブランチ上のファイルを正しい形式で配信する外部サービス。公式サイトへの公開ではない）。

- 検証する版を固定するURL（推奨。`<SHA>` は PR #224 の最新コミットSHA。チェックリストに記録する）:
  `https://raw.githack.com/celticmusic-nagoya/the-windbound-oath/<SHA>/tools/character-asset-studio/index.html`
- ブランチの最新版（数分遅れることがある）:
  `https://raw.githack.com/celticmusic-nagoya/the-windbound-oath/feature/character-asset-studio/tools/character-asset-studio/index.html`

注意:
- 動画・PNG・JSONは端末内だけで処理する。外部へ送信しない（ページのプログラムを配信サービスから読み込むだけ）。
- 参考動画は、端末の「ダウンロード」や Google ドライブなどに置き、「参考動画（MP4）を選択」から選ぶ。
- `http://192.168.x.x:8000` のような HTTPS でないアドレスは使わない。ブラウザが SHA-256 計算機能を無効にするので、動画の読み込みと正本の照合が失敗する（エミュレーションで確認済み）。
- 保存したJSON・PNGは、Chrome の「ダウンロード」（端末の Download フォルダ）に入る。

### 実機チェック手順
`qa/ANDROID_DEVICE_QA_CHECKLIST.md` に手順と期待結果がある（起動3項目、動画の読み込み5項目、タッチ操作7項目、390px前後の固定表示4項目、保存5項目）。結果は同じファイルに記入する。主な確認点は次のとおり。
1. **動画の読み込み:** 同梱JSONを読み込んでから Grid Overlay の MP4 を選び、「618コマ」「参照JSONと一致」になる。再生・一時停止・±1／±10コマ送りで、表示とコマ番号が一致する。
2. **タッチ操作:** 動画をタップしてアンカーを記録しても、ページがスクロール・拡大しない。タイムラインのタップ、スライダー、マスターキャンバスのマーカーのドラッグ、「足元を揃える」が動く。
3. **固定表示:** 390px前後で比較画面を上部に固定したまま、各ボタンを押せるか。エミュレーションでは、固定部分が画面の6〜7割を占め、ボタンが隠れることがあった。実機でも支障があれば、固定の解除・折りたたみの切り替えを最小修正で追加する。
4. **保存:** モーションJSON・素体仕様JSON・QA JSON・合成／シルエット／ガイドPNGがダウンロードに保存され、開ける。書き出したモーションJSONを読み込み直しても内容が変わらない。

事前確認（エミュレーション）は `python3 tools/character-asset-studio/tests/android_prep_check.py [OUT_DIR]` で行う。実機QAの代わりにはならない。

## 参照しない素体（BLOCKED）
`profiles/reference_bodies.json` 参照。素体 R2.1 は、以前の候補画像で計測したもので、最終正本4方向では計測していない。そのため、R2.1 の座標は読み込まず、新しい座標を推測で作ることもしない。

## テスト
```sh
node --test tools/character-asset-studio/tests/*.cjs                    # 中核ロジック（v0.2 6件 + モーション 13件）
python3 tools/character-asset-studio/tests/e2e_studio.py [OUT_DIR]       # v0.2 機能（390px・1440px）
python3 tools/character-asset-studio/tests/e2e_motion.py [OUT_DIR] [--real-video PATH]   # v0.3 モーション
python3 -m unittest discover -s tools/character-asset-studio/pipeline/tests             # v0.5 パイプライン
```
`e2e_motion.py` は、テストのたびに ffmpeg で合成動画（コマ番号を灰色の濃さで表した可逆H.264）を作り、コマ送りが正確かを確かめる。`--real-video` を付けると実際の参考動画でも確かめるが、そのスクリーンショットは一時ディレクトリにだけ保存する。
結果は `qa/QA_REPORT_v0.5.md`（以前の版は `qa/QA_REPORT_v0.4.md`、`v0.3`、`v0.2`）、`qa/e2e_report.json`、`qa/e2e_motion_report.json`、`qa/*.png` に保存している。

## 実装していないこと
- 自動リギング、隠れた部分の自動補正、IK、解剖学的な整合性の証明
- GitHub への書き込みと、オンライン同期
- Android 実機・iOS Safari での確認

## ファイル
- `index.html`、`styles.css`、`app.js`: 画面
- `studio-core.js`: DOM を使わない中核ロジック（Node でもテストできる）
- `motion-core.js`、`motion.js`: v0.3 モーション参考の中核ロジックと画面
- `motion/`: 参考動画から作った未承認の参考JSON（画素は含まない）
- `profiles/`: プリセット、制約、参照する素体の状態
- `demo/`: v0.1 に同梱されていた派生候補4枚（正本ではない）
- `docs/`: 引き継ぎ書、v0.1 の QA と FILE_MANIFEST（受け取ったときのまま）、スキーマ、例
- `tests/`、`qa/`: テストと証跡
