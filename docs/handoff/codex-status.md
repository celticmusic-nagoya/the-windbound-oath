# Codex 作業状態 / 再開手順

更新日: 2026-10-13（Asia/Tokyo）。基準main: `058cfc8`。現在ブランチ: `work/codex-standing-orders`。
常設指示: [codex-standing-orders.md](codex-standing-orders.md)。mainへの反映はClaude担当。

## 完了

- 夜間I: 風の舞3案/最小導入点。`work/codex-night-i` / `b57b663`。未決数値は未採用。
- 夜間J: 29マップ調査/新規survey tool。`work/codex-night-j` / `fcd5ab4`。
- 夜間K: 独立検証/旧save/縦横94画像。`work/codex-night-k` / `5890e83`。当時はm18/旧save3ケース失敗。
- Claudeのmain反映を確認: 装備/剣4977df8、高さ基盤998d6f7、夜間フォロー7b2e2a2。前回失敗は修正コミットを確認したが、Codexによる最新mainでの再検証とは区別する。高さは本編全マップOFF。
- 以前のG/H剣案、D/E/F高さ分析は納品済み。詳細はgit履歴とdocs/reports/overnight-20261013.mdを参照。

## 今回完了 / ファイル担当宣言

- 常設運用の初期化: 本statusとCLAIMSへ記録・初回checkpoint `2f4367a` をpush。
- 優先1完了: 高さ対応接触の設計レビュー/14テスト設計。敵移動のplayer-level依存とpending commit順序も記録。新規 `docs/handoff/height-contact-review-20261013.md`。
- 優先2完了: 最新30JSONの高さ候補具体化（旧29からDEV高さmap1件追加、本編28/DEV2）。新規 `docs/qa/map-height-plan-20261013.md`。
- 本ブランチで既存ゲーム/マップ/テスト/採用素材を変更しない。Claudeの実装領域へ直接編集しない。

進行中: なし。優先3の祭壇12/30/33短縮案を追加納品（docs/handoff/altar-shortening-proposal-20261013.md、QA画像/計測JSON）。原文3行→案2行を縦390×844で確認、横844×390は全案1行、誓い/ページ数/prefixを維持。未適用。実装/動的回帰は未実施。検証: 全30JSON parse、ID重複なし、height有りはDEV1件のみ、保護対象のコード差分なし。

## 未着手 / 要判断

- 優先3の文面短縮案は納品済み、Claudeの採用判断/適用後回帰待ち。誓いは逐語固定。
- 優先4: 風の舞の比較/シミュレーション（3案の資料は納品済み、追加シミュレーション未着手、適用不可）。
- 優先5: 剣付きAidan18コマの受入チェックリスト/検品スクリプト。素材受領状況は要確認。
- 優先6: 家02のspawn衝突の追加調査/修正案（Jの静的重なり報告まで完了）。
- 優先7: 全テストrunnerのFAIL検出/個別サーバー管理。夜間専用runnerは納品済み、全件対応は未着手。
- Android実機未測定。高さの本編有効化は承認外。風の舞数値/正式素材交換/非加算save変更/main更新も承認外。

## 再開手順

1. `AGENTS.md`、常設指示、本statusを読む。`git status --short --branch` で手元変更を確認。
2. `git fetch origin '+refs/heads/*:refs/remotes/origin/*'`、`git log -8 --oneline` と `git log -5 --oneline origin/main` を読む。ブランチの成果物と差分を確認して重複作業を避ける。
3. 本ブランチのremote checkpointと本statusの進行中/未着手を確認。mainに本statusがまだ無ければ `git show origin/work/codex-standing-orders:docs/handoff/codex-status.md` で読む。ClaudeのCLAIMS/最近のコミットも読む。同一ファイルを編集する前に本statusへ担当を宣言しpushする。
4. 最新mainが進んでいる場合、履歴をforceで書き換えず、通常mergeまたは新規候補ブランチで対象差分を再確認。
5. テストは関連対象を直列で実行。各テストのサーバーを自分で起動/終了。`^FAIL ` / `^FAILS [1-9]` も確認。既存失敗はm13_elder_attack_text/m4_e2eのみ、その他は新規扱いで原因を報告。
6. 利用制限/中断が見えたら本statusへ完了/進行中/未着手/未コミット懸念を書き、`wip:`コミット＋通常push。ユーザーがClaudeへ停止を共有する（Codexが外部へ自動連絡する手順ではない）。

## 未コミットの懸念

開始時作業ツリーはclean。最終checkpointで全資料をcommit/push。未解決のユーザー変更/秘密情報/起動サーバーなし。各checkpointのcommitはgit logで確認する（自分のcommit SHAを同じcommitの本文へ埋め込まない）。

## Claudeへの統合引継ぎ

本statusと設計2資料は `work/codex-standing-orders` にのみpush。mainへまだ反映しない。Claudeが本statusをmainへ通常統合すると、main checkoutでも常設指示の再開導線が使える。そこまでの再開は上記remote branchから読む。文書のみなのでゲームテストは未実施。main更新はClaude担当でCodexは行わない。

