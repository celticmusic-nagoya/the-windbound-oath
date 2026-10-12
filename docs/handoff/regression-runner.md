# 全テストrunner（O）

基準main53180f3、branch work/codex-regression-runner。STATUS: READY。
要約: 新規runnerで全59本を直列実行、57合格/main既存2/新規0/未実施0。各testで自分の8783 serverを起動・終了。exit0のFAIL/FAILSも検出する。

## 変更ファイル

新規tools/qa/run_all.sh（entry）・run_regressions.py（実行/分類）、本書、docs/qa/regression-20261013とrunner-check/negative/guardの結果表・JSON・logs/artifacts。status/CLAIMS追記。既存tests/game/maps/assets未変更。

## テスト結果

```sh
PATH=/workspace/.cloud-setup/venv/bin:$PATH PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium \
bash tools/qa/run_all.sh --timeout 600 --out docs/qa/regression-20261013
```

全59件: **合格57 / main既存2 / 新規0 / 未実施0**、runner exit1。main既存はm13_elder_attack_text（朝の台詞）とm4_e2e（Fiona stage9）の既知FAIL文言のみ。timeout/Traceback/console error/別FAILは同ファイルでも新規。失敗が残るので全件成功のexit0へ変えない。

全実行のsource HEADは58df9f7（runtime/testsはmain53180f3と同一）。全testのSHA256前後一致、server終了確認。元checkoutのゲーム/assets/tests差分なし。表はdocs/qa/regression-20261013/results.md、機械結果は同.json/.tsv、test毎stdout/stderr/server.log、PNG/計測JSONも同フォルダ。

全実行後にrunnerを改良し、全59の既存ログを最終の厳格なFAILS-prefix/console分類で再判定、分類は変わらず57/2。改良に関係する再実行はm19_plan_bench（--out転送、合格）とframe_clock（clean snapshot guard、合格）。全59を最終版で再実行したという報告ではない。snapshot内.gitはなく、benchmarkの個別git SHAはnullになり得るが、master結果JSONのsource HEAD/test hashで実行基準を保持する。

runner自身の合格検証:
- --self-test: exit0のFAIL、末尾説明付きFAILS>0、厳格な既知文言、timeoutを検証。
- 外部ダミー3本: 合格exit0 / FAILS2を出してexit0 / timeout。runnerは期待どおりexit1、後続も実行、各server終了。negative結果の「新規2」は意図したrunner負例で、アプリ全59の新規失敗とは区別。
- 未コミットnon-docファイルを作るとsnapshot開始前に停止、server起動なし。作ったファイルは削除済み。

## 実行契約 / 要判断

git archiveのcommit済みHEADをtemp snapshotへ展開して実行。一時manifest/素材を書換える既存testも元repoを触らない。未コミットtracked変更とnon-doc未追跡ファイルは停止するので、まずwork branchへWIP commit（pushは任意）してから実行する。docsの未追跡出力は許容。主画面の手元変更を黙って除外した旧HEADテストを防ぐ。

テスト引数はJSONのstructured listで渡し、walk_mapにはA2 map、plan_benchには出力dirを明示。PORT/OUT/Chromiumだけ実行adapterで上書き、assert/待機/ゲーム入力は変更しない。target発見対象はtests内*.py/*.test.js、run_python.pyは実行helperなので除外。

1回目のplan_benchはchild引数転送の問題で出力先がsnapshot内defaultになったため、その終了後に生成JSON/MDを回収。structured argsへ修正後の単独再実行では正しいartifacts dirへの出力を確認済み。

未実施: Android実機、追加Rのm22（現在対象remote branch未検出でmainにもtest無し）、最終runner版での全59の再実行。既知失敗2件の修正は今回行わない。新規UI変更なし。

## 次の提案

Claudeの新規testがmainへ入れば次の全実行で自動検出。main既存2件の台詞期待値は担当判断後に更新し、余分な失敗をknown扱いしない。mainマージはClaude担当、Codexはwork branchへのpushだけ。main未変更/ロールバック不要。
