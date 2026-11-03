# DIRECTIVE-ART-01 — 序盤マップ完成化・素材監査（ART-01A / 01B / 01C）

- 基準main: `ad4a3d679987a540fc0248c9b5bfd0e8c43a15a3`（PR100, DIRECTIVE-26A後）／作業ブランチ: `art/art-01-early-maps`
- Codex 26B（`codex/26b-early-rewards`）とは別ブランチ。ゲームコード・map JSON・manifest・台帳・既存PNGは**一切変更していない**。
- 追加物は本書、候補PNG（`docs/art/candidates/art-01/`）、候補生成・プレビュー用の2スクリプト（`tools/art/`）のみ。候補は**未採用**で、ゲームから参照されない。
- 保護: 25A固定の正式259PNGは作業前後とも 259/259 SHA一致（`docs/qa/evidence/directive-25a/static-inventory.json`）。

調査方法: 現行mainをローカルHTTPで起動し、`?title=0`＋既存DEVジャンプで PC 1280×720／Android縦 412×915／横 915×412 を撮影。map JSON・`img/field/moss/manifest.json`・`tools/moss/report_placeholder_art.py`（再実行）・`js/field/*`・`index.html`/`css/style.css` を照合。Android実機確認ではない。

## 1. 分類サマリ

| 対象 | 既存素材で完成できる | 新規画像が必要 | Codex接続が必要 |
|---|---|---|---|
| A 室内（14map） | 家具54PNG・当たり判定・調査点・遷移はそのまま | 床・壁・巾木・外壁天端・出入口・玄関マット＝**10候補を制作済み** | 床壁の画像タイル描画（K1）、自宅への配置（K2） |
| B 襲撃後の村（stage5〜8） | 正式ruin map一式（廃墟建物29PNG・炎/煙・瓦礫）、村人/兵士/フィオナ/エイダンのfield絵 | フィールド用ゴブリン（通常・異形）**2件**（仕様のみ、未制作） | 旧DOM→ruin mapへの移設（K3）、帰路/河川シーンの文字カプセル置換（K4）、ゴブリンfield art接続（K7） |
| C ルーとの出会い | A3正式map・封印3状態・古代遺物・祭壇正式絵＋契約FX・CG01〜05・ルーfield 6コマ | `tree_dead_taint_M_01`、祭壇の誓いの剣オーバーレイ **2件**（仕様のみ、未制作） | ルー登場シーン（K5）、祭壇の文字カプセル（K6）、枯死樹のmanifest登録（K8） |

## 2. 対象A｜リルド村の室内

現行室内map: `rilde_in_aidan / barn / elder / house_01〜04 / inn_1f / inn_2f / shop / storage`（11）＋`fort_in_tavern / royal_in_guild / royal_in_inn`（3）。全14mapで家具propは全件manifestで実PNGに解決（placeholder 0）。

**簡易表示（全14map共通）**

| 部位 | 現状 | 根拠 |
|---|---|---|
| 床・奥壁 | 単色fill＋`pattern:'planks'`の手続き線（画像なし） | `terrain.fills`、`js/field/forest-layer.js` paint()「no image assets」 |
| 巾木 | 単色帯 12px（`#3a2c20`） | `fill_3` |
| 左右・手前の外壁 | 背景色`#17110d`のみ。壁の天端が描かれない | `fills[0]`＋edgeBlockers 48px |
| 出入口 | 平坦な淡色の`furn_doormat`のみ。扉の開口がない | `tr_exit`（自宅: x410 y598 w140 h62） |

**エイダンの自宅（初回対象）の現状**: world 960×720、spawn `default/from_bed`=(250,330)↓、`from_village`=(480,532)↑、遷移 `tr_exit`→`rilde_village/from_aidan`、調査7点。**タンス `ev_cupboard_06`(320,172 r46)・壺 `ev_jar_19`(870,569.2 r40) は位置不変**（候補は床・壁・外周のみで、家具・eventZones・collisionに触れない）。Android縦は横スクロールで部屋の右半分が画面外、横は奥壁上部が切れるが操作上の問題は見当たらない（実機未確認）。

### ART-01B 制作済み候補（10件・未採用）

画風契約は既存家具から実測: 4×4px＝1ドット（world 2px）、@2x制作・manifest w/hで半分表示、輪郭`#2b211c`、木`#7c5834/#9a7042/#b88c56`、金`#d6ac46`。床・壁の色調は現行fill色（`#a98b5c`/`#76654f`）を維持。寸法は現行map形状（壁帯150・巾木12・外壁48・開口140）と手続き板幅28から決定し、根拠のない寸法は使っていない。