## GitHub上のClaude指示を自律取得する事前承認 (2026-10-13)

ユーザー決定: 「今後はGit hub内にClaudeからの作業指示があれば取得して積極的に取りかかることを事前承認します。」
作業開始/再開/区切りにremote branchesをfetchし、最新mainとClaudeのhandoff/CLAIMS/status/関連branchのgit logを読む。未納品の依頼から優先順に着手し、担当を本statusに宣言する。調査/提案/テスト/work branchでの実装とpushは都度確認不要。既存納品とClaudeの修正/統合を区別し、重複作業を避ける。
承認外は常設指示のまま（main更新、force push、非加算save、未決戦闘数値の確定、採用素材差替え、Android未実測の本編高さON等）。mainへの資料統合はClaude担当。この取得方針はCodexが稼働している時の運用であり、セッション停止中の常時監視を設定したものではない。

## 再開: N→O→P→Q / 追加R (2026-10-13)

main53180f3を取得し、status/常設/第2弾指示と履歴を確認。接触レビュー/L相当/M相当はmain統合済みで再作業しない。
現在: `work/codex-wind-dance-sim`、Nの新規tools/sim/wind_dance_sim.pyとdocs/handoff/wind-dance-sim.md/結果JSONを担当。O/P/Q/Rは未着手。N→O→P→Qの順で区切りpush。Rはfeat/height-contact-levelsの読取レビューのみでdocs/qa/height-contact-impl-review.mdへ指摘。開始時点ではremote R branchが未検出、後続fetchで確認する。
ゲーム/マップ/未決戦闘数値/採用素材/mainは変更しない。新規ツール・テストとdocsの範囲。コミット署名はCodex。

N完了: 再現sim/結果JSON/報告を作成。20,000試行・18条件で解析5SE照合合格、MP/期限/対象self-test合格。固定攻撃列の比較であり実engine勝率未検証。ゲーム数値未適用。次はOの全件runner。
作業中の追加方針（ユーザー事前承認）: 各成果物の完了時にremote指示をfetchし、現在作業が終わったら追加指示へ続けて着手する。現N→O→P→Qの順序を維持しRを後続、未完/新規は本statusへ登録する。

Q着手: work/codex-q / main88ae6c0。P=work/codex-aidan-walk-acceptance/21a0ee9完了（実素材未着）。Qは新規tests/field/house02_spawn.test.js、tools/moss/build_rilde_village.pyの家02だけのsy override、生成物data/maps/rilde_in_house_02.json、docs/qa/rilde-house02-spawn.mdを担当。ユーザーのQ小規模安全修正許可を適用し、入口Y452→472、arrival zoneだけ追随。家具/他map/素材/物語/高さ変更なし。変更前後testを行う。

Q完了: 家02のspawnY452→472を生成元/生成物で小修正、arrival zone追随のみ。旧足元とstoolの重なりを新規Node回帰で再現→修正後合格。その他室/家具/衝突/出口不変。実入室/村への歩行/関連m10合格console0。補助FAILS[]判定は直して再確認。docs/qa/rilde-house02-spawn.md参照。次はR、コード修正せず指摘のみ。
S着手: work/codex-wind-dance-sim2、main e694817。tools/sim/wind_dance_sim.pyと新規wind-dance-mana-sim.md/結果JSONを担当。確定風の舞15pt/3/MP10全体をモデルに使用、魔弾回復2/3/4と命中/実行条件を比較。ゲームコードは変更しない。R dda97df納品済み。

S完了: MP台帳拡張とwind-dance-mana-sim.md/結果JSONを作成。engineは有効対象への暗黙100%命中で回復条件2案同値。暫定3で18フェーズcast3→6、撃破/勝率/戦闘終了MPは算出不可としてnull。自己テスト・JSON再現・既存N20k解析照合合格。ゲーム未編集、数値未適用。進行中なし、新規remote指示を最終fetchで確認する。再開は最新main/本status/branch履歴から。未コミット懸念なし。
P着手: work/codex-aidan-walk-acceptance / 最新main88ae6c0。Nはmain88ae6c0に統合済み、Oはwork/codex-regression-runner / 56f6050で全59（旧main531）納品済み。Rのfeat/height-contact-levels / 5c33f9fの公開とmain5e682e7の統合を確認、P→Q後にレビューする。新規tools/field/check_aidan_walk_assets.py、docs/art/aidan_walk_acceptance.md、template/ダミー検証記録を担当。素材未着・採用素材未変更。

