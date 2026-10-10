# FieldChoreo — 立ち位置接近・移動演出

`js/field/field-choreo.js`。時計（performance.now/rAF）基準なので Hz に依存しない。

## 構成
- **Actor アダプタ** `{get():{x,y}(足元), set(x,y), pose?(state,dir), release?()}` — 描画エンジンとの唯一の接点。`MossForest.actor('aidan'|'fiona')`、将来は村/屋内用を追加するだけ。仮矩形も同じ形で動く（tests/moss/m7_choreo.py）。
- **FieldChoreo** — `moveTo(actor,{x,y},{ms|speed,ease,blocked,face})` / `approach(a,b,{ms,gap,share,ease,blocked})`（互いの足元が `gap`px になるまで。share=aが進む割合、1で片方のみ）/ `all` / `cancelAll`。
  移動開始で `pose('walk',dir)`、到着で `pose('idle',向き)`。**状態が変わる時だけ**呼ぶ。`blocked(x,y)` が真になった地点で止まり false を返す（壁抜け防止）。
- **FieldScene ステップ** — `{approach:{a,b,ms,gap,share}}` `{move:{actor,x,y,ms}}` `{follow:'fiona'}`（フィオナを通常の追従へ戻す）。この後に `{talk:…}` を置けば「近づく→会話」。本番の星空シーンには**まだ挿入していない**（キャラ画像到着後）。`FieldScene.play(定義オブジェクト)` でテスト用シーンも直接実行可。
- Aidan は座標を動かすだけで歩行アニメが付く。Fiona は `data-pose`/`data-dir` を出すので、歩行・待機画が揃ったら CSS/manifest で割り当てる。

## マップオブジェクト差し替え（柵/ベンチ/標識/立石）
`img/field/moss/manifest.json` の `node` に実画像ルールを**先頭に**追加するだけ（コード変更不要）。`python3 tools/moss/check_assets.py` が順序ミス（SHADOWED）と、実画像幅と当たり判定プリセット幅の食い違い（COLLISION）を警告する。当たり判定は各マップの `collision.presets["<asset>"]`（足元基準の矩形）。検証 `tests/moss/m7_prop_swap.py`。
