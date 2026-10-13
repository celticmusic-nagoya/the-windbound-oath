# T: 実エンジンの風の舞・魔弾MP計測

基準main49660b7。work/codex-tz。ゲームコード変更なし。Playwrightの仮想時計fast_forwardで演出待ちを進め、正規のcutin OFF設定を使用。会心/回避のMath.random呼出（battle-critical.js / battle-status.js）だけをLCG seed20261013へ固定し、演出乱数とは分離した。

| 戦闘 | 条件 | 結果 | round | 終了MP | 実cast | 有効対象への魔弾 | 入力魔弾 | 実HP減少合計 | 回避 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| normal | off | victory | 4 | 30 | 0 | 3 | 4 | 27 | 0 |
| normal | dance | victory | 5 | 10 | 2 | 2 | 3 | 36 | 0 |
| normal | hit | victory | 5 | 16 | 2 | 2 | 3 | 36 | 0 |
| normal | action | victory | 5 | 16 | 2 | 2 | 3 | 36 | 0 |
| raider | off | defeat_rewind | 7 | 36 | 0 | 7 | 7 | 196 | 0 |
| raider | dance | defeat_rewind | 11 | 6 | 3 | 8 | 8 | 262 | 1 |
| raider | hit | defeat_rewind | 11 | 17 | 4 | 7 | 7 | 262 | 1 |
| raider | action | defeat_rewind | 11 | 17 | 4 | 7 | 7 | 262 | 1 |

通常fieldGob1は全条件勝利。Raiderは本固定方針で全条件defeat_rewind（時間巻き戻しログで直前MP/HP/roundを保存、再開後の初期MPと混同しない）。単一seedの勝利指標であり母集団勝率ではない。敗北にはkill_round=null、勝利には実際の撃破roundを出す。

Aidanは通常攻撃、Fionaは効果が切れMP>=10なら風の舞、それ以外は通常攻撃。増援を優先、2人とも同一対象を選択する。Aidanが先に対象を倒すとFionaの選択が無効になり、hitとactionの回復条件に差が出る。提出行動数とログで確認した実cast/実命中を別列にした。敵は正規AI、Lou支援/被回復/撤退を維持。ヒール/TP技/風の一閃は使わないため実プレイヤー難易度の評価ではない。

被ダメージはHP減少を各ログ境界と5msタイマーで観測した合計（0でclamp後の実HP損失）。過剰ダメージは含まない。回復を相殺しない。回避率上昇castログは回避回数から除外。勝敗はエンジンの敵HP0/巻き戻しログで判定、round_limitは未完了。

変更: tools/sim/engine_wind_dance_bench.py、docs/qa/engine-wind-dance-20261013.json、本報告、status。8条件直列計測完了、page/console error0。初期実時間runは中止して全件やり直し。旧共有乱数/回避率ログの誤カウントを修正後、最終8件を再実行した。再現性検証は後続の再実行JSON参照。実機性能は未測定。

再実行: PATH=/workspace/.cloud-setup/venv/bin:$PATH python3 tools/sim/engine_wind_dance_bench.py --out /tmp/engine.json。--seedsで複数seed、--max-roundsで上限を指定可。自前HTTP server8789はfinallyで終了。

要判断: 暫定回復3のまま。固定方針ではRaiderを勝ち切れないため、ヒール/増援処理/TP技を含む別方針で評価する。数値採用/main統合はClaude。
