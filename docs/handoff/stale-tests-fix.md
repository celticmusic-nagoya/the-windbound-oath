# W: 古い台詞テストの更新差分と検証

STATUS READY / work/codex-tz。コード・既存testをCodexが直接変更していない。調査中にClaudeの8155fddがmainへ統合済みと判明したため重複編集を避け、実際の最小修正をstale-tests-fix.patchへ履歴参考として保存した。**現在mainへ再適用する必要はない**。

- m13: 後から読み込むTalkDataRildeが同じelder_closed entryを上書きし、警告追加で朝台詞が3番目→4番目へ移動した（js/field/talk-data-rilde.js:14–20、field-talk.jsのentry-id merge）。NPC IDと朝台詞自体は変更不要。巡回3→4だけの修正。初期調査でNPC ID不一致と見たが、全文とロード順を確認して訂正した。
- m4: index.html:1148がscene_forest_arrivalを呼び、現行10ページの先頭は「冷たい土と、苔の匂い」。旧warningは先頭ではない。台詞/進行は変えず、現在の到着先頭の期待値へ変更。Fionaの奥地警告は7ページ目に残る（talk-data-scenes.js:37–48）。将来の追加案: 先頭と7ページ目のspeaker/文言を個別確認する（今回未適用）。

Patchは230a29cでgit apply --check合格、d153d06でreverse --check合格（既に適用済みを確認）。ゲーム台詞、誓い、10ページ、歩行/戦闘/遷移assertを変えない。

検証: Vの230a29c全回帰では旧2件のみ失敗。修正後d153d06を独立clone/git archiveに固定し、m13/m4/m22/m23/m26を各自server8793で直列実行、**5/5合格・FAILなし・未実施0**。m4は約168秒で祭壇まで到達、console errors[]。追加のlevel保存/回避ポーズ/DEV overlayも合格。全test SHA前後一致/server終了。

全件表: ../qa/latest-delta-20261013/results.md。d153d06はこの5本の差分検証であり、全63本を同コミットで実行した結果ではない。V全件の基準230a29cと区別する。

変更: 本説明、stale-tests-fix.patch、差分検証証跡、V追記/status。旧main既存2件は現mainで解消済み。今後同じFAILを既知として自動許容しない（O runnerのKNOWN登録は旧コード基準なので、基準コミット/原test SHAと照合が必要）。main更新はClaude担当、Codexのmain変更なし・ロールバック不要。
