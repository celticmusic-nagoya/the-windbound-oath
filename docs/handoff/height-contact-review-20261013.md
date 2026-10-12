# 高さ対応接触: 設計レビューとテスト設計

基準main: `058cfc8`。ブランチ: `work/codex-standing-orders`。STATUS: READY（設計レビュー、実装なし）。
要約: 異なる階層の誤接触を、NPC/敵/宝箱/イベント/遷移の全経路で防ぐ必要がある。敵の移動にも独立レベルが必要。height無しは既存挙動を完全維持し、本編有効化はAndroid実測と作者判断後。
変更ファイル: 本書とstatus/CLAIMS、別のマップ計画書のみ。ゲーム/マップ/テストは未編集。

## 現状の穴と最小変更箇所（Claudeへの設計依頼）

| 経路 | 現在の判定 / 問題 | 必要な対応 |
|---|---|---|
| moss-forest-runtime interactAt: story symbols | タップ75px・足元距離210px、階層なし | target levelで候補を絞り、startBattleでも再確認。距離値はそのまま |
| 同: treasurePoints | タップ55px・足元距離190px、heightは見ない | 宝箱/草むら双方をlevel-qualifiedに。openTreasureで再確認してからopenedを変更 |
| 同: NPC/interact eventZones | タップshapeから最近傍選択。90px内は即fireEvent、遠方は2D destination→pending | 候補選択→階層付き経路→到着時再検証→fireEventの全段階で同じ対象レベルを保持 |
| updateのpending完了 | 260px内で発火。高さcommitはこの後 | 移動の高さcommit後に到着判定。pendingにmap/generation/id/levelを保持し、target階層・条件を再検証 |
| checkZones: locationCard/trigger/rest/ambience | 足元XYがshape内なら発火/滞在。inside Setはidのみ | XY AND levelをinside条件にし、別階層ではinside登録しない。階層移動で退出/再進入を更新 |
| checkZones: story symbols | touch90px（定義可変）だけでbattleLatch/startBattle | eligibleな階層の敵だけをnearに数える。別階層の敵の存在でlatchが固定されないようにする |
| checkZones: transitions | enabled+XY rectだけ。transitionLatchは全出口のXYで解除 | 源出口レベルを条件に含める。toSpawnのlevelを使用し転送先で再設定。onTransition等story gateは維持 |
| field-monsters think/contact | dP<=touchでengage、探知detectにも階層なし | 同じ接触可能面の時だけ接触。別面は少なくともengage不可。探知/追跡方針は要判断 |
| field-monsters engage遅延 | 遅延中にプレイヤーが別階層へ移動し得る | 遅延終了/実engage callbackで階層・距離・generationを再確認し、無効ならengage解除 |
| mountのmonster ctx.blocked/advance | runtimeのS.forest.blockedはFieldHeightの共有st.level＝プレイヤーのレベル | 敵ごとにlevelを持ちblockedAtLevel/levelAtをその敵で使う。プレイヤーのsetLevelを一時変更して流用しない |
| field-walkers | 純粋描画。会話ゾーンはhomeに固定。プレイヤー56px近接で停止 | home eventとwalkerの所属面を整合。現会話home方式を勝手に動的追従へ変えない。別面なら停止しない案 |
| fireEvent / once・startMonsterBattle | 通知前にfired/latch/敵state等を書き換える箇所あり | 不成立の階層でfired/opened/claim/slain/latch/transitionを消費しない。入口の判定に加えside effect直前もガード |
| 表示座標 / タップ | screenToWorld後に足元から一定y offsetで判定 | 見た目は56px持上げ得る。画面で対象を拾ってid/levelへ変換し、行動距離は未持上げのworld feetで計算する。画面yから所属階を推測しない |

現FieldHeightは階層をactor stateとして持ち、同XYに橋の上/下を重ねられる。deriveやpickLevelはプレイヤー移動/旧save fallback用であり、全NPC/敵の恒常所属面を決めるAPIとして流用すると上下混同が起きる。

## 提案する契約（仮称・未実装）

- height無しmapでは旧処理をそのまま通す。FieldHeight helper呼出・追加状態・追加timer・新経路探索を行わない。旧速度/距離/エンカウント/物語条件は変更しない。
- height有りのみ、static entity/spawn/transitionにoptional `level`、複数面を意図するeventにはoptional `levels` を提案。宣言なしは0扱いを互換既定にできるが、上階walkとのXY重複はlintで未宣言を検出し、作者がレベルを明示する。
- levelは描画z-indexでも地形のunitScaleでもない。距離はworld feet、単位は現在のworld px。1階差の持上げ56pxへ再び2.5を掛けない。
- 敵はspawn levelから独立したruntime levelへ移行。移動後に自分のlevelAtをcommit相当に更新する。共通FieldHeightのplayer levelは変更しない。return先にもhome levelを保持。
- 接触判定を純粋な共通関数へ集約する案: height有りか→面が適合するか→既存XY条件→既存story gate→副作用。実装名や保存項目はClaudeの最小差分で決める。
- 非戦闘NPC/宝箱は、上下でXYが同じでもidを別々に持つ。タップ候補のレベル情報をpendingに保持し、到達後に別対象へ自動差替えしない。
- `MossForest.snapshot()` は現map/x/yのみ、heightStateは別DEV API。高さ有りmapで将来saveへlevelを足すならv30のoptional additive fieldとして提案し、height無しの旧saveを変えない。新階層の導入で旧XYが上下両方に該当する場合、highest deriveを無条件で選ぶと橋上へ化ける。曖昧な旧saveは安全な0階spawnへの復帰を別途判断し、物語/所持品を捨てない。

