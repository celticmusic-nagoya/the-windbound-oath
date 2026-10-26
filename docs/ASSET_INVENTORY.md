# THE WINDBOUND OATH — Asset Inventory / 正式採用アセット台帳

この台帳は `docs/ASSET_GENERATION_RULES.md` に従って管理する。**デザイン正式採用**と**リポジトリ格納・実機統合検証**は別の状態として記録する。未登録のファイルを登録済みと扱わない。

| アセット名 | 正式採用ファイル名 | 用途 | 予定リポジトリ格納先 | 状態 | 原本 SHA-256 | 備考 |
|---|---|---|---|---|---|---|
| モスの森A3 古代祭壇・通常状態 v1 | `moss_ancient_altar_idle_v1.png` | 古樹の聖域の祭壇本体（契約発動エフェクトなし） | `assets/images/environments/moss_ancient_altar_idle_v1.png` | **デザイン正式採用済み／リポジトリ格納済み（Issue #70 Draft PR #71、main未マージ）／祭壇シーン `#altarScene` で使用（A3フィールドには未配置）／Android実機検証待ち** | `86334929fa35673aec62a29818d7850e4694106893c12f6b6fa37b97028d1855` | 元画像 1536×1024 RGBA PNG、3,273,807 bytes。無加工で格納し SHA-256 一致を確認。参照: `index.html` `#altarArtBase`（祭壇シーン開始時に読み込み、`js/altar-art.js`）。A3フィールド配置は MOSS-02 との整合確認後の別工程。 |
| モスの森A3 古代祭壇・契約発動FX v1 | `moss_ancient_altar_contract_fx_v1.png` | 祭壇v1に重ねる契約発動エフェクト（魔法陣・光柱・風のリボン一体） | `assets/images/effects/moss_ancient_altar_contract_fx_v1.png` | **ユーザー正式採用済み（2026-10-26）／リポジトリ格納済み（Draft PR #71、main未マージ）／祭壇シーン `#altarScene` に実装済み（Chromium QA済）／Android実機検証待ち** | `8424bbd7933d956924f3b3f96a7daf81563e2279699857e0cc6d1fb248b23df0` | 1536×1024 RGBA PNG、343,861 bytes。祭壇v1と同一キャンバスで位置合わせ済み（オフセット0,0で重ねる）。参照: `index.html` `#altarContractFx`。「エイダンが柄を握る」行でフェードイン0.9秒→保持2.6秒→フェードアウト1.4秒（`js/altar-art.js`）。加工元: WIP `assets/images/effects/wip/moss_ancient_altar_contract_fx_base_fd470536_20261026.png`（SHA-256 `fd470536d2cf2432ee0166503fbba823126f631251031625ddb4c9a293d3a0af`、Issue #70表の「前回試作」。直近ベース 94f47151… は未受領）。`tools/assets/clean_altar_contract_fx.py` で決定的に再生成可能（もや除去・局所グロー18px＋10pxフェード・縮尺0.45）。透過QA: 外周alpha=0、alpha 0画素のRGB=0、明/灰/暗/緑背景で矩形・もやなし。 |

## 登録・検証手順

1. 元画像 `moss_ancient_altar_idle_v1.png` を**加工せず**所定パスへ格納する。
2. 格納後の SHA-256 が台帳記載の値と一致することを確認する。
3. 画像本体と台帳の状態更新を同じ作業でコミットする。必要に応じて実装側の参照パスも別途安全に接続する。
4. A3フィールドで背景透過・位置・縮尺を確認し、Android実機の結果を台帳に追記する。
5. 画像が実際にGitHubへ格納されたことを確認できるまでは「格納待ち」と記録する。

※ 契約発動FXは Issue #70 で品質検査に合格し、2026-10-26 にユーザーが正式採用した。mainへのマージはユーザーの承認後に行う。WIP原本は `assets/images/effects/wip/` に置き、正式採用を意味しない。
