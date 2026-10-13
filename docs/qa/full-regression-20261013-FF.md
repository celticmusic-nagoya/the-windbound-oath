# FF: 最新main全回帰（2026-10-13）

基準main `169f197bafd0511475253649c16b6916aa738165`。検証source `fb2bfff68291921a5c5d80c91d0bda8e0f5805ff`（work/codex-ff-source）=開始時最新main+新規m28/m29/m30のみ。O/V runnerを変更せず使用し、git archiveでcommit済みsourceを固定。port8801、各testごとに静的serverを自前起動/停止、直列、timeout600秒。

|分類|件数|
|---|---:|
|合格|75|
|main既存|0|
|新規|0|
|未実施|0|

全75件のtest source hashは実行前後同一、各server停止を確認。従来の台詞期待値2件も合格、既知扱いで隠していない。新PC keyboard/Lou idleのmainテストと、BB/CC/EEの新規3本を含む。BBは直進24+dl/ul12の36枚で実検品、KO6と回避8経路も最新mainで再合格。

完全な件別結果/秒数/失敗行/shaは[results.md](full-regression-20261013-FF/results.md)、JSON/TSV/全log/server log/artifactも同directory。console/page errorは各testの収集範囲で判定し、runnerによる全page共通console監視は追加していない。BB/CC/EEの収集は0件。Chromium cloudの結果でありAndroid実機は未測定。

ゲームコード・採用素材・map本体・mainはCodexから変更していない。AAの未採用cliff overlay/m27は別branchであり、FF main snapshotに混ぜていない。FF後のheight validator追加負/正例とschema再検査は別logに記録する。mainへの統合はClaude担当、統合後の戻し方は `git revert -m 1 <merge commit>`。
