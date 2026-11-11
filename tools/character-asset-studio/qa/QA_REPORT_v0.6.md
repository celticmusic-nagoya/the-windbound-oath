# QA REPORT — v0.6 Morwen Canonical Body Measurement（CHARACTER-ASSET-STUDIO-08）

実施: Claude による自己QA（AIによる自動テストと、AIの目視による観察）。日付: 2026-11-11。人間QA・独立QAではない。

| 区分 | 結果 | 証跡 |
|---|---|---|
| 計測QA（`measure-canon`） | 全体 FAIL（PASS 62／FAIL 2／BLOCKED 23／NOT_RUN 9）、`adoptionReady: false` | `measurements/morwen-final-canon-20261111/qa_report.json` |
| 4方向の接地の比較 | **FAIL**: 接地の行 front 1542／back 1549／left 1537／right 1540（差12px、許容6px） | 同上 |
| 接地点とアンカー x=600 の比較 | **FAIL**: left だけ −108px（front −0.2、back +7.8、right 0） | 同上 |
| 正規化座標とピクセル座標の一致 | PASS（計測した17点すべて。`to_pixel(n) == px`、`to_norm(px) == n`、画面の丸め方と同じ） | 同上 |
| 測定不能の項目 | 23件すべて BLOCKED。仕様ファイルでは template_default／provisional で、計測値と区別されている（PASS 23） | 同上 |
| 推定・目視の項目 | 7件は人間の確認待ち（NOT_RUN） | 同上 |
| BASE_BODY_SPEC v2.0 スキーマ、画面の読み込み（parseSpec） | PASS | 同上、`studio-core.js` |
| 正本17件の SHA-256（実行の前後） | PASS | `qa/pipeline/protect_verify.json` |
| R2.1 が BLOCKED のまま | PASS | `profiles/reference_bodies.json`（変更なし） |
| パイプラインのテスト | PASS 31/31（v0.5.1 の 25件 + 計測 6件） | `pipeline/tests/test_pipeline.py` |
| 画面のユニットテスト／E2E モーション／E2E v0.2 | 19/19、106/106、44/44（変化なし） | |
| リポジトリ回帰 | 52 pass / 8 fail（変化なし、8件は以前からの既知の失敗） | |

## 計測のテスト（6件）
- 正本を読み取り専用で扱い、17件の SHA-256 と R2.1 の BLOCKED が変わらない
- 測定不能の点は、仕様ファイルで template_default／provisional になり、QA で BLOCKED になる。目視・推定の点は NOT_RUN で、PASS にはならない。`adoptionReady` は false
- 頭頂・肩・骨盤は4方向とも測定不能で、衣装の外接矩形は体の寸法として扱わない
- 座標の一致、4方向の接地の値、2つの FAIL を確認する
- コミットした結果が、新しく実行した結果と一致する（再現できる）
- 出力の上書き禁止、保護フォルダへの出力の拒否。観察が空の場合、テンプレートの値を計測値として使わず「測定不能」になる

## 判断が必要な事項（ディレクター）
1. 4方向の接地のずれ（最大12px）と、left 画像の横ずれ（−108px）の扱い（位置をそろえた作業用コピーを作るか、方向ごとにアンカーを持つか）
2. 帽子・ケープ・スカートで隠れている頭頂・肩・骨盤の基準をどう得るか（例: 衣装なしの素体を別に描く）
3. 目視・推定の7点（膝6点のうち4点は目視の可視点、首と側面の膝は推定）の確認
