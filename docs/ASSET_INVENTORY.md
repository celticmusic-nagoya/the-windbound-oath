# THE WINDBOUND OATH — Asset Inventory / 正式採用アセット台帳

この台帳は `docs/ASSET_GENERATION_RULES.md` に従って管理する。**デザイン正式採用**と**リポジトリ格納・実機統合検証**は別の状態として記録する。未登録のファイルを登録済みと扱わない。

| アセット名 | 正式採用ファイル名 | 用途 | 予定リポジトリ格納先 | 状態 | 原本 SHA-256 | 備考 |
|---|---|---|---|---|---|---|
| モスの森A3 古代祭壇・通常状態 v1 | `moss_ancient_altar_idle_v1.png` | 古樹の聖域の祭壇本体（契約発動エフェクトなし） | `assets/images/environments/moss_ancient_altar_idle_v1.png` | **デザイン正式採用済み／リポジトリ格納済み（Issue #70 Draft PR #71、main未マージ）／祭壇シーン `#altarScene` で使用（A3フィールドには未配置）／Android実機検証待ち** | `86334929fa35673aec62a29818d7850e4694106893c12f6b6fa37b97028d1855` | 元画像 1536×1024 RGBA PNG、3,273,807 bytes。無加工で格納し SHA-256 一致を確認。参照: `index.html` `#altarArtBase`（祭壇シーン開始時に読み込み、`js/altar-art.js`）。A3フィールド配置は MOSS-02 との整合確認後の別工程。 |
| モスの森A3 古代祭壇・契約発動FX v1 | `moss_ancient_altar_contract_fx_v1.png` | 祭壇v1に重ねる契約発動エフェクト（魔法陣・光柱・風のリボン一体） | `assets/images/effects/moss_ancient_altar_contract_fx_v1.png` | **ユーザー正式採用済み（2026-10-26）／リポジトリ格納済み（Draft PR #71、main未マージ）／祭壇シーン `#altarScene` に実装済み（Chromium QA済）／Android実機検証待ち** | `8424bbd7933d956924f3b3f96a7daf81563e2279699857e0cc6d1fb248b23df0` | 1536×1024 RGBA PNG、343,861 bytes。祭壇v1と同一キャンバスで位置合わせ済み（オフセット0,0で重ねる）。参照: `index.html` `#altarContractFx`。「エイダンが柄を握る」行でフェードイン0.9秒→保持2.6秒→フェードアウト1.4秒（`js/altar-art.js`）。加工元: WIP `assets/images/effects/wip/moss_ancient_altar_contract_fx_base_fd470536_20261026.png`（SHA-256 `fd470536d2cf2432ee0166503fbba823126f631251031625ddb4c9a293d3a0af`、Issue #70表の「前回試作」。直近ベース 94f47151… は未受領）。`tools/assets/clean_altar_contract_fx.py` で決定的に再生成可能（もや除去・局所グロー18px＋10pxフェード・縮尺0.45）。透過QA: 外周alpha=0、alpha 0画素のRGB=0、明/灰/暗/緑背景で矩形・もやなし。 |
| モスの森A3 ルー初登場イベントCG v1 | `moss_lou_first_meeting_cg_v1.png` | ルー初登場イベント（`#louIntroScene`）。フィオナの手のひらの上に浮かぶルー。祭壇CG③とは別素材 | `assets/images/events/moss_lou_first_meeting_cg_v1.png` | **ユーザー正式採用済み（2026-10-27）／リポジトリ格納済み（Draft PR #71、main未マージ）／`js/event-cg.js` で表示（Chromium QA済）／Android実機検証待ち** | `960ac2335348195e68cf06094228cbdf272fd55a1137b037d340a5b65c3c79bf` | 1536×1024 RGB PNG、3,207,600 bytes。`louIntroLines` 3〜5行で表示。 無加工（再生成・トリミング・圧縮なし）。透過不要（不透明CG）。 |
| モスの森A3 祭壇イベントCG① 父の剣の破損 v1 | `moss_altar_cg01_father_sword_break_v1.png` | 祭壇イベント（`#altarScene`）。レイダーの攻撃で父の剣が折れる | `assets/images/events/moss_altar_cg01_father_sword_break_v1.png` | **ユーザー正式採用済み（2026-10-27）／リポジトリ格納済み（Draft PR #71、main未マージ）／`js/event-cg.js` で表示（Chromium QA済）／Android実機検証待ち** | `94ed1387d2268a783b57e2147292b82b6c7fc01268e861190205aec4078fb2c7` | 1536×1024 RGB PNG、3,167,353 bytes。`altarLines` 14〜16行で表示。 無加工（再生成・トリミング・圧縮なし）。透過不要（不透明CG）。 |
| モスの森A3 祭壇イベントCG② 風の舞の初発動 v1 | `moss_altar_cg02_wind_dance_first_v1.png` | 祭壇イベント。フィオナの「風の舞」初発動 | `assets/images/events/moss_altar_cg02_wind_dance_first_v1.png` | **ユーザー正式採用済み（2026-10-27）／リポジトリ格納済み（Draft PR #71、main未マージ）／`js/event-cg.js` で表示（Chromium QA済）／Android実機検証待ち** | `e695a27c81f9c65f4999549fd41dec44670a171833f0036fffa03d88dcd7f4c3` | 1536×1024 RGB PNG、3,268,763 bytes。`altarLines` 18〜20行で表示。 無加工（再生成・トリミング・圧縮なし）。透過不要（不透明CG）。 |
| モスの森A3 祭壇イベントCG③ ルーの足止め v1 | `moss_altar_cg03_lou_stall_v1.png` | 祭壇イベント。ルーが加勢してレイダーを足止め | `assets/images/events/moss_altar_cg03_lou_stall_v1.png` | **ユーザー正式採用済み（2026-10-27）／リポジトリ格納済み（Draft PR #71、main未マージ）／`js/event-cg.js` で表示（Chromium QA済）／Android実機検証待ち** | `28138ecc2ee022c2bb85b5cde4af0d034ada5289dd20182a24ba882a067e988c` | 1536×1024 RGB PNG、3,406,431 bytes。`altarLines` 21〜23行で表示。 無加工（再生成・トリミング・圧縮なし）。透過不要（不透明CG）。 |
| モスの森A3 祭壇イベントCG④ 誓いの剣の契約 v1 | `moss_altar_cg04_oath_contract_v1.png` | 祭壇イベント。エイダンと誓いの剣の契約 | `assets/images/events/moss_altar_cg04_oath_contract_v1.png` | **ユーザー正式採用済み（2026-10-27）／リポジトリ格納済み（Draft PR #71、main未マージ）／`js/event-cg.js` で表示（Chromium QA済）／Android実機検証待ち** | `0e8963dc3afe3c192d71bb761c609fccfe7273a98a00c91ac27c23ee0a68d92a` | 1536×1024 RGB PNG、3,376,649 bytes。`altarLines` 32〜35行。32行目の祭壇FXフェードアウト（握ってから3.5秒後）と同時に1.4秒でフェードイン、36行目で祭壇画面へ戻る。 無加工（再生成・トリミング・圧縮なし）。透過不要（不透明CG）。 |

