# 全回帰結果（O）

source HEAD `4532bc7369bba47bf230d7acaba01ee471542a0c` / main基準 `deadf3da88c416cea420905ef4dbeb7a12893015`、port 8835、直列、各test自前server、timeout 180秒。

合格 / main既存 / 新規 / 未実施の分類。main既存はm13/m4の既知文言失敗だけ（別原因/timeoutは新規）。失敗を許容してexit0にはしない。

| テスト | 分類 | exit | 秒 | FAIL行数 / FAILS | ログ |
|---|---|---|---|---|---|
| tests/field/m0.test.js | 合格 | 0 | 1.032 | 0 / [] | tests_field_m0.test.js.log |
| tests/field/frame_clock.test.js | 合格 | 0 | 0.17 | 0 / [] | tests_field_frame_clock.test.js.log |
| tests/field/talk_conditions.test.js | 合格 | 0 | 0.138 | 0 / [] | tests_field_talk_conditions.test.js.log |
| tests/input/kb_field.py | 合格 | 0 | 13.621 | 0 / [0] | tests_input_kb_field.py.log |
| tests/input/kb_menu.py | 合格 | 0 | 12.191 | 0 / [0] | tests_input_kb_menu.py.log |
| tests/moss/m31_aidan_heading.py | 合格 | 0 | 18.038 | 0 / [0] | tests_moss_m31_aidan_heading.py.log |
| tests/moss/m32_lou_follower.py | 合格 | 0 | 8.305 | 0 / [0] | tests_moss_m32_lou_follower.py.log |

集計: 合格 7, main既存 0, 新規 0, 未実施 0。

原テストのassert/待機は変更せず、URL port/Chromium実行ファイル/出力先だけ環境adapterで指定。git archiveのsnapshot内で一時素材・manifestを変更するtestもあり、元checkoutの素材/追跡ファイルを変更しない。benchmarkのsnapshot内には.gitがなく、個別benchmarkのgit SHAはnullになり得る。source HEADとtest SHA256は本結果JSONが保持する。
