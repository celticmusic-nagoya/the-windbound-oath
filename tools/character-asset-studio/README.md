# Character Asset Studio v0.2

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

## 参照しない素体（BLOCKED）
`profiles/reference_bodies.json` 参照。素体 R2.1 は、以前の候補画像で計測したもので、最終正本4方向では計測していない。そのため、R2.1 の座標は読み込まず、新しい座標を推測で作ることもしない。

## テスト
```sh
node --test tools/character-asset-studio/tests/studio_core.test.cjs     # 中核ロジック（6件）
python3 tools/character-asset-studio/tests/e2e_studio.py [OUT_DIR]       # Playwright で 390px と 1440px を確認
```
結果は `qa/QA_REPORT_v0.2.md`、`qa/e2e_report.json`、`qa/*.png` に保存している。

## 実装していないこと
- 自動リギング、隠れた部分の自動補正、IK、解剖学的な整合性の証明
- GitHub への書き込みと、オンライン同期
- Android 実機・iOS Safari での確認

## ファイル
- `index.html`、`styles.css`、`app.js`: 画面
- `studio-core.js`: DOM を使わない中核ロジック（Node でもテストできる）
- `profiles/`: プリセット、制約、参照する素体の状態
- `demo/`: v0.1 に同梱されていた派生候補4枚（正本ではない）
- `docs/`: 引き継ぎ書、v0.1 の QA と FILE_MANIFEST（受け取ったときのまま）、スキーマ、例
- `tests/`、`qa/`: テストと証跡
