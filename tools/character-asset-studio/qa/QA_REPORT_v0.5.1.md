# QA REPORT — Pipeline Reliability v0.5.1（CHARACTER-ASSET-STUDIO-07）

実施: Claude による自己QA（AIによる自動テスト）。日付: 2026-11-11。人間QA・独立QAではない。

## 修正
| # | 内容 | 確認方法 | 結果 |
|---|---|---|---|
| 1 | `pr-append` を冪等にした（key ごとの begin／end マーカーで範囲を置き換える。v0.5 の旧マーカーは本文を変えずに変換する。マーカーが重複・欠けている場合は推測せず BLOCKED） | ユニットテスト3件。加えて実際の PR #224 で同じ集約を2回送信: 1回目 `appended+legacy-converted`、2回目 `unchanged`。本文中のマーカーは key ごとに1組だけ | PASS |
| 2 | 終了コードと QA 判定を分けた。`overall`、`adoptionReady`、`adoptionBlockers` を JSON に出し、終了コードは `--gate`（none／no-fail／adoption）を指定したときだけ判定を反映する | 自動検査がすべて PASS でも人間の検査が NOT_RUN なら `overall: NOT_RUN`、`adoptionReady: false`。`--gate adoption` で終了コード 3。スキーマも「adoptionReady が true なら overall は PASS」を強制する | PASS |
| 3 | `--overwrite` の範囲を整理した（保護対象は常に拒否 → 新しいファイルは可 → 既存ファイルは `--overwrite` があり、`assets/` の下でなく、パイプラインが作ったものだけ置き換える）。ブリーフは書き込む前に全出力先を確認する | ユニットテスト3件（CLI を含む）。asset-set、候補PNG、手書きの Markdown、`assets/` の下、正本 MANIFEST は `--overwrite` 付きでも終了コード 64 で拒否され、SHA-256 は変わらない | PASS |
| 4 | 旧形式 `docs/BASE_BODY_SPEC.example.json` は原本のまま残した（SHA-256 不変）。旧形式用スキーマ（読み込み専用）と `body-spec-upgrade` を追加し、2.0 への変換例 `docs/BASE_BODY_SPEC.example.v2.json` を別ファイルで追加した | 変換結果が `studio-core.js` の parseSpec＋buildSpec の出力とバイト単位で一致する。2.0 スキーマで PASS。既存の出力先には書かない | PASS |

## テスト結果（変更前 v0.5 → 変更後 v0.5.1）
| 区分 | v0.5 | v0.5.1 | 差分 |
|---|---|---|---|
| パイプライン | 17/17 | 25/25 | +8件（冪等化3、adoptionReady 1、終了コードと上書き1、上書きの範囲2、旧形式の変換1）。デグレなし |
| 画面のユニットテスト | 19/19 | 19/19 | 変化なし |
| E2E モーション | 106/106 | 106/106 | 変化なし |
| E2E v0.2 | 44/44 | 44/44 | 変化なし |
| リポジトリ回帰 | 52 pass / 8 fail | 52 pass / 8 fail | 変化なし（8件は以前からの既知の失敗） |
| 正本17件の SHA-256 | PASS | PASS | 変化なし |
| スキーマ検証（`qa/pipeline/schema_validation.json`） | PASS 6／BLOCKED 1 | PASS 9 | 旧形式の例が BLOCKED から PASS に。2.0 の変換例と MANIFEST を対象に追加 |
| 同梱候補の画像QA | NOT_RUN（自動 40 PASS／人間 14 NOT_RUN） | 同じ。`adoptionReady: false` | 判定は変わらない。採用できないことを明示する欄を追加 |

QA の JSON（`qa/pipeline/*.json`、`qa/android_device_qa_20261111.json`）は、`adoptionReady` と `adoptionBlockers` を含む新しいスキーマで作り直した。Android 実機QAは 4/4 PASS のまま（ツールの検査記録なので `adoptionReady: false`）。

## 修正の試行回数
- 素体仕様の変換が `studio-core.js` と一致しなかった（テスト側が `console.log` を使っていたため、末尾の改行が1つ多かった）。1回目の修正で解決した。
- そのほかの項目は、初回で通った。
