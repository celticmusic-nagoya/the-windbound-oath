# 全回帰結果（O）

source HEAD `d671f7b543ba6f6268445ce5b7d69cfe62046de9` / main基準 `e63780543d7ba1719a39a2f68b9924dc6d5b3933`、port 8783、直列、各test自前server、timeout 900秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m59_dev_down_cycle.py | 合格 | 0 | 44.26 | 0 / [0] | tests_moss_m59_dev_down_cycle.py.log |

集計: 合格 1, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
