# MORWEN-CANON-CLEANUP-02 — 自己QA

- 基準main: `cab9aa52da653198a712bd986992adc03ea4bfe2`。
- 最新ディレクター指示: Issue #240 `issuecomment-6822050005`。旧画像の保存方針を更新し、将来のBlender完成版は `FUTURE_CANON_PENDING_APPROVAL`、今回の12枚は `REFERENCE_ONLY`。
- 原本保管コミット: `5092ae35674d245a8beb3b858bc8b587058131e6`。GitHub上の同コミットをAPIで検証した後に削除。

## ZIP受領・原本保護

`morwen_asset20261112.zip` / 11,828,264 bytes / SHA-256 `4a1a23fd0f0197b8b21019229d9f5340b1a8e28c0fd70607d54f02ff3d4bbcf9`。

ディレクターが本タスクへ直接添付したZIPを取得。CRC PASS。PNG12枚を `assets/references/morwen/reference_20261112/` に元のファイル名・元のバイト列で保存し、元ZIP各memberとの完全一致を再検証。SHA・寸法・モード・α・4方向ラベル・役割は同フォルダのMANIFESTに記録。原本ZIPは添付をそのまま使用し、類似画像で代替していない。原本の再エンコード・拡縮・色変更・α変更なし。

構造参照と衣装付き画像の差、RGB黒背景、眼鏡/衣装/装飾/縮尺の違いを統合索引に記録。12枚を完成版・正式採用と扱わず、補助8枚の向きを推測で正本に割り当てていない。

## 棚卸し・削除

対象: main上のMorwen名434パス＋新規原本12枚、計446件。
**KEEP 112 / DELETE 12 / BLOCKED 322**。KEEPには原本12枚・現行素材・最小の決定/QA記録・共有スクリプトを含む。

削除12件、計2,415,104 bytes:

- `assets/candidates/morwen-right-walk/70/art/ART-70C/PROPOSAL_DIFF_F00.png` ～ `PROPOSAL_DIFF_F05.png`（6枚）
- `assets/candidates/morwen-right-walk/71/proposals/{FLOWER,GLASSES,HAT_GOLD,UPPER_GOLD}/COMPARE_<同名>_F00_71_vs_proposal_vs_diff.png`（4枚）
- `assets/candidates/morwen-right-walk/71/morwen_right_walk_71.gif`
- `assets/candidates/morwen-right-walk/71/qa_preview_71.html`

全具体パス・削除前SHA・サイズ・根拠: `DELETED_PATHS.json`。旧生成プレビューだけを削除。フレーム・マスク・生成コード・QA数値・採用判断は保持。2つのREADMEから削除した派生プレビューへの古いワイルドカード案内を外し、削除台帳へ案内を更新した。AGENTS.mdの冒頭に最新のビジュアル方針と参照先を追記し、既存の設定・年齢規定は保持した。322件は画像/共有入力/動的依存/必要QAの不使用が未証明なのでBLOCKED。branch-only資産と他PR・他ブランチ・Git履歴は変更しない。

過去の大量棚卸しはPR #241を再利用し、最新main・関連PR・websiteのスナップショットで依存を再走査。`SNAPSHOTS.json`、`OPEN_PRS.json`、`DEPENDENCY_QA.json`に固定値と方法を記録。完全パス/ファイル名の消費参照0件に加え、差分画像の動的命名は生成側 `.save()` の出力であることを確認。旧READMEのワイルドカード案内は上記の通り更新。PR #241の不変な履歴棚卸しは実行時消費者ではなく、元Git blobを保持したまま参照可能。

## 実行QA

PASS:

- `python scripts/qa_morwen_cleanup_02.py --source-zip <受領ZIP>`: ZIP/12原本一致、446分類整合、KEEP/BLOCKEDのハッシュ保護、削除対象12件一致、変更範囲制限。
- 同スクリプト: 170 runtime source files不変、literal asset参照の既存欠損0・新規欠損0。
- `node --test tests/moss/test_field_headgear_layers.js tests/moss/test_field_headgear_renderer.js tests/moss/field_ro_asset_registry.test.js`: 3ファイルPASS、失敗0。
- `python tests/moss/test_qa_field_hd_pixel.py`: 4テストPASS。
- `python -m py_compile scripts/qa_morwen_cleanup_02.py`、`git diff --check`: PASS。
- `/usr/bin/chromium` + Playwright: 基準/候補 × PC1280×900/スマホ390×844の4ケース。全HTTP 200、JS例外0、失敗リクエスト0、HTTPエラー0。削除前後のスクリーンショット差分は両幅0画素。`BROWSER_QA.json`参照。実行はローカルHTTP、スマホはエミュレーション。
- ゲーム本体/シナリオ/SAVE/稼働中素材/他キャラ/公式サイトの変更0。公式サイトの固定commitは `722d05998dd6ade39db82aa9fee6868dd416d041`。

初回ブラウザ起動はPlaywrightの同梱ブラウザ未配置で失敗し、既存の `/usr/bin/chromium` 指定で解消した。環境のsocket制限は承認されたローカル検証実行で解消。無関係なアプリ修正や依存追加は行っていない。

現行private canon mainと追補/状態表を照合済み。設定依存の変更はなし、本文は非公開のまま保持。新規のClaude独立美術QA・人間による完成版採用審査・Android実機QAはNOT_RUN。今回のPASSは自己QAとブラウザの比較検証で、正式ビジュアルの採用判定ではない。

mainマージ・履歴書換・リグ生成・ゲーム組込・公式サイト公開・自動採用は未実施。残る旧候補は、必要QAと動的/PR依存を解消するまで削除しない。
