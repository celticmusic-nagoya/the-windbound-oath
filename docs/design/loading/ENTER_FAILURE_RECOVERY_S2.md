# `MossForest.enter()` 失敗時回復(S2)— 分析と最小修正案

STATUS: **ANALYSIS / PROPOSAL — 製品コード変更なし。修正PRは作者承認後。**
基準: `main` = `e8ecb5dceea3513bbc22028dcff9365b6718d20c`。対象: `js/field/moss-forest-runtime.js` の `enter()`(~239〜270行)。
区分: 「確認済み(コード読解)」「Claude環境の再現」「Codex独立再現=**未実施**」「未確定」を分けて書く。Claude環境の再現は Codex の独立判定ではない。

## 1. 現状の状態遷移(確認済み・コード読解)
| # | 処理 | 変更される状態 | ここで例外が出た場合 |
|---|---|---|---|
| 1 | `S.busy=true; S.active=false` | 入力凍結(`active`/`busy` を見る全ハンドラが停止) | — |
| 2 | `mountPlayerSprite` / `mountFionaSprite` | スプライトDOM | 稀。busy 固着 |
| 3 | `await loadMap(id)`(`ForestLoader.loadAssets` → `ForestLoader.load(MAP_BASE+id+'.json')`) | `cache`(成功時のみ) | **busy=true / active=false 固着。旧マップは未アンマウントなので画面は旧マップのまま、入力のみ死ぬ** |
| 4 | `Object.assign(S.flags, options.flags)`、`S.slain.delete(id)` | **フラグ・撃破記録を先に書き換える**(コミット前の副作用) | 以降の失敗で、旧マップに居るのに新マップ用フラグ/respawn が反映済み |
| 5 | `await setFade(1)`(first 以外) | フェード黒 | 例外は出にくいが、以降の失敗でフェード黒のまま |
| 6 | `await ForestLoader.prepare(...)` | 画像キャッシュ | 画像失敗は握りつぶされる(`decode` 失敗は `failed` へ、3.5秒でタイムアウト解放)。**画像失敗は例外にならない** |
| 7 | `unmount(); mount(map)` | **`S.map/S.mapId/S.forest` を破棄→新規**(ここがコミット点) | `mount` 失敗なら旧マップ破棄済み・新マップ未構築。**マップ無し・黒フェード・busy 固着** |
| 8 | 位置決定、`S.x/S.y`、`S.keys.clear()`、`render()` 等 | プレイヤー座標、キー入力、遭遇タイマ | `blocked()`/`h.commit` 等の例外は中途半端な座標 |
| 9 | `setFade(0)` → `S.busy=false; S.active=true; startLoop(); hooks.onEnter` | 入力復帰 | `onEnter` 例外は Promise reject だが状態は復帰済み |

`try/catch` は無い(確認済み)。呼び出し側 `transitionTo` は `enter()` の戻り Promise を捨てる(`enter({...})` で未処理 rejection)。`MossForestStory.enterMap` は `return MossForest.enter(...)` のみ。`hooks.onTransition`(ストーリーゲート)は `enter()` の**前**に走るため、失敗しても story 側の状態は進んだままになり得る(**未確認:** 各ゲートが enter 前にどの story 状態を書くか。S2 着手前に全件列挙が必要)。

## 2. 失敗種別ごとの現状挙動
| 種別 | 発生箇所 | 現状(Claude環境再現 `tools/qa/loading_failpath_probe.py`) | 回復に必要な状態 |
|---|---|---|---|
| 不正マップID / マップJSON取得失敗(404・オフライン・JSON壊れ) | #3 | `enterMap('does_not_exist_map')` が reject、`busy=true / active=false` が固着=**入力不能(ソフトロック)**。画面は旧マップのまま | 旧マップ/座標はそのまま。`busy/active` と入力の復帰だけで足りる |
| 例外(コード不具合・フラグ処理) | #2〜#5 | 同上。#5 以降ならフェード黒も残る | 上に加え **フェード開放**、#4 の副作用の巻き戻し |
| 画像取得失敗 | #6 | 例外にならず進行(プレースホルダ描画)。3.5秒で打ち切り | 回復不要(ただし「失敗を可視化するか」は設計事項) |
| 初期化失敗(`mount` 以降) | #7〜#8 | 旧マップ破棄済みで**自力復帰不能**。再現は **未実施**(`mount` に故障注入が必要=テストフックが要る) | 旧マップ再 `mount`(`prevMap`/座標を退避しておく)、または安全な既定マップへ退避 |

