# 接触レベル対応 実装レビュー（R）

対象: `feat/height-contact-levels` / **5c33f9f**。基準main88ae6c0（runtime/m22は対象branchと同一）。レビューbranch: `work/codex-height-contact-impl-review`。
STATUS: READY（指摘のみ、コード未変更）。
要約: lvOkの静的接触ガードとheight無しの互換は限定検証で合格。動く敵の階層無視を有効な橋上下で再現した。対象levelの経路への受渡し、walker、到着順序、m22の追加検証が必要。

## 指摘1 [P1] 動く敵の別階層接触が残る（実ブラウザで再現）

対象: moss-forest-runtime.js:143–145 / :289、field-monsters.js:75–82 / :150 / :187。

lvOkはS.symbols（story.prologue.symbols）へは適用されるが、FieldMonstersには適用されない。spawnRecはJSONのlevelを保持せず、ctx.playerはx/yだけ、thinkのtouchはXY距離、遅延後のstartMonsterBattleにもlevel guardがない。

**再現:** dev_height_protoの同XY `(1560,900)` で、player=level1、monster定義=level0。blockedAtLevelでこのXYが0/1両方の有効面であることを確認した。runtimeMonsterLevelはnullになり、解凍後に `mossSlime1` の通常戦闘へ入りmonster.state=engaged。pageerror0。測定はブラウザのJSON route fixtureだけで、mapファイルは編集していない。証跡: height-contact-impl-review/moving-monster-evidence.json。

本編28mapはheight無しなので現時点の本編回帰とは区別するが、height ON前には必要。敵の所属levelを保持し、探知/接触/遅延callback/開始直前を面で判定する。敵移動のctx.blocked/advanceもplayerの共有st.levelを参照しているため、接触guardだけでは敵自身の衝突面を直せない。追加testはvalid bridge上下・接触遅延中の階変更・敵移動/return/boar rushの独立levelを含める。

## 指摘2 [P1] NPC/interact対象のlevelを目的地へ渡していない（公開APIで確認）

対象: moss-forest-runtime.js:310–322、field-navigation.js:56–65。

候補をlvOkで選んでも、FieldNavigation.destinationにはXY/blockedしか渡さず、height.pickLevelが「見た目の最上面」を選ぶ。pendingにはzがあるがgoal levelを指定しない。ground NPCを橋外から選ぶと、NPC=0でも橋上の目的地1が選ばれ得る。

公開APIでstart feet(300,1250)/level0/under=null、target feet(1560,900)/declared0、targetは0/1両方freeという条件を確認。destinationの戻りは `{x:1543,y:858,level:1}`。height-contact-impl-review/planner-target-evidence.json参照。会話のdrop/歩行までのend-to-endは未実施なので、結果をそこまで断定しない。

対象id/levelをgoalへ明示し、タップが対象指定か自由移動かで意味を分ける必要がある。別面で見えない対象は候補に含めない設計なら、そのvisibility契約も明示する。追加test: 橋外のground player→橋下NPC/宝箱、逆面NPC、levels:[0,1]の対象、移動到着時に同じid/levelで発火すること。

## 指摘3 [P2] pending発火がheight.commitより先（ソース確認）

対象: moss-forest-runtime.js:469–472。

最終移動後、pendingを消してfireEventし、その後height.commit。fireEventへlvOkが増えたため、connector端で階が変わる最後のtickでは旧h.levelで判定する可能性がある。実際の1tick再現は未実施。移動位置/levelを先に確定し、到着した対象のmap/id/level/条件を再確認してから消費する順序を検討する。

追加test: connector端に近い対象・期限/条件変化・移動中のmap切替・誤面到着後の再タップ。再現にはvalid walk/connectorを使い、setLevelだけの無効状態で代用しない。

## 指摘4 [P2] field-walkersのlevel未対応（ソース確認）

対象: field-walkers.js:23 / :32 / :35–40。

walker recordにlevelなし、描画はworld Yのみ、56px近接停止はplayer snapshotのXYだけ。上階playerが下階walkerの真上に来ても止める。同じ階のNPC会話zoneにはlvOkがあるが、歩行NPCの所属/描画/停止は別経路。

