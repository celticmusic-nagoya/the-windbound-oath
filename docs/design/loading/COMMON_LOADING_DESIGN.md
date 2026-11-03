# 共通 Loading システム設計(BL-01 戦闘開始 / ML-01 マップ移動) — 設計案

STATUS: **DESIGN PROPOSAL — 実装は未承認。** 作者が採用したのは「戦闘開始とマップ移動の両方に共通 Loading を導入する」という方向性のみ(2026-10-22 指示書)。以下の具体仕様は `PROPOSED`。
基準: `main` = `e8ecb5dceea3513bbc22028dcff9365b6718d20c`、ブランチ `design/common-loading-bl01-ml01-20261022`。正典 v5.0・`AGENTS.md`・`AI_HANDOFF_PROTOCOL` v1 が優先し、本書は何も許可しない。製品コード・素材・演出の変更なし。
測定は Claude 環境(2 CPU、headless Chromium、ローカル静的サーバ)。**Android 実機・実ネットワーク(GitHub Pages / モバイル回線)は `NOT_RUN`**。ローカルは遅延ゼロなので、実機の待ち時間はここより長い。
Fiona 待機 v3 の 8.7 秒停止(FIX2)は **未確定のまま**。Loading が初回画像表示を安定させても、それが解消したとは扱わない。

## 1. 既存処理の調査(確認済み事実)
| 領域 | 現状(ファイル / 関数) | 備考 |
|---|---|---|
| 戦闘開始 | `index.html` `startAttackBattle()`(784行〜)/ `startRaiderBattle()`(1295行〜)。`#attackBattle` / `#raiderBattle` を**即座に display** し、`BattleBackground.applyForEnemy` → `BattleActorState.begin` → `PrologueCombat.begin*` → `BattleOpening.play` | **待機ゲートなし**。同期コスト 49 ms(負荷下 357 ms) |
| 戦闘素材の取得 | 背景は `battle-background.js` が CSS 背景 + `Image` probe(失敗時のみ解除)。多コマ(`motion-manifest.json`)は `BattleMotion.load()` が**起動時に全 preload**(`Image()`+`decode()`、`cache` Map、解放なし)。単発 still は `BattleActorState.paint` の `img.src` 代入で**初回使用時に遅延ロード** | 初回戦闘は開始後 約 3.1 秒(ローカル、負荷下 4.4 秒)で 22 件 / 約 10 MB が流れ込む(`baseline_*.json`) |
| 戦闘開始演出 | `battle-opening.js` `BattleOpening.play()` が `BattleMotion.has/info` の `CASTS` を再生し、`BattlePresentation.hold(ms)` で入力ロック(`battlePresentationBusy`) | 画像が未準備でも再生は始まる |
| 戦闘終了 | 各戦闘関数内で `display:none`、`BattleActorState`/`PrologueCombat` の世代(`generation`)で非同期をキャンセル | 世代トークンは遷移制御の既存手本 |
| マップ移動 | `moss-forest-runtime.js` `enter()`(239行〜)/`transitionTo()`(291行)。流れ: `S.busy=true` → `loadMap()`(fetch、`cache` Map) → **フェードアウト 0.35 s** → `ForestLoader.prepare(map, spawn)` → `unmount/mount` → フェードイン 0.35 s → `S.busy=false` | **フェード=既存の遷移演出**。進捗表示・Loading 画面はない |
| 画像取得・decode | `forest-loader.js` `img()`+`decodeAll(list,batch,tries)`(バッチ・最大 3〜4 回のリトライ)、`prepare()` は**最初の画面付近(半径 1100)だけ待ち、最大 3.5 秒でタイムアウト**、残りは近い順にバックグラウンド(`warm` Set)。`loadAssets()` は地面・レイヤ・エンティティを eager | **既に「必須=近傍、任意=遠方」の二段構え**がある。共通 Loading はこれを置き換えず利用する |
| 起動時イベント | マップ JSON の `spawns/zones/events`、`hooks.onEnter`、`MossForestStory`(`enterMap`、`WORLD_MAPS`、`fromSave`、`enterAt`) | 物語ゲートは `hooks.onTransition` が先に判定 |
| NPC・当たり判定 | `ForestLoader.collision()`/`mount()` が map ごとに生成、`unmount()` で `destroy()` | マップ切替時に必ず作り直し |
| セーブ・ロード | `MossForestStory.fromSave/openedFromSave`、`restoreState`/`snapshot`。形式 v30(**追加のみ可**) | Loading は**セーブに状態を持ち込まない**(一時 UI のみ) |
| 村・町・建物 | `rilde-village.js` → `MossForestStory.enterMap(...)` に集約。マップ JSON は 30 本弱(`data/maps` 524 KB) | 経路が `enter()` に一本化されているのは好都合 |
| メモリ | `ForestLoader.art.images`・`warm`・`runtime cache`(map JSON)・`BattleMotion.cache` は**いずれも解放しない**。`img/field` 224 MB、`img/battle` 297 MB(ファイル総量) | モバイルでの上限・解放方針は未実装 |
| 既存の欠陥(今回の測定で確認) | `enter()` に try/catch がない。存在しない map を指定すると `loadMap` が reject し、**`S.busy=true / S.active=false` のまま復帰しない**(フェードも途中で止まる。`tools/qa/loading_failpath_probe.py`) | 遷移失敗時に「元のマップ・プレイヤー状態を維持」できていない = ML-01 の設計上の最優先要件。**製品修正は未承認** |

