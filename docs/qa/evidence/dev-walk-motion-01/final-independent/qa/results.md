# 全回帰結果（O）

source HEAD `f7311fa468391df1c8f00aeca8027d6ebb177d99` / main基準 `22efe877fbbfef5c5ec3445109b32bff70575da3`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m55_dev_walk_motion.py | 合格 | 0 | 173.068 | 0 / [0] | tests_moss_m55_dev_walk_motion.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 19.199 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/system/save_continue_lifecycle.py | 合格 | 0 | 26.951 | 0 / [] | tests_system_save_continue_lifecycle.py.log |

集計: 合格 3, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
