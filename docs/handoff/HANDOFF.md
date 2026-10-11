# THE WINDBOUND OATH — 引き継ぎ書（2026-10-11 時点 / main `f83ab09`）

対象読者: 並行開発する Codex / 次のセッションの Claude / 作者。
正典: **`docs/story/WORLD_STORY_BIBLE_v1.1.txt`**（世界観・外見・導線の source of truth。衝突したらバイブル優先）。
本書は「いま何がどこまで出来ていて、どう作られていて、次に何が要るか」をまとめる。作業依頼は `docs/handoff/CODEX_BRIEFS.md`。

---
## 1. プロジェクト概要
- ブラウザJRPG（HTML/CSS/素のJS、ビルド工程なし）。GitHub Pages で配信、作者は Android 実機で確認して報告。
- リポジトリ: `celticmusic-nagoya/the-windbound-oath`。`main` が公開。作業は `work/<topic>` ブランチ → テスト → 報告 → ff-merge（危険でない変更は作者の事前許可あり）。
- 画面構成: フィールド = **Moss ランタイム**（`js/field/moss-forest-runtime.js`、マップ schema v2 JSON）。戦闘 = 旧DOMシーン（固定シーン、リアムはまだ戦闘に出ない）。主スクリプトは `index.html` のインライン（巨大）。
- 進行: `storyStage`（数値）+ FieldTalk のフラグ。0〜3 村/訓練/断崖、5〜8 襲撃、9〜14 モスの森、15 = プロローグ後の自由行動（砦から開始）。

## 2. 地理ルート（バイブル7）
リルド村 → モスの森 → ドゥンヴァル砦(DUNVAR FORTRESS) → 街道 → 王都カエルディン(CAERDYN)。
マップID は互換のため `fort_dunvall_* / road_dunvall_*` のまま（**表示名のみ DUNVAR**。IDを変えないこと）。

## 3. マップ接続図（現状）
```
[リルド村 peace/ruin] ─(stage15 + road_dunvall_open)→ [砦 中庭]
 └ 屋内11 (aidan/elder/inn_1f/2f/shop/house_01-04/barn/storage)   │ 東門            │ 西:城壁 北:主塔 酒場の扉
 (ruin は屋内なし)                                                  ↓
                                  [街道 road_dunvall_capital_01] 丘で王都一望(cut-in)
                                                                     ↓
              ┌──────────── [王都 00 南大城門・旅人街] ────────────┐
              │ 西:ギルド兼大酒場(royal_in_guild) 東:宿屋(royal_in_inn)│
              └──────────────── 北 ↓ ───────────────────────────────┘
        [03 住宅地区] ←西── [01 商業・市場] ──東→ TBD 職人地区(ブラムの工房)
              │東                 │北
              └──→ 西 [02 中央広場(城前)] ──東→ TBD 騎士団/大聖堂/魔法学術(王立魔法研究院)
                              │北 → TBD 王城
砦: 中庭 ⇄ 城壁(02) ⇄ 主塔(03) / 中庭 ⇄ 酒場「錆びた角笛」(fort_in_tavern: リアム加入)
```
`toMap:"TBD"` の出口は「道が続いていない」トーストになる未実装接続（市場東・広場東・王城門）。

### 3.1 マップ一覧（サイズ px）
| ID | サイズ | 備考 |
|---|---|---|
| rilde_village_01_peace / ruin | 2400×1750 | ruin: 煙→(長老が街道を示す)霧、風0.02、BGM bgm_rilde_ruin |
| rilde_in_* ×11 | 〜1200×800 | 平和時のみ入れる |
| moss_forest_01/02/03 | 9600×6000 等 | プロローグ森（既存） |
| cliff_moher_01_spiral_ascent | 4800×4800 | 風見の断崖 |
| fort_dunvall_01_courtyard | 3200×2400 | 山と滝の背景(town_fort_ridge)、青金旗、風0.3 |
| fort_dunvall_02_ramparts / 03_keep | 2800×1600 / 2400×1800 | 城壁(霧) / 主塔 |
| fort_in_tavern | 1400×1000 | リアム(加入)、酔っ払いのドワーフ(匿名, f4_dwarf)、主人、常連 |
| road_dunvall_capital_01 | 5600×2600 | 丘の頂で `road_overlook`（レターボックス+パン） |
| royal_capital_00_gate | 4400×3400 | 二重城門・検問所・旅人街。ギルド/宿屋の入口 |
| royal_in_guild / royal_in_inn | 1800×1100 / 1400×1000 | 掲示板 r1_board はギルドにある。宿屋のベッドで全回復 |
| royal_capital_01_market | 4800×3200 | 市場。南=旅人街、北=広場、西=住宅、東=職人(TBD) |
| royal_capital_02_castle_plaza | 4000×3600 | 噴水・建国記念碑・城。風0.12 |
| royal_capital_03_residential | 3600×3200 | 雨（失くし物クエスト完了で晴れ）|