### 測定ベースライン(`tools/qa/loading_baseline_probe.py`、`baseline_noload.json` / `baseline_load.json`)
| 条件 | A1(初回) | A1→A2 | A2→A3 | A3→A2(再訪) | 戦闘 1 回目(開始後 4 秒) |
|---|---|---|---|---|---|
| 無負荷 | 991 ms・39 req・1.8 MB | 1038 ms・18 req | 975 ms・20 req・3.5 MB | 951 ms・18 req | 同期 49 ms / 22 req・10.3 MB・完了まで 3.1 s |
| CPU 競合 2+CPU×4 | 2409 ms | 2039 ms | 1614 ms | 1991 ms・**0 req** | 同期 357 ms / 15 req・9.9 MB・完了まで 4.4 s |
読み取り: ①移動時間の大半(約 740 ms)は固定フェード。画像待ちは残りの 200〜300 ms。②再訪(A3→A2)はリクエストが 0 件(負荷下)〜18 件(無負荷、HTTP キャッシュの状態で変わる)でも所要時間はほぼ同じ = 固定フェードと描画処理が支配的。③戦闘は**画面が先に出て、素材が後から流れ込む**。

## 2. 共通アーキテクチャ案(`PROPOSED`)
**原則**: 新しい取得経路は作らない。既存の `ForestLoader.decodeAll/prepare`(リトライ・タイムアウト付き)と `BattleMotion` の preload キャッシュを**呼び出す薄い制御層**にする。
```
LoadingController(1 つ。window.Loading 相当)
  request({kind:'battle'|'map', id, required:[urls], optional:[urls], timeoutMs, onProgress})  → Promise<{ok, missing[], ms}>
  ├ AssetPlanner      : kind/id → required / optional の一覧を返す(戦闘=パーティ+敵+背景+開始演出、map=近傍 prop+ground+spawn 周辺)
  ├ AssetPool         : url → {Image, state: pending|ready|failed, bytes, lastUsed, pin}(既存 Map を包む。decode 完了で ready)
  ├ TransitionGate    : 遷移トークン(世代)。実行中の request があれば後続を無視 or キューし、二重遷移を防ぐ(PrologueCombat.generation と同じ考え方)
  └ LoadingView       : 軽量オーバーレイ(DOM 1 枚、CSS のみ。画像 0 でも成立)
```
**遷移の制御**: `enter()` は現在 `S.busy` の旗だけ。LoadingController を挟み、(1) トークン発行 → (2) required の decode 待ち(タイムアウトで打ち切り=今の 3.5 s と同方針) → (3) 成功: 従来の `unmount/mount` → (4) 失敗/タイムアウト: **元の map・プレイヤー座標・`S.busy/S.active` に戻して**ユーザーへ通知。`unmount` は新 map の準備が成功してから呼ぶ(現状は先に呼ぶ構造のため、順序の見直しが必要)。
**進捗率**: required の「decode 完了数 / 総数」だけを根拠にする(バイト数は `encodedBodySize` が取れる範囲)。疑似パーセントは出さない。required が 0 件(全部 warm)なら**Loading 画面を出さず**短いフェードのみ。
**固定待機の排除**: 現状の 0.35 s フェードは画像待ちと**並行**に走らせ、画像が既に ready ならフェード時間だけで切替える(再訪 951 ms の大半は固定フェードなので、フェードを 0.2〜0.35 s に保ったまま、待ちを増やさない)。フェード長は演出仕様(作者承認事項)なので変えない前提。
**軽量性**: LoadingView は CSS アニメーション(transform/opacity のみ)・テキスト・任意の 1 枚 CG。decode 中にメインスレッドを塞ぐ処理を載せない。

