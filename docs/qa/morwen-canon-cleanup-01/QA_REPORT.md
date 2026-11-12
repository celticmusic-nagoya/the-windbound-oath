# MORWEN-CANON-CLEANUP-01 — self-QA

2026-11-12 / inventory-only Draft / Refs #240

- 基準main: `cab9aa52da653198a712bd986992adc03ea4bfe2`。
- 関連20ブランチ＋game main＋website mainの22スナップショットを固定。website: `722d05998dd6ade39db82aa9fee6868dd416d041`。
- Issueのblender系列「morwen名450 blob」を再現。game mainは434件。共通ツール・スタジオ・共有manifestも追加し、全系列1835件を棚卸し（単位: repository/path/blob。main単独は共有manifest込み435件）。
- KEEP 610 / ARCHIVE 21 / DELETE_CANDIDATE 0 / BLOCKED 1204。
- SHA完全一致の重複120組。候補系列の重複256レコードを削除レビュー台帳に列挙。ブランチ別バイナリ・サイトコピーを含むため、組数は削除可能数ではない。

## 実行した検証

PASS: 1835レコードのGit blobからSHA-256・bytesを再計算、登録原本/表示派生/portraitの18 SHAを既存manifest・公式登録記録と照合。サイトの4画像もgame側の対応画像とSHA一致。画像寸法・モード・αを実バイトから取得（GIFの透過indexも検査）。参照IDの整合、レコード一意性、集計、保護素材KEEP、固定ブランチcommit一致を検証。

PASS: `python -m py_compile scripts/audit_morwen_inventory.py scripts/verify_morwen_inventory.py`。

PASS: 文書・台帳・監査/検証スクリプトの追加のみ。既存ファイル変更・削除・移動・画像追加・本番コード差分は0。正式採用デザイン、ゲーム機能、SAVE、サイト、他キャラへの適用変更なし。

再実行:
```
python scripts/audit_morwen_inventory.py --website /path/to/the-windbound-oath-website
python scripts/verify_morwen_inventory.py --website /path/to/the-windbound-oath-website
```
`SNAPSHOTS.json`のコミットがローカルGitに必要。監査結果は固定commitに対するもの。削除前には最新のmain/関連PR/サイトを再監査する。

## 具体的パスのレビュー例（削除しない）

| パス | SHA-256 / 根拠 | 判定 |
|---|---|---|
| `assets/candidates/morwen-right-walk/71/proposals/FLOWER/masks/accessories_fixed.png` | `29911324a5dc9399237ae75f7ddbc951c867469a312b0c68360e2e2bd7883805`。他版maskと完全一致。不採用案でも再現用metadata・動的読込への依存が未解決 | BLOCKED |
| `assets/candidates/morwen-right-walk/72/masks/accessories_fixed.png` | 同SHA。72のQA/再現用素材を保護 | BLOCKED |
| `assets/candidates/morwen-walk-4dir/sheet_left_74G_48x64.png` | `08817e452e39b7bdefb174a72813576c9a0019d17af70c4ec5cf141b65d161ad`。74G系列と重複するが、未マージ4dir系列の候補・動的依存を保護 | BLOCKED |

具体的な全パス・SHA・ブランチ・保留理由は `DELETION_MANIFEST.json`、参照元は `MORWEN_ASSET_INVENTORY.json` → `DEPENDENCIES.json` に記録。**確定削除対象/承認済み削除対象とも0件**。重複のみを根拠に削除対象を作らない。

## 残るBLOCKED / NOT_RUN

- v5.61の指定JPEG原本は対象Git画像中にSHA一致なし。添付/Driveの原本は今回未取得。リグのsource/target対応は確定せず、新規制作保留。
- 公式3方向登録文書の「未登録」は実バイナリ・サイトコードと不一致。既存記録を上書きせず統合索引で補正。
- 後発HD左採用記録と旧3方向の左除外指定は異なる系列。最新左の採用画像とのSHA対応未確定、勝手な一本化不可。
- 1912テキスト文書variantをpath/basename/stem/ディレクトリ/近傍動的loaderで保守的に照合。ヒットは依存可能性であり、実行到達の証明ではない。ヒットなしも動的未使用の証明ではない。ARCHIVEは現位置で保全する分類。
- 調査範囲は公開mainと関連PRの固定snapshot、公式サイトmain。private lore、外部ストレージ全体、他の非関連PR、ライブサイト表示は未検証。
- 今回のQAはCodex自己QA。Claude独立美術QA・人間視覚承認・Android実機QAはNOT_RUN。過去のQA文書は再利用した履歴で、今回の実行結果ではない。
- ゲーム/サイトの実行経路は変更していないため、アプリのブラウザ回帰は今回実行していない。

次工程は依存と採用画像の対応解消後、ディレクターがrepo/ref/path/SHA単位で対象を確定・明示承認し、別cleanup commit/PRで削除。本PRはDraftを維持し、mainへのマージ・サイト公開は行わない。
