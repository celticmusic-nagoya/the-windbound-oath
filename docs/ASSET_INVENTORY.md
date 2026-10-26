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

## 登録・検証手順

1. 元画像 `moss_ancient_altar_idle_v1.png` を**加工せず**所定パスへ格納する。
2. 格納後の SHA-256 が台帳記載の値と一致することを確認する。
3. 画像本体と台帳の状態更新を同じ作業でコミットする。必要に応じて実装側の参照パスも別途安全に接続する。
4. A3フィールドで背景透過・位置・縮尺を確認し、Android実機の結果を台帳に追記する。
5. 画像が実際にGitHubへ格納されたことを確認できるまでは「格納待ち」と記録する。

※ 契約発動FXは Issue #70 で品質検査に合格し、2026-10-26 にユーザーが正式採用した。mainへのマージはユーザーの承認後に行う。WIP原本は `assets/images/effects/wip/` に置き、正式採用を意味しない。
