# MORWEN_CANONICAL_INDEX — 正本参照の統合窓口

Task: MORWEN-CANON-CLEANUP-01 / Issue #240 / 2026-11-12
状態: **棚卸しDraft。採用・削除・移動・本番切替は行っていない。**

制作時はこの索引から目的別の原本へ進む。優先順位はディレクターの明示採用 > 検証済み公式参照 > 本番素材 > 参照専用派生 > 実験候補。同じキャラクターでもデザインシート、立ち絵、公式3方向、HDドット、歩行、リグを同一の正本と扱わない。バイナリの存在・SHA一致は美術採用や本番接続の証明ではない。

## mainで保護する正本

| 用途 | パス / 識別子 | SHA-256 | 状態 |
|---|---|---|---|
| v5.61制作デザインシート（正面を含む比較資料） | 添付 `7374.png`、実体JPEG・1536×1024 | `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638` | DESIGN_REFERENCE_APPROVED。監査したGitスナップショットの対象画像に一致するバイナリなし。**取得・制作はBLOCKED** |
| v3正式全身・サイト正面の元絵 | `assets/companions/morwen/master/morwen-full-body-v3.png` | `96a88e1deb86734fc18b5d762bad6d5c33b9a481cdbf76d45d954e92a875f990` | KEEP、マニフェスト一致 |
| v3設定参照シート | `assets/companions/morwen/reference/morwen-design-sheet-v3.png` | `384268738ff34d653dd5fb9077728d33dbedc7485aae45e5eb6b87d828a472e9` | KEEP、マニフェスト一致、RGB |
| 公式右側面 | `assets/official/characters/morwen/turnaround/file_00000000a6308211aaeeb9e2482c2e83.png` | `7eeff76ac07f631c14cb536e0e08346cfe815247a88520fb5a68cf0e877e5548` | KEEP、登録記録と一致 |
| 公式左側面 | `assets/official/characters/morwen/turnaround/file_0000000035a0820989d20c639724cc25.png` | `d858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591` | KEEP、登録記録と一致。旧左の廃止指定があるHD制作系列では使用禁止。サイトで使用中につき削除不可 |
| 公式背面 | `assets/official/characters/morwen/turnaround/file_00000000055481f8bac7574e5cab00dc.png` | `9cf2f27448303aa60c603f0f32a7baada234fec8cae5108bf8103a9ae7547e69` | KEEP、登録記録と一致 |

公式3方向は1024×1536 RGBA、αの範囲0–254。原本バイトを保護し、α255化やリカラーをしない。左向きの**鞄・帽子の花/リボン装飾・肩紋章を除外**する既存指定を保護する。後発の左向き・装飾指定は下記HD系列の決定記録として別管理し、旧左のミラーや補完生成で混ぜない。

参照: [v5.61採用記録](MORWEN_V561_CANONICAL_20261108.md)、[公式3方向登録記録](MORWEN_OFFICIAL_3V_REGISTRATION_20261109.md)、[公式設定](../lore/MORWEN_CANON_20261108.md)、`data/morwen-design-canonical.json`、`data/characters/morwen-canon.json`。既存年齢・衣装・設定の矛盾は本棚卸しで変更しない。

## HD原本・画素素材・リグの分離

PR #221 `feature/morwen-hd-canonical-v2-registration` の `data/morwen-hd-canonical-v2.json` と `assets/official/characters/morwen/hd-v2/DELIVERY_MANIFEST_V2.json` が、同系列の8原本＋4表示派生を識別する。索引末尾の表は実バイトで照合した値。**mainのv5.61デザインロックを置換する承認ではない。** 原本はKEEP、表示派生も参照依存のため保持する。

- 正面/右/左/背面HD pixel原本: `assets/official/characters/morwen/hd-v2/originals/pixel/{front,right,left,back}.png`。PR #228でもタスク固有の入力としてSHAを照合済み。旧左をHD制作へ混入しない。
- real原本: 同階層 `originals/real/`。pixel原本やv3立ち絵とは別。
- 表示派生: `display/pixel/*_1200x1600.png`。足元anchorや縮尺の未解決事項があり、本番スプライトではない。
- 旧歩行: `assets/candidates/morwen-right-walk/` の66〜72、ART案、QAを保持。72は最終美術**候補**、本番登録と同義ではない。PR #213/#214/#217〜#220等で系列を使用するため撤去不可。
- `assets/candidates/morwen/real-canon-v2/`、`real-canon-v3/`、`real-canon-final-04/`、`real-canon-final-align-01/` は候補/QA系列。`canonical`というファイル名だけで正式採用しない。
- 後発左採用記録 `docs/design/morwen-hd-walk/MORWEN_LEFT_PROFILE_APPROVAL_20261111.md` は「正本候補として正式採用」と記す一方、無加工PNGの保存・SHA登録を後工程としている。画像への一意な結び付けは**BLOCKED**。肩紋章や月桂樹の記載も旧3方向の除外指定と相違するため、別系列として保持。
- リグ: PR #238の `docs/qa/MORWEN_RIG_SOURCE_AUDIT_01.md` が48×64シート系列とHD系列の混同を禁止。PR #239の `tools/blender/` は共通基盤・測定ガイドであり正式キャラモデルではない。Source/target/anchorの採用対応が未確定のため**新規リグ・画像生成を保留**。

