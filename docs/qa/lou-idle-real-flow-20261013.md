# II ルー待機・祭壇からの実フロー

基準main31a5f5e / work/codex-gg-kk。新規 tests/battle/lou_idle_real_flow.py と本報告/ログ/縦2画像のみ。

## 結果

9/9合格、FAILS0、pageerror0。390×844・is_mobile/has_touchのChromiumでモーション軽減no-preference/reduceを各1回。`devJump('altar')` で祭壇開始を準備し、全ページを実click→祭壇の元onclickがstartRaiderBattleを呼ぶ→最初のコマンド→敵ターン→被弾後まで記録した。直接devJump('raider')は使っていない。

バトル開始と敵ターン後の各3秒でルーの6コマが循環。reduceでも停止せず。両条件とも敵ターン後HP120/94、round2。被弾対象は通常コマンド対象のAidan/Fionaであり、SUPPORTのルー自身への被弾試験ではない。

250msごとのBattleIdleMotion.status全体、body.className、document.hidden、InputManager.state、Lou canvas.dataset.frame、HP、roundを [results.json](lou-idle-real-flow-20261013/results.json) に保存。250msサンプルは6FPSより遅いため隣接フレームが飛ぶこと自体は停止ではない。

## 停止条件と時系列

| 条件 | samples | dialogueOpen | busy/actionCinematic | initialの異なるコマ | post-hitの異なるコマ |
|---|---:|---:|---:|---:|---:|
| no-preference | 53 | 0 | 3 | 6 | 6 |
| reduce | 54 | 0 | 3 | 6 | 6 |

`paused()`はdocument.hidden / battlePresentationBusy / dialogueOpen / actionCinematicで停止する。敵行動の演出中の休止は仕様上の停止条件に合い、後に再開を確認。今回の経路ではクラスの付きっぱなしによる持続停止は再現しなかった。

未実施: Android実機、ブラウザをバックグラウンドへ移す/復帰する実端末経路、低メモリ/画像decode失敗、全敵行動/全シーン。実機「1枚で止まる」の原因が解決済みとは断定しない。端末で再現する際は同じ250msログと`document.hidden`、ルーstatus.enabled/state/showing、Network画像失敗を照合する。ゲームコード修正案は追加再現後に判断。

再実行: `python tests/battle/lou_idle_real_flow.py`、自身の8813サーバー起動/終了。次JJ。main未統合、将来の戻し方 `git revert -m 1 <merge>`。
