# 全回帰結果（O）

source HEAD `9fa6b89ead967f2ec860a0c3e04e46ee259accc7` / main基準 `3d1794340feb7210f209ae4beea2dc879034e92f`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m55_dev_walk_motion.py | 合格 | 0 | 180.175 | 0 / [0] | tests_moss_m55_dev_walk_motion.py.log |
| tests/moss/m56_dev_walk_stride.py | 合格 | 0 | 58.354 | 0 / [0] | tests_moss_m56_dev_walk_stride.py.log |
| tests/system/walk_bootstrap_network.py | 合格 | 0 | 0.285 | 0 / [0] | tests_system_walk_bootstrap_network.py.log |

集計: 合格 3, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
