# 風の舞 数値比較シミュレーション（N）

基準main53180f3、branch work/codex-wind-dance-sim。STATUS: READY（提案シミュレーション、ゲーム未適用）。
要約: 保守10pt/2敵フェーズ/MP6/単体Aidan、標準15pt/3/MP10/全体、強20pt/3/MP12/全体を比較。固定攻撃列ではボスで標準がMPを6残しつつ軽減し、通常戦MP30では強案のcast回数が減って標準より総軽減が小さくなる。実戦勝率/撃破ターンは算定しない。

## 何を比較したか

現在のモス森ボスはゴブリン・レイダー1種類で、「モス森ボス戦」と「レイダー戦」は同一のcaseとして扱う。別bossのHP/数値を創作しない。補助caseは通常のforestGob3（ゴブリン2＋異常化1）で、bossではない。

ゲームの効果は未実装、SupportMagicDataはnullのまま。このスクリプトはPython単独で同じ物理hit列に仮の回避を適用する**反実仮想の露出比較**。現engineの実行やHP/KO/回復/勝敗の完全再現ではない。被弾率は「18敵フェーズ中の全hit機会に対する命中の割合」で、表示される15%等の効果量そのものとは異なる。被ダメ量はHP上限で切らない入力攻撃の総量であり、パーティーが実際に失ったHPではない。

- 18敵フェーズ、seed20261013、各案/条件20,000試行。各hit/破砕の各対象/連撃の各hitを独立抽選。解析期待値とMC平均を照合し、5標準誤差以内を必須にした。
- 発動フェーズを含め2/3フェーズ。残り0時にMPがあれば更新、重複加算なし。MP初期36（boss）/30（通常）、回復item/etherは使わない。最初から期限切れ毎に使う固定方針で、最適なcastタイミングの探索ではない。
- bossのHPphaseを選ぶ外生モデルは1250−64×round（最低1）。phase閾値820/400、召喚820/500、予告3の倍数/phase3偶数、queued→破砕の順をコードから参照。増援は生まれた当日は行動せずsupply/burst/frenzy/attackを巡回。supply/burstは物理hitに含めず、供給回復/ATK低下がphaseや撃破を変えるフィードバックは再現しない。
- targetはA/Fを交互にした比較条件。実AIのHP比/絶対HP選択とは異なる。保守案はAidan単体で固定し、Fionaを選ぶ方針は未試算。
- 追加条件guarded/Lou DEF+15% guardedはダメージ式の感度分析。全hitでdefendする実戦手順ではなく、cast時に同時guardできるという意味ではない。Louの通常戦参加も想定しない（通常caseのLou列は仮想倍率比較）。

## 再現結果（guardなし）

| case / 案 | baseline物理総量 | 被弾率 | 被ダメ期待値 | 軽減/MP | 消費MP/残MP | cast phase |
|---|---|---|---|---|---|---|
| raider_moss_boss / conservative | 594 | 97.917% | 578.5 | 0.4306 | 36/0 | [1, 3, 5, 7, 9, 11] |
| raider_moss_boss / standard | 594 | 95.625% | 561.15 | 1.095 | 30/6 | [1, 4, 7] |
| raider_moss_boss / strong | 594 | 94.167% | 550.2 | 1.2167 | 36/0 | [1, 4, 7] |
| forestGob3_nonboss_reference / conservative | 324 | 97.222% | 315.2 | 0.2933 | 30/0 | [1, 3, 5, 7, 9] |
| forestGob3_nonboss_reference / standard | 324 | 92.500% | 299.7 | 0.81 | 30/0 | [1, 4, 7] |
| forestGob3_nonboss_reference / strong | 324 | 93.333% | 302.4 | 0.9 | 24/6 | [1, 4] |

全18組（2case×3条件×3案）のMC平均が解析期待値の5SE以内。詳細のhit列、phase/召喚/予告、covered hit数、MC平均/SE/10-90percentile、source SHA256はwind-dance-sim-results.jsonへ保存。

## 解釈・要判断

- bossで標準3cast/MP30、強3cast/MP36。標準はMP6を残すが、それでもヒールMP8には足りない。強はMPを使い切る。保守は6castでMP36を使い、Fionaの行動をより多く失う。今回はcastによる攻撃/祈り/回復の逸失をincoming traceへ反映していない。
- 通常MP30では標準3castに対し強は2cast（MP24/残6）。効果率だけ強くても総軽減は標準より小さい。残6で祈りを使う等の選択はこのモデルには含まない。
- 同一3フェーズの全体保護だけを比べれば20%は15%より期待軽減が4/3倍。上の差はMP予算・範囲・保護期間による。保守単体は他人へのhitを減らせない。
- 全被ダメ/MP効率はcaster行動とヒール機会を無視した指標で、ヒールMP8/+48等の実回復と単純に優劣を決めない。実戦の必要ターン、勝率、増援処理、風の一閃の構え取消、Lou介入は未検証。
- 数値/範囲/重ねがけ/効果寿命の採用は作者判断。既存proposal20%/3/10も確定しない。ゲーム数値、HP1250、phase、save、assetは変更しない。

## 変更ファイル / 実行と分類

新規tools/sim/wind_dance_sim.py、本報告、結果JSON。status/CLAIMSへ記録。

```sh
python3 tools/sim/wind_dance_sim.py --self-test
python3 tools/sim/wind_dance_sim.py --json > docs/handoff/wind-dance-sim-results.json
python3 tools/sim/wind_dance_sim.py --trials 1000
```

合格: MP不足/cast日を含む期限/別対象/no-effectのself-test、20,000試行の解析照合、固定seedの再実行JSON一致。失敗なし。ゲーム変更前後の回帰は未実施（コード未変更）。main既存m13/m4は今回未実行。

次の提案: 採用判断後、ClaudeのDEV/feature gate内の実engineへ仮値を入れ、固定入力/乱数でcast行動損失・回復・ターゲット変化を含む実戦を比較する。本作業では適用/main mergeしない。