| ファイル | 用途 | px（@2x） | world | 区分 | 透過 | 配置・反復 | レイヤー | 当たり判定 |
|---|---|---|---|---|---|---|---|---|
| `art01_int_floor_planks_01.png` | 床 | 224×224 | 112×112 | タイル | 不透過 | fill_2矩形に縦横反復、world原点基準 | GROUND | 変更なし |
| `art01_int_wall_planks_01.png` | 奥壁（rilde 150高） | 224×300 | 112×150 | タイル | 不透過 | fill_1矩形にX反復、上端揃え | GROUND | 既存`cb_00` |
| `art01_int_baseboard_01.png` | 巾木 | 224×24 | 112×12 | タイル | 不透過 | fill_3矩形にX反復 | GROUND | なし |
| `art01_int_wallcap_left_01.png` | 左外壁天端 | 96×224 | 48×112 | タイル | α | x0〜48をY反復 | GROUND | 既存edgeBlocker |
| `art01_int_wallcap_right_01.png` | 右外壁天端（左の鏡像） | 96×224 | 48×112 | タイル | α | 右端48pxをY反復 | GROUND | 既存edgeBlocker |
| `art01_int_wallcap_bottom_01.png` | 手前壁天端 | 224×96 | 112×48 | タイル | α | y672〜720をX反復 | GROUND | 既存edgeBlocker |
| `art01_int_wallcap_corner_sw_01.png` / `_se_01` | 手前左右の角 | 96×96 | 48×48 | タイル | 不透過 | (0,672)／(912,672) | GROUND | 既存edgeBlocker |
| `art01_int_door_threshold_01.png` | 手前壁の扉開口・石の敷居・外光 | 280×96 | 140×48 | オブジェクト | 不透過 | 左上(410,672)＝`tr_exit`と同じx幅 | GROUND（壁天端の上） | なし（遷移rect不変） |
| `art01_furn_doormat_woven_01.png` | `furn_doormat`の代替案（同一footprint） | 168×72 | 84×36 | オブジェクト | α | 既存`mat`(480,644) 下中央anchor・z1 | LOWER_PROP decal | なし |

- プレビュー: `preview_aidan_house_before.png`（現行fillの近似）／`preview_aidan_house_after.png`（候補適用の合成。実map・実manifest・実家具PNGから合成した**オフライン画像**でゲーム画面ではない）。
- 再現: `python3 tools/art/make_art01_interior_candidates.py && python3 tools/art/preview_art01_house.py`（決定的出力。SHAは`candidates.json`）。
- 自己検査: 全ファイルのαは0/255のみ（半透明残留なし）、床・壁タイルの3×3反復で継ぎ目なし。既存`doormat.png`は上書きせず別名。
- 他13室内への展開: 壁帯200のfort/royal用は高さ違いの壁タイルが別途必要（未制作）。床・巾木・外壁天端はそのまま流用可能。

## 3. 対象B｜襲撃後のリルド村（25A MAP-03）

**現状**: stage5〜8は`index.html`の旧DOM world（`#world`）を使用。背景は道・川・建物の単色ブロック、人物/敵は文字入りカプセル（「母」「子」「老人」「ゴブリン」「異形」「騎士」「F」）、炎は「♨」、瓦礫/煙はCSS図形。プレイヤーも濃色カプセル。一方、正式な`rilde_village_01_ruin`（2400×1750、廃墟建物29PNG、`furn/rubble_*・scorch・burnt_beam・post_burnt・cart_wreck・banner_torn`、炎/煙weather）はstage15以降で実装済み。→**既存の廃墟村を再利用でき、新しい村全体画像は不要**。

続く演出シーン: `#returnScene`（帰路、ゴブリン＝文字カプセル）、`#escapeScene`（河川脱出、「A」「F」「異形」カプセル＋CSSの川）も簡易表示。

### 正式素材と現在のイベント座標の対応表（暫定提案）

旧DOM座標は`index.html` l.41-112。ruin座標は現行ruin mapの名所に意味対応させ、`MossForest.blocked()`で歩行可能を実測（stage15状態のruin mapで確認）。全体図: `docs/art/candidates/art-01/ruin_event_mapping_draft_v0.png`（青＝味方/NPC、赤＝敵）。

