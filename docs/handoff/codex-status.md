# Codex 作業状態 / 再開手順

更新日: 2026-10-13（Asia/Tokyo）。基準main: `058cfc8`。現在ブランチ: `work/codex-standing-orders`。
常設指示: [codex-standing-orders.md](codex-standing-orders.md)。mainへの反映はClaude担当。

## 完了

- 夜間I: 風の舞3案/最小導入点。`work/codex-night-i` / `b57b663`。未決数値は未採用。
- 夜間J: 29マップ調査/新規survey tool。`work/codex-night-j` / `fcd5ab4`。
- 夜間K: 独立検証/旧save/縦横94画像。`work/codex-night-k` / `5890e83`。当時はm18/旧save3ケース失敗。
- Claudeのmain反映を確認: 装備/剣4977df8、高さ基盤998d6f7、夜間フォロー7b2e2a2。前回失敗は修正コミットを確認したが、Codexによる最新mainでの再検証とは区別する。高さは本編全マップOFF。
- 以前のG/H剣案、D/E/F高さ分析は納品済み。詳細はgit履歴とdocs/reports/overnight-20261013.mdを参照。

## 今回完了 / ファイル担当宣言

- 常設運用の初期化: 本statusとCLAIMSへ記録・初回checkpoint `2f4367a` をpush。
- 優先1完了: 高さ対応接触の設計レビュー/14テスト設計。敵移動のplayer-level依存とpending commit順序も記録。新規 `docs/handoff/height-contact-review-20261013.md`。
- 優先2完了: 最新30JSONの高さ候補具体化（旧29からDEV高さmap1件追加、本編28/DEV2）。新規 `docs/qa/map-height-plan-20261013.md`。
- 本ブランチで既存ゲーム/マップ/テスト/採用素材を変更しない。Claudeの実装領域へ直接編集しない。

進行中: 優先3の祭壇12/30/33短縮案（新規docs/handoff/altar-shortening-proposal-20261013.md）。実装/動的回帰は未実施。検証: 全30JSON parse、ID重複なし、height有りはDEV1件のみ、保護対象のコード差分なし。

## 未着手 / 要判断

- 優先3: 祭壇12/30/33の文面短縮案。誓いは逐語固定。
- 優先4: 風の舞の比較/シミュレーション（3案の資料は納品済み、追加シミュレーション未着手、適用不可）。
- 優先5: 剣付きAidan18コマの受入チェックリスト/検品スクリプト。素材受領状況は要確認。
- 優先6: 家02のspawn衝突の追加調査/修正案（Jの静的重なり報告まで完了）。
- 優先7: 全テストrunnerのFAIL検出/個別サーバー管理。夜間専用runnerは納品済み、全件対応は未着手。
- Android実機未測定。高さの本編有効化は承認外。風の舞数値/正式素材交換/非加算save変更/main更新も承認外。

## 再開手順

1. `AGENTS.md`、常設指示、本statusを読む。`git status --short --branch` で手元変更を確認。
2. `git fetch origin '+refs/heads/*:refs/remotes/origin/*'`、`git log -8 --oneline` と `git log -5 --oneline origin/main` を読む。ブランチの成果物と差分を確認して重複作業を避ける。
3. 本ブランチのremote checkpointと本statusの進行中/未着手を確認。mainに本statusがまだ無ければ `git show origin/work/codex-standing-orders:docs/handoff/codex-status.md` で読む。ClaudeのCLAIMS/最近のコミットも読む。同一ファイルを編集する前に本statusへ担当を宣言しpushする。
4. 最新mainが進んでいる場合、履歴をforceで書き換えず、通常mergeまたは新規候補ブランチで対象差分を再確認。
5. テストは関連対象を直列で実行。各テストのサーバーを自分で起動/終了。`^FAIL ` / `^FAILS [1-9]` も確認。既存失敗はm13_elder_attack_text/m4_e2eのみ、その他は新規扱いで原因を報告。
6. 利用制限/中断が見えたら本statusへ完了/進行中/未着手/未コミット懸念を書き、`wip:`コミット＋通常push。ユーザーがClaudeへ停止を共有する（Codexが外部へ自動連絡する手順ではない）。

## 未コミットの懸念

開始時作業ツリーはclean。最終checkpointで全資料をcommit/push。未解決のユーザー変更/秘密情報/起動サーバーなし。各checkpointのcommitはgit logで確認する（自分のcommit SHAを同じcommitの本文へ埋め込まない）。

## Claudeへの統合引継ぎ

本statusと設計2資料は `work/codex-standing-orders` にのみpush。mainへまだ反映しない。Claudeが本statusをmainへ通常統合すると、main checkoutでも常設指示の再開導線が使える。そこまでの再開は上記remote branchから読む。文書のみなのでゲームテストは未実施。main更新はClaude担当でCodexは行わない。

## GitHub上のClaude指示を自律取得する事前承認 (2026-10-13)

ユーザー決定: 「今後はGit hub内にClaudeからの作業指示があれば取得して積極的に取りかかることを事前承認します。」
作業開始/再開/区切りにremote branchesをfetchし、最新mainとClaudeのhandoff/CLAIMS/status/関連branchのgit logを読む。未納品の依頼から優先順に着手し、担当を本statusに宣言する。調査/提案/テスト/work branchでの実装とpushは都度確認不要。既存納品とClaudeの修正/統合を区別し、重複作業を避ける。
承認外は常設指示のまま（main更新、force push、非加算save、未決戦闘数値の確定、採用素材差替え、Android未実測の本編高さON等）。mainへの資料統合はClaude担当。この取得方針はCodexが稼働している時の運用であり、セッション停止中の常時監視を設定したものではない。
