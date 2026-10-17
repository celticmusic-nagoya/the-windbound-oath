# BATTLE-UI-INTEGRATION-03 — DEV overlay P1修正

対象branch: `work/codex-battle-ui-integration-02`。基準commit: `fd5a8576a5e18dfc1e5ea903cdf7d210f3d2be13`。

## 原因・修正範囲

既存style.cssには通常戦/ボス戦でdevBtnを隠す規則があったが、後読込battle-polish.cssの`body.developmentMode #devBtn{display:block!important}`が優先され、z-index:10100の浮動ボタンが左操作領域を覆った。

battle-polish.cssの既存表示条件を`body.developmentMode:not(.battleMode)`に限定し、`body.battleMode #devBtn{display:none!important}`を明示。index.htmlは当該CSSのcache-bustだけ変更。領域/レイアウト/操作/戦闘/モーションJavaScriptは変更していない。

CSSは現在のbody状態だけを見るため新たなイベント/タイマー/保存状態なし。戦闘中とRESULT中は隠し、native結果確定/取消でbattleModeが外れると元のdevelopmentMode条件に復帰。非developmentModeでは従来どおり非表示。

## QA導線への影響

浮動DEVメニューの戦闘中タップ入口は依頼仕様どおり使えなくなる。#devPanelとdevJump等のAPIは変更していない。既存テストを検索し、浮動ボタンを戦闘中にクリックする依存はなかった。戦闘COMMAND内のnDevKill/rbDevKillは残し、実タップ→KO→RESULT→継続を新テストで通常/ボス各サイズ検証。フィールドのDEVボタン→メニュー開閉、結果復帰後の同じ操作も検証。会心予約やイベントジャンプを戦闘中に浮動メニューから開く操作は対象外となるが、新たな代替UIは追加していない。

## 新テスト

`tests/battle/ui_dev_overlay.py`は360×800 / 390×844 / 412×915 / 800×360 / 844×390 / 915×412 × 通常/ボスの12シナリオ。collapsed/commands/items/targets/回転/RESULTで対象ボタン内6座標ずつ実touchscreen.tapを送り、pointerdown.target.closest(selector)を判定（計432座標）。測定時はcaptureでイベント伝播を止めて状態を維持し、別途通常の実タップでCOMMAND展開・項目選択・対象cancel・戻る・DEV撃破・RESULT確定・DEVメニュー開閉を実行。矩形だけの検査ではない。

開始後は通常戦のidle canvas、ボスのLou flightが動作中であることも検証。reduced-motionを有効にせず、モーションを止めない。再戦・devJumpによる取消、developmentMode表示クラスのOFF/ONも確認。OFF/ON検査はCSS表示条件の検査で、コンパイル時DEV_MODE定数を切り替えた検査ではない。

修正前の診断ではDEV可視性の失敗と、pointerdownの実target=devBtnを検出。再現が得られた時点で診断をSIGINT終了（exit130）したためbefore.logは部分実行。初回ログを上書きせず保存し、完走合格として数えていない。

## 結果

- 新規DEV overlay: PASS 336 / FAIL 0
- ui01_regions: exit 0 / PASS 38
- ui02_states: exit 0 / PASS 206
- ui03_responsive: exit 0 / PASS 794
- related8: exit 1 / PASS 6 / FAIL 2

