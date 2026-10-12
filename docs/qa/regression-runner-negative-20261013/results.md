# 全回帰結果（O）

source HEAD `90f2917f3fbc10659d1f212490df4ff1ee298f06` / main基準 `53180f3e9932c320f9929c9ef66eddb08eeb6fa7`、port 8783、直列、各test自前server、timeout 2秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| /tmp/runner-fixtures-25hs0mzy/pass.py | 合格 | 0 | 0.23 | 0 / [0] | _tmp_runner-fixtures-25hs0mzy_pass.py.log |
| /tmp/runner-fixtures-25hs0mzy/zero_exit_fail.py | 新規 | 0 | 0.221 | 0 / [2] | _tmp_runner-fixtures-25hs0mzy_zero_exit_fail.py.log |
| /tmp/runner-fixtures-25hs0mzy/timeout.py | 新規 | 124 | 2.108 | 0 / [] | _tmp_runner-fixtures-25hs0mzy_timeout.py.log |

集計: 合格 1, main既存 0, 新規 2, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
