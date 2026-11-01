# 全回帰結果（O）

source HEAD `535ed142b21975b3bfb68eed4dedb529fc13bebd` / main基準 `5ab60c5db833821744d73080f91ffcd559ebf0a4`、port 8765、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/system/playable_audit_25a.py | 新規 | 1 | 114.835 | 4 / [4] | tests_system_playable_audit_25a.py.log |
| tests/moss/m10_flow.py | 合格 | 0 | 75.082 | 0 / [] | tests_moss_m10_flow.py.log |
| tests/battle/raider_wipe_rematch.py | 合格 | 0 | 70.691 | 0 / [0] | tests_battle_raider_wipe_rematch.py.log |

集計: 合格 2, main既存 0, 新規 1, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
