# 夜間K: Claudeへの独立検証結果

基準mainコミット: 0d48324。
ブランチ: work/codex-night-k。
基準実装: feat/equipment-unlock-sword / be6af1f（最終fetchでも最新）。
STATUS: READY（報告完了。対象実装は不合格あり、main未統合）。

変更ファイル一覧: 新規tools/qa/run_night_tests.py、night_verify_sword.py、docs/qa/night-verify-20261013.mdと証跡、本報告。既存CLAIMSへの追記以外、既存コード/テスト/マップ未編集。
追加・変更したID・フラグ: なし。

実行コマンド/結果はQA報告参照。専用8783のHTTPサーバーを新規runnerが起動/health確認/終了。5テスト順次4PASS/1FAIL（m18は30ページ期待/実37。FAILS1でもexit0に注意）、独立検証62項目中59PASS/3FAIL。各console/page error0。実行前後の既存test SHA256一致。

修正依頼（今回未適用）:
- indexのObject.assignによるmembers読込とsupport-magic: 後半→キー無し序盤saveでlearnedが残る。同一contextの読込切替で再現。明示した既存learned状態を復元し、保存にない状態を前のセッションから持ち越さない。
- equipmentの移行: 旧Aidan装備の鉄剣/鋼剣を新equipByで拒否する前にバッグへ返す。今はowned0になる。所持数量上限時は捨てず停止/相談。
- m18の37ページ期待値/失敗終了コード、装備テストの常にtrue条件/save条件の優先順位、docsの旧章/ページ数/宝箱名を同期。
- 横画面の祭壇2/5/12/19/30/33ページで文章箱が人物を覆う。縦の祭壇12/30/33は3行。文字切断なし。画像差替えなし。

誓いは一字一句不変、順序・初回習得・武器切替・砦支給・EQUIP解放は基本ケース合格。旧木剣/旧accessory/キー無しstage15+の個別ロードと支給の繰返しは合格。fixture stage18は既存loaderにより15へclampされることを明記。

未検証: 全回帰/全ルート徒歩/Android実機/回避効果（現実装なし）。mainマージなし、ロールバック不要。修正後の再検証と通常の退避目印/no-ff運用はClaude側。force pushなし。
