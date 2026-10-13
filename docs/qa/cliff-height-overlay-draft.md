# AA: 断崖高さ overlay draft（DEV限定、未採用）

基準main 7abb9f3。入口0→螺旋中腹1→頂上2。既存path_spiral/path_summit_walkの中心線に床矩形を重ね、既存colliderを全階で維持する。階の接続は下部の既存螺旋路と既存頂上坂の2箇所。画像・map本体・runtimeを変更せず、通常プレイではheightSpecsフラグOFF。

`python3 tools/field/lint_height_spec.py cliff_moher_01_spiral_ascent --out /tmp/cliff-lint.json` は本番FieldCollision/FieldHeightをNode VMで実行する。全条件付きblocker組合せでconnector両端の22×10足元、接続外側の床連続性、入口から各上階床への経路、spawn/level参照/座標を確認。任意画像の不透明部、全てのalternate path、動的NPCを保証する検査ではない。

lintは合格。未宣言上階entityは失敗ではなく警告。宣言案はcliff-height-entity-levels.md。E2Eでは実歩行を使い、teleportで階を飛ばさない。上階に着いただけで夕日は始まらず、ベンチで「はい」を選ぶ必要がある。現mapのlevel省略=0によるgate問題は未解決の採用条件として報告する。
