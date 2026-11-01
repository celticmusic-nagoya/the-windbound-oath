# Source findings — 25A

基準 `5ab60c5db833821744d73080f91ffcd559ebf0a4`。ソース確認と実行結果は区別する。製品コードの変更なし。

## シナリオと到達範囲

`index.html`のstoryStageは0家／Fiona、1訓練待ち、2訓練、3断崖、4夕日後、5襲撃、6再会待ち、7北側襲撃、8逃走、9森、10結界／古代石、11ルー、12祭壇／レイダー、13余韻、14砦、15プロローグ終了。`mainQuestData()`と各handler、`js/field/moss-forest-story.js`、`rilde-village.js`を照合した。

主要経路は house→village/training→cliff bench→`cliff_sunset_to_fire`→`returnScene`→burning village、`finishAttackBattle()`の`attackGob1/2`分岐→`attackFiona`→royalKnight/northEscape→escapeScene→A1→A2→A3。森は`PrologueProgress.count()`3勝で封印を解除、Lou intro→hidden wind path→altar→Raider→aftermath→fort→PROLOGUE END。scene名だけの存在を全経路通常プレイ完走の証拠にはしない。

stage15後は`endReturn`→`RildeVillage.afterPrologue()`→砦自由探索。砦酒場のリアム実会話、街道検問の`capital_gate_passed`、王都4外部mapと宿/ギルド、`q_capital_comb`・`q_capital_delivery`がある。現在の実装終点を砦だけに限定するのは誤り。王都後の新chapter本編進行は未接続。

30mapデータ=28production+2DEV、transition63。全mapのID/spawn/event/treasure/遷移はstatic-inventory.jsonに列挙。`rilde_village_01_*`のTBD出口6件は`RildeVillage.exit()`に専用接続hookがあり、未実装出口と数えない。王都`tr_r1_to_craft`、`tr_r2_to_east`、`tr_r2_castle_gate`は明示的接続未実装。runtimeのguardが通知して留まる。森`tr_to_deep`は`enabled:false`かつfuture rootsで閉鎖。これら4境界は将来MISSINGであり、現行プロローグのsoftlockと断定しない。

平和村の風船・迷子猫はlegacyflags保存のテストがあるが、今回2依頼を受注から報告まで実ブラウザ完遂していない。エマのお守りはm6_questで別途実行。砦支給はm20で実行するが、同testは終了前にstage15を代入するためEND→自由探索の全クリック証拠とはしない。

襲撃の全救助・北側battle・河川逃走を、今回の新規NEW GAMEの同じSAVEから最後まで無条件に通せたとは主張しない。既存ブラウザテストはseed/DEV/teleport/HP操作を含み、分割回帰のCOMPLETEは該当条件・対象に限る。連続経路の不足はS03/S07に明示する。

## 戦闘の現在仕様

`js/prologue-combat.js`通常敗北は`enemyRound()`末尾の『態勢を立て直した』でAidan35/Fiona32以上に復帰。一般的GAME OVERがないこと自体をBUGとしない。RaiderはHP0時、ルーの風→1200ms後の`BattleLoading.rematch()`で再戦する。古いm36内に再戦が拒否されるというNOTEが残るが、現行の専用`tests/battle/raider_wipe_rematch.py`と実測を正本にし、歴史コメントだけで現在BUGにしない。

balance数値は変更しない。訓練はHP100/木人180、通常攻撃28/+15TP、一閃42/-30TP、防御+10TP、木人反撃13（防御6）、HP55以下でFiona38回復（index）。レイダーHP1250、phase境界820/400、攻撃21/27/32＋add×3、破砕斬42/48、増援round2/5/8 max4（現行コード／AGENTS）。これはコード値の監査であり、初見勝率・適正難度の実測評価ではない。訓練の実UI行動履歴のみprobeに実測保存し、レイダー通常戦略の分布は未測定。

`index.html`PartyManagerはmaxActive4、6member定義とreserve/squads、加入者全員の100%EXPあり。`FieldTalk`のjoin処理は空枠があればactiveへ追加。リアム加入、装備、保存、保証人は実装済み。一方`js/battle-action-targets.js`のallies、battle party HUD、normalActor/rbActorはAidan/Fiona中心。menuには『正式な編成変更UIは仲間加入に合わせて実装予定』と明記される。4人実戦はPARTIALであり、加入自体をMISSINGとも、確定将来仕様を既存battleの新規BUGとも判定しない。

## 素材・音

保護は21A46＋22A120＋23A29＋Aidan54＋CG10=259。現在使用するFiona修正版へ参照済み、旧原本も正式履歴として保全。中央台帳は1196records（同一sourceが複数recordの場合あり）、277approved_implemented、0approved_not_implemented、179delivered_not_merged、2pending、885approval_unknown、45unreferenced。これらは排他的集合ではない。

