# M10 リルデ村 本編統合 + 屋内マップ

## 概要
- 村は `data/maps/rilde_village_01_peace.json`(襲撃前)/ `rilde_village_01_ruin.json`(襲撃後)と、屋内11マップ(訓練場関連は屋外のみ。見張り小屋は飾りで入れない) `rilde_in_*.json`。Moss ランタイム(schema v2)上で動く。
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
- 襲撃シーン本体(stage 5–8)の進行(戦闘・目的・演出)は従来の DOM スクリプト。台詞だけは FieldTalk 化済み(下記)。
- BGM は手続き生成。録音音源に差し替える場合は `FieldBgm` の PROFILES を置換。
- ruin 村人の台詞は仮(`talk-data-rilde.js`)。
- 家具/廃墟は手続き生成の仮絵。差し替えは manifest ルール経由。

## テスト
`python3 tests/moss/m10_rilde.py`(要 `python3 -m http.server 8765`)。

## 襲撃(stage 5–8)の FieldTalk 化と廃墟村の統合 (M12)
- 台詞: `js/field/talk-data-attack.js`(`TalkDataAttack`)。`atk_enter / atk_old / atk_mother_before|after / atk_child / atk_gob2_wait / atk_rescued / atk_fiona / atk_knight_first|again / scene_escape`。index.html は `atkTalk(id)` で呼ぶだけ。進行(`attackStep` / `northPhase`)がどの id を呼ぶかを決める。
- フラグ: `atk_started / atk_rescued / atk_fiona_found / atk_knight_met / atk_escaped`（`enterBurningVillage` で全て下ろす）。セーブは FieldTalk の flags に乗る。
- 脱出シーンの文言も `TalkDataAttack.escapeLines`（`escapeLinesNow()`）。※ 主スクリプトは talk-data より先に実行されるため、関数内で遅延参照すること。
- 廃墟村(`rilde_village_01_ruin`): BGM `bgm_rilde_ruin` / 時間帯 `ember` / 天候 `smoke` → 長老が街道を示す(`road_dunvall_open`)と `mist` へ（8秒かけて）/ 風 0.02（風が止まった。水は止まらない）。
- 街道: 出口 `tr_v_to_fort`・旧 `#roadExit`・東の標識は `rr_road_early` / `rr_road_ask` / `rr_sign_east`（FieldTalk）。長老 `rr_elder_road` の終了で目的が「東の街道から、ドゥンヴァル砦へ向かおう」に進む。
- 風を戻す(風の石が復活する)演出は未実装（`wind` はマップ固定値）。
- テスト: `python3 tests/moss/m12_attack_ruin.py`

## 道の整合 (M12 追記)
旧 Lind の道データは宿屋の小道が道に届かず浮いた「楕円」になる等の問題があったため、`build_rilde_village.py` で補正: 宿屋の小道は玄関〜大通りまで直線、エイダンの家の小道は玄関階段から、大通りの西端・北端はマップ端まで、東の大通りは川岸で止めて橋に引き継ぐ。
