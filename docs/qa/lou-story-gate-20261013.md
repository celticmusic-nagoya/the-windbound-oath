# NN ルー合流とfield表示の整合性

基準mainf0fe968 / work/codex-ll-pp。m34_lou_story_gate.pyと本報告/JSON/3画像/ログのみ。

17検査: 合格15 / 失敗2 / 未実施0、pageerror0。通常のpublic story経路では救出前のfield followerを認めず。欠落/型不正loadでstage9に表示する2経路を再現しFAILS2/exit1を保持。

## joinedを書き込む経路（source監査）

| 経路 | 時点 | 表示条件/扱い |
|---|---|---|
| PartyManager初期値 index.html | 新規0 | joined:false、非表示 |
| aftermathScene最後のonclick index.html | Raider後13→14 | trueを書き、演出終了後の屋外で表示 |
| prologue-dev.js devJump | destination index>=18 | 準備用のtrue。DEV専用で通常進行ではない |
| loadGrowthData Object.assign(support) index.html | ロード時 | bool型・stageの整合を検査しない |
| missing supportのload | 同一ページ内 | 前のsupport状態が残る（新しい初期値にならない） |

fieldのlouJoinedはBoolean(support.joined)、屋内はfionaVisible(map)で非表示。storyStageを直接条件にしていない。静的検索では上記以外の通常true書込みを確認しなかった。物語のNPCルーとfield followerは別物で、今回の表示監査は#forestLouを対象とする。

## 時系列

| 経路/時点 | stage | joined | map | 表示 | 想定との差 |
|---|---:|---|---|---|---|
| new-game | 0 | False | rilde_in_aidan | False | なし |
| forest-entry | 9 | False | moss_forest_01_sunlit_path | False | なし |
| corruption-1 | 9 | False | moss_forest_03_ancient_grove | False | なし |
| corruption-2 | 9 | False | moss_forest_03_ancient_grove | False | なし |
| corruption-3 | 9 | False | moss_forest_03_ancient_grove | False | なし |
| lou-intro-ended | 11 | False | moss_forest_03_ancient_grove | False | なし |
| raider | 12 | False | moss_forest_03_ancient_grove | False | なし |
| aftermath-start | 13 | False | moss_forest_03_ancient_grove | False | なし |
| join-committed | 14 | True | moss_forest_03_ancient_grove | False | なし |
| free-roam | 15 | True | fort_dunvall_01_courtyard | True | なし |
| loaded-free-roam | 15 | True | fort_dunvall_01_courtyard | True | なし |
| interior | 15 | True | rilde_in_house_01 | False | なし |
| normal-battle | 15 | True | road_dunvall_capital_01 | False | なし |
| normal-return | 15 | True | road_dunvall_capital_01 | True | なし |
| missing-support-early-load | 9 | True | moss_forest_01_sunlit_path | True | 救出前表示 |
| string-false-early-load | 9 | false | moss_forest_01_sunlit_path | True | 救出前表示 |

DEVジャンプは一切使わず、新規→enterMossForest→3corruptionの実勝利登録→Lou intro→祭壇全ページ→実Raider開始→結果→aftermath→砦→afterPrologueを通した。移動/戦闘を全てプレイした試験ではなく、corruptionはPrologueProgress.defeatで登録し、ボス/通常敵はinstantKillで本来の終了callbackを検査する準備短縮を使う。正常flagがfalseの自然な物語段階で早期表示はない。

合流後はpublic field reentry、ロード→field reentry、屋内、通常戦闘の突入/復帰を確認。stage15ロードが正確な保存mapへ復元されるという主張ではない（MMの保存map制限と区別）。

## 指摘と再現

1. 合流後の同じページで、stage9/prologueを持ちsupport項目のない旧形状をload。joinedが前のtrueを継承しA1で見える。欠落入力の試験であり、完全な正規旧serializerが常にsupportを省くという意味ではない。
2. 同じstage9データにsupport.joined='false'（文字列）を指定。Object.assignが文字列を保持し、Boolean('false')でfield側はtrue。

[early-missing-support.png / early-string-false.png等](lou-story-gate-20261013/) に保存。MMのload指摘がfieldの早期表示へつながる因果を確認した。

提案: load前のboolean/既知ID検証、欠落時の初期値と既存状態を混同しない復元、stageとjoinedの整合性検査。進行を持たないv28のjoin済みsaveは何を復元するか作者判断を必要とする。単純なstage>=13強制をゲームコードに入れていない。

Android実機未測定。修正はClaude担当。次OO、main未統合、将来の戻し方git revert -m 1 <merge>。
