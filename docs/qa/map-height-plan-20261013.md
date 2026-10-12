# マップ別高さ計画（提案、2026-10-13）

基準main: `058cfc8`。ブランチ: `work/codex-standing-orders`。STATUS: READY（計画書、未採用/未実装）。
要約: 崖/夕日の丘→砦→モスA1/A2/A3→村→他の順で、既存歩行経路に沿う局所段差から検討する。接触レベル対応・セーブの加算対応・Android実測が先行条件。JSON/生成元/素材/物語進行は変更しない。

## 調査基準と全体ルール

前回 `work/codex-night-j` / fcd5ab4の29マップ表を参照し、最新data/maps/*.jsonを全件読み直した。現在は **30JSON**（旧29にdev_height_protoが追加）。内訳: 本編28＋DEV2。本編28はheight無し、height有りはdev_height_protoのみ。メインマップに高さを有効化していない。

下記のlevel/領域は**提案・要判断**。座標は実JSONのspawn/prop/transitionから採った調査地点で、walk rectの確定値ではない。propの画像anchorを移動面の中心/足元に取り違えない。全てworld pxで、既存unitScale2.5を再度掛けない。DEVのlevelHeight56は参照値、全本編の最終段差量を確定するものではない。

- 複数mapの0/1はローカル番号。城壁mapや宿2Fだから必ずlevel1にする必要はない。既存の別map構成を維持し、巨大な単一mapへの統合を提案しない。
- connectorは既存ルートの坂/階段/橋端へ合わせ、片端がwalk22×10足元を完全に支え、上階床に連続することをlint/歩行で確認。段差の追加で通行時間、回り道、物語gateを変えない。
- NPC/monster/宝箱/event/transition/spawnのlevelを一緒に計画する。上階だけ作って接触を2Dのままにしない。橋上下の同XY・敵の独立レベルは接触レビュー書を参照。
- 樹冠/屋根/門の見た目の重なりだけならheight無しの遮蔽を優先。橋下や洞窟など新しい通行経路を推定で追加しない。
- 素材は必要種類の候補のみ。採用済み素材を置き換えず、追加用透過素材の仕様書を別作成する。大規模再レイアウトは承認外。

## 全マップ計画（30件）

| マップID / 表示名 | 調査地点（world px） | 面/接続の候補 | 接触・進行で保護するもの | 追加素材候補 |
|---|---|---|---|---|
| cliff_moher_01_spiral_ascent / 風見の断崖 | 入口from_lind(150,3658)、path_spiral、summit(2280,1262)、ベンチp_c1_020(2400,982) | 候補: 入口0→螺旋中腹1→頂上2。現ルートに沿う階段/坂のみで接続。迂回や近道を追加しない | 夕日の丘/宝箱/頂上会話を各面へ明示。夕日→襲撃のstory条件維持 | 崖正面/上端/曲角、坂/階段、頂上床 |
| fort_dunvall_01_courtyard / ドゥンヴァル砦　中庭 | 中庭from_tavern(710,990)、城壁出口rect(360,1000,80,220)、主塔出口(1500,960,200,60) | 主床0を維持。城壁入口の踊り場1は局所候補。城壁は既に別mapなのでこのmap内へ再レイアウトしない | captain/quartermaster/bed、出口源levelと先spawn levelを明示。支給/解放進行を維持 | 石壁側面/上端、踊り場/階段 |
| fort_dunvall_02_ramparts / ドゥンヴァル砦　城壁 | from_courtyard(300,800)、from_keep(1400,300)、tr_f2_to_keep | この別mapの通路をlocal0とする候補。城壁下を同mapへ追加しない。内部段差が必要なら局所1 | lookoutの会話面、隣接mapのspawnレベルを照合。高さが違うmap間でもlocal番号を強制一致させない | 欄干/胸壁側面、石床/階段 |
| fort_dunvall_03_keep / ドゥンヴァル砦　主塔 | from_courtyard(1200,1400)、from_wall(1820,860)、tr_f3_to_wall | 屋内基準床0。階段/上層は既存通路の範囲内の候補のみ。壁mapと全体levelを共有しない | commander/armory、扉イベント/帰路の接触を固定 | 屋内階段/手すり/石段 |
| fort_in_tavern / ドゥンヴァル砦　酒場「錆びた角笛」 | from_courtyard(700,830)、既存NPC配置 | 全床0を維持。当面高さ不要 | Liam加入/各NPC/出口を既存のまま検証 | 現素材維持、必要なら装飾のみ |
| moss_forest_01_sunlit_path / 陽だまりの森道 | from_lind(1429,5673)、from_area2(7559,490)、stream_a1/pond_a1、path_main | 主道/到着点0を維持。分岐の岩丘/低地を局所1候補として調査。存在しない橋/上下経路を新設しない | 到着会話/帰れない出口/採取/宝箱/18monstersを所属面へ明示 | 低い崖/縁、岩丘床、川岸 |
| moss_forest_02_mossy_ravine / 苔むした渓谷 | bridge prop(3775,4062)、root arch(6206,4305)、overlook(5070,5685)、fall_a2 | 候補: 橋床1/橋下0、滝の足場1、崖帯。主道0と橋上への両端connectorを検討。橋下通行は現歩行域内に限る | 24monsters/宝箱/休憩と両出口。橋上・下の同XY接触を重点検証。根アーチは同level遮蔽だけでも実現可 | 橋床/側面/欄干/橋脚、滝/岩側面、根アーチ |
| moss_forest_03_ancient_grove / 古樹の聖域 | gate(3900,3390)、great tree(4440,2740)、sentinel(6255,5175)、dev_sanctuary(4300,3140) | 結界/祭壇の主床0を維持。巨木根/祭壇縁の局所1は候補。樹冠は遮蔽だけならlevel不要 | 討伐3/結界/ルー/祭壇onceを最優先。9monsters+story symbols3。無効tr_to_deepは有効化しない | 巨木/根/樹冠、石段、結界前面 |
| rilde_village_01_peace / リルド村 | 橋prop(1640,736)、桟橋(1598,1518)、village-west-east/bridge-east | 広場/家前0。川橋1/川岸0候補。桟橋は単に水際の床なら0で足り、下層を新設しない | walkers home会話、木剣少年/風船/猫、全建物の入口。動くNPC停止の異階層誤判定を検証 | 橋側面/欄干/水際/橋脚 |
| rilde_village_01_ruin / リルド村（襲撃後） | 平和版と同じ橋(1640,736)/主要街路。既存破損区画 | 平和版のwalk/connector配置を継承し、破壊物で既存進行を表す。別のルートを作らない | 襲撃イベント/救出/通行禁止とNPCの状態。平和版の高さを適用して逃走路を塞がない | 平和版と共通橋、破損側面/炎遮蔽 |
| rilde_in_aidan / エイダンの家 | default(250,330)、from_village(480,532) | 屋内全床0、高さ不要 | ベッド/冒頭/家出口の互換 | 現素材維持 |
| rilde_in_barn / 納屋 | default(500,512) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| rilde_in_elder / 長老の家 ― 風見の丘 | default(480,532) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| rilde_in_house_01 / 村人の家 | default(430,452) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| rilde_in_house_02 / 村人の家 | default/from_village(430,452)、椅子cb_09(430.4,436,19.2,14) | 全床0。高さで既存spawn衝突を回避しない | まず2D foot overlapを担当生成元で修正する案を別途調査 | 現素材維持 |
| rilde_in_house_03 / 村人の家 | default(430,452) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| rilde_in_house_04 / 村人の家 | default(690,452) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| rilde_in_inn_1f / 宿屋「風見鶏」 1階 | from_village(600,612)、既存階段/遷移 | 現1F/2Fは別map、全床local0。階段は必要なら装飾/局所1 | innkeeper/traveler/階段の会話と遷移、2Fspawnを照合 | 階段/手すりは任意 |
| rilde_in_inn_2f / 宿屋「風見鶏」 2階 | from_stairs(220,330) | 2Fであっても別mapのlocal0。1Fからのlevel番号を引継がない | stairs帰路の対称性/休息 | 現素材維持 |
| rilde_in_shop / 道具屋「若葉の袋」 | default(480,532) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| rilde_in_storage / 倉庫 | default(380,412) / 既存室内家具 | 屋内全床local0を維持。高さ不要 | 既存家の会話/家具/出入口、足元spawn整合 | 現素材維持 |
| dev_height_proto / DEV　高さプロトタイプ | bridge walk[1500,480,120,640]、plateau[1750,120,500,300]、既存connector4 | 現在height有り唯一のDEV検証map。0/1・levelHeight56を維持。本編へ転用しない | ここへ接触fixture上下同XY/敵独立level/once/遅延テストを追加する候補 | DEV仮描画を維持、正式素材不要 |
| dev_monster_arena / DEV　モンスター配置アリーナ | center(2400,1600) | 現height無し/全床0。別height fixtureは新規DEV提案で | 既存monsters配置/同時負荷を維持。Android実測の代替にしない | DEV専用、現素材維持 |
| road_dunvall_capital_01 / 街道　砦と王都のあいだ | overlookベンチ(3960,860)、from_fort(200,1900)、from_capital(5400,1800) | 道0、見晴らし台の局所1候補。既存展望カメラを維持 | boar6/NPC/王都加入gate/出口、展望イベントonce | 坂/低い崖/展望柵 |
| royal_capital_00_gate / 王都カエルディン　南大城門・旅人街 | 既存門/旅人街、from_guild(900,1090)、from_inn(3500,1090) | 広場0。門の立体表現はまず装飾、歩行段差は局所候補 | 門衛/王都加入/宝箱/宿とguild遷移 | 石門側面/段/手すり |
| royal_capital_01_market / 王都　商業区 | from_gate(2400,2850)、from_plaza(2400,360)、tr_r1_to_craft | 市場床0を維持、歩行段差は不要。屋根遮蔽はheight無しでも検討可能 | 店舗/NPC/宝箱。職人受け側JSON未確定の出口はTBD維持 | 現素材維持、屋根/段は要判断 |
| royal_capital_02_castle_plaza / 王都　城前広場 | from_market(2000,3300)、tr_r2_to_east/tr_r2_castle_gate | 広場0。王城門前の階段/踊り場1は候補、接続先map未確定なのでwalk rectを確定しない | 城門/東方面の未実装先を先に整備。宝箱/告知/NPC | 石段/門前床/手すり |
| royal_capital_03_residential / 王都　住宅街 | from_market(360,1200)、from_plaza(3300,1500) | 住宅街0。道幅を保ち屋根遮蔽だけの検討を優先 | 住民/猫/長老quest/宝箱 | 現素材維持 |
| royal_in_guild / 冒険者ギルド兼大酒場 | from_gate(900,920)、受付/掲示板/階段zone | 屋内local0、未接続の上階をheightで代用しない | 受付/掲示板/パトロン/出口の接触 | 現素材維持 |
| royal_in_inn / 宿屋「旅人の灯」 | from_gate(700,830)、bed/guest | 屋内local0、歩行段差不要 | 宿/bed/guest/出口 | 現素材維持 |

## 段階導入案（全て本編OFFのまま設計/DEV検証から）

1. **DEV**: 既存高さmapで上下NPC/敵/宝箱/trigger/transitionの接触を検証。field-monstersのplayer-level依存を取り除く実装をClaudeが担当。height無し回帰を先に成立させる。
2. **崖/夕日の丘**: path_spiralの現経路を複数面として表すDEV複製案。入口/中腹/頂上と階段端を実地で測り、22×10foot・既存宝箱/ベンチ・夕日/襲撃遷移の整合を確認。直線ショートカットを追加しない。
3. **砦**: 別map構成を維持し、中庭入口の局所段差→壁面/主塔の描画を検討。story支給、Liam、加入条件、menu解放を保護。複数map間のspawn levelを個別に明示する。
4. **A1→A2→A3**: A1は局所段差、A2は橋上下/滝足場、A3は結界/巨木周辺を設計。A3の無効出口/祭壇once/結界条件を変えない。A2橋の既存歩行域と画像anchorを確認してからwalk/overpass範囲を決める。
5. **村→他**: 平和/襲撃版で基礎座標とconnector対応を揃える。室内は大半をheight無しで保持。街道展望/王都門前だけ局所候補、TBD出口の受け側mapが無い間は接続を進めない。

## 実装前の受入条件

| 条件 | 現在 |
|---|---|
| 接触のlevel対応 / 敵自身のlevel | 設計レビューまで、未実装 |
| 局所walk/connector/overpassの確定 | 未確定。上記地点をClaudeが生成元へ反映する前に測定/確認 |
| 旧save/newoptional levelの互換 | 現本編には不要。導入時にv30加算のみ・曖昧上下XYのfallbackをレビュー |
| 28本編height無しの不活性 | ソース/JSON読取で確認。動的spy回帰は未実施 |
| Androidの読込/fps/操作性 | 実機接続なし、未測定。メインmap有効化不可 |
| 再生成素材/正式追加素材の受領 | この作業では未受領/未生成/未採用 |

## テスト/要判断/次の提案

実行: Python標準jsonで全30ファイルをparse、id/height/spawn/props/transitionsを集計。表示名/サイズ/座標は実JSONから採取。30IDの重複なし・DEVだけheight有りを確認。本編のゲーム/マップ/テストは未変更のため、ブラウザ回帰・UI画面撮影・Android計測は未実施。既存m13/m4の失敗を今回の実行結果として引用しない。

要判断: 崖の0/1/2構成、A2橋下通行の必要性、各mapの局所段差量、素材追加、移動中enemyの階層越え、旧saveの復帰方法。次はClaudeがDEV複製/生成元で確定領域を検討し、接触テストとAndroid計測を揃える。main更新/本編height有効化をCodexが行わない。main未変更でロールバック不要。
