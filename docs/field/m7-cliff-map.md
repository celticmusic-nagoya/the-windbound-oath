# 風見の断崖 (cliff_moher_01_spiral_ascent) — map, time of day, scene runner

仮名: マップID `cliff_moher_01_spiral_ascent` / 表示名「風見の断崖」(Windward Cliffs)。名称は後から JSON の `displayName` と `locationCard` だけで変更できる。

## 構成
- 世界 4800×4800。西端(リルド村南門側)から入り、**ゆるやかな螺旋(約265°、反時計回り)**を南→東→北へ登り、岩壁のランプを抜けて頂上の草地へ。頂上の北縁(リップ)の先が海。
- 高低差は「層」ではなく**1枚のマスク**で表現する: `walkable = 坂道の回廊 ∪ 頂上草地`。それ以外は全部 blocked で、見た目は
  `face`(崖の岩肌) / `slope`(丘の斜面) / `foam→shallow→deep`(海) に自動分類。衝突と絵が食い違わない。
- 生成: `python3 tools/moss/build_cliff.py` → `data/maps/cliff_moher_01_spiral_ascent.json`(決定的)。検証: 全採取点・頂上への到達可能性、**頂上はランプ以外から入れない**(近道なし)。
- アート: 手描きアセット未着。現状は既存スタンドイン(木・岩・草)＋プレースホルダ。差し替えは `img/field/moss/manifest.json` の規則だけ(`ASSET GENERATION REQUIRED`: 崖の柵 `prop_post_boundary_wood`、ベンチ `prop_bench_view`、標識、立石 `anc_*`)。

## 薬草・宝箱 (サブクエスト連動)
`treasurePoints[].kind:'herb'` は草むらノード(✿)。通常の宝箱と同じ配管(Inventory/`ItemData.treasure`/セーブの `moss.opened`)。
`tr_c1_herb_slope_a / _slope_b / _ramp / _lip` = 薬草 ×1 ずつ(合計4。農作業の女性のクエストは3つ)、`tr_c1_cairn` = きずぐすり+40G。

## 時間帯 (`js/field/field-timeofday.js`)
`FieldTimeOfDay.set('day'|'dusk'|'night',{ms,instant})`。画面空間のオーバーレイ(multiply の色補正＋太陽/月のグロー＋ビネット＋星空)で、マップの絵に依存しない。
マップは `"timeOfDay":{"default":"day"}` で opt-in(無指定のマップは常に day＝既存マップは不変)。保存しない(ストーリーか操作で決まる)。
頂上のベンチ(`hook:'cliff_time_cycle'`)でプロローグ後は 朝昼→夕→夜 を切替できる。

## 遠景の演出 (`js/field/field-vista.js`)
炎上する村は **vista**: マップ JSON `vista[]` にワールド座標で置く遠景。**夜の色補正より上の専用レイヤー**にあり、毎フレーム world の transform をミラーするので、夜でも炎が青く沈まない。
`village_fire` は CSS だけで生成(家のシルエット・炎・煙・火の粉・グロー)。画像が届いたら `{image}` 指定に差し替え可能。`MossForest.vista(id,on,{ms})` で点火。

## シーン進行 (`js/field/field-scene.js` + `scene-data.js` + `talk-data-scenes.js`)
- 会話は `talk-data-scenes.js`(FieldTalk のテーブル)。演出手順は `scene-data.js` の `steps`(talk / fade / tod / vista / focus・release / pan / shake / wait / set / stage / call)。
- 進行の粒度: **マクロ進行は storyStage**(3=訓練後、崖へ → シーン → 4 → 村へ戻る場面 → 5)。**シーンは原子的**(途中保存なし、やり直しは頭から)。条件は `requireStage`。
- 流れ: 村の南門の標識 → 崖(夕暮れ) → 頂上トリガー → 夕暮れ会話 → 暗転(夜へ) → 星空会話 → 鐘の音 → カメラが村へ滑り炎上を点火 → 緊迫会話 → 暗転 → 既存の `returnScene`。
- 崖から村への戻りは stage 3 と 15 以降のみ可。途中の stage では出口は閉じる。
- テスト: `tests/moss/m7_cliff.py`。