## 3. 回復すべき状態(要件案 `PROPOSED`)
1. 元マップ: `S.map/S.mapId/S.forest`(#7 より前の失敗では不変であること。#7 以降は退避した `prev` から再 mount)。
2. プレイヤー座標: `S.x/S.y/S.fl/S.fx/S.fy` と高さレベル(`height.level`)。#8 に入る前に退避。
3. イベント状態: `S.flags`(#4 の `Object.assign` はコミット点の後へ移すか、失敗時に退避値へ戻す)、`S.slain`(同様)、`S.opened/S.fired`(変更なし)、`hooks.onTransition` が進めた story 状態(**要調査・要作者判断**)。
4. 入力制御: `S.busy=false`、`S.active=(元の値)`、`S.keys` クリア、`S.target=null`、`FieldNavigation.cancel()`、`transitionLatch`/`battleLatch` の扱い(復帰直後の誤遭遇防止に既存の `enc.until` 相当を再設定)。
5. 表示: フェード不透明度を 0 へ、トースト(`hooks.toast`)で失敗を短く通知(文言は作者確認)。
6. 初回(`first`、旧マップ無し)の失敗: 戻り先が無い。フィールドを `hide()` してタイトル/呼び出し元へ戻すか、再試行導線を出す(**作者判断**)。

## 4. 最小修正案(提案のみ・未実装)
- `enter()` を **二相**にする: (A) 準備相 = #3・#5 を除く取得系(`loadMap`、`prepare`)を**状態変更前**に完了、(B) コミット相 = `unmount→mount→座標→フラグ`。(A) の失敗は何も変更せず `busy/active` を元に戻して reject を握りつつ `false` を返す。
- (B) は `prev={map,x,y,fl,flags(shallow copy),slain}` を退避した上で `try{…}catch(e){ rollback(prev) }`。rollback は旧マップ再 mount → 座標復元 → フェード 0 → `busy=false/active=prevActive`。rollback 自体が失敗したら `S.active=false` のまま「再試行/タイトルへ」導線を出す(無言ロックを残さない)。
- `enter()` の二重呼び出しガード: 入口で `if(S.busy&&!S.entering)`… 既存の `lock()`(`busy` を外部が立てる)と衝突するため、**専用の `S.entering` トークン**を使い、`busy` の意味は変えない(`lock(on)` は演出用に残る)。
- `transitionTo` は戻り値/rejection を受けて通知する。
- 変更量の見積り: runtime 1ファイル、~30〜50行。素材・マップデータ・story には触れない。

## 5. 回帰テスト案(S2 実装時に追加。許容値の緩和はしない)
| ID | 内容 | 期待 |
|---|---|---|
| R1 | 不正マップIDへ `enter` | resolve(false)/通知、`busy=false`、`active=元`、`mapId/x/y` 不変、キー入力で移動可能 |
| R2 | マップJSON 404 / 壊れたJSON(route abort / 不正本文) | R1 と同じ |
| R3 | `loadMap` 後に `mount` へ故障注入(テスト用フック、`?dev=1` 限定) | 旧マップ再 mount、座標・フラグ復元、フェード 0、入力可 |
| R4 | `options.flags` 付き遷移が失敗 | `S.flags` 不変(#4 の巻き戻し) |
| R5 | 失敗直後の再試行 | 成功遷移できる(固着なし)、`slain` が正しく扱われる |
| R6 | 連続遷移(失敗中に別 `transitionTo`) | 二重 mount なし、後続は無視またはキュー(方針は作者判断) |
| R7 | 初回 `enter`(旧マップ無し)の失敗 | 規定の退避挙動(§3-6)、無言ロックなし |
| R8 | 画像だけ失敗(個別画像 abort) | 遷移成功、プレースホルダ、失敗が記録される |
| R9 | 既存回帰 | `m33b`/arena/field 系の既存テストが全て従前どおり |
R3・R6・R7 は故障注入フックまたは `page.route` が必要。既存の Playwright 基盤で可能だが、テスト専用フックは製品コード変更に当たるため作者承認が要る。

## 6. S2 を S1(最小Loading基盤)より先にやるか — 比較
| | S2 先 | S1 先 | 並行 |
|---|---|---|---|
| 利点 | 現在進行形の不具合(ソフトロック)を Loading の有無と無関係に除去。S1/ML-01 は「失敗しても安全に戻れる」前提で作れる | Loading 実装の土台が先にでき、S2 を Loading の失敗経路として一体設計できる | 日程短縮 |
| 欠点 | S1 のコントローラ導入時に `enter()` を再度触る(二重修正) | 不具合を抱えたまま新機構を載せる。Loading 失敗時の復帰先が未整備 | QA・差分が混ざり、固定SHAが崩れる |
| 推奨度 | **推奨**(Codex が独立再現した場合) | 次点 | 非推奨(PR混在回避) |
理由: S2 は `enter()` の「準備相/コミット相」分離を導入し、これは ML-01 の LoadingController が必要とする構造そのもの(準備を前倒しできる分割点)。S2 をそれの先取りと位置づければ二重修正は小さい。ただし **Codex の独立再現が出るまで推奨は暫定**。

## 7. 未確定
- Codex 独立再現: **未実施**(PR #47 コメントで依頼済み)。
- `mount` 失敗の実再現と、story ゲート各件の enter 前副作用の全件調査: 未実施。
- 実機(Android)・実ネットワークでの失敗確率: NOT_RUN。
- 失敗時のトースト文言、初回失敗時の戻り先: 作者判断。

## 8. 作者承認が必要な操作
S2 修正PRの作成(対象: `js/field/moss-forest-runtime.js`)、テスト用故障注入フックの追加、失敗時文言の決定。承認までは本書のみ。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