## 4. バイブル整合の状況
- 済: 名称/旗(青金)/山と滝/リアム外見/匿名ドワーフ/白灰石造+青緑屋根+金装飾/軸(南大城門→旅人街→市場→広場)/ギルド兼大酒場+宿屋/地区TBD出口/風の強弱/ロケーションカード「王都カエルディン — 南大城門 CAERDYN」。
- **未着手（バイブル記載）**: 騎士団地区・大聖堂地区・魔法学術地区(王立魔法研究院/モルウェン)・職人地区(ブラムの工房 BRAM'S FORGE: 「酒場の若造じゃねぇか！」再会)・裏路地・地下(旧水路/地下墓所/第七封鎖区画)・王城内部/高台(強風の再演出)・周年祭(セレナ「踊り子」先行登場)・時間帯(朝昼夕夜)・ギルド2階(会議室)/地下(倉庫)・宿屋の時間帯選択(朝/昼/夕/夜まで休む)・宴イベント(リアム演奏+セレナ舞+ブラム歌)。
- 初訪問導線(バイブル56): 南大城門→旅人街→市場→広場→王国/騎士団へ報告→証拠不足→リアムが学者を提案→魔法学術地区→研究院→モルウェン→第七封鎖区画→地下ボス→魔王の紋章の矛盾→モルウェン加入→地上→周年祭→セレナ先行登場。**この導線は未実装（広場の北・東出口がTBD）**。

## 5. 仕組み（実装メモ）
### 5.1 マップ生成（手書きJSONではなくツールで生成）
- `tools/moss/build_town_maps.py`: 砦/街道/酒場/王都8+3マップ。`Map` クラス（`wall/solid/floor_rect/spawn/door/npc/chest/prop/deco/decal`, `m.paths`, `m.wind`, `m.card_area`）。到達性を自動検証（失敗で exit 1）。**ドア矩形は外周48pxブロッカーの内側の歩ける場所に置く**。
- `tools/moss/build_rilde_village.py`: 村と屋内。旧Lindレイアウト由来の道は同ファイル内で補正済み。実行すると manifest の整形が大きく変わるので、**`git checkout img/field/moss/manifest.json` で戻す**（ルール内容は同じ）。
- 素材: `make_town_art.py`（建物/門/記念碑/山と滝ほか37種, 1ドット=2px）、`make_npcs.py`（チビ56×84・6フレ歩行。`LOOKS` に追加→`npc_slot_<look>`）、`make_props.py`、`make_rilde_art.py`。manifest は `^town_<name>$` 等の正規表現ルールで最初に一致したものを使う。差し替え前提の仮絵が多い（`check_assets.py`: standin 17 / placeholder 14）。
- 検証: `python3 tools/moss/check_assets.py`（0 error / 13 warning が基準）。

### 5.2 会話・イベント（FieldTalk）
- `js/field/field-talk.js`: テーブル `{npc, entries:[{id, priority, mode:'once'|'cycle', when, lines}]}`。`when` = flag/stage/talked/all/not/quest。効果 `set / give / take / quest / join / shop / scene`。会話終了で `field-talk-end` イベント。
- データ: `talk-data*.js`（本体/quests/scenes/capital/rilde/**attack**）。台詞は仮が多く、作者シナリオで差し替える前提。
- 注意: **主インラインスクリプトは talk-data より先に実行される** → データ参照は関数内で遅延させる。`FieldTalk.flag` を `flagsNow()` 内で呼ばない（無限再帰）。`PartyManager` は `const`（`typeof` で判定）。
- ストーリーフック: `js/field/moss-forest-story.js`（`onEvent / onVillageExit / onEnter / flagsNow`）。マップのゾーンは `interact`（クリック）と `trigger`（踏む、`once`/`requires`/`hook`）。

### 5.3 ランタイム/ローダ
- `forest-loader.js`: ground/layer/entity は先読み、props は可視優先の遅延読込＋失敗リトライ（失敗した画像が永久に紫の四角になる問題の恒久対策）。`prepare()` が出現地点付近を待つ。
- 天候 `field-weather.js`（clear/mist/fog/rain/storm/smoke、`when` ルール）、時間帯 `field-timeofday.js`（day/dusk/night/ember）、BGM `field-bgm.js`（WebAudio 手続き生成: bgm_rilde_day/home/ruin のみ）。
- DEV メニュー: `js/prologue-dev.js` の `entries`（索引 01〜22 と `map:<id>` M1〜M8, M4a-c）。`index.html` の `devJump` が `map:` を処理。

### 5.4 ショップ・クエスト
- `js/data/shop-data.js`（dunvall_arms/royal_general/royal_arms, 王都限定装備と鋼の剣のクエスト解禁）、`js/shop.js`。クエスト: 王都の失くし物、商業区の納品依頼（掲示板=ギルド内）。

## 6. 仲間の状態
- リアム: 酒場で加入（`join` 効果、flag `liam_joined`）。外見はバイブル35に準拠（アッシュブロンド/ウルフヘア/赤バンダナ/ゴーグル）。**戦闘にはまだ出ない**（戦闘は固定シーン）。武器=ショートソード+弓、マンドリン系楽器。
- ブラム: 砦酒場で匿名の「酔っ払いのドワーフ」（look `dwarf_drunk`）。工房再会は未実装。
- モルウェン/セレナ: 未登場（先行登場の場所と流れはバイブル56-57）。
- ルー: モスの森で加入済み。

## 7. テスト（要 `python3 -m http.server 8765`）
`tests/moss/*.py`（m4_*, m6_*, m7_*, m8_town_maps, m9_*, m10_*, m11_*, m12_attack_ruin）、`tests/system/*.py`（capital_story_test, shop/equipment）。
- 注意: `grep FAIL` は "FAILS []" 行を拾う → 終了コードで判定。`pkill -f chrom` はシェルごと落ちる。http.server はコマンド間で落ちやすいので同じコマンド内で起動。
- 既知: `m6_quest.py` は **変更前から失敗**（今回の作業と無関係、原因未調査）。`m6_*` はページ読込後 ~2.6秒待ち＋`closeDialogue()` が必要（冒頭台詞と衝突）。
- 全回帰の目安: 本書時点で m6_quest 以外すべて合格。

## 8. 既知の課題 / 保留
1. 120Hz 端末でキャラ速度が速い（フレーム依存の移動量）。
2. 長老(`elder`)の本実装台詞、襲撃の戦闘・目的表示そのものの FieldTalk 化。
3. リアムを戦闘に出す（PartyManager の active と戦闘レイアウト）。
4. 風の石復活→風が戻る演出（マップの wind は固定値）。
5. BGM は手続き生成のみ（砦/王都/街道は `bgm_town` 流用）。
6. 見た目が仮絵の建物・家具・NPC（作者承認待ちの差し替え）。
7. セーブ: FieldTalk の flags/seen/cycle と Inventory/Quest は保存対象。マップ位置の保存仕様は要確認。

## 9. 作業ルール（Claude/Codex 共通）
- ブランチ `work/<topic>`、小さくコミット、`index.html` の `?v=` を更新（キャッシュ対策）。作者は Android 実機。
- 報告は日本語・簡潔に（変更点/未実装/テスト結果）。コミット末尾に Co-Authored-By / セッションURL。
- バイブルと矛盾する設定を作らない。迷ったら TBD として残し報告。
- **ファイル所有の目安**（衝突回避）は `CODEX_BRIEFS.md` の冒頭を参照。
