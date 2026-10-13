# 全回帰結果（O）

source HEAD `d153d06584accf494794dcb466409fc0c715ea24` / main基準 `d153d06584accf494794dcb466409fc0c715ea24`、port 8793、直列、各test自前server、timeout 600秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/moss/m13_elder_attack_text.py | 合格 | 0 | 6.673 | 0 / [] | tests_moss_m13_elder_attack_text.py.log |
| tests/moss/m4_e2e.py | 合格 | 0 | 168.37 | 0 / [] | tests_moss_m4_e2e.py.log |
| tests/moss/m22_height_contacts.py | 合格 | 0 | 35.035 | 0 / [0] | tests_moss_m22_height_contacts.py.log |
| tests/moss/m23_wind_dance_battle.py | 合格 | 0 | 59.739 | 0 / [0] | tests_moss_m23_wind_dance_battle.py.log |
| tests/moss/m26_height_spec_overlay.py | 合格 | 0 | 16.432 | 0 / [0] | tests_moss_m26_height_spec_overlay.py.log |

集計: 合格 5, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
