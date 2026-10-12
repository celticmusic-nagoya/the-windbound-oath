# 夜間J: 全マップ調査

基準mainコミット: 0d48324。基準実装: feat/equipment-unlock-sword / 03d053e。
ブランチ: work/codex-night-j。
STATUS: READY（静的調査完了）。mainマージなし。

変更ファイル一覧: 新規 tools/moss/survey_maps.py、docs/qa/map-survey-20261013.md、同.json、本報告。既存CLAIMSに担当と結果を追記。コード/マップ/テストの既存ファイルは未変更。
追加・変更したID・フラグ: なし。

結果: 29マップを全件読取。地形/props、NPC propsとwalkers、monsters57体とstory symbols3体、採取を含む宝箱、イベント、遷移、高さ、屋内外、立体化/素材候補を優先順に表とJSONへ出力。全マップでheightなし（高さprototypeの別ブランチは対象外）。

実行コマンド: python3 tools/moss/survey_maps.py（Markdown）、同 --json（JSON）、python3 -m py_compile tools/moss/survey_maps.py。出力29件/ユニークID/優先順/JSONの実数一致を検証。外部の小型fixtureで条件付き1px壁の有無を変え、壁なし2spawn到達・壁あり1spawnのみ到達を確認（薄い壁の飛び越しを防止）。

未到達候補: A3は結界閉鎖時dev_sanctuary/tr_a3_hollowlog、開放後は到達。tr_to_deepは無効出口で未到達。rilde_in_house_02 default/from_village (430,452)は足元22×10とcb_09 stool (430.4,436,19.2,14)が重なる。修正せず担当へ共有。

未検証と理由: 静的格子32px/8px辺サンプルで、runtime scatter node・動くNPC・全マップ歩行・イベントゲート・高さ・Androidは未検証。宝箱は100pxへの接近だけで開封可否を保証しない。屋内外/必要素材は命名と地形からの推定。詳細表/限界/接続の未解決一覧はQA報告参照。

王都出口 tr_r1_to_craft / tr_r2_to_east / tr_r2_castle_gate はJSON接続先未解決。受け側JSONが存在しない状態でIDを確定せず、担当の接続待ち。lind_village等の未解決先はruntime hookの場合があるのでJSON不在を即バグ扱いしない。

03d053eからbe6af1fのremote更新を検出。変更はindex/support-magic/装備UIテストのみでマップJSON差分なし。Jの29マップ調査の基準は03d053eを保持。Kは最新で実施する。

戻し方: main未変更、資料/新規ツールだけなのでmainロールバック不要。force pushなし。