## 3. 画面遷移フロー(案)
**マップ移動 (ML-01)**
```
入力(出口に接触/イベント)→ story gate(hooks.onTransition)→ TransitionGate.acquire()
 → LoadingController.request(map, required=近傍+spawn周辺, optional=遠方)
     ├ 全 ready ─────────────→ 短いフェードのみ(既存 fade out/in)
     ├ 未準備あり(≤ 閾値、例 300 ms)→ フェードアウト中に待つ → 既存フェード
     ├ 未準備が閾値超 ───────→ LoadingView 表示(進捗=実数)→ ready で解除
     └ 失敗/タイムアウト ────→ 元 map を維持し toast「移動できなかった」+ 再試行可(busy/active を必ず復元)
 → mount → フェードイン → optional は idle でバックグラウンド(既存 prepare の far と同じ)
```
**戦闘開始 (BL-01)**
```
遭遇確定(startBattle の呼び出し側)→ TransitionGate.acquire()
 → request(battle, required=背景+参加者の idle/entry+開始演出の frames, optional=初回に使う可能性が高い単発 still)
     ├ 全 ready(2 戦目以降・先読み済み)→ 従来どおり即開始(Loading なし)
     └ 未ready(初回)→ 戦闘画面は出さず LoadingView(短い・進捗実数)→ ready → 戦闘開始(BattleOpening)
 失敗 → 必須が欠けても「開始する」(今の挙動=静止画/空欄フォールバック)を既定にし、戦闘不能にしない。ログのみ。
```
フィールド上の遭遇は `S.battleLatch` / `S.busy` で二重発火を抑えている。TransitionGate はその上位互換(戦闘と map 移動の相互排他)。

## 4. 必須素材 / 任意素材の分類(案)
| 種別 | 必須(待つ) | 任意(待たない・先読み) |
|---|---|---|
| 戦闘 | 戦闘背景 1 枚、参加キャラの idle 全コマ(Aidan 6 / Fiona v3 の MASTER+eye overlay)、敵の idle、`BattleOpening` の `CASTS` が使う frames | **単発 still の初回使用分**: `lou_support_heal.png` / `lou_support_charge.png` / `fiona_skill_charge.png`(各 PNG 約 3.2〜3.5 MB、デコード後 約 6.3 MB)。`fiona_skill_heal` は既存先読み対象 |
| マップ | ground テクスチャ・layer・entity(`loadAssets()` で eager)、spawn 半径 1100 の prop 画像(最大 60 枚) | 遠方 prop(既存のバックグラウンド)、隣接 map の JSON と ground(下記 5) |
| 演出 | なし(CG が無くても成立) | 地域紹介 CG・Tips(第 6 節) |
単発 still は**必須にしない**: Lou heal の未準備は A/B で 28/32 → 0/32(Claude 環境の測定・製品未実装・Codex 独立 QA の PASS ではない)。先読みの所要は負荷下 0.4〜3.1 秒 / long task 最大 189 ms なので、**必須に入れると戦闘開始が最大 3 秒伸びる**。任意として戦闘開始直後に非同期で流す(既存 `Image()+decode()`、`cache`、失敗時は従来の遅延ロード)。manifest の `preloadStills` で宣言する案(`fiona-v3-fix3/DESIGN_PROPOSALS.md` 第 1 節)と同じで、BL-01 の AssetPlanner が読む。

