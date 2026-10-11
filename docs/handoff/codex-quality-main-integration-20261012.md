# 依頼G: 承認後のmain統合記録

基準mainコミット: `c4c536aad49bfa6d94ffbf79b951767627ee10ea`（戦闘演出・A1/A2新配置を含む）
統合元ブランチ: `work/codex-quality-approved-20261012` / `26e63667e71ac7549a36c115e22d642bf042c5ae`
mainの機能マージコミット: `390f74aea90e449a50846e93496abc5b7be99632`（`--no-ff`）
ロールバックタグ: `rollback/before-quality-foundation-20261012` → `c4c536aad49bfa6d94ffbf79b951767627ee10ea`
変更ファイル一覧: field-movement、index/DEVのcache query、Gのテスト基盤・素材棚卸し資料、m6_quest待機、m8_town_maps待機/診断、CLAIMS・QA資料。詳細は先行再検証報告に記載。
追加・変更したID・フラグ: なし。
テスト結果: 全52対象に合格結果、最新候補のm6_quest単独10回連続合格。下記の初回失敗と再実行を区別。
未実装・要確認: PLAYER QA、Android実機（未測定）、王都受け側JSON（未作成/TBD）、画像生成（利用上限）。
STATUS: READY — 作者の依頼G承認に基づきmainへ機能単位で統合。PLAYER QA待ち。

## 実装と保持したmain変更

Gは高fps時のframeScale下限の修正、再利用可能な回帰runner・素材棚卸し、テスト/資料基盤。目標移動速度や操作方式は変更しない。m6_questは開始台詞の実表示を待ち、本文をクリックして選択肢への誤クリックを避ける。

最新mainの戦闘演出、ルーの動き、A1/A2敵配置、長押し、onTransition、ストーリー/セーブ、戦闘ルール、Raider、納品済み素材は保持。アプリ差分は `js/field/field-movement.js` とindex/DEV cache queryのみ。画像・map JSON・戦闘コードの変更なし。

## 検証結果

| 実行 | 対象数 | 合格 | 失敗 | 備考 |
|---|---:|---:|---:|---|
| 最新main+Gの全回帰初回 | 52 | 51 | 1 | m8街道→王都の固定30秒待機 |
| CPU負荷模擬の再現診断 | 1 | 1 | 0 | 正常歩行が30秒を超えることを再現 |
| 待機修正後: m8/加入ゲート/新戦闘演出 | 3 | 3 | 0 | 実遷移と操作可能状態を確認 |
| 最終版m8再実行+m6単独10回 | 11 | 11 | 0 | m8期限超過も明示的な失敗とする |

初回の失敗記録は `full-results.tsv` に保存。負荷模擬ではCPU throttle 18倍で約10.21fps、30.04秒時点でも正常歩行中（戦闘なし・リアム加入済み・通行flagあり）、51.03秒で王都に遷移した。これはPC Chromium上の待機診断で、Android実機の測定ではない。初回失敗時の詳細状態は未記録だったが、同じ30秒期限不足を制御条件で再現した。

ゲームには既存のframe-time上限があるため低fpsでは長距離歩行に時間がかかる。m8の実遷移期限を90秒にし、map ID変更だけでなくactive/非busyまで待つ。到達先assertionは維持し、期限超過は失敗・状態を出力。TBD出口は従来の30秒/同一map確認を維持。テレポート、加入条件の迂回、敵抑制、assertion削除、ゲームの速度変更は行っていない。

修正後の全出口確認は2回合格。加入ゲートと新戦闘演出も合格。最新候補でクエストを新しいChromiumで10回連続実行して10/10合格。`resolved-52-results.tsv` は初回51件と修正対象の再実行を統合した52対象の結果で、全回帰を修正後にもう一度52件実行したという意味ではない。ログは末尾空白のみ整理。m6の同名ログは最後の1試行のみ（10試行の終了コードはTSV）。

全検証は `tests/run_all.sh`、Node 24.19.0、Python 3.12.14、Playwright 1.62.0、system Chromium 154.0.8037.57、Pillow 12.3.0、NumPy 2.5.4。mainへのmerge後のtreeは検証済み統合元と同一。画像/マップ/最新戦闘コードの保持を確認。

## 戻し方

main上で次を実行し、関連チェックを確認して通常pushする。

```bash
git revert -m 1 390f74aea90e449a50846e93496abc5b7be99632
git push origin main
```

比較用タグは `rollback/before-quality-foundation-20261012`。Gだけを戻し、直前main `c4c536aad49bfa6d94ffbf79b951767627ee10ea` の戦闘演出・敵配置を維持する。タグを使ったreset/force pushはしない。反映記録は機能mergeに自己SHAを書き込む形にせず、既存CLAIMSの独立した先頭記録とこの別報告に置き、資料によるrevert競合を避ける。資料追加後treeの逆mergeを非破壊に検証済み。競合はなく、アプリ・tests・toolsは直前mainのtreeへ完全一致で戻ることを確認した。

## PLAYER QA

main反映後に、長押し方向変更/離す際の停止、60/120Hz等の移動感、クエスト受諾/辞退/報酬、Raider HUDと納品モーションを確認。

敵の探知距離/速度、ボア予備動作0.6秒・硬直1.4秒の回避、バット吸血60%、スマホ負荷も確認。A2はスライム・ボア・バット各2体の同時配置なので混在負荷をここで測定できる。Android実機は未接続・未測定。素材軽量化やゲーム側の数値調整は今回行っていない。

GitHub Pagesのdeploy完了や実機での公開版動作は、このGit統合検証とは別で未確認。
