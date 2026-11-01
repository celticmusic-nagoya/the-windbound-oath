# DIRECTIVE-26A — Phase 6 旧QA基盤修復

**修復範囲PASS。P6-QA-01 COMPLETE。製品全体のQAはFAILを維持。**

基準main `2f5312efdfd4f5ad48439dd5bca17bb0b801bffc`（PR99）。[25A監査](DIRECTIVE-25A.md)とその証拠は当時の記録として変更しない。Phase5 COMPLETEと正式採用259PNGを保護。本編・報酬・台詞・戦闘・セーブ形式・素材参照・描画・瞬き・採用台帳は変更なし。

## 修復

- `startup_race`: `function say(t)`固定検索をやめ、関数名に基づく引数非依存の抽出へ。開始宣言、終了境界、`say`/`closeDialogue`が欠けたら即FAIL。VMが実製品関数を実行していることもsourceと照合。既存20ケースのassert/実行を維持。
- `continue_restore`: 本編sceneが使用する実製品`storyPortraitPage`を厳密に抽出・実行。関数がない状態を正常化せず、fixture組立時にFAIL。既存37ケースを維持。
- `asset_registry_audit`: Android全件UNVERIFIED固定assertを、21A/22A/23Aの正式採用台帳と実機合格根拠・manifest/SHAに対応する照合へ置換。中央台帳の195記録はAndroid/QA PASS・APPROVED・原本SHA一致を要求。それ以外1001記録はUNVERIFIEDを要求し、未確認素材の無断PASSを拒否。Aidan/CG等64PNGの保護とAndroid履歴を中央台帳に捏造して追加しない。
- テストの削除・skip・無条件真・製品stubへの置換なし。元のcase filterは変更せず、全14本の本実行では空にして全ケースを走らせた。故障注入子processのみ対象caseに絞るものがある。

## 検出力

[9チェックの結果](evidence/directive-26a/faults/negative-results.json)。厳密抽出契約1件PASSに加え、**故障注入8件すべてが原版子processでexit1**になったことを確認。各失敗の原ログを同ディレクトリに保存。

| 故障 | 検出結果 |
|---|---|
| say宣言欠落 | fixture宣言不在でFAIL |
| dialogue終了境界欠落 | fixture境界不在でFAIL |
| storyPortraitPage欠落 | fixture宣言不在でFAIL |
| 古い起動ナレーションの再発 | 実製品コードをメモリ上で故障させ、会話終了後の上書きでFAIL |
| LOAD適用処理の破壊 | 原版cold CONTINUEの復元assertでFAIL |
| 正式Android PASSをUNVERIFIEDへ改竄 | 台帳との履歴不一致でFAIL |
| 未確認素材を無断PASSへ改竄 | 根拠なし実機確認主張でFAIL |
| Android合格素材のSHA記録を改竄 | 正式台帳SHAとの不一致でFAIL |

注入は専用process内のファイル読み取りだけをメモリ上で変える。製品・台帳・PNGのディスク書換なし。注入済み`INJECTED`印と固有の失敗内容・exit1のすべてを要求し、注入target不在や起動失敗を検出成功に数えない。従来のduplicate ID／MAIN file missingのnegative controlも素材原版内で維持。

## 隔離fixtureのGit履歴

初回の`run_all.sh`内の素材回帰は、git archiveだけのsnapshotにGit履歴がなく、画像導入commit/dateを復元できず鮮度2assertがFAILした。[初回結果](evidence/directive-26a/browser-initial/results.json)を保全し、合格扱いしない。実リポジトリでの原版はPASS。

QA補助runnerにopt-in `--git-history`を追加。archive済みexact HEADに独立したGit index/refを作り、既存のimmutable objectをalternatesで読み取る。元リポジトリのindex/config/remotes/hooksはコピー・書換しない。これで鮮度checkを維持したまま、[履歴付き隔離fixtureで素材原版PASS](evidence/directive-26a/history-fixture/results.json)。defaultのブラウザfixture動作は変えない。

## 回収したQA

- Node原版 **14/14本PASS**。うち修復対象startup **20/20**、continue **37/37**。各原版testSHAの前後・最終一致と全出力を[Node証拠](evidence/directive-26a/node/results.json)に記録。
- 素材原版PASS。鮮度・1196record台帳監査・map/manifest実参照は0errors。Android状態は195 PASS／1001 UNVERIFIEDの既存履歴を維持。
- 既存回帰の最新結果は **9種類中8本PASS／製品監査probe1本FAIL**。save_continue_lifecycle、title_official_layout、m53（本編115ページ）、m45（実画素/瞬き/後片付け）、m16（戦闘）、m49/m51（固定採用SHA）、素材回帰を実施。ブラウザは直列、ソースはcommitted HEADの隔離snapshot。
- 初回9本＋履歴fixture再実行1本＝10実行。初回の履歴不足FAILも証拠に残す。最新8PASSという値に失敗実行を混ぜていない。
- 故障注入 **8/8検出PASS**、厳密抽出契約PASS、runnerの既存`--self-test`PASS。
- [保護証拠](evidence/directive-26a/protection.json): 正式259PNG・製品1456ファイルのbyte不変、素材台帳・参照も変更なし。25Aの固定manifest digest `429afe58311f7fb8d983c90e68cda6bdfc7ca7500b857477593aa4efbdb8b5ef`を使用。

[集計](evidence/directive-26a/summary.json)。初回回帰source `fbafe47064b1d453f46a302073ddac8ebba3ee56`、Git履歴fixture source `f423afe`。後続変更は証拠・文書のみ。Android実機は今回NOT_RUN。

## 製品報酬FAILの維持

同じ未変更の`playable_audit_25a.py`で[実測](evidence/directive-26a/product-probe.json)：

| 対象 | 期待 | 実測 |
|---|---|---|
| 家のタンス | 薬+1 | 4→4、取得表示あり |
| 家の壺 | 3G | 0→0、取得表示あり |
| 風船依頼 | 薬+2 | 4→4、完了flagあり |
| 迷子猫依頼 | 毒消し+2 | item定義なし、完了flag・取得表示あり |

probeのFAILS4とexit1を保持。console/pageerror/HTTP失敗は観測範囲0。26Aの修復結果をこれら未修正の製品不具合と混同せず、製品全体PASSにはしない。次工程は **DIRECTIVE-26B／P6-REWARD-01**。P6-QA-03の`or True`等は今回の対象外として残す。

## 再実行・公開

```bash
node tests/startup_race.test.cjs
node tests/continue_restore.test.cjs
python tests/system/asset_registry_audit.py
QA_OUT=/tmp/26a-faults python tests/system/qa_fixture_negative_controls.py
bash tools/qa/run_all.sh --git-history --out /tmp/26a-history tests/system/asset_registry_audit.py
```

全14本は`tests/*.test.cjs`を直接実行。ブラウザ対象・testSHA・印字FAIL・終了code・server停止はresults.jsonを参照。独立exact-head QA、rollback refのremote読み戻し、最新main/head/競合/必須checkを確認して通常mergeする。Pagesのbuildと公開ファイル/main一致はmerge後に回収し最終報告。公開設定変更なし。