## 5. 先読み・キャッシュ・メモリ管理(案)
- **近隣マップの先読み**: 現在 map の出口 `transitions[].toMap` だけを対象に、map JSON(数十 KB)と ground を idle で先読み。prop 画像は先読みしない(必要になってから required)。同時に保持する先読み対象は**最大 1〜2 map**。
- **解放方針**: `AssetPool` に LRU + `pin`(現在 map・現在戦闘は pin)。目標は**デコード済み画像の合計バイト**の上限(PC / モバイルで別値。モバイル上限は実機測定が前提のため `UNKNOWN`)。上限超過時は最も古い非 pin から `art.images.delete` + 参照を落とす(ブラウザが再デコードできる)。**現行は解放ゼロ**なので、まず「計測だけ」入れて挙動を見る段階が妥当。
- **既存キャッシュとの整合**: `BattleMotion.cache`(多コマ、起動時 preload、解放なし)は温存。戦闘用の多コマを起動時から全保持しているので、モバイルのメモリ負担は**既に大きい可能性**がある(`UNKNOWN`、実機測定が必要)。Loading の導入はこれを悪化させない設計(新規保持は単発 still 3 枚 ≈ 19 MB だけ)。
- **二重取得の防止**: `AssetPool` が url で in-flight を共有。同じ画像を `ForestLoader` と `BattleMotion` が別々に `new Image()` している箇所は統合の候補(別 PR)。
- **セーブ**: 一切持たない。

## 6. 地域紹介 CG・Tips の UI 案(`PROPOSED`・正式採用は作者確認)
- LoadingView は**テキスト + 任意の 1 枚 CG**。CG は required に入れず、**ready なら表示・未準備なら出さない**(待たない)。Loading が 300 ms 以内に終わる場合は CG も Tips も出さずフェードのみ(固定の見せ時間を作らない)。
- Tips/紹介文は JSON(`data/loading-tips.json` 案)で map id・戦闘種別に紐づけ、複数ある場合はローテーション。**未確定設定は `PROPOSED` と付けて内部資料に留め、ゲーム内には出さない**。出す文は正典 v5.0・追補と照合し(非公開 lore の全文はコピーしない)、早期ゲームで主人公が知らない情報(ネタバレ)を含めない(`AGENTS.md` §0)。
- レイアウト: 縦持ち = 画面下 1/3 にテキスト、上に CG;横持ち = 左 CG・右テキスト。`env(safe-area-inset-*)` を考慮、`prefers-reduced-motion` ではアニメ無し。
- CG の新規制作・採用は**別途作者確認**。軽量化: 最大辺 1024 px 程度・WebP/PNG 圧縮・1 枚 200 KB 目安(仮、実測で決定)。

## 7. 段階的な実装計画(各段階で独立 QA、いずれも**作者承認後**)
| 段階 | 内容 | 製品コード | 検証 |
|---|---|---|---|
| S0 | 本設計のレビュー(Codex)と作者承認 | なし | 設計レビュー |
| S1 | **計測だけ**: 戦闘開始・map 移動の `performance.mark`/Resource Timing を DEV 限定で収集 | DEV のみ | 実機でベースライン(Android) |
| S2 | ML-01 の**失敗時復帰**(`enter()` の try/catch、busy/active 復元、unmount の順序見直し) | あり(欠陥修正) | 既存フィールド回帰 + 失敗注入テスト |
| S3 | 単発 still の先読み(`preloadStills`、3 枚) | あり(小) | Lou heal A/B の再測定(3 枚のみ)、`ally_motion_p3` 通常/競合 |
| S4 | LoadingController 骨格(TransitionGate + AssetPool、Loading 画面なし。挙動は現状と同じ) | あり | 全回帰(挙動不変の確認) |
| S5 | ML-01: required の待機 + LoadingView(300 ms 閾値) | あり | 初回/再訪/遅延/失敗 |
| S6 | BL-01: 初回戦闘の required 待機 | あり | 通常戦/ボス戦、負荷、Fiona soak(8.7 秒とは別評価) |
| S7 | 近隣 map 先読み + LRU 解放 | あり | モバイル実機メモリ |
| S8 | 地域紹介 CG・Tips | あり + 素材 | 作者の素材承認後 |
各段階を別 PR・別固定 SHA・別 rollback 参照とし、Fiona FIX3・PR #46 と混在させない。

