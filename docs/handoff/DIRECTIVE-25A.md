# DIRECTIVE-25A audit handoff

基準main: `5ab60c5db833821744d73080f91ffcd559ebf0a4` (PR98)
ブランチ: `codex/25a-playable-audit` (`work` refを保護しnamespace競合を回避)
変更: `docs/qa/DIRECTIVE-25A.md`, `docs/qa/evidence/directive-25a/`, `docs/planning/{PHASE6_BACKLOG,ASSET_GAP_LIST}.md`, audit-only2tests, CLAIMS/本引継ぎ。
追加・変更したゲームID/flag: なし。

結果: **監査総合PARTIAL**。61項目=COMPLETE43/PARTIAL10/MISSING1/BUG5/BLOCKED2。BUG5は製品報酬2分類4再現箇所＋QA基盤3分類。P0/P1/P2/P3=0/4/8/2、素材10制作/接続検討単位。

QA: 既存browser33/33PASS、追加3本中2PASS/1FAIL（取得/依頼報酬4件を実測検出）。Node原版12suitePASS/2FAIL、asset原版1FAIL。FAILを合格化せず生ログ保存。原因診断adapterのみ20+37PASS。台帳/実参照0errors、259固定SHAとruntime1456file不変。監査成果物整合性20checksPASS。独立exact-head QA・rollback remote読み戻し・最新main/PRhead/checks/競合・通常mergeを別途必須gateとする。

未実装・要確認: full NG→王都の同一SAVE連続通常プレイ、襲撃legacy全flow、Android総合実機/OS復帰・長時間性能。通常NGは家→実walk→Fiona→木人6行動勝利→断崖登頂→夕日/帰路→襲撃stage5まで実行。seeded END→fort自由探索、capital cold CONTINUE/Liam EXP13、normal低HP復帰/Raider再戦はPASS。詳細再現/期待/実測/証拠/端末要否はmatrixを正本とする。

次工程: QA-01（旧テスト基盤）→REWARD-01（報酬実給付）→QA-02（連続通常経路）。今回ゲーム修正なし。過去完了Phase4/5A/5Bと正式採用259PNGは維持。

公開: 基準main Pages299file一致確認済み。本監査PR公開は通常merge後にbuild/main/公開文書一致を別回収し最終報告。実機QAは未実施。

STATUS: READY（監査資料・証拠の準備完了。製品全体PASSやrelease-readyを意味しない）