## キャラクター（タイトル画面）

| アセット名 | 正式採用ファイル名 | 用途 | 格納先 | 状態 | 原本 SHA-256 | 備考 |
|---|---|---|---|---|---|---|
| エイダン後ろ姿 v2（タイトル画面） | `aidan_back_v2.png` | タイトル画面のエイダン（縦・横画面共通の主役レイヤー）。物語上の誓いの剣の入手時期（モスの森の祭壇での契約後）とは無関係な象徴的ビジュアル | `assets/images/characters/aidan_back_v2.png` | **ユーザー正式採用済み（2026-10-27）／main統合承認済み（PR #72、2026-10-27）／タイトル画面で参照（`js/title-screen.js`）** | `763648ab515a07d48100fa8991286374ce60761a08466cc71bbfbcc1894a9160` | 1152×1536 RGBA PNG、1,926,965 bytes、完全透過（アルファ0の画素のRGB=0、つながった塊は1つ）、左右に透明余白64px。受領元画像（SHA-256 `85caaedc…f91a`）→ 透過仕上げ v1（`e9173ea7…1178`）→ v2（柄頭・鍔を正式設定画に合わせ、柄を鞘の直線軸にそろえた）。原本・v1・品質レポートは handoff リポジトリ `reports/ASSETS/AIDAN-BACK-20261027/`。旧タイトル画像 `img/title/aidan-portrait.png`（SHA-256 `0dd61691…74a6`）は削除せず保管、タイトルからの参照のみ v2 へ切替（台帳上は置換済み：既存ルールどおり approval_status `REVISION_REQUIRED`＋備考 `superseded`、`ASSET_BACKLOG.md` の「置換済み」に掲載）。Android実機での表示確認待ち。 |

