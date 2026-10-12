# モスの森・納品素材検証

最終統合基準mainコミット: `499f78175f9c643d7b4ad6fbba538ee46ec82e3b`（追加はシナリオ資料のみ、検証済みゲーム/testsと同一）
最終検証基準mainコミット: `35834dd96c049e9c1930b5f0fd18100c9cb91369`
初回検証/座標撮影基準: `ce2b3663b031631c858f922ded8390a89ffd48cf`
ブランチ: `work/codex-moss-delivered-art-verification`
STATUS: READY — 指定8本合格。資料/テスト入力をno-ffでmainへ反映、PLAYER QA待ち。素材本体は既存mergeで反映済み。

## 統合済み状態

着手時点ですでにClaudeが `feat/moss-delivered-art` (`26cb6fc`) をmainへmerge済み。機能mergeは `ce2b3663b031631c858f922ded8390a89ffd48cf`、第一parentは `0372ef604b39205f1a356e6c6b417f44e02ac0b0`。remoteの `rollback/pre-moss-delivered-art` が第一parentに一致することを確認。対象branchとmainのtreeも同一。二重の素材mergeは行わない。

既存機能mergeの変更ファイル: `img/field/moss/art/` の68枚、manifest、`index.html` のcache query、`js/field/forest-loader.js`、`js/field/moss-forest-runtime.js` のopening画像適用、`tests/moss/m6_asset_swap.py`、`tools/moss/check_assets.py`、`tools/moss/install_delivered_art.py`、素材依頼資料。本検証の変更はm15bの退避先fixture、未納品一覧とCLAIMS・この報告・QA記録。最新mainの当たり判定幅、エイダン横歩行6コマ、森の奥地を警告する台詞変更を保持。
追加・変更したID・フラグ: 本検証ではなし。

## テスト（初回と調査）

`tests/run_all.sh` がリポジトリ直下の `python3 -m http.server 8765` を起動/停止し、指定順に1本ずつ実行。sealを含む各プロセスの上限600秒。Playwright 1.62.0 / system Chromium 154、Python 3.12。初回8本は7合格、m15bの `player outruns the slime` が1失敗（gap43）。browserテストのconsole/pageerrorはすべて0、CLIのm9_hero_intakeはブラウザを使用せずFAILS0。

納品前main `0372ef6` のm15bは単独合格（gap655）。納品後 `ce2b366` の同時撮影なし単独再実行は同じ項目で失敗（gap268）。未解決のまま成功扱いにはしない。AI/移動/navigation/A1マップは納品mergeで変更されておらず、外部診断で移動先が `blocked-destination`、goFeet=false、足元が変わらず接触戦闘を開始することを再現。15秒待っても移動しない。徘徊中に取ったランダム位置から計算した座標が障害物内だった。納品前後のA1マップ/移動/navigation/AIは完全同一で、素材mergeが衝突や速度を変えた失敗ではない。m15bのテスト入力だけ修正し、現在のスライム位置から衝突なしの500px直線退避を選択、追跡状態とgoFeet受付を明示確認。元の5秒待機・350px超/戦闘0のassertionを維持する。

新main `35834dd` のFiona台詞が「奥には絶対行くなって」へ変更された一方、m4_e2eの期待値は「近付くなって」のまま（source上で不一致を確認）。m4は初回基準で合格しているが、最新mainではこのassertionが不一致となる。素材mergeによる問題ではない。作業3の指定に従って作者へ期待値1か所の更新可否を確認し、未承認の段階では変更しない。

最終検証: `9dbb274`（main `35834dd` 取り込み済み）で指定順の **8/8合格、失敗0、browser console/pageerror 0**。m15bの5秒後gap701、退避経路・追跡・移動受付も合格。m7/m6の一時manifest変更が復元されたことを確認。sealのprocess期限600秒、実行ログに期限超過なし。関連ブラウザ7本はエラー収集を確認、CLIのhero_intakeはFAILS0でブラウザエラー対象外。

| test | 最終結果 |
|---|---|
| seal_a3.py | 合格 / errors [] |
| m9_env.py | FAILS 0 / console 0 |
| m9_hero.py | FAILS 0 / console 0 |
| m9_hero_intake.py | FAILS 0 / CLI |
| m55_chest.py | 合格 / console 0 |
| m15b_slime_symbol.py | 合格 / console 0 |
| m7_prop_swap.py | 合格 / console 0 |
| m6_asset_swap.py | 合格 / console 0 |

全52本の一括再実行は今回行っておらず、依頼指定8本と任意4本の実行基準を区別している。初回失敗・納品前比較・外部診断・単独修正後・最終8本のログをすべてQA資料に保存し、初回失敗を消していない。

## 見た目

外部 `/tmp/moss_visual_check.py` で指定9座標を撮影。リポジトリのtoolsや画像を変更せず、退避mainの同じ座標も比較。1280×720、PC Chromium。スクリーンショットは `docs/qa/moss-delivered-art-20261012/current/`、比較用は `baseline/`。元PNGをリポジトリ外に保ち、資料用に画素内容を維持するlossless WebPで保存。指定DEVページの結界自体はforest-dev.jsの色付きplaceholderで、本番の納品結界画像を検証できないため、index.htmlのMossForestで別途状態を撮影した。