| 旧要素（id） | 旧座標 | 場面 | ruin提案座標 | 使う既存素材 | 備考 |
|---|---|---|---|---|---|
| 開始位置 | DEV attack | stage5開始 | (830,1552) `from_cliff`↑ | Aidan field | 南門から帰還、既存spawn名を流用 |
| `attackOld` 老人（負傷） | 930,1110 | 南の農地 | (905,1440) | `rv_npc_elder_man` | 負傷姿勢は素材なし→idleで代替 |
| `attackMother` 母 | 1090,940 | 救助地点 | (1106,1181) | `rv_npc_young_woman` または `farmer_female` | 母娘の配役はユーザー確認推奨 |
| `attackChild` 子 | 1160,900 | 救助地点 | (1170,1165) | `rv_npc_girl`／`rv_npc_boy` | 同上 |
| `attackGob1` ゴブリン | 1060,820 | 救助戦 | (1060,1110) | **新規: field goblin 通常** | 現行は`goblin.art:null` |
| `attackFiona` フィオナ | 1040,690 | 再会 | (1103,877) | Fiona field frames | 広場東。炎FXと重ならない位置へ補正済み |
| `attackGob2` 異形 | 1130,665 | 再会戦 | (1210,890) | **新規: field goblin 異形** | 同上 |
| `royalKnight` 騎士 | 980,315 | 北側合流 | (830,330) | `npc_slot_captain`／`npc_slot_soldier` | 王国騎士の配役は確認推奨 |
| `northGob1/2` 異形 | 1080,350／1150,395 | 北側戦闘 | (930,360)／(999,372) | **新規: field goblin 異形** | |
| `northEscape` 北の退路 | 900-1230,180 | 逃走開始 | eventZone中心 (830,200) | なし（zoneのみ） | `tr_v_to_moss`(770,48)とは**別**のstage限定zoneとし、既存遷移は変更しない |
| `firefx/attackFlame/attackSmoke/debris` | 各所 | 炎・瓦礫 | ruin mapの既存炎/煙/瓦礫 | 既存 | 追加画像不要 |

注意（Codex側）: ruin mapの既存NPC（`p_rr_*`、兵士2名含む）はstage15以降の配置。stage5〜8では非表示にし、上表のactorをstage限定で出す必要がある。シナリオ・flag・戦闘ID（`attackGob1/2`, `northGob1/2`）・報酬は変更しない。

### 新規制作候補（仕様のみ・ChatGPT制作想定）

| ID | ファイル名案 | 用途 | 寸法根拠 | 透過 | 備考 |
|---|---|---|---|---|---|
| B-N1 | `goblin_field_idle.png`＋`goblin_field_walk_01〜04.png`＋`goblin_field_alert.png` | 通常ゴブリンのフィールドシンボル（救助戦・森の通常ゴブリン共用） | 既存field人物 `npc_slot_*` と同じ **112×168 px（world 56×84）**、下中央anchor・足元接地 | 必要（α0/255） | `field-monsters.js` goblinのpatrol/alert構造に合わせ walk4＋alert1（boarと同形式）。合成シートからの切出し禁止、1ファイル1コマ |
| B-N2 | `goblin_tainted_field_*`（同構成） | 異形（異常化ゴブリン）フィールド | 同上 | 必要 | 黒紫ルーン。戦闘版の採用デザインに準拠 |

## 4. 対象C｜ルーとの出会い（モスの森A3〜誓いの剣契約）

**既存の完成素材（不足扱いしない）**: A3 `moss_forest_03_ancient_grove` の地面・樹木・遺跡（`anc_*` delivered 15件、`tree_ancient_*`）、封印 `a3_seal_closed/corrupted/opening`、祭壇正式絵`moss_ancient_altar_idle_v1`（1536×1024）＋契約FX、CG01〜05（保護259に含む）、ルーfield idle 6コマ、Fiona/Aidan field。`standin/tree|rock`19件はLind正式絵由来のstand-inで、画面上はpixel絵として成立しているため今回は改善対象外。

**簡易表示が残る箇所**

| # | 場所 | 現状 | 判定 |
|---|---|---|---|
| C1 | A3聖域 `tree_dead_taint_M_01` ×3（4220,2710／4700,2690／4630,2820） | manifestで`file:None`→**緑の矩形プレースホルダー**（`div.forest-ent`, 70×104）。barrierAfter視点の画面端で実際に表示 | 新規画像が必要 |
| C2 | `#louIntroScene`（台詞0〜2・6行目） | CSSの月・楕円リング・「ルー」文字カプセル。3〜5行目はCG01 | 新規画像不要。A3 field＋封印opening絵＋ルーfield frameで再構成（Codex） |
| C3 | `#altarScene` | 正式祭壇絵の上に「A」「F」「ルー」「異形」×4の文字カプセル | 既存field絵で置換（Codex）。異形はB-N2を共用 |
| C4 | `#altarScene` `#oathSword` | 文字「†」(66px)を回転表示 | 新規画像が必要 |
| 観察 | barrierAfter DEV spawn(3910,3340) | プレイヤーが`anc_arch_broken_01`(3900,3390)の前景に隠れる | DEV用spawn。前景フェード対象か要確認（BUG判定しない） |