## 8. 性能検証・回帰テスト計画
| 軸 | 比較 | 手段 |
|---|---|---|
| キャッシュ | 初回 / 再訪問 | Playwright 新規 context vs 同一 context、Resource Timing |
| CPU | 無負荷 / 競合 2〜4 本 / CDP throttle | 既存プローブと同じ |
| 端末 | PC / **Android 実機(NOT_RUN)** | 実機は作者または Codex、`performance.memory`・Chrome DevTools |
| 戦闘 | 通常戦 / ボス(Raider) | `startAttackBattle` / `startRaiderBattle` |
| マップ | 初回移動 / 連続移動(A1→A2→A3→A2 を連打、遷移中の再入力) | `loading_baseline_probe.py` を拡張 |
| 通信 | 通常 / 遅延 / 失敗 | CDP `Network.emulateNetworkConditions`、route で 404/abort 注入 |
| 画像 | decode 成功 / 失敗 | route で壊れた PNG |
| メモリ | 使用量 / 解放 | `performance.memory`(JS ヒープのみ)+ CDP `Memory.getDOMCounters`;デコード画像は計測困難 → 実機 |
| 描画 | rAF 停止 / 最大描画間隔 | Fiona v3 の W/T/R/D 独立時計 + `host_sampler`(FIX3 のツール) |
既存回帰: `fiona_idle_v3`(短縮 + 320 s soak)、`battle_idle6`、`arena_motion_test`、`ally_motion_p3`、フィールド系(m33b など)、`m36_continue_cold_restore`(赤のまま)。**アサーション・許容時間は緩めない**。判定は固定 SHA ごと。

## 9. リスクとロールバック
| リスク | 対策 |
|---|---|
| 遷移が戻らない(今も存在) | S2 を最優先。失敗注入テストを必須化 |
| 戦闘開始が遅くなる | required を最小に、既 ready なら Loading 無し。閾値 300 ms は仮(実機で決定) |
| モバイルのメモリ逼迫 | S1 計測 → S7 は実機結果が出るまで入れない |
| 二重遷移 / 戦闘中の map 移動 | TransitionGate 一本化、世代トークン |
| 見た目・演出の変更(承認済み演出に触れる) | フェード長・戦闘開始演出は不変。変更は作者承認 |
| セーブ互換 | Loading は一時 UI、セーブ変更なし |
ロールバック: 各段階を 1 PR・フラグ(`?feature=loading` のような DEV 切替を S4〜S6 で用意)。問題時は PR を revert、または manifest の `preloadStills` を空にする。

## 10. 作者の追加承認が必要な項目
1. 設計全体の採用と実装の開始(段階 S1 から)。
2. ML-01 の失敗時復帰(S2)を先行修正してよいか(既存欠陥の修正)。
3. 単発 still 先読み 3 枚の採用(S3)。
4. Loading 画面の見た目(最小のテキスト + スピナ / 地域 CG)と、300 ms 閾値の考え方。
5. 地域紹介 CG の新規制作・採用、Tips の文面(正典との照合を含む)。
6. 近隣 map 先読みと解放方針、モバイルのメモリ上限(実機測定後)。
7. 「戦闘開始を待たせる」ことの是非(初回戦闘のみ待つ / 常に即開始のまま任意素材だけ先読み)。
8. Aidan 待機の時計基準化は**保留のまま**(別件)。

## 未確定・限界
Android 実機・実ネットワークは `NOT_RUN`。ベースラインは 2 CPU のローカル測定で、遅延ゼロのため待ち時間は過小評価。ボス戦(Raider)の開始素材・ダンジョン/町/建物の個別素材量は未調査。`BattleMotion` と `ForestLoader` の二重 Image 保持の実際のメモリ影響は未測定。