## タイトル画面（前景）

| アセット名 | 正式採用ファイル名 | 用途 | 格納先 | 状態 | 原本 SHA-256 | 備考 |
|---|---|---|---|---|---|---|
| タイトル前景・草花と岩（エイダンの足元） | `foreground-meadow.png` | タイトル画面でエイダンの両足の下に敷く透過前景。旧 `img/title/foreground-grass.svg` の表示を置き換え（SVG ファイルは削除せず残置・参照なし） | `img/title/foreground-meadow.png` | **ユーザー提供・採用（2026-10-27、PR #76 で main 統合）／`css/title-screen.css` の `.title-foreground` で参照／Android実機確認待ち** | `cfcc624adbfa8c29994f9c3fd81f41d606dfa623325bedbcca5b3743e554c9f1` | 2014×781 RGBA PNG、1,403,346 bytes。草花・岩のみ（遺跡・樹木なし）。アルファ最大 254。無加工（再生成・トリミング・圧縮なし）。表示位置・大きさは CSS のみで調整（2026-10-27、両足の接地） |
| タイトル前景・縦画面用（草と小花） | `foreground-meadow-portrait.png` | 縦画面のタイトルでエイダンの両足の下に敷く透過前景（横画面・PC は `foreground-meadow.png` のまま） | `img/title/foreground-meadow-portrait.png` | **ユーザー承認の派生素材（2026-10-27、DIRECTIVE-17E 案①）／`css/title-screen.css` の縦画面ルールで参照／Android実機確認待ち** | `05b5b3e19e9606801c9cc19ede94e465ee625a19a3ee85f321ff4fe8ec10811c` | 540×200 RGBA PNG。`foreground-meadow.png`（`cfcc624a…`、不変）から `tools/assets/make_title_foreground_portrait.py` で生成：岩のない草と小花の層（x20–560, y330–530）、縦画面背景の足元に合わせた色調、上縁のみ軽いぼかし、左右と上のアルファグラデーション。`--check` で再現性を確認 |

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

## Phase4 normal-only adoption (DIRECTIVE-19B, 2026-10-29)

採用者：ユーザー。下記normal3枚のみ正式採用。その他21表情は未承認、瞬きは未実装（静止画）。[新しい承認記録](portraits/PHASE4_ADOPTED_NORMALS.md)・[過去の19A監査](portraits/PHASE4_ADOPTION_AUDIT.md)。

| キャラ | 正式格納先 | SHA-256 | 解像度 | 状態 |
|---|---|---|---|---|
| フィオナ | `assets/images/characters/portraits/fiona/fiona_normal.png` | `89efd67352ac7f03882242d2363a2a2c8762bc0489e447a7d6089745a227094a` | 1024×1536 | APPROVED / normalのみ / 無加工 / 瞬き未実装 |
| ルー | `assets/images/characters/portraits/lou/lou_normal.png` | `c2cc6d70614b18c685ef773e27bf4f50a7ed2947cb6e6b9367a5ba9e32e59e8f` | 1312×1199 | APPROVED / normalのみ / 無加工 / 瞬き未実装 |
| エマ | `assets/images/characters/portraits/emma/emma_normal.png` | `f4dfd09d08e3bd333743f677afbe84e4e1771b295863e92a96a3b4c0904114b2` | 1024×1536 | APPROVED / normalのみ / 無加工 / 瞬き未実装 |

## 登録・検証手順

1. 元画像 `moss_ancient_altar_idle_v1.png` を**加工せず**所定パスへ格納する。
2. 格納後の SHA-256 が台帳記載の値と一致することを確認する。
3. 画像本体と台帳の状態更新を同じ作業でコミットする。必要に応じて実装側の参照パスも別途安全に接続する。
4. A3フィールドで背景透過・位置・縮尺を確認し、Android実機の結果を台帳に追記する。
5. 画像が実際にGitHubへ格納されたことを確認できるまでは「格納待ち」と記録する。

