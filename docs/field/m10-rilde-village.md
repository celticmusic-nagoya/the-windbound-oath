# M10 リルデ村 本編統合 + 屋内マップ

## 概要
- 村は `data/maps/rilde_village_01_peace.json`(襲撃前)/ `rilde_village_01_ruin.json`(襲撃後)と、屋内12マップ `rilde_in_*.json`。Moss ランタイム(schema v2)上で動く。
- 論理ID `rilde_village` は `RildeVillage.resolve()` が状態で振り分ける。ドア/出口は常に `toMap:'rilde_village'`。peace/ruin のスポーン名は同一。
- 状態: `storyStage >= 5` または flag `rilde_ruined` → ruin。それ以外 peace。DEV/テスト用に `RildeVillage.force('peace'|'ruin'|null)`。
- `?legacyVillage=1` で従来の DOM 村に戻せる(`RildeVillage.enabled()===false`)。

## 本編フロー
新規ゲーム → `RildeVillage.startOpening()`(エイダンの家で起床)→ 村 → フィオナ(stage 0→1)→ 訓練用木人(訓練戦闘, →3)→ 南の小径 → 風見の断崖 → 戻り `tr_c1_to_lind`。
襲撃(stage 5–8)は従来のスクリプトシーン。終了後 `afterPrologue()` で stage 15、砦から自由行動。ruin 村は焼け跡、街道(東)は flag `road_dunvall_open`(長老と会話)で開通。
出口の特例は `hooks.onVillageExit` → `RildeVillage.exit()`。

## ランタイム拡張
- hooks: `resolveMap` / `fionaVisible` / `onEnter`。
- `FieldBgm`(新): マップ `audio.bgm.id` を `play()`。WebAudio の手続き生成(`bgm_rilde_day/home/ruin`)。初回ジェスチャで開始、設定タブの「音楽」でミュート(localStorage `windbound.bgm`)。
- `FieldTimeOfDay` に `ember`(襲撃後の煤けた夕方)、`FieldWeather` に `smoke`(暗い霧+灰/火の粉)、`FieldVista` に `fire_spot` / `smoke_column` / `hearth`(`"on":true` で常時表示)。
- カメラ: ワールドが画面より小さい屋内は中央寄せ。

## 再生成
```
node tools/moss/export_lind_layout.js > ...   # (内部で使用)
python3 tools/moss/prepare_rilde_lind.py      # Lind画像→村用素材 + 廃墟バリアント
python3 tools/moss/make_rilde_art.py          # 家具/瓦礫/デカール 54種 (1dot=2px)
python3 tools/moss/build_rilde_village.py     # マップJSON14本 + manifest ルール(gen:'rilde')
```

## 既知の制約
- 襲撃シーン本体(stage 5–8)は従来の DOM スクリプト。
- BGM は手続き生成。録音音源に差し替える場合は `FieldBgm` の PROFILES を置換。
- ruin 村人の台詞は仮(`talk-data-rilde.js`)。
- 家具/廃墟は手続き生成の仮絵。差し替えは manifest ルール経由。

## テスト
`python3 tests/moss/m10_rilde.py`(要 `python3 -m http.server 8765`)。
