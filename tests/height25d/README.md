# 2.5D検証ケース（2026-10-14）

ブランチ: `work/codex-night-20261014-x2`。基準main: `aba3d8d`。担当は新規 `tests/height25d/` のみ。X1/X3とは独立。既存のゲーム・map・テスト・run_all.shは編集しない。

## 実行

Python3 + Playwright Chromiumが必要。リポジトリ直下で:

```sh
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium OUT=/tmp/height25d python3 -u tests/height25d/verify.py
```

Chromiumのパスは環境に合わせる。PORT未指定なら自身の静的サーバーを8842で起動/終了。PORT指定時は既存runner側で所有する。各テストを直列実行する。標準出力の `FAIL ` / `FAILS` とexitを確認。結果JSONと3画面の前景スクリーンショットはOUTへ保存。run_all.shには登録しない。

## ケース

| 対象 | 検証方法 | 期待 |
|---|---|---|
| 階段なし登攀 | feet(1800,520),0 → 上1.5秒 | cliffに止まり0維持 |
| 通常移動の落下 | feet(1800,380),1 → 下1.5秒 | 足元を高台内に保ち1維持 |
| 階段 | (1960,580),0 → 上1.7秒 | 1へ |
| 坂 | (1560,270),0 → 右1.6秒 | 1へ |
| 橋上/橋下 | 同XY(1560,900),level0/1 | 別level、同XYを維持 |
| 描画順 | 橋上/下のactor zとdeck440比較 | 下<床<上、橋下は床fade |
| 前景 | 高台(2100,395),1とcanopy470比較 | actorが前景より後ろ |
| runtime復元 | snapshot→別位置→enter(snapshot) | 曖昧な橋下0を維持 |
| 実セーブ/ロード | stage9、saveGrowthData→localStorage v30→loadGrowthData | map/levelを復元（発見事項あり） |
| 高さなし | Aidan家/納屋/A1で鍵入力・元の遷移 | height null / level0 / FieldHeight.create呼出0 |
| 旧save | A1位置+opened、levelキー無し → fromSave | A1/0/宝箱履歴を維持 |
| level2 | DEVレスポンスのみ一時walk2/connector0→2 | 階段2、runtime復元2、崖端から落ちない |
| PC/縦/横 | 1280×720 /390×844 /844×390 | 描画エラーなし、同じ0/1検証 |

level2は現DEVの実データには無い。Playwright routeでDEVのJSONレスポンスにのみ追加するfixtureであり、製品/マップの対応済みという意味ではない。teleport/enterは開始地点を整えるために使い、通行は実Arrowキーで確認。橋の2levelは単一playerの切替による同XYの状態共存で、2player同時描画ではない。

## 発見事項

**H25-01（仕様確認）**: DEVマップの実セーブ読込はA1へ戻る。`MossForest.snapshot()` がlevelを加算して保存するが、`js/field/moss-forest-story.js:178-191` のfromSaveはMAP_IDS=A1〜A3だけをvalidとし、DEVを拒否する。stage9で橋下0をsaveGrowthDataするとv30とlevel0は保存されるが、loadGrowthData後はA1のfrom_cliff_fall（feet2020,5043.6）になる。全3viewportで同じ。DEV限定の仕様制限の可能性があり、新規リグレッションとは断定しない。

再現: DEVを開く→MossForest.enter({map:'dev_height_proto',x:1543,y:858,level:0})→storyStage=9→renderSystemTab('save')→saveGrowthData()→loadGrowthData()→MossForest.mapId確認。公開ロードはPrologueProgress.load→MossForestStory.fromSaveの実経路を通る。ゲーム修正は行わず、この3件はFAILを保持する。

高さ未使用の旧saveは元のfromSave入口を直接検証（過去ユーザーの実データではなく代表fixture）。runtime snapshot→enter復元とは区別する。本編height導入時はMAP_IDSに含まれるマップの曖昧XYでlevelが復元されるか、別途要検証。セーブ形式v30は変更しない。

初回の屋内出口2件はテスト期待値の誤りだった。stage15は `js/field/rilde-village.js:19-21` により村ruinを選択する。実際の遷移は正常なのでpeace→ruinへ期待値を訂正し、初回ログを保存。失敗を隠すためのゲーム変更はない。

## 結果・限界

最終結果: **42項目39合格/3失敗（H25-01のみ）、console/pageerror0**。results.json / run.logに記録。関連既存m19(pc)/m22/m26を2巡直列で照合、ファイルhash不変・結果同一を確認する。m24/全回帰/Android実機は未実施。既存ファイルは一切変更しないため「変更前後」は同じmainの関連回帰2巡の比較。新規テストの追加に伴うゲーム差分はゼロ。

Claudeへ: DEVを本編セーブで復元する必要性、および本編の将来level保存契約の判断をお願いします。高さの本編有効化/実機性能はこのタスクの範囲外。mainへマージしない。

## 完了checkpoint

関連既存テスト2巡 **6/6合格**、各testのSHA256が両巡で一致。m19はpcのみ（既存のVIEWSパラメータ）、m22/m26は元の全ケース。各serverを起動/終了し、printed FAILとexitを照合。`existing/results.json` と6ログが根拠。新規verifyの42件39合格/3失敗・エラー0と合わせて、失敗理由を明記する完了条件を満たした。STATUS: READY（指摘保持、機能修正済みではない）。

追加ファイル: verify.py / README.md / results.json / run.log / run-initial.log / 前景3PNG / existingの結果JSON・6ログ。検証実装コミット `848d845`。最終報告のcommitはブランチ履歴を参照。main未更新なのでロールバック不要。X3へ続ける。

統合時の注意: run_all.shを編集していないが、既存 `tests/run_all.sh:36` / `tools/qa/run_regressions.py:109` はtests配下のPythonを自動列挙する。従って本ブランチを統合して全回帰を実行するとverify.pyも対象となり、H25-01のFAIL3で失敗になる。失敗をskip/xfail等で隠していない。Claudeは統合前にDEVセーブをどの契約で検証するか判断し、修正/テスト契約を確定してから全回帰を実施してください。
