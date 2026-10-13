# JJ テスト安定化 (完了)

基準main31a5f5e / work/codex-gg-kk。変更はtests/tools/docsのみ。

修正前: m31 3/3、m32 1/1、m6_inventory 1/1合格。報告されていたstraight upの間欠失敗は今回の小標本では未再現。固定1000ms/8000ms/700msは画像decode・移動先map・停止を保証しないため、準備条件を明示して修正した。

m31では初期マップready→森A1のmap ID/active/busy→全コマdecode→描画IDLE相当を待つ。runtimeのspr.stateはprivateなので、IDLEの公開描画結果（bob/mirror transformなし）と足元・コマが160ms以上不変の両条件で判定する。単純に「正解のup画像が出るまで待つ」形にはしていない。各方向20サンプル/60msと方向・反転の期待値は維持。入力後は方向に依存しない変位+WALK描画を確認してから採取する。

中間版で斜め2件が失敗。TRACE座標はx500/y540付近で、初期の家の非同期読み込みを森のreadyとして誤認していた。初期mapのreadyと移動先A1のID確認を追加して解消。中間失敗/診断ログは削除せず証跡に保存した。

修正後m31 **20回連続合格**（全回FAILS0、console0）。m32/m6_inventoryも各1回合格、変更対象の合計22回合格。 [after.json](test-stability-20261013/after.json) と各ログを保存。途中の失敗版はこの合格列に数えず保管した。

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

## 再実行 / 引継ぎ

リポジトリ直下で `PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/moss/m31_aidan_heading.py` を20回直列実行し、各終了codeと `^FAIL ` / `^FAILS [1-9]` を確認する。m31は自身の8822サーバーを起動/終了（PORT指定時はrunnerが所有）。今回の実行は共通runnerのChromium/URL adapterと各回自身の8821サーバーを使用、既存assertを書き換えない。

不安定性の一般原因である準備/停止の固定待機を状態待機へ変更したが、元のstraight up間欠失敗は修正前3回では再現しておらず、全ての原因がこれだけだとは断定しない。新しい中間版の初期map raceは実測で原因を特定した。

変更ファイル: m31/m32/m6_inventory、tools/qa/audit_dialogue_prelude.py、本報告と証跡。ブランチ `work/codex-gg-kk`（本成果のcommitは履歴参照）。要判断: 追加の実機/低FPSでの間欠失敗がある場合のログ採取。次KK。将来main統合後の戻し方 `git revert -m 1 <merge>`。
