# BB: 剣付きエイダン歩行の受入検品

基準main3208079（93b6193/373cd44の納品素材を含む）。新規m28はFAILS0、console/page error0。manifest24枚=実ファイル、RGBA、足元anchor±1px、体高差4%以内、端の切れ、前後6/左右4/idle4方向を確認。実index.htmlでdevJump('forest')を使い、MossForest.goFeetで移動中の`.forest-aidan:not([hidden])`のsrcが4方向それぞれのwalk名になることを確認した。

既知の警告: 前後歩行は斜め向き。平均alpha bbox幅/idle幅はup0.913、down0.731。これは向きそのものを測る指標ではなく、既知の見た目差の補助値。足元や方向名の自動合格は正面/背面の作画承認を意味しない。PLAYER QAではidle→前後歩行の向き、背中の剣、足運びを確認。

テストfixtureのmap名誤記とDOMのdataset.frame仮定を修正して再実行。実runtimeは表示中imgのsrcを使い、dataset.frameは別actorモジュールだけにある。これらはゲーム不具合ではない。素材/runtime変更なし。詳細metricsは添付log。main未変更、統合後の戻し方は `git revert -m 1 <統合コミット>`。
