# Y: walkerの所属面・home会話・height無し互換

STATUS READY、work/codex-tz。新規tests/moss/m25_walkers_level.pyと証跡のみ。JS/マップ本体未編集。

有効な橋上下同XY1560,900にlevel0/1の実FieldWalkersをmountする。各player配置前に22×10足元のblockedAtLevel=falseをassert。JSON route fixtureだけで、歩行経路は橋内の縦60px。ランダムな初期待機をpublic recordで0へ戻し、同じhomeからupdate(.2)して停止/継続を確認する。脚本/実ゲームのNPC配置は変えない。

- 同XYの同面walkerだけ停止、反対面は移動を継続。
- live recordの所属面とmap宣言を確認、homeの位置は歩行に追従せず元位置のまま。
- 同XYのhome会話zoneへtapし、eligible planeのhookが1回、反対面は0回。onceも確認。
- heightなしの同じfixtureでは宣言levelを無視し、両walkerが近接停止。遠方では両方歩く正例も確認。

旧160bead: **FAILS8/exit1**、全8件はheight面の無視/record欠落、height無し挙動とhookは合格。修正後d153d06: **FAILS0/exit0、console/page error0**。両方とも自前server8795を直列起動/停止。結果JSON/ログはwalkers-level-20261013/。

初回fixtureのroute callbackでSDKが2番目の引数へRequestを渡す問題を修正し、bounded enterと120秒外側timeoutを加えて前後runをやり直した。ゲームの不具合ではない。クリック前はcamera更新を待つ。

未実施/追加設計: 実マップ全walkerとhome zoneのID対応監査、connectorを跨ぐNPC経路、anim=trueの訓練/釣り、縦横の描画/タップ一致、旧セーブ。現在のwalker drawはworldYのみ（top/zIndexの高さliftは今回の停止/会話テストに含めない）。高さの本編ON前に表示面も検証する。main統合はClaude、Codexのmain変更なしでロールバック不要。