P完了: 検品tool/template/checklistとダミーQAを作成。正常18コマ合格、7負例検出、alpha/footproxy/任意機械反転を検査。原シートは白背景、prepared RGBAを対象。実素材/剣の見た目/ゲーム組込は未実施、採用素材未変更。次はQ→R（R公開5c33f9fを取得済み）。
R着手: work/codex-height-contact-impl-review / main88ae6c0。対象origin/feat/height-contact-levels / 5c33f9f（mainに同コード統合済み）。新規docs/qa/height-contact-impl-review.mdと読取検証logsのみ。コード/マップ/既存testsは変更しない。m22と高さ無し経路・field-monsters/walkers・pending/表示をレビュー。N/O/P/Qは納品済み(Q306ef3a)。


R完了: m22合格、height無しm14/m55/m6の3/3合格。実browserでplayer1/動く敵0の戦闘を再現。NPC goalのlevel欠落をAPIで確認、pending/walkers/試験fixture不足も指摘。コード未編集。docs/qa/height-contact-impl-review.mdと証跡を納品。
今回の納品: N2e9bb42（Claudeがmain88ae6c0へ統合）、O56f6050（旧531対象57合格/既存2/新規0）、P21a0ee9（dummy検品、実素材未受領）、Q306ef3a（家02spawn限定修正、関連検証合格）、Rは本branchの最新commit参照。全件最終main回帰/Androidは未実施。
区切りfetchでmain e694817と新規依頼Sを検出。Rをpush後に指示を読み、専用branchで着手。未コミット懸念なし。

T〜Z着手: work/codex-tz / main49660b7。元worktreeはwork/codex-wind-dance-sim2のまま保持。独立clone /workspace/codex-tzで作業し、テスト期間にbranch/ソース変更を行わない。担当: 指定T bench/報告、U m24、V全回帰証跡、W未適用patch、X protocol、Y m25、Z spawn監査。js/マップ/採用素材は未編集。T→U→V→W→X→Y→Z、区切りpush。

T完了: 正規engine8条件/固定seed、通常全勝・Raider全巻き戻し。実cast/魔弾命中/入力回数を分離、console0。tools/sim/engine_wind_dance_bench.pyと報告/JSONを納品。未決数値/ゲームコード未編集。次U。
U完了: m24/helperと前後証跡。49660b7の5失敗→160beadの2失敗（上階宝箱の縦横視覚tapのみ）。動く敵/ground NPC goal/遅延中階変更は修正後合格。コード/マップ未編集、失敗exit1。次V、最新mainの独立snapshotで全回帰。元worktreeは保持。
T追加検証: main160bead（battleエンジン不変）で8件再実行、結果配列が完全一致。seeded再現性合格、repeat JSON保存。
V進行中: main160bead + 変更無しO runnerをcommitした独立work/codex-v-source。port8791/timeout600、git archive固定snapshot、全件直列。出力docs/qa/full-regression-20261013/、/tmp/v-full.log。テスト中にsource branch/ファイルを変更しない。新規失敗を即時報告し切り分ける。W〜Z未着手（出典調査は待機中に可）。停止時はrunner完了/中断状況とresults.jsonの未実施数を確認して再開。

V完了: main160bead/source313b25a全62本、60合格/main既存2/新規0/未実施0、exit1。全test SHA不変・server終了。docs/qa/full-regression-20261013.mdと全証跡。W着手: stale-tests-fix.patch/説明/未適用の2test案を担当、元tests/js不変。次X→Y→Z。
V追加再実行: 区切りfetchでmain230a29c（altar短縮/walker階層/static lift）が入り、m24もmainに追加された。160beadの全62結果は保存済み。work/codex-v-latestで230a29c+変更無しO runnerを固定し全63本を直列で再実行。/tmp/v-latest.log、docs/qa/full-regression-latest-20261013/。Wは担当宣言/出典確認まで、V再実行後にpatchを作る。元worktree/各source branchをテスト中に切り替えない。

V最新版完了: main230a29c全63=61合格/既存2/新規0/未実施0、Uも全合格。全SHA不変/server終了確認。W着手（巡回3→4、到着page1/7を確認する未適用patchのみ）。利用枠の解除状態は読めないが、現在作業可能。
W完了: Claude8155fddの採用済み差分を参考patchとして保存、再適用不要。main d153d06でm13/m4/m22/m23/m26の5/5合格、旧2失敗解消。V全件は230a29c、d153全件とは区別。X着手: android-perf-protocol.md/既存meter UI確認だけ。Y→Z、追加AA受領（Z後着手）。js/マップ未編集。
X納品: android-perf-protocol.md、PC機能確認（縦横表示/実60秒JSON/clipboard同値/console0）。Android未測定。js/prologue-dev.jsがDEV一覧を再生成しheight proto項目が無いため、スマホ単独の高さ起動はBLOCKED。X指示の新規実装は提案のみを守り、導線追加案を記載。ゲーム未編集。Y着手: m25_walkers_level.py/報告、Z後AA。
Y完了: m25新規、旧160の高さ8失敗→d153で0、height無し互換は両方合格、console0。表示lift/全homeリンク監査は別途。Z着手: tools/qa/check_spawn_feet.py/監査表のみ、実FieldCollisionを使用、マップ修正なし。Z後AA。
