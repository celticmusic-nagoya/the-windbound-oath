# Codex GG〜KK 納品 / 2026-10-13

GG→HH→II→JJ→KKを完了し、各区切りで通常push。基準main31a5f5e、ブランチ `work/codex-gg-kk`。
GGの2指摘を保留し、JJはm31を20回連続合格。KKは折りたたみ+44px以上の常設COMMANDを推奨（未適用）。
Android実機の停止/性能は未測定。main/ゲームコード/採用素材は未変更。

## 納品一覧 / 結果

| 項目 | 報告 | 実行結果 | milestone commit |
|---|---|---|---|
| GG | [keyboard-audit-20261013.md](../qa/keyboard-audit-20261013.md) | 42項目、合格40/失敗2/未実施0、pageerror0 | ac7c313 |
| HH | [lou-field-review-20261013.md](../qa/lou-field-review-20261013.md) | 37項目合格。初回と一時候補自動生成版の最終実行ともFAILS0 | 7a0bf7d（自動生成版2b294fd） |
| II | [lou-idle-real-flow-20261013.md](../qa/lou-idle-real-flow-20261013.md) | 9項目合格。祭壇→入力→敵ターン→被弾、reduce両条件 | fcc1a0f |
| JJ | [test-stability-20261013.md](../qa/test-stability-20261013.md) | m31修正後20連続+m32/m6_inventory各1回、22/22合格 | 83756b5（修正908e168/a5242d8） |
| KK | [command-initial-open-mobile-20261013.md](../qa/command-initial-open-mobile-20261013.md) | 3画面×2戦闘×開閉=12計測、FAILS0。UIは判断待ち | 2b294fd |

## 変更ファイル

新規tests: kb_audit.py / m33_lou_field_review.py / lou_idle_real_flow.py。既存tests変更: m31_aidan_heading.py / m32_lou_follower.py / m6_inventory.py。
新規tools: make_lou_field_frames.py / audit_dialogue_prelude.py / measure_command_mobile.py。
上記5報告と各ログ・JSON・計30画像（GG10/HH6/II2/KK12）、handoff/status/CLAIMS。採用img配下には差分なし。

検証コードHEAD2b294fd、ゲーム基準31a5f5e。 [コード照合JSON](../qa/codex-GG-KK-source-20261013.json) にSHA256を保存。最終commitは本branchのGitHub履歴を参照（自身のhashは同じcommit本文には埋め込めない）。

## 未解決 / 要判断

- GG: 旧宿屋店主#innKeeperにEnterが届かない。合成非repeat Enter2回で祭壇が2ページ進む。後者は実機の物理二重入力を再現したとはしない。ゲームコード修正はClaude担当。FAILS2を隠さず保存。常設runnerの分類では新規発見2、既知main既存分類のm13/m4失敗とは別。Codex変更によるゲーム回帰ではない。
- HH: 縮小PNG6枚2,303,132→93,723bytesの提案。採用していない。演出でFionaが前方へ動くと2.4倍オフセットがルーも前方に置く点は見た目の判断待ち。
- II: PC模擬では持続停止を再現せず。Android実機報告の原因を解決済みとは断定できない。
- JJ: 元のstraight up間欠失敗は修正前3回未再現。準備/停止の待機条件は補強して20連続合格。中間版の別のmap raceは特定・修正済み、失敗ログも保存。
- KK: 縦レイダーでも味方ほぼ100%にpanelが重なる。現在のCOMMANDボタン高さ34pxは44px基準未達。横/小型で初期表示の末尾が切れる。3案比較は提案のみ、採用はユーザー判断。

Android実機・全回帰は今回未実施。過去FF75/75（169f197ゲーム基準）を今回の全回帰結果として扱わない。テストは全て直列、自身のサーバーを起動/終了。

## PLAYER QA / 次の提案

1. 縦/横のCOMMANDと味方の見え方、初期表示で切れる末尾項目のスクロール到達、44pxの操作領域。
2. ルーの演出時追従位置と縮小版の見え方（採用前）。実端末で止まる場合はIIの250msログ/画像失敗/hiddenクラスを照合。
3. GG2指摘の対応範囲をClaudeが判断し、統合後の全回帰を実行。

次の作業: 最終fetchでmain31a5f5e、新規後続指示なし。再開時はcodex-status/最新main/briefsを取得する。X/Y/Zはwork/codex-tzのClaudeレビュー待ちという以前の分担を維持。

## ロールバック

Codexはmainへマージしていないので、現時点のmainに戻す操作は不要。Claudeが統合する場合は事前のrollback branchを通常push→機能単位 `git merge --no-ff`→push前回帰。統合後に戻す場合は `git revert -m 1 <マージコミット>`、通常push。force pushなし。