pure presentation・会話はhome固定という現仕様を勝手に変えず、walker/home zoneの面を一致させ、別階層で止めない/表示順を検証する。追加test: sameXY上下walkerの停止有無、home会話zoneとの一致、height無しで従来停止/会話位置が同じ。

## 指摘5 [P2] m22のlevel1 fixtureは歩行不可能な場所（公開APIで確認）

m22:21ではfeet(310,1250)へteleportしsetLevel(1)。DEVのlevel1 walkはbridge/plateauだけなので、`blockedAtLevel(310-17,1250-42,1)===true` を確認した。lvOkだけの単体挙動としては役立つが、有効な橋上/下・移動/階段・接地の統合検証にはならない。

valid feet(1560,900)などの上下同XYを使い、各配置前にblockedAtLevel=falseをassertする。onceはfiredの集合だけでなくhook call回数/報酬/戦闘開始0/1回を確認する。現テストにはNPC/宝箱/草むら/story symbol/動く敵/遷移/rest/ambience/target level/spawnの検証がない。

## 指摘6 [P2] m22はFAILS>0でもexit0、console errorを監視しない

末尾はFAILSをprintするだけでsys.exitなし。旧runtime531をroute overrideして同じm22を実行すると **exit0 / FAILS1** を確認した。standing-ordersのFAIL grepが必要。pageerrorは監視するがconsole error listenerがない。

追加: failsまたはerrsで非0終了、console errorの収集、各case終了後にonce/loot/encounterの副作用をassert。原テストは今回修正していない。

## 指摘7 [P2] 静的entityの表示持上げ/タップ領域・spawn検証が未検証

lvOkは所属面の論理判定で、static props/treasure/symbolの表示やwalkerの持上げを実装していない。表示位置とworld feetの混同を避け、上階物体の可視位置からタップできることを縦390×844/横844×390で確認する追加testが必要。今回画面tapのずれをend-to-endで再現したという指摘ではない。

spawn.levelは追加対応されるが、default spawnの位置/所属面の歩行可能性を検証していない。無効level/未定義levelや上階歩行域外のspawn、explicit位置+level、旧saveの上下曖昧XYを追加testにする。データの不正なlevel文字列等を0へ黙ってdefaultする扱いもschemaで明示する。

## height無し互換 / 検証結果（指摘の根拠）

lvOkはS.forest.heightが無ければtrueで戻り、level/levelsを使わない。追加spawn.level経路もheight有りのbranch内。既存story gate/loot once/半径の数値を変更していない。コード読取と限定testではheight無しの新規失敗を検出していないが、全接触/全mapの不変を証明したとは言わない。

| 実行 | 結果 / 分類 |
|---|---|
| m22 + 旧531 runtime override | 比較の失敗1、exit0（追加機能未実装の対照）。main既存m13/m4の分類には含めない |
| m22 + 対象5c33f9f相当 | 合格、FAILS0、pageerror0。無効level1配置の弱点は上記 |
| 有効橋上player1/ground敵0のbrowser fixture | **別階層戦闘を再現**（指摘1の根拠、pageerror0） |
| public planner/height API | target0でもgoal1、m22の上階配置blockedを確認 |
| m14_hold_move / m55_chest / m6_quest（height無し） | 3/3合格、FAIL行なし・exit0。plain-map-results.jsonに保存。同一testsを88で再実行 |

各testは8787自前serverを直列起動/終了。原testのassert変更なし、URL/Chromiumだけadapter。旧runtimeはGitから/tmpへ読み、ブラウザrouteで差替えて比較し、repoコードを変更していない。logs/results/fixtureをheight-contact-impl-review/に保存。外部スクリプト: /tmp/r_contact_child.py。

変更ファイルは本指摘doc、証跡、status/CLAIMSのみ。未実施: 最終88で全回帰、全接触種、Android、NPC goalの実歩行/会話drop、connector1tickの実再現、原m22のexit改善。コード修正/本編height有効化/main更新を行わない。

## 次の提案 / 要判断

本編height OFFを維持し、ClaudeがDEV fixtureで指摘1/2を先に対応、3/4/7の追加testを揃える。探知の跨階仕様、connector上の面契約、schema/旧save fallbackは作者判断。レビューブランチのmain統合とコード修正はClaude担当。main未変更、ロールバック不要。