CG→フィールド復帰: `louIntro`終了で`forestShow()`／stage11、祭壇終了後はRaider戦。EventCGの行範囲・画像は保護対象のため変更提案なし。Android縦横: CGはportrait/landscape別画像が既にあり、C2/C3のカプセルは縦で `bottom` 補正（`css/style.css` l.3587）があるだけ。

### 新規制作候補（仕様のみ）

| ID | ファイル名案 | 用途 | 寸法根拠 | 透過 | 備考 |
|---|---|---|---|---|---|
| C-N1 | `img/field/moss/art/tree_dead_taint_M_01.png` | A3聖域の穢れた枯死樹 | manifestの`^tree_.*_M_` = **world 120×110**（@2x 240×220）、下中央anchor | 必要 | 既存`veg_thorn_L_*`の黒紫・桃色ルーン光と同系の画風。`^tree_(log\|ancient\|dead)`ルールより前に個別登録が必要（K8） |
| C-N2 | `assets/images/effects/moss_ancient_altar_oath_sword_v1.png` | 祭壇に現れる誓いの剣（「†」の置換） | 契約FXと同じく**祭壇canvas 1536×1024**に位置合わせ済みのオーバーレイ（AltarArtの同一box方式） | 必要 | 剣の意匠はCG05の誓いの剣に一致させる。CG05自体は改変しない |

## 5. ART-01C｜Codex向け接続引継ぎ

| K | 内容 | 変更対象（Codex） | 依存 | QA条件 |
|---|---|---|---|---|
| K1 | fillに画像タイルを追加（例 `{"texture":"int_floor_planks_01"}`。manifest `ground`同様に@2x→0.5倍pattern、world原点基準で反復しchunk境界で継ぎ目なし。未指定時は現行手続き描画） | `js/field/forest-layer.js`, manifest | 候補のユーザー採用 | 14室内で未指定mapの画素不変、chunk境界の継ぎ目なし、PC/縦/横 |
| K2 | 自宅へ候補を配置（床/壁/巾木=fill texture、外壁天端・角・敷居=GROUND層、マット差し替えは任意） | `data/maps/rilde_in_aidan.json` | K1・採用 | collision/eventZones/transitions/spawnsのJSON差分ゼロ、タンス・壺の調査可、`tr_exit`遷移可 |
| K3 | stage5〜8を旧DOMから`rilde_village_01_ruin`へ移設（§3の対応表、stage限定actor/zone、stage15 NPCの非表示） | `rilde-village.js`, map/talk data | B-N1/N2（未納品の間は既存symbol placeholderで可） | flag・戦闘ID・台詞・報酬・SAVE形式不変、旧legacy経路をrollback用に保持 |
| K4 | `#returnScene`/`#escapeScene`の文字カプセルを既存field絵へ | `index.html`, CSS | なし（異形はB-N2） | 台詞進行・タップ・skip・回転 |
| K5 | `#louIntroScene`のCSS月/リング/カプセルを封印opening絵＋ルーfield frameへ | 同上 | なし | CG01の行範囲・fade不変 |
| K6 | `#altarScene`の4種カプセルを既存field絵へ、「†」をC-N2へ | 同上, `js/altar-art.js` | C-N2 | AltarArt契約FX・CG02〜05のタイミング不変 |
| K7 | `field-monsters.js` goblinの`art`をB-N1/N2へ接続 | `js/field/field-monsters.js` | B-N1/N2採用 | 接触判定・detect等の数値不変 |
| K8 | `tree_dead_taint_M_01`をmanifestへ個別登録 | manifest | C-N1採用 | A3の他assetの解決結果不変 |

## 6. 禁止事項の遵守

既存正式PNGの上書き・シナリオ/flag/当たり判定/遷移/報酬/CGの変更・未承認素材の正式採用・Codexブランチへの変更・mainマージ・台帳更新は、いずれも実施していない。候補は`docs/art/candidates/`にのみ置き、`img/`・manifest・`ASSET_REGISTRY`へは入れていない。
