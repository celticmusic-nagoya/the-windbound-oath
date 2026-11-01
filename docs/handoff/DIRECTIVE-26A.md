# DIRECTIVE-26A handoff

基準main: `2f5312efdfd4f5ad48439dd5bca17bb0b801bffc`（PR99）
ブランチ: `codex/26a-qa-fixture-repair`。既存work refは保全。
変更: Node原版2本、素材原版1本、test-only helpers/negative control、QA runnerのopt-in履歴fixture、26A証拠/文書、P6-QA-01完了記録。
ゲームID/flag・台帳・素材・本編の変更: なし。

修復範囲PASS: startup20/20、continue37/37、Node原版全14/14、素材原版PASS。故障注入8/8が原版child exit1・注入印・固有エラーを検出、厳密抽出契約PASS。

回帰の最新9種類=8PASS＋製品監査probe1FAIL（報酬4箇所のみ）。初回archiveにGit履歴がないため素材鮮度2assertがFAILした証拠を保管。鮮度検査を緩めず`--git-history`で再実行しPASS。製品1456ファイル・正式259PNG・台帳/参照/描画/瞬き不変。25A報酬FAIL、未実施Android、他の未完成事項は維持。

詳報: `docs/qa/DIRECTIVE-26A.md`。証拠: `docs/qa/evidence/directive-26a/`。
独立exact-head QA、rollback remote SHA読み戻し、最新main/PRhead/checks/競合確認後に通常merge。Pages/main一致はmerge後に別回収。製品全体PASSを宣言しない。

次工程: DIRECTIVE-26B（P6-REWARD-01、序盤報酬4箇所）。P6-QA-03の無条件真assert修復は別件。
STATUS: READY_FOR_REVIEW
