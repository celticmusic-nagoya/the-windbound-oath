# AA: 断崖高さ overlay draft（DEV限定、未採用）

基準main 7abb9f3。入口0→螺旋中腹1→頂上2。既存path_spiral/path_summit_walkの中心線に床矩形を重ね、既存colliderを全階で維持する。階の接続は下部の既存螺旋路と既存頂上坂の2箇所。画像・map本体・runtimeを変更せず、通常プレイではheightSpecsフラグOFF。

`python3 tools/field/lint_height_spec.py cliff_moher_01_spiral_ascent --out /tmp/cliff-lint.json` は本番FieldCollision/FieldHeightをNode VMで実行する。全条件付きblocker組合せでconnector両端の22×10足元、接続外側の床連続性、入口から各上階床への経路、spawn/level参照/座標を確認。任意画像の不透明部、全てのalternate path、動的NPCを保証する検査ではない。

lintは合格。未宣言上階entityは失敗ではなく警告。宣言案はcliff-height-entity-levels.md。E2Eでは実歩行を使い、teleportで階を飛ばさない。上階に着いただけで夕日は始まらず、ベンチで「はい」を選ぶ必要がある。現mapのlevel省略=0によるgate問題は未解決の採用条件として報告する。

## 実測結果

- lint: FAILS0。歩行可能floorの入口からの到達、connectorの両端/外側が合格。
- m27: overlayのみは実歩行合格、ベンチ会話gateが失敗（FAILS1、stage3のまま）。上階の2 zoneをlevel2にしたbrowser-only提案fixtureは実歩行・会話・夕日→襲撃が合格、stage4到達。console/page error0。
- したがってAAはdraft/検査/提案を納品したが、**物語gateを保ったままoverlayだけを採用する条件は未達**。Claudeによるentity宣言の別変更待ち。m27はこの未達を隠さずexit1を返す。FFで採用する場合、このDEV draft依存の新規失敗をmainの既存失敗として扱わないこと。
- タップ座標は既存eventZoneの論理座標960を使う。イベントtapはstatic propの高さ補正とは別経路である。初回テストの高さ補正したクリックはfixture誤りとして修正後再検証した。

PLAYER QA: 仮床と地形の段差表現、頂上のcairn/薬草への到達、坂途中の採集物を両階から取れる設計の可否、Android性能は未実施。画像変更なし。旧saveの最高階deriveについては別途EEで監査する。
戻し方: main未変更。本作業ブランチを採用しない。後日統合する場合はClaudeがmerge前rollbackを確保し、戻す場合は `git revert -m 1 <統合コミット>`。
