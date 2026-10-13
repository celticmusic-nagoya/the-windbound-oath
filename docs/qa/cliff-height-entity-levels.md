# 風見の断崖: entity level 宣言案（未採用）

対象 main 7abb9f3。AA の overlay は高さだけを読み込み、既存 map の entity 宣言を上書きしない。以下は Claude に渡す提案であり、map 本体・物語・採用素材は変更していない。

|対象|宣言案|理由|
|---|---|---|
|spawn from_lind|level: 0|入口|
|spawn summit|level: 2|頂上。省略時 runtime derive は2を選ぶが明示推奨|
|tr_c1_to_lind / ev_c1_arrival / ev_c1_sign|level: 0|入口のみ|
|ev_c1_summit / ev_c1_view_bench|level: 2|頂上の通知と夕日会話。現行は省略=0|
|tr_c1_herb_slope_a|level: 0|下層|
|tr_c1_herb_slope_b|level: 1|螺旋中腹|
|tr_c1_herb_ramp|levels: [1,2]（要判断）|坂途中。接続中は進入側の階層を維持するため両方を許可する案|
|tr_c1_herb_lip / tr_c1_cairn|level: 2|頂上|

既存の sunset は zone に立つだけでは始まらず、ベンチをタップして「はい」で開始する。この会話 gate を省略 level=0 のままにすると高さ2のプレイヤーから届かない。draft の採用には宣言の別変更と検証が必要。AA の browser fixture は頂上の2 zoneだけを一時的に level2 とし、提案の効果を分けて検証する。ディスクの map は変更しない。
