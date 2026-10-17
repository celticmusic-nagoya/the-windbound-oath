# BATTLE-UI-INTEGRATION-02 実装・検証報告

基準main: `746cd1553fadfb06a872805a40585ee7c5b5f30d`。作業ブランチ: `work/codex-battle-ui-integration-02`。

## 実装範囲

- 戦場・ログ・COMMAND・行動一覧・アイテム・対象選択を、通常戦/レイダー戦で同じregion構造に分離。追加敵は戦場内に移動し、敵ID/HP/行動順はそのまま。
- UI-02のcollapsed / commands / items / targets / busyを維持。戦闘開始・次の入力はCOMMANDだけ。アイテム/対象は排他。戻る/キャンセルで直前の画面とフォーカスを復元。世代/ラウンド/入力actorが変わった古いtarget callbackを拒否。
- 旧160ms再展開ループを除去。HUD更新/リサイズはdrawer状態を変更しない。UI-02で収納後450ms待機＋HUD更新も検証。
- 縦は上戦場/下ログと操作、横/PCは左ログと操作/右戦場。領域内スクロール・44px・dvh/セーフエリア・回転時状態維持。trainingBattleField等への旧DOM改名で重複IDを解消。
- BG-01を戦場先頭に維持。data-bg/適用敵/フォールバック/画像/下14%・左右4%の設定は維持。動的sprite配置のみ戦場基準に合わせる。ルーの既存飛行制御・transform・速度は変更しない。
- js/prologue-combat.js / battle-motion / actor-state / opening / presentation / idle-motion / lou-flight / background / target-selector、motion-manifest、BG-01画像の11点を基準mainとバイト照合し不変。SHA-256は同フォルダに保存。

## 既存成果の採用判断

mainとde10677の製品コードは同一（差分はIssue/引継文書と背景前景の納品画像）。旧UI-03のregion/state/responsiveと、index/style/input/target UI/party layoutの必要接続だけを採用。旧環境には書き込んでいない。変更したCSS/JSのcache-bustは20261017ui-integration02へ更新。

参照した測定ブランチは `ci-measure/int02-battle` a3f4bb82ec87953c18a35aac5a3178897159d47d と `ci-measure/int02-p0` a95ce3ab3972fafde52673d5c06e45ff4b0cedb4。これらの全差分は採用していない。

`battle-command-gate.js`はreceiptの発行/確定・独自legal条件・Loading provider契約を持ち、単なるUI状態コンポーネントではない。現行mainにはLoading/adapterがなく、既存の戦闘開始/計算を維持する今回のUI限定統合ではreceipt確定入口への差し替えを採用していない。UIの表示前判定とtarget callback世代判定、既存engine busy/Presentation busyは維持。Loading/adapter/P0-D/manifest同期/モーション変更をUI変更へ混入させない。今後Loadingを統合する場合はGate/adapter/P0-Dをまとまった別工程で独立QAすること。現行ブランチをINT-02全機能の統合完了とみなしてはならない。

KO消滅・敵4枠・後衛前進・新増援仕様は対象外。表示regionへの既存追加敵の移設のみで、スロット機能を追加していない。

## 検証

- ui01: PASS 38 / FAIL 0
- ui02: PASS 206 / FAIL 0
- ui03: PASS 794 / FAIL 0

UI-03は9サイズ×通常/ボス×4ビュー=72枚を新規撮影。戦場/操作の交差0、横スクロール0、主要actor/HUD境界内、44px、排他状態、field寸法不変、選択marker、キャンセル、回転、セーフエリア模擬、文字拡大、pageerror0を確認。指定6サイズ360×800/390×844/412×915/800×360/844×390/915×412を含む。代表8枚と全測定JSONを登録。

関連8本: bg01_background / kb_audit / kb_battle / kb_raider / battle_opening / battle_idle6 / raider_mobile_layout / m16_battle_feel は全てexit0、ログのFAILも0。実際のattack/guard/skill/アイテムcancel/単体auto-target/複数target/勝利/RESULT/連戦/古いcallbackを検証。開始/待機の順序・既存duration許容差は変更していない。Node syntax6ファイル、Pythonテストsyntax、git diff --check合格。

既存4テストの変更は確定仕様に対応: kb系は初期展開から収納へ期待値を変更し、操作前に明示展開。BGテストは新シェルのdisplay:gridを検証。assert削除やtimeout緩和はしていない。UI-03は指定2サイズを追加。

A2のLoading post-begin期待値テストは現行mainにないためNOT_RUN。U-08はINT-02のLoading/adapter世代契約に依存する既知fixture問題で、このbranchのkb_audit/m16はmainの非Loading経路で合格。これをA2/U-08修正完了とは数えない。P0-D CONDITIONALとLou v5 HOLDは変更なし。

FullはNOT_RUN（今回関連8本とUI3本に限定）。Android実機NOT_RUN、タッチはChromiumエミュレーション。Claude独立QAはこのbranchの固定SHAで別途実施待ち。

## 再現コマンド

```sh
# PlaywrightとChromium導入済み環境。各UIテストは独自loopback serverを起動/停止する。
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium TMPDIR=/path/to/writable-temp \
  OUT=/path/to/new-results python3 tests/run_python.py tests/battle/ui03_responsive.py
# ui01_regions.py / ui02_states.pyも同じ形式。テストは直列。
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium TEST_RESULTS_DIR=/path/to/new-related \
  bash tests/run_all.sh tests/battle/bg01_background.py tests/input/kb_audit.py \
  tests/input/kb_battle.py tests/input/kb_raider.py tests/battle/battle_opening.py \
  tests/battle/battle_idle6.py tests/battle/raider_mobile_layout.py tests/moss/m16_battle_feel.py
```

run_all.shのexitだけでなく各logのFAILを確認する。今回システムChromiumを指定して実行。最初のUI01起動はPlaywright同梱ブラウザ未導入で未実行だったが、既存システムChromiumへ実行器だけ変更して38項目を実行・合格。製品やassertを変更して回避したものではない。

## Android実機用の公開準備

静的HTML/CSS/JSなのでビルド工程不要、repository rootをHTTP(S)配信する。GitHub Pages APIは既存サイトのsource=main /、build_type=legacy、html_url=https://celticmusic-nagoya.github.io/the-windbound-oath/ を返す。ただしこのURLはmain用でありUI統合branchの検証URLではない。本環境からのHTTPアクセスはproxy CONNECT 403のため到達性未確認。完成済み検証URLとして案内しない。

既存サイトを上書きせずbranch版をHTTPSで確認するには、専用previewサイト/別Pages repo/preview deploymentの公開先と権限・公開範囲の承認が必要。現状公開設定変更なし・新規URL発行なし。ソースとローカル検証までは準備済み。実機では縦横回転・ブラウザ下部バー・ノッチ・タップ/スクロール・回復/対象cancel・連戦・既存モーションをユーザー確認する。

## 次の判断と戻し方

main変更/PR作成/マージ/公開設定変更なし。Claudeが固定SHAで独立QAした後にPR/main統合の承認を得る。既存mainには未反映なので現在のmainにロールバック操作は不要。専用branchで問題が見つかった場合は修正commitまたは通常のgit revertで戻し、force-pushはしない。将来承認されたmergeでは直前mainのrollback refを確保し、merge commitをgit revert -m 1で戻せる状態にする。