※ 契約発動FXは Issue #70 で品質検査に合格し、2026-10-26 にユーザーが正式採用した。mainへのマージはユーザーの承認後に行う。WIP原本は `assets/images/effects/wip/` に置き、正式採用を意味しない。

## DIRECTIVE-20D (2026-10-30): Phase4 revised20C provisional Android QA

Exactly43 PNGs (19 expressions,24 normal-eye overlays) are **PROVISIONAL_ANDROID_QA**, not formally adopted. Source commit `b8517c2cf74445362ce1a557cf7c4ecd280d94fe`; immutable paths/hashes/quality concerns in [the ledger](portraits/PHASE4_PROVISIONAL_20C.json), [usage and adoption scope](portraits/PHASE4_PROVISIONAL_20C.md). Adopted normal3/Aidan54 remain unchanged. Lou smile/relieved excluded. Android physical judgment pending.

## Eyelid correction after Android feedback (20E,2026-10-30)

User requested Fiona/Lou eyelid correction for blinking AND static expressions and approved the natural-curve reference.16blink overlays +12expression versions now live under `provisional-20e/`; old20C PNGs remain unchanged as history. New derived assets stay **PROVISIONAL_ANDROID_QA**. Emma was declared Android QA PASS and its15candidate PNGs, normal, geometry and paths are unchanged. Formal normal3/Aidan54/CG10 are preserved. [Source/sha/mask ledger](portraits/PHASE4_EYELID_REVISION_20E.json), [user feedback](qa/PHASE4_ANDROID_FEEDBACK_20261030.md).

## DIRECTIVE-21A (2026-10-30): Phase4正式採用

ユーザーAndroid実機QA全4項目PASSを根拠に、PR91マージ `bdf6a6dd50a26183daa181342d1fa546f5873418` で実際に公開・使用した22表情PNG(normal3を含む)＋24normal瞬きPNG、計46枚を正式採用。既存normal3の採用を維持し、現行43候補をAPPROVEDへ昇格。Fiona/Lou20E・Emma20Cを正とし、旧Fiona/Lou20C候補やLou smile/relievedは含めない。PNG/runtime/表示logicは無変更。

正式台帳：[PHASE4_FORMAL_ADOPTION_21A](portraits/PHASE4_FORMAL_ADOPTION_21A.md)、[46枚の固定SHA](portraits/PHASE4_ADOPTED_SHA256SUMS)。過去の暫定採用資料は当時の履歴として保持し、本決定で対象パスのみ上書きする。回帰m49は全46枚＋Aidan54/CG10のSHAと実登録先・未採用ステータスを保護。

## DIRECTIVE-21C (2026-10-30):15表情瞬き・暫定Android QA

Fiona/Lou/Emmaのangry/sad/surprised/worried/determined用120PNGを **PROVISIONAL_ANDROID_QA** として追加。source handoff21B @883624694e73a0839fc0db684ca76067765e7338、全SHAと親43素材SHAは正式21A台帳に一致。正式46PNG・エイダン/CGは無変更。静止4表情とLou未採用2表情は変更しない。残存課題・出典：[21C台帳](portraits/PHASE4_EXPRESSION_BLINK_21C.md)。最終Android判断はユーザー待ち。

## DIRECTIVE-22A (2026-10-30):120表情瞬き正式採用

ユーザーAndroid実機QAで全キャラクターの瞬き合格、PR93の120PNGを正式採用。実公開runtime merge72c83eeからSHAを固定し、120件をAPPROVED/QA・AndroidPASSへ昇格。既存21A46PNG・Aid54/CG10は無変更。Phase4は22表情＋144瞬き＝166正式PNG。[22A正式台帳](portraits/PHASE4_EXPRESSION_BLINK_FORMAL_22A.md)。

フィオナ5枚修正版の受領は別工程。現handoff5fa3532はピンク線を消したが茶色の二重眉が残るためQA差戻し・未統合。原本・144瞬きPNGは変更せず、[Claude向けレビュー](handoff/DIRECTIVE-22A_FIONA_CHANGES_REQUESTED.md)を正とする。