| map / 座標 | 確認結果 |
|---|---|
| A3 門 (3900,3420) | DEVの結界は色付きplaceholderのまま。本番は4状態へ正しく切り替わるが、石構造/紋様と重なり、正面から閉鎖と紫侵食の違いが読み取りづらい。画像の単体表示では違いを確認。 |
| A3 棘 (4100,2850) | 棘の足元と周囲の石の接続に明確な浮きなし。広場の緑のplaceholderが残る（未納品の古代樹等、以前から存在）。 |
| A3 紋様 (4320,2860) | 紋様の光は透過して地面に乗る。明確な白い矩形縁なし。未納品placeholderが周辺に残る。 |
| A3 小屋 (5600,3780) | 小屋の足元は地面に接地。近くの道の斜線区間で水平の継ぎ目が目立つ。道の区間重なりは以前もあり、新しい高密度テクスチャで目立ちやすい。 |
| A2 橋 (3775,4120) | 横長の橋画像が縦向きの渡河通路に配置され、橋の床が通路/川幅を覆わない。以前は縦長の仮表示だった。向き/寸法のPLAYER QAが必要。 |
| A2 滝 (1200,3560) | 小型の滝画像が導入されたが、茶色の崖と水色の縦長矩形地形は以前のまま残り、接続が不自然。背景の仮形状は以前から存在。 |
| A2 根のアーチ (6206,4360) | 足元が地面に接地し、明確な透過の白縁なし。河川側の背景は簡易地形のまま。 |
| A1 小屋 (5560,1440) | 明確な足元ずれ・白縁・過大なサイズなし。 |
| A1 道標 (1687,5690) | 地面に接地し、矢印を視認できる。明確な白縁なし。 |

ゲーム画像の置換・向き/サイズの調整・地形変更は行っていない。スクリーンショットで確認できる範囲の指摘であり、全ピクセルの境界保証ではない。

## 任意調査（修正なし）

`ce2b366` 基準の `m14_hold_move.py` と `walk_a1.py` は実行時出力あり・合格・console/pageerror 0。Pythonをパイプ/ファイルへ出力すると通常のprintはバッファリングされる。`python3 -u tests/run_python.py <test>` で途中出力を確認できる。run_all.shもこの形で実行し、各結果はlogへ保存して完了時にtest名を出す。walk_a1は経路全体を単一evaluateで歩いてから各区間をprintするため、最初のstatsのあとしばらく無出力となる。なおwalk_a1はerrorsをprintするだけで非ゼロexitを設定していないため、終了codeだけで合否判定しない（今回は `errors []` を確認）。

`m4_e2e.py` も今回合格。従来のタイムアウトは未再現。長距離歩行の各区間は最大120秒、map待機30秒、戦闘開始待機15秒で、どの待機が失敗したかの元logがないため原因の確定はできない。途中のシンボル戦・イベント停止・描画負荷は切り分け候補であり、今回の原因として断定しない。

m8は前回Gで実遷移待機を90秒に修正済み。旧30秒の問題はCPU負荷下で正常歩行が51秒かかることを前回確認済み（G統合報告参照）。今回 `ce2b366` 基準で合格、街道→王都18.70秒。TBD王城出口の30秒待機は「遷移しない」確認の期待どおりであり、タイムアウト失敗ではない。

## PLAYER QA

- A3結界の閉鎖・割れる途中・開放・紫侵食が見分けられるか、開放後に通行できるか。
- A2橋の向きと足場、滝と背景地形の接続。
- A3未納品古代樹の仮表示、道の継ぎ目。
- 宝箱・植生・石の接地とサイズ、スマホでの表示負荷（Android実機未測定）。

## 結界4状態の確認範囲

本番MossForestの画像選択をブラウザ内の隔離fixtureで確認（sealCorrupted hookだけを手動制御し、リポジトリの実装は変更しない）。closedはa3_seal_closed、corruptedはa3_seal_corrupted、openingはa3_seal_openingが適用され、開放1秒後はnode0。console/pageerrorは0。元画像でも閉鎖/紫侵食/中央割れを目視確認。通常の3シンボル撃破→開放/通行はseal_a3と初回m4で別途確認している。割れる途中は既存の1秒fade/blurで短時間表示され、専用コマは1枚なので、動きの読みやすさはPLAYER QA対象。

## ロールバック

この検証の追加mergeは `Merge delivered moss art verification and pending asset list`。そのSHAは完了報告に記載する。追加差分の直前mainを `rollback/pre-moss-delivered-art-verification` と `rollback/before-moss-delivered-art-verification-20261012` に保存する。

今回のテスト修正・資料だけを戻す場合は `git revert -m 1 <追加mergeのSHA>`。素材全体を戻す場合は、素材依頼資料との競合を避けるため追加mergeを先に戻し、その後既存の素材mergeを戻す:

```bash
git revert -m 1 <追加mergeのSHA>
git revert -m 1 ce2b3663b031631c858f922ded8390a89ffd48cf
git push origin main
```

比較用branch `rollback/pre-moss-delivered-art` は `0372ef6`。reset / force pushは使用しない。後続変更がある場合は通常のrevert競合を解決して検証する。
