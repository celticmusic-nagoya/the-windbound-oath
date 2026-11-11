# QA REPORT — Character Asset Studio v0.5（CHARACTER-ASSET-STUDIO-06 AI Collaboration Pipeline）

実施: Claude による自己QA（AIによる自動テスト）。Android 実機QAは、ディレクターから報告された人間による結果を記録したもの。日付: 2026-11-11。

| 区分 | 結果 | 証跡 |
|---|---|---|
| パイプラインのユニット／統合テスト | PASS 17/17 | `pipeline/tests/test_pipeline.py` |
| 画面のユニットテスト（v0.2〜v0.4） | PASS 19/19 | `tests/*.cjs` |
| E2E モーション（v0.3〜v0.4、390px／1440px） | PASS 106/106 | `qa/e2e_motion_report.json` |
| E2E v0.2 | PASS 44/44 | `qa/e2e_report.json` |
| リポジトリ回帰 | 52 pass / 8 fail（既知の基準値と同じ） | — |
| 正本保護（`cas.py protect-verify`） | PASS 17/17 | `qa/pipeline/protect_verify.json` |
| 同梱候補の画像QA（`cas.py qa`） | 自動検査 PASS 40／人間の検査 NOT_RUN 14 → 全体 NOT_RUN | `qa/pipeline/demo_candidates_qa.json` |
| スキーマ検証（`cas.py validate`） | PASS 6／BLOCKED 1 | `qa/pipeline/schema_validation.json` |
| Android 実機QA | **4/4 PASS**（ディレクター報告・人間QA） | `qa/android_device_qa_20261111.json` |

## パイプラインのテスト内容
- 座標（toPixel／toNorm／placement）、テンプレートのランドマーク、JSON の出力が `studio-core.js`（Node）と完全に一致する
- 画面の書き出す BASE_BODY_SPEC 2.0 と motion-reference 1.0 がスキーマを満たす。壊れた文書は FAIL、種類が分からない文書は BLOCKED になる
- 合成画像で次をすべて FAIL として検出する: 寸法違い、アルファなし、透明部分なし（背景の焼き込み）、外周の不透明画素、接地のずれ、アンカーの x のずれ、フレームの欠落、同じ画像の連続、高さのばらつき、接地行のばらつき、SHA-256 の不一致、ファイルの欠落
- 承認記録のない DIRECTOR_APPROVED は FAIL、BLOCKED の素体（R2.1）を参照すると BLOCKED。人間の検査は、記録がなければ NOT_RUN、記録があればその結果になる
- MANIFEST は、改ざんと MANIFEST にないファイルを FAIL にする。保護対象への書き込み・既存ファイルの上書き・承認状態での書き出しは拒否される
- 位置合わせは新しいファイルにだけ書き出し、接地をアンカーに一致させる。はみ出す場合は書き出さない
- ブリーフはスキーマを満たし、`autoAdopt: false` になる。納品先が保護フォルダの場合、BLOCKED の素体を使う場合は停止する

## 既知の制限（未対応）
- `docs/BASE_BODY_SPEC.example.json`（v0.1 で受け取った v1.0 形式の例）には v0.5 のスキーマがないため、検証は BLOCKED（画面での読み込みは引き続き可能）
- 人間の検査項目（デザインの一致、骨格、年齢にふさわしい表現、装備の構造、モルウェンの制約10項目）は自動化しない。記録がない限り NOT_RUN
- Android 実機QAは4項目の総括の結果のみ。端末名・バージョンと、24行の個別結果は記録されていない
