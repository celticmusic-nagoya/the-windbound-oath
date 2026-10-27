# THE WINDBOUND OATH — Asset Inventory / 正式採用アセット台帳

この台帳は `docs/ASSET_GENERATION_RULES.md` に従って管理する。**デザイン正式採用**と**リポジトリ格納・実機統合検証**は別の状態として記録する。未登録のファイルを登録済みと扱わない。

| アセット名 | 正式採用ファイル名 | 用途 | 予定リポジトリ格納先 | 状態 | 原本 SHA-256 | 備考 |
|---|---|---|---|---|---|---|
| モスの森A3 古代祭壇・通常状態 v1 | `moss_ancient_altar_idle_v1.png` | 古樹の聖域の祭壇本体（契約発動エフェクトなし） | `assets/images/environments/moss_ancient_altar_idle_v1.png` | **デザイン正式採用済み／リポジトリ格納待ち／A3実機合成検証待ち** | `86334929fa35673aec62a29818d7850e4694106893c12f6b6fa37b97028d1855` | 元画像 1536×1024 RGBA PNG、3,273,807 bytes。元画像はチャット作業環境に存在。リポジトリには未登録。 |

## キャラクター（会話立ち絵）

会話立ち絵の正式な置き場所は `assets/images/characters/portraits/{characterId}/`、参照先は `js/field/portrait-registry.js` で一元管理する。既存ブランチの `img/portraits/`（フィオナ・ルー・エマ）は移植元であり正式参照先ではない（未採用の表情を含むため、Phase 4 で表情ごとに採用判断）。

