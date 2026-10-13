# U: 接触level E2E

work/codex-tz、指定m24とtools/qa/browser_support.py追加。repo runtime/mapは未編集、browser JSON route fixtureのみ。feet1560,900/1050は配置のたびblockedAtLevel=falseをassert、NPC/宝箱/herb/trigger/story symbol/moving monster/出口/rest/ambienceを上下同XYで検証。hookカウンタとonce/取得idで0/1を確認。rest/ambienceは公開zone idで確認、外部効果hookが無いためその副作用回数はSKIP明示。

基準49660b7: FAILS5、exit1、console/page error0。moving monsterの他階接触、橋外から橋下NPCへのtarget level、遅延中の階変更、縦横上階宝箱tapが失敗。
Claude修正後160bead: **FAILS2、exit1、console/page error0**。動く敵/target/遅延の3失敗が解消。残る失敗は390×844 / 844×390の上階宝箱のlift後視覚位置tap。通常の同階宝箱の論理位置tapと報酬onceは合格。現在の静的宝箱はheight liftを描画へ反映しないため、未実装の表示契約に対する赤テストとして納品。ゲーム側へ修正は加えない。

初回fixtureのテレポートが接触ラッチを再設定してstory/exitの正例を阻害した。修正後は有効な離れた位置からgoFeetで実歩行して入り、両基準で正例合格。起動時のdefault map非同期遷移も待機してからfixtureへenterする。

実行: `python3 tests/moss/m24_height_contacts_e2e.py`。PORT未指定なら8790自前serverをfinally停止、指定時はrunnerがserver管理。失敗とconsole errorはexit1。証跡: height-contact-e2e-20261013/ の前後ログ/JSON/縦横画像。厳密な上下対象の同時設置、全オブジェクトのlevel1描画、connector端などは追加余地あり。

要判断: 静的上階物体の表示liftとタップ位置の契約をClaudeが実装してから赤テストを再実行。通常main全回帰(V)とは分けて集計する。STATUS READY（失敗テスト納品、main統合はClaude）。
