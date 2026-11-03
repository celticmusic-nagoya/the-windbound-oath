# 全回帰結果（O）

source HEAD `1c5bda76a0f90854db606ec7b19cc5553741430a` / main基準 `3d1794340feb7210f209ae4beea2dc879034e92f`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m55_dev_walk_motion.py | 合格 | 0 | 169.582 | 0 / [0] | tests_moss_m55_dev_walk_motion.py.log |
| tests/moss/m56_dev_walk_stride.py | 合格 | 0 | 57.659 | 0 / [0] | tests_moss_m56_dev_walk_stride.py.log |

集計: 合格 2, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