## 文書の不整合とサイト依存

`MORWEN_OFFICIAL_3V_REGISTRATION_20261109.md` の「BINARY UPLOAD NOT YET COMPLETED; NOT PUBLISHED」は現状と不一致。3点はmainに存在してSHA一致し、別リポジトリ `the-windbound-oath-website` の `js/site.js:124` がサイト内の同一SHAコピーを参照している。既存文書は履歴として改変せず、この索引で現状を補正する。ライブ配信状況のブラウザ検証は今回未実施。

サイトの正面は `assets/companions/morwen.webp`（ゲーム側 `web/companions/morwen.webp` と同一SHA）。v5.61 JPEGやHD pixel正面と置換しない。サイトのHTML/CSS/JS/画像は変更しない。

## 棚卸しと削除ゲート

- [機械可読棚卸し](../qa/morwen-canon-cleanup-01/MORWEN_ASSET_INVENTORY.json): repository/path/Git blob/スナップショット/SHA-256/bytes/寸法/α/分類/参照/KEEP・ARCHIVE・DELETE_CANDIDATE・BLOCKED。
- [依存関係](../qa/morwen-canon-cleanup-01/DEPENDENCIES.json)、[固定コミット](../qa/morwen-canon-cleanup-01/SNAPSHOTS.json)、[未マージPR](../qa/morwen-canon-cleanup-01/OPEN_PRS.json)。同一パスの異なるバイナリは別レコード、同一バイナリの複数ブランチはスナップショット配列に集約。
- [削除レビュー台帳](../qa/morwen-canon-cleanup-01/DELETION_MANIFEST.json): 具体的パス・SHA・ブランチ・保留根拠。**承認済み削除パスは空**。重複は削除の十分条件ではない。
- ARCHIVEは「履歴として現位置で保持する」分類。移動は参照更新を伴うため未実施。BLOCKEDは依存/採用/ソース対応が未解決。
- 正式素材、他キャラ、共有ツール、既存QAを保護する。監査は字句・basename・ディレクトリの保守的照合。動的ロードの完全な不使用証明にはならない。
- Claude独立美術QA、ディレクターの新規採用判断、Android実機QAはNOT_RUN。過去のQAを今回実行したものとして扱わない。

技術QA・実行結果: [QA_REPORT.md](../qa/morwen-canon-cleanup-01/QA_REPORT.md)。対象確定と明示承認後にのみ、再監査のうえ別cleanup commit/PRで削除する。

## PR #221 HD系列・実バイト照合表

コミットは `SNAPSHOTS.json` に固定。全件のパスとSHAは登録JSONと照合。

| 登録キー | SHA-256 | 状態 |
|---|---|---|
| `pixel.front` | `d6fe876bf997dda37aa513519f940f5560ea21ec2ac8332a05c1e1e82d2c2b5a` | KEEP / 原本 |
| `pixel.left` | `5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8` | KEEP / 原本 |
| `pixel.right` | `f2a485d2d9591cb4cdc5b5d7aabb87f539546b53899bbb1dfd8410ba99c060c7` | KEEP / 原本 |
| `pixel.back` | `64bc5cbe418d39255d28830e317c8b22fe19cb7fa5da626281fa9bca9b91e03f` | KEEP / 原本 |
| `real.front` | `f9a0272c99059480a59fdcb8a6278f318bc2da6f14f160e08f01eefdfe1d13ec` | KEEP / 原本 |
| `real.left` | `a48ab1bc86bb7a1597b701575657b95ddbbb153c5f7b0528d3e885cca7645279` | KEEP / 原本 |
| `real.right` | `b435dde0b048b1d4d7a36dd6b7b3437c6977581049ef400b3dcd290e21f50850` | KEEP / 原本 |
| `real.back` | `66bc519ddd54878b66e298b72919d52d3727f2fdfdcf8c9cfc706c699cdad8ab` | KEEP / 原本 |
| `display.pixel.front` | `a1cec16d21c6427c5b876324a7a14a2b21d83bce9cbc13ae80c0589db245ac9c` | KEEP / 派生・参照専用 |
| `display.pixel.left` | `e0fe405042d2aac57a1cebf233af5b8f0c238a12c9562394e676615235a8d7e7` | KEEP / 派生・参照専用 |
| `display.pixel.right` | `531c4ee0618f2d7648cc76e4f83c3390de0e470badccb13e159ca909e5d68144` | KEEP / 派生・参照専用 |
| `display.pixel.back` | `047fb26bd6ae5598178a8a9897454aac1e5a155d5613ccf9e35628ece3db7f64` | KEEP / 派生・参照専用 |
| `real.portrait` | `141a6955af90f8678e408efd3649e3e114c3c4c44c682e00c6679e386474581b` | KEEP / 原本 |