### 階段・坂の面判定は要判断

`FieldHeight.levelAt` はconnector端zoneでfrom/toへ切り替え、中間では進入したlevelを維持。一方liftは連続補間なので、同じ坂上の2人が近くてもlevel値が異なることがある。単なる `a.level===b.level` だけでは坂の中程の自然な接触まで失う。

初回の安全案: static interact/triggerはconnector中央に配置せず、上下踊り場に属するlevelを明示する。敵/NPCの階層移動を初回はしない（各面の巡回範囲を指定）。坂上の相互接触を必要とする仕様は、同一connector・連続する歩行面・通行可能性を加えた別契約として承認後に扱う。別橋/別connectorのXY重なりを「lift差が小さい」だけで通さない。Z差許容値・跨階探知・階段追跡は未決数値として今回確定しない。

## テスト設計（追加候補、未作成・未実施）

| ID | 条件 / 操作 | 合格条件 |
|---|---|---|
| H-C01 | height無しmapで全接触種、helperを呼ぶとthrowするspy | 旧結果一致、helper呼出0、旧save/速度/距離/フラグ不変 |
| H-C02 | DEV bridge同XYの上下にNPC/宝箱/story symbol/敵を置く、player0→1 | 同じ面の対象だけ選ばれ発火。別面のopened/fired/latch/戦闘0 |
| H-C03 | 同階層の宝箱190境界、symbol touch定義境界、NPC90境界 | <=境界の旧挙動を維持、半径を調整して誤接触を隠さない |
| H-C04 | 遠方NPCへtap→pending中にmap/level/条件を変える | 到着時無効になった対象は会話しない、generation/id不一致も拒否 |
| H-C05 | 発火onceのzone上階を下階で通過→上階で通過→再通過 | 最初は消費0、正面で1回、再通過はonce不変 |
| H-C06 | rest/ambience内のXYを維持し階層切替 | 別面では退出扱い、休息/ambience持越しなし |
| H-C07 | 上階出口のXYを下階で通る、then上階→転送 | 下階は転送0、上階だけ1回、story hook順序維持、toSpawn level復元 |
| H-C08 | enemy engage遅延中にplayerが階を変える/転送 | callback再判定で戦闘0、state/latch回復、後に正面接触可能 |
| H-C09 | enemy0/player1を交互に移動し同一矩形のlevel別blockerへ接近 | 敵は0階の衝突、playerは1階の衝突。共有st.levelの混入0 |
| H-C10 | 0階敵・1階player、巡回/alert/chase/return/boar rush | 接触誤発火0、敵自身のhome/level維持。探知の仕様は採用案別にassert |
| H-C11 | 390×844/844×390、橋上対象/下対象をそれぞれtap | 可視対象のid/levelを選択、表示持上げで当たり領域がずれない |
| H-C12 | 旧map/x/y save、新optional level save、曖昧上下XY | 旧通常map不変、新level復元、曖昧fallbackを明示、v30/所持/進行維持 |
| H-C13 | 戦闘return/敗北/再入場/teleport/DEV jump | player/敵/フォロワーlevel、pending、once、latchの漏れなし |
| H-C14 | 同connector from/toの両方向、境界直前/直後 | 初回は中央に接触物なし。将来跨階接触は採用済み契約通り、別connectorは拒否 |

既存関連回帰候補: m19_height_proto、m15b_slime_symbol、m18_moss_scenario、m55_chest、m6_quest、m8_town_maps/王都gate、m14_hold_move、m55_hz。直列/各test自前server、FAIL行grepで判定。これらは今回未実施（資料のみ、ゲーム変更なし）。既存m13/m4だけ別分類、その他失敗を既知扱いしない。

## 要判断・次の提案

ClaudeがDEV map限定/本編OFFで共通面判定と敵独立levelを実装し、上のテストを新規追加する。static entityのoptionallevel、動く敵の階層移動、跨階探知、connector中央の扱い、saveのoptionallevel/fallbackは設計判断が必要。既存素材差替え・大規模map変更はこのレビューに含めない。

検証分類: 静的レビュー完了。実装/自動回帰/Android実機は未実施。前後コード差分はdocsだけ。main未変更・ロールバック不要。
