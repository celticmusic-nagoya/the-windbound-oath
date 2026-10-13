# Codex 指示 AA: 高さ仕様(オーバーレイ)ドラフトとlint (2026-10-13)
前提: main に DEV 用オーバーレイが入った。`?feature=heightSpecs` を付けたときだけ、高さを持たない既存マップに `data/height-specs/<mapId>.json` の高さ仕様(`height` と同じ構造: levelHeight/levels/connectors/overpasses/visuals)が重なる。通常プレイでは読み込まれない(マップ本体JSONは不変)。実装: js/field/moss-forest-runtime.js、テスト: tests/moss/m26_height_spec_overlay.py。構造の見本は data/maps/dev_height_proto.json の `height`。
ランタイム(js/)は変更しない。

## AA-1: lint ツール
`tools/field/lint_height_spec.py <mapId>`: 対象マップ(data/maps)と `data/height-specs/<mapId>.json` を読み、実 FieldCollision/FieldHeight 相当の判定で次を検査:
- level>=1 の walk 矩形が下層の通行可能領域と連続しているか(各 connector 端が上階床に連続、22×10足元が両端で非衝突)。
- connector の from/to/axis/rect 整合、spawn(level指定)が歩行可能か。
- 既存の transitions/eventZones/treasurePoints/symbols/monsters/walkers の level 宣言と座標の整合(宣言なし=0扱いで上階とXY重複する場合は警告)。
- 出力: 合否表 + 警告(JSON も)。

## AA-2: 風見の断崖 (cliff_moher_01_spiral_ascent) の高さ仕様ドラフト
`docs/qa/map-height-plan-20261013.md` の計画(入口0→螺旋中腹1→頂上2)に従い `data/height-specs/cliff_moher_01_spiral_ascent.json` のドラフトを作成。既存ルート(path_spiral)に沿う階段/坂だけで接続し、近道・迂回を作らない。画像は変更しない(visuals は DEV 仮描画のみ)。lint 合格を確認。
- 夕日の丘/宝箱/頂上会話の level 宣言案は別ファイル `docs/qa/cliff-height-entity-levels.md` に提案(マップ本体は変更しない)。
- 検証: `?feature=heightSpecs` で実際に入口→頂上まで歩けること、物語gate(夕日→襲撃)が壊れないことを自前Playwrightで確認(`tests/moss/m27_cliff_height_overlay.py`)。
- 禁止: マップJSON本体・素材・ランタイムの変更、メインでの有効化。