| アセット名 | 正式採用ファイル名 | 用途 | 予定リポジトリ格納先 | 状態 | 原本 SHA-256 | 備考 |
|---|---|---|---|---|---|---|
| エイダン会話立ち絵・通常（`normal`） | `aidan_normal.png` | 会話立ち絵（FieldTalk の `char:'aidan', face:'normal'`） | `assets/images/characters/portraits/aidan/aidan_normal.png` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | `c2036b46c91a3a47ffeec43b5b5ebb0035e8b347f82ee6338ab23d6062dfce53` | 1024×1536 RGBA PNG、無加工。原本 handoff `handoff/aidan-expressions-claude-20261027` の `reports/ASSETS/AIDAN-EXPR-20261027/v2/``aidan_expr_normal_candidate_v1.png`（ファイル名のみ表情IDに変更）。顔以外の画素・アルファは通常と同一。基準画像（正式採用立ち絵の透過仕上げ） |
| エイダン会話立ち絵・微笑み（`smile`） | `aidan_smile.png` | 会話立ち絵（FieldTalk の `char:'aidan', face:'smile'`） | `assets/images/characters/portraits/aidan/aidan_smile.png` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | `8cb95b14db8e2508d5b0b5ae95d0657f19fccacdca7019ce21fcabe6bc4e69cf` | 1024×1536 RGBA PNG、無加工。原本 handoff `handoff/aidan-expressions-claude-20261027` の `reports/ASSETS/AIDAN-EXPR-20261027/v2/``aidan_expr_smile_b_candidate_v2.png`（ファイル名のみ表情IDに変更）。顔以外の画素・アルファは通常と同一。微笑みB v2（案A・B v1 は参考素材として handoff に保管、不採用） |
| エイダン会話立ち絵・怒り（`angry`） | `aidan_angry.png` | 会話立ち絵（FieldTalk の `char:'aidan', face:'angry'`） | `assets/images/characters/portraits/aidan/aidan_angry.png` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | `6152d05b31a357aea6a091107c4e011f1bb55c914e4ede6eac8bdc281138af35` | 1024×1536 RGBA PNG、無加工。原本 handoff `handoff/aidan-expressions-claude-20261027` の `reports/ASSETS/AIDAN-EXPR-20261027/v2/``aidan_expr_angry_candidate_v1.png`（ファイル名のみ表情IDに変更）。顔以外の画素・アルファは通常と同一。 |
| エイダン会話立ち絵・困り顔（悲しみ）（`worried`） | `aidan_worried.png` | 会話立ち絵（FieldTalk の `char:'aidan', face:'worried'`） | `assets/images/characters/portraits/aidan/aidan_worried.png` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | `0d3d63643ff90dbb28b1a1e5beeacc0a205ed1aa462c14231158c72c29e939d4` | 1024×1536 RGBA PNG、無加工。原本 handoff `handoff/aidan-expressions-claude-20261027` の `reports/ASSETS/AIDAN-EXPR-20261027/v2/``aidan_expr_sad_troubled_candidate_v1.png`（ファイル名のみ表情IDに変更）。顔以外の画素・アルファは通常と同一。表情ID `worried`（2026-10-27 承認） |
| エイダン会話立ち絵・伏し目（悲しみ）（`sad`） | `aidan_sad.png` | 会話立ち絵（FieldTalk の `char:'aidan', face:'sad'`） | `assets/images/characters/portraits/aidan/aidan_sad.png` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | `c53e564c73e8b97d5a4268a642b5fda0c2c8c5b60db236c49ea4ca3e33d2873d` | 1024×1536 RGBA PNG、無加工。原本 handoff `handoff/aidan-expressions-claude-20261027` の `reports/ASSETS/AIDAN-EXPR-20261027/v2/``aidan_expr_sad_downcast_candidate_v1.png`（ファイル名のみ表情IDに変更）。顔以外の画素・アルファは通常と同一。表情ID `sad`（2026-10-27 承認） |
| エイダン会話立ち絵・驚き（`surprised`） | `aidan_surprised.png` | 会話立ち絵（FieldTalk の `char:'aidan', face:'surprised'`） | `assets/images/characters/portraits/aidan/aidan_surprised.png` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | `50f7b7f2628d2aa3bed57d697bf823c702feb1199d9a8db8977c4d1b30f94182` | 1024×1536 RGBA PNG、無加工。原本 handoff `handoff/aidan-expressions-claude-20261027` の `reports/ASSETS/AIDAN-EXPR-20261027/v2/``aidan_expr_surprised_candidate_v1.png`（ファイル名のみ表情IDに変更）。顔以外の画素・アルファは通常と同一。 |
| エイダン会話立ち絵・瞬き重ね画像 Phase 2 Rev2 | `blink/<表情ID>_{L,R}_s{1..4}.png`（48枚） | 会話立ち絵の瞬き（閉じ度30/60/85/100%、260ms、3〜6秒間隔、左右同期） | `assets/images/characters/portraits/aidan/blink/` | **ユーザー正式採用済み（2026-10-27）／作業ブランチ `feature/talk-portrait-common` に格納（Draft PR、main未マージ）／会話立ち絵レジストリ `js/field/portrait-registry.js` から参照** | 48枚と表情6枚の個別値は `assets/images/characters/portraits/aidan/SHA256SUMS`（同ファイルの SHA-256 `55d8677373cd2c2ea13a9ccf999fa0c3afe183fc66e8c8b916430087cab5674b`） | 目元だけの RGBA パッチ（変化した画素のみ不透明）、貼り付け位置は L `[570,268,654,320]`・R `[672,314,716,350]`（6表情共通、元画像の座標）。原本 handoff `handoff/talk-portrait-blink-claude-20261027` の `reports/TALK-PORTRAIT-BLINK-20261027/phase2-aidan-rev2/`（採用記録 `ADOPTED.md`、`MANIFEST_ADOPTED.sha256` とバイト一致）。前版 `phase2-aidan/`・`phase2-aidan-rev1/` は不採用。無断で再生成・改変しない。 |

## 登録・検証手順

1. 元画像 `moss_ancient_altar_idle_v1.png` を**加工せず**所定パスへ格納する。
2. 格納後の SHA-256 が台帳記載の値と一致することを確認する。
3. 画像本体と台帳の状態更新を同じ作業でコミットする。必要に応じて実装側の参照パスも別途安全に接続する。
4. A3フィールドで背景透過・位置・縮尺を確認し、Android実機の結果を台帳に追記する。
5. 画像が実際にGitHubへ格納されたことを確認できるまでは「格納待ち」と記録する。

※ 契約発動の魔法陣・風エフェクトは品質不合格／未承認のため正式採用台帳には追加しない。
