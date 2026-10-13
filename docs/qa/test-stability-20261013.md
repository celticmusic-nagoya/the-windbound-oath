# JJ テスト安定化 (検証中)

基準main31a5f5e / work/codex-gg-kk。変更はtests/tools/docsのみ。

修正前: m31 3/3、m32 1/1、m6_inventory 1/1合格。報告されていたstraight upの間欠失敗は今回の小標本では未再現。固定1000ms/8000ms/700msは画像decode・移動先map・停止を保証しないため、準備条件を明示して修正した。

m31では初期マップready→森A1のmap ID/active/busy→全コマdecode→描画IDLE相当を待つ。runtimeのspr.stateはprivateなので、IDLEの公開描画結果（bob/mirror transformなし）と足元・コマが160ms以上不変の両条件で判定する。単純に「正解のup画像が出るまで待つ」形にはしていない。各方向20サンプル/60msと方向・反転の期待値は維持。入力後は方向に依存しない変位+WALK描画を確認してから採取する。

中間版で斜め2件が失敗。TRACE座標はx500/y540付近で、初期の家の非同期読み込みを森のreadyとして誤認していた。初期mapのreadyと移動先A1のID確認を追加して解消。中間失敗/診断ログは削除せず証跡に保存した。

修正後20連続を直列検証中。現状の完了数は [after.json](test-stability-20261013/after.json)（完了時に全20ログをpushする）。途中失敗を合格列に数えない。

## 会話前置き走査

全Python69ファイルとNode7ファイルを走査。 [prelude-audit.json](test-stability-20261013/prelude-audit.json) はhelper定義内の文字列と実行順を区別するための静的資料であり、全テスト実行の結果ではない。

| 候補 | 判断/対応 |
|---|---|
| m6_inventory | 森の到着会話の後、実click移動の前にcloseDialogueを追加 |
| m32_lou_follower | map readyとcloseDialogueを追加して追従移動を準備 |
| m31 | 上記状態待機、到着会話のcloseを維持 |
| kb_field | 初期会話をEnterで終えて歩く意図的試験。変更しない |
| m4_e2e | GO helperの定義がcloseより先だが呼出は入口会話の確認/close後。変更不要 |
| m7_choreo | 仮rectangleの演出後、会話を最後まで実clickしてから実fieldへ移動。変更不要 |
| m8_town_maps | enterWorldMapがcloseDialogueする間接前置き。変更不要 |
| seal_a3 / walk_a1 / walk_map | DEV harnessで本編会話UIなし。変更不要 |
| Node7本 | ブラウザ会話操作の対象外。変更不要 |

元のassertを弱めず、ゲームの会話中移動不可仕様を変えない。全回帰は今回未実施（前回FF75/75とは別）。Android実機未測定。main未統合。
