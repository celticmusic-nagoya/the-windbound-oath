# Loading CG 制作計画・生成待ち

基準main: `e3565b68acc581759d24c7f6154cdeb51d58f049`。ブランチ: `work/codex-loading-cg`。

**未生成・未実装**。画像生成APIの初回が HTTP 429 `usage_limit_reached` で終了。成功したCGは0枚。生成制限を回避せず停止した。

## 画風・制作方針

バイブルv1.1と正式バトル画像に合わせた、ケルト／ヨーロッパ風の手描きアニメ・絵画調の背景CG。既存フィールドの石と木材・緑の屋根・苔・花・生活感を引き継ぐ。Loading CGは地形そのものの変更ではない。

最初は人物を中心にせず、場所の雰囲気を描く。仲間の先行登場、未確定の王族・敵、真相を示す紋章などは描かない。文字やLoading表示を画像に焼き込まない。背景CGなので全面不透明が正常であり、透過PNGは要求しない。

構図: 横長、中央に主要ランドマーク、下20%に穏やかな余白。縦画面で見切れる場合は全体表示（contain）を第一候補とし、無理な中央cropを必須にしない。実生成寸法を確認してからPC/スマホ表示を決める。

## 現行マップ対応（28 / 28）

| Map ID | 表示名 | CG案 |
|---|---|---|
| `cliff_moher_01_spiral_ascent` | 風見の断崖 | `windward_cliff` |
| `fort_dunvall_01_courtyard` | ドゥンヴァル砦　中庭 | `dunvar` |
| `fort_dunvall_02_ramparts` | ドゥンヴァル砦　城壁 | `dunvar` |
| `fort_dunvall_03_keep` | ドゥンヴァル砦　主塔 | `dunvar` |
| `fort_in_tavern` | ドゥンヴァル砦　酒場「錆びた角笛」 | `dunvar_tavern` |
| `moss_forest_01_sunlit_path` | 陽だまりの森道 | `moss_path` |
| `moss_forest_02_mossy_ravine` | 苔むした渓谷 | `moss_ravine` |
| `moss_forest_03_ancient_grove` | 古樹の聖域 | `moss_grove` |
| `rilde_in_aidan` | エイダンの家 | `rilde_home` |
| `rilde_in_barn` | 納屋 | `rilde_storage` |
| `rilde_in_elder` | 長老の家 ― 風見の丘 | `rilde_home` |
| `rilde_in_house_01` | 村人の家 | `rilde_home` |
| `rilde_in_house_02` | 村人の家 | `rilde_home` |
| `rilde_in_house_03` | 村人の家 | `rilde_home` |
| `rilde_in_house_04` | 村人の家 | `rilde_home` |
| `rilde_in_inn_1f` | 宿屋「風見鶏」 1階 | `rilde_inn` |
| `rilde_in_inn_2f` | 宿屋「風見鶏」 2階 | `rilde_inn` |
| `rilde_in_shop` | 道具屋「若葉の袋」 | `rilde_shop` |
| `rilde_in_storage` | 倉庫 | `rilde_storage` |
| `rilde_village_01_peace` | リルド村 | `rilde_peace` |
| `rilde_village_01_ruin` | リルド村（襲撃後） | `rilde_ruin` |
| `road_dunvall_capital_01` | 街道　砦と王都のあいだ | `road_caerdyn` |
| `royal_capital_00_gate` | 王都カエルディン　南大城門・旅人街 | `caerdyn` |
| `royal_capital_01_market` | 王都　商業区 | `caerdyn` |
| `royal_capital_02_castle_plaza` | 王都　城前広場 | `caerdyn` |
| `royal_capital_03_residential` | 王都　住宅街 | `caerdyn` |
| `royal_in_guild` | 冒険者ギルド兼大酒場 | `caerdyn_guild` |
| `royal_in_inn` | 宿屋「旅人の灯」 | `caerdyn_inn` |

現行28マップを16種類のCGでカバーする案。一般住宅6マップ、王都屋外4マップ、砦3マップなどで共有し、通信量と画風のばらつきを抑える。森は3エリアの特徴を分け、平和村と廃墟村は混用しない。

## 設定確定・未実装エリア

以下10案はバイブルにあるが、現在のマップIDを捏造して割り当てない。Claude側でID・入口と詳細が確定後に対応させる。王城内部・周年祭専用・各施設内部の独自構図は詳細確定後の別工程。

- `capital_knights`: 騎士団地区【予定】
- `capital_cathedral`: 大聖堂地区【予定】
- `capital_academy`: 魔法学術地区【予定】
- `capital_craft`: 職人地区【予定】
- `capital_alley`: 裏路地【予定】
- `capital_castle`: 王城地区【予定】
- `underground_waterway`: 旧水路【予定】
- `underground_crypt`: 地下墓所・旧王国施設【予定】
- `underground_ruins`: 古代都市遺構【予定】
- `seventh_sector`: 第七封鎖区画【予定】

## 再開手順

1. 最新mainのマップ追加・バイブル変更を再確認。
2. `production-plan.json` のpromptで、まず平和村・森・王都の代表CGを個別生成。確定画像は参考画像として使い、合成シートのcropは使わない。
3. 実画像を視覚確認し、画風・地理・不要な文字・欠損・ネタバレ・PC/スマホ構図を確認。代表絵を作者PLAYER QAへ提示する。
4. 承認された画風で残りのCGを生成。初回候補は全26種類（現行16＋予定10）。
5. 実測dimensions/形式/サイズ/SHA-256を記録。配信用圧縮版を作る場合は元PNGを保持し、サイズ削減後の視覚QAも実施。
6. 全マップIDの対応漏れと画像404をテスト。存在しない候補パスをruntimeに登録しない。

## Loading連携の調査

`js/field/moss-forest-runtime.js` の `enter()` が論理map ID解決、loadMap、ForestLoader.prepare、mount、fadeを管理する。現状この箇所にCG選択のフックはない。今回は画像生成に至らないため実装変更なし。

将来は独立したLoading CGモジュールとmapId→CG manifestを使用し、runtimeの開始/終了に最小フックを追加する案。Claude所有のstory/index本体は無断変更しない。CG読込失敗時も既存のmap loadingを継続し、CGのために待機時間を増やさない。全26枚の先読みはせず、遷移先の1枚だけcacheする。inputのbusy保護を維持し、save/map/戦闘処理は変更しない。

## 今回の確認結果

- 全28 map JSONを読み込み、重複なし・対応漏れなしを検証。
- 出力は資料2ファイルのみ。HTML/CSS/JS、data/maps、正式画像は変更なし。
- 画像生成0枚、画像QA／CG表示QAは未実施。
- mainへのmerge、push、本番Pages deploymentは行わない。作業ブランチだけpushする。

STATUS: BLOCKED — IMAGE GENERATION USAGE LIMIT
