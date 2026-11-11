# QA REPORT — v0.7 Morwen Master Body & Four-Layer Modular Pipeline（CHARACTER-ASSET-STUDIO-10）

実施: Claude による自己QA（AIによる自動テストと、スクリーンショットのAI目視）。日付: 2026-11-11。人間QA・独立QAではない。
**v0.7 の実装が終わっても、モルウェンのマスター素体を正式に採用したことにはならない。**

## 必須QA
| # | 項目 | 結果 | 証跡 |
|---|---|---|---|
| 1 | v0.6 の計測データと正本17件の SHA-256 が変わっていない | PASS（`measurements/` に差分なし、protect-verify 17/17、各処理の実行前後で照合） | `qa/pipeline/protect_verify.json`、テスト |
| 2 | 正規化した4方向の接地点の一致 | PASS（変換後に再計測して4方向とも (600, 1540)） | `normalized/morwen-final-canon-20261111/normalize_qa.json` |
| 3 | 4階層それぞれの ON/OFF と、合成の再現性 | PASS（合成例: 4方向 × 2フレーム × 4階層、ON/OFF 32件、再現性 8件） | `qa/v0.7/synthetic_layer_qa.json`、`qa/v0.7/synthetic_previews/` |
| 4 | v0.5.1 以前のパイプライン・画面・E2E の回帰 | PASS（パイプライン 49/49、画面のユニットテスト 19/19、モーション E2E 102/102、v0.2 E2E 44/44） | — |
| — | リポジトリ全体の既知の FAIL 8件 | 変更前（166cd11）と変更後で、失敗したテストの名前と件数（52 pass／8 fail）が完全に一致。新しい FAIL はなし | 下の一覧 |

既知の FAIL（変更前後で同じ）: common_loading、continue_restore、early_rewards、field/frame_clock、s2_transition_recovery、save_compatibility、startup_race、title_continue。

## TASK ごとの結果
- **A 正規化:**
  - 変換量は v0.6 で実測した接地点から計算した（front (0, −2)、back (−8, −9)、left (+108, +3)、right (0, 0)）。
  - 画素とアルファは保持した（はみ出した前景画素 0。RGB は RGB、RGBA は RGBA のまま）。
  - 元の画像の SHA-256 は変わらず、2回実行して同じ結果になった。
  - 骨格の整合は NOT_RUN（接地点をそろえても骨格がそろったことにはならない）。
- **B 4階層スキーマ:**
  - 必須13項目がそろっていない場合は FAIL になる。
  - L0 には bodyGuidePolicy が必須で、未成年は neutral 以外を使えない。
  - 承認状態には承認記録が必須。
  - 描く順番は zOrder で決まる（L3 の背面ローブを体の後ろに描けることを確認した）。
  - 既存の BASE_BODY_SPEC v2.0 は変更していない。
- **C Layer 0 候補（`layer0/morwen-v0.7/BODY_QA_REPORT.json`）:**
  - 全体は BLOCKED で、採用不可。
  - VERIFIED 10／ESTIMATED 7／UNKNOWN 23。UNKNOWN の23点は計測値として登録していない（テンプレートの値は仮置きで、QA では BLOCKED）。
  - 設計値（DESIGNED_CANDIDATE）は、共通の膝の高さ y=1076 の1つだけで、仕様ファイルとは分けて記録した。
  - デザイン保護の12項目は NOT_RUN。
- **D レイヤー検証:** 合成例の自動検査はすべて PASS（506件）、ディレクターの承認は NOT_RUN。プレビューは元のパーツとは別のファイルに出力し、元のパーツの SHA-256 は変わらない。
- **F デザイン保護:** `profiles/morwen_design_protection.json` に12項目を登録した。Layer 0 の QA と asset-set の画像 QA に、常に NOT_RUN（人間の記録がない限り）として出る。

## 未解決事項（ディレクターの判断が必要）
1. Layer 0 素体の画像生成（制作指示: `layer0/morwen-v0.7/production_brief.json`）と、それを使った骨格の比較。
2. 隠れている関節（頭頂・肩・骨盤など）の設計値を、DESIGNED_CANDIDATE としてどう決めるか。
3. 正規化後も、膝の高さは方向ごとに 1059〜1093px と34px 違う（ESTIMATED）。4方向の体格の差をどう扱うか。
4. デザイン保護12項目と ESTIMATED の7点の、人間による確認。