会話表情28（Aidan6/Fiona8/Lou6/Emma8）、24表情瞬き、Fiona/Emmaのsmile/relieved4つ静止。ルーsmile/relieved未採用維持。provisionalというフォルダ名・registry内旧metadataは履歴であり、現在の正式採用を否定しない。今回採用状態を変更しない。

`img/battle/motion-manifest.json`複数frame登録: Aidan attack/skill/draw/damage/low_hp/ko、Fiona ready/attack/damage/heal/ko/winddance、Lou damage/blessing/ko、slime/boar attack/damage/ko、goblin/tainted ko、Raider attack/damage/enrage/call/idle。描画／delivery台帳と照合し、未登録motionを全て参照切れとは扱わない。採用済みLou KOに専用失神triggerが不足しても画像を再制作しない。Raider元sheet5件はbranch保管だがmainに派生6frameあり、未使用候補KO dissolve/poweredは未承認のまま。

mapのbgm宣言9IDに対し`js/field/field-bgm.js`のPROFILESはbgm_rilde_day/home/ruinの3つ。unknownIDはplay内でstopとなる。録音mp3/ogg/wavは追跡treeになく、存在しない音源URLの404を推測しない。対応方針不足としてPARTIAL。画像制作を伴わないAUD-01仕様検討へ分離。

## QA基盤の再現可能な問題

1. 原版`node tests/startup_race.test.cjs` FAIL: VMが`html.indexOf('function say(t)')`で抽出するが、現行は`function say(t, portrait)`。-1/空文字を見逃してstubに留まり、dialogueRevisionの観測がずれる。
2. 原版`node tests/continue_restore.test.cjs` FAIL:同setupをimportし、legacy restore用の抽出に`storyPortraitPage`を含めない。初期5ケース後のlegacy stage4で復元falseとなる。実ブラウザはhelperを持つ。製品SAVE破損と短絡しない。
3. `fixture_preload.cjs`はNodeのloaderで**メモリ上のテスト抽出だけ**を補正。`node -r <preload> tests/startup_race.test.cjs`で20PASS、continue_restoreで37PASS。原版・ゲームはディスク不変。これは原因診断であり原版FAILをPASSへ置換しない。
4. 原版`python tests/system/asset_registry_audit.py` FAIL1: 全assetのandroid_statusをUNVERIFIED固定で要求する旧assert。現在はユーザーAndroid採用済みPASSがあり矛盾。build --check、audit_registry、check_asset_refsの実toolは0error。
5. 無条件真: `tests/system/capital_story_test.py:39`の宿舎全回復、`m14_capital_gate.py:28`の騎士字句、`m12_attack_ruin.py:32,48`の風/看板、`m11_road_tavern.py:16,58`の景観/party表示等は`or True`。その項目をPASSの実測根拠にしない。`check(True)`でも直前wait_for_functionが実際の失敗を検出するm4/m36とは区別。

今回は監査のみ。これら3種類のQA基盤BUGを次期backlogへ送り、ゲーム・既存テストを合格化する修正を混入させない。

## 追加probe実測 — 報酬4ケースの製品BUG

本番RildeVillage interact hookをfresh contextで実行（通常連続経路とは隔離）。タンス: potion4→4（期待+1）、壺: gold0→0（期待+3）、風船: potion4→4・balloonDone=true（期待+2）、猫: catDone=true・毒消しitemIdなし・所持数なし（期待+2）。各取得/完了文言は表示された。`updateSubQuest()`はjournal/text更新のみで実給付せず、drawer/pot hookもflag/textのみ。動的canvas/HTTP/Promiseの問題ではない。既存表示と確定報酬に反するため、S24/S25の2分類・4再現ケースをBUG、P6-REWARD-01/P1とする。今回修正しない。

通常NEW GAME→家の出入口を歩行→Fiona実tap→木人6行動で勝利→村南出口→断崖登頂→ベンチ/選択/夕日/帰路→襲撃stage5は実行成功。stage5ではlegacy fieldが表示され、`MossForest.mapId`は非表示となった断崖mapのcacheを返すため、snapshotのmap文字列だけで現在の可視fieldを判断しない。通常経路はここまで、森以降の分割回帰をつなげて全経路完走と偽らない。

通常到達stage5のcaptureでは、本編がMossForestの正式ruin mapからではなく旧DOM worldの文字/CSS図形NPCを使う。rilde-village.jsもstage5〜8をscripted legacy scenesと明記。pixel版ruin mapが存在することと、本編襲撃へ接続済みであることは別。M08/P6-FIELD-01は仮表示／統合不足のPARTIALとし、259正式会話PNGやCGの品質問題にはしない。