新テスト12シナリオ、432probe、24画面でFAIL0/pageerror0。既存UI03は9サイズ・通常/ボス・4ビュー72画面で再確認。関連8本はbg01_background / kb_audit / kb_battle / kb_raider / battle_opening / battle_idle6 / raider_mobile_layout / m16_battle_feel。各終了コードと印字FAILを確認。既存assert/timeoutは変更なし。候補の初回結果はPASS6/FAIL2で保持。開始motionは7項目、待機motionは1項目FAIL。基準fd5a857のindex.html/battle-polish.cssを仮想HTTPサーバから配信し、他の製品ソースが基準と一致することを確認したうえで同じテスト/ブラウザ/条件で独立比較。基準結果: [('tests/battle/battle_opening.py', 1, ['FAIL (1280, 720) normal: both play frames 1..6 once, in order ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])', 'FAIL (1280, 720) normal: frame timing (aidan last frame ~480ms, fiona ~760ms) (561, 807)', 'FAIL (1280, 720) raider: both play frames 1..6 once, in order ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5])', 'FAIL (1280, 720) raider: frame timing (aidan last frame ~480ms, fiona ~760ms) (578, 753)', 'FAIL (844, 390) normal: both play frames 1..6 once, in order ([1, 2, 3, 4], [1, 2, 3, 4, 5, 6])', 'FAIL (844, 390) normal: frame timing (aidan last frame ~480ms, fiona ~760ms) (567, 1156)', 'FAIL (844, 390) normal: input lock ~ longer motion (880ms) then released (1069, False)', 'FAIL (844, 390) raider: both play frames 1..6 once, in order ([1, 2], [1, 2, 3])', 'FAIL (844, 390) raider: frame timing (aidan last frame ~480ms, fiona ~760ms) (565, 1152)', 'FAIL (844, 390) raider: input lock ~ longer motion (880ms) then released (1124, False)', 'FAILS 10']), ('tests/battle/battle_idle6.py', 0, [])]。候補の失敗を再試行成功で置き換えず、元ログを残す。モーション変更は本件対象外。全体QAは条件付きとし、詳細はbaseline-comparison.jsonを参照。

## P2・未実施

390×844・ボス・COMMAND展開・初期scroll位置の「風の一閃」の一部見切れは未修正。元の`docs/qa/battle-ui-integration-02-20261017/390x844-raider-commands.png`を基準fd5a857とバイト照合して保持。p2-original-sha256.jsonに元SHAと再現条件を記録。今回の同サイズの新画像も別フォルダで保存。実機判断待ち。

A2/U-08/P0-D CONDITIONALは従前どおり。A2/U-08固有のLoading/Gate契約は今回の関連8本では検証しておらず、これらの解消は主張しない。今回観測したモーションFAILは上記のとおり別に記録した。Loading/Gate/P0全件回帰やFullも実施していない。Android実機はNOT_RUN。今回は独立QA後のP1修正であり、今回commitへのClaude再レビューは別途必要。

P1のタップ遮断は解消したが、総合QAはCONDITIONAL。開始モーションは基準でも同種FAILを再現（候補7項目・基準10項目）。待機は候補1項目FAIL・基準1回PASSのため、タイミング変動が疑われても新規回帰を除外できず原因未確定とする。再試行で合格扱いにはしない。AndroidでP1の操作確認は可能だが、総合受入/完了判断はこの待機FAILの切り分けとClaude再QA待ち。公開検証URLは未発行、公開設定変更なし、既存サイト上書きなし。公開先の別承認も必要。既存のP2は実機確認で判断する。

## 操作・復元

前回ローカル作業領域が現在環境になかったため、GitHub固定SHAから復元。環境が用意したworkブランチと名前階層が衝突したため別の新規Git領域を作り、既存branchを削除/改名せず同じremote対象branchを継続。元環境のpartial checkoutは指定commitへのdetached状態に整合させた。既存未保存作業は存在しないことを確認済み。ディスク整理やworktree除去はしていない。

既存QA02原本、バックアップ、mainには変更なし。新規QA証拠のみ追加。コミット後の通常pushまで実施しPR/merge/force-push/公開設定変更は行わない。戻す場合はこの修正commitを通常git revertする（main未反映なのでmain rollback不要）。

## 再実行

```sh
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium OUT=/path/to/new-dev-results \
 python3 tests/run_python.py tests/battle/ui_dev_overlay.py
# UI01/02/03も同じrun_python経由、OUTは各回に新規の別領域を指定する。
```

関連8本は既存tests/run_all.shを直列利用。結果の詳細はsummary.json、regression-results.json、related-results.tsv、各log、dev-hit-results.json、ui03-measurements.json、画像24枚。SHA256SUMSは自身以外を網羅。
