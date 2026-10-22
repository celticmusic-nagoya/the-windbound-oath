# Fiona idle v3 - 描画停止の原因切り分け (Codex 独立再QA FAIL 対応)

基準 SHA `320ba8ca7c480f77e69a6e48faf8238772c1567c`(Codex 環境の 320 秒 soak が 2 回 FAIL、最大約 7.9 秒の描画停止)。
**結論: 原因は未確定。当環境では 7.9 秒級の停止を再現できなかった(最大 0.57 秒)。製品コードは推測で変更していない。**
停止時に「どの層が止まったか」を自動で記録する仕組みを soak に組み込んだので、Codex 環境での再実行で原因の層が分かる。

## 1. 何を区別したか(`tools/qa/fiona_v3_stall_probe.py`)
同一時間軸(`performance.timeOrigin + performance.now()`)で、独立した 4 つの時計を同時に記録する。

| 記号 | 時計 | 止まったときの意味 |
|---|---|---|
| W | Worker の心拍(25ms)。ページのメインスレッドに依存しない | W も止まる = プロセス/ホスト全体の凍結(CPU 枯渇・VM 停止) |
| T | メインスレッドの `setTimeout`(25ms) | T が止まる = メインスレッドが塞がれている(長タスク・GC 等) |
| R | `requestAnimationFrame` | R だけ止まる = フレーム供給の停止(コンポジタ/ラスタ) |
| D | `BattleIdleMotion.traceStart()` の描画ログ(製品自身の描画記録) | D だけ止まる = 描画器が描かなかった(paused()/eligible/例外) |

加えて longtask、body class・visibility の変化、`performance.memory`(1Hz、減少=GC)、ホスト側の `/proc/stat` の steal/iowait、`/proc/pressure/cpu`、loadavg、CDP `Performance.getMetrics` を記録する。
フィオナ待機の ON/OFF は同一ページ・同一画面で切り替える(`BattleIdleMotion.begin/stop`)。判定関数は `tools/qa/fiona_v3_trace.py` の `classify_incident` / `stall_layers`(`tests/battle/fiona_v3_trace_qa.py` で単体検証)。

## 2. 結果(当環境: 2 CPU、headless Chromium、ソフトウェア描画)
`*.summary.json` が各実行の要約。rAF 間隔(ms)の最大 / 100ms 超の回数 / 取得フレーム数 / longtask 数。

| 実行 | 条件 | rAF 最大 | フレーム数・100ms 超 | 備考 |
|---|---|---|---|---|
| A | ON 320s、無負荷 | 150 | 18473 f(57.7 fps)・1 | Worker 最大 61ms、longtask 0 |
| B | ON 320s、CPU 競合 2 本 | 341 | 13924 f(43.5 fps)・305 | longtask 1(66ms) |
| C | **OFF** 320s、CPU 競合 2 本 | 339 | 16826 f(52.6 fps)・108 | B と同一条件でフィオナ待機だけ OFF |
| D | ON/OFF 交互 40s×2、競合 2 本 | 270 | ON0 2183 f・6 / OFF0 2178 f・10 / ON1 2001 f・16 / OFF1 2363 f・0 | |
| E | 交互 40s×2、競合 4 本 | 451 | ON0 1837 f・43 / OFF0 2182 f・10 / ON1 2148 f・10 / OFF1 2186 f・10 | |
| F | E + `imageSmoothingQuality='low'`(ページ内 A/B。ゲームは無変更) | 572 | ON0 1894 f・29 / ON1 2163 f・4 | smoothing を下げても明確な差は出なかった |
| G | 交互、競合 2 本 + CPU×4 | 464 | ON0 572 f・127 / ON1 980 f・89 / OFF0 1461 f・66 / OFF1 1629 f・52 | ON の longtask 11 / 8(最大 119ms)、OFF は 1 / 0 |
| H | 交互 30s×2、競合 8 本 + CPU×6(load1 最大 11) | 450 | ON0 756 f・70 / ON1 641 f・74 / OFF0 1191 f・40 / OFF1 868 f・68 | ON の longtask 35 / 29(最大 109ms)、OFF は 0 / 7 |

読み取れること(測定事実):
1. **7.9 秒級の停止は 8 条件・合計約 25 分のどこでも出なかった**(rAF 最大 0.57 秒、Worker 最大 0.15 秒、ホスト側 1 秒周期サンプラの遅れは最大 +0.34 秒)。極端な負荷(競合 8 本 + CPU×6)でも 0.45 秒止まり。したがって「CPU が足りないとこうなる」という単純な一般論では説明できない。
2. **負荷が高いと止まるのは rAF(フレーム供給)で、メインスレッドのタイマーと Worker は動き続ける**。Codex の測定項目(rAF 5.5 秒 / longtask 4.9 秒)と照らすと、longtask が数秒出た Codex 環境はこれとは別の状態(メインスレッドが実際に塞がれていた)の可能性がある。**推測であり、Codex 環境のログでしか確定できない。**
3. **フィオナ待機 ON は、競合下で OFF よりフレームが少なく 100ms 超の揺れが増える**(B 対 C: 43.5 対 52.6 fps、305 対 108 回。G/H: ON は 572〜980 / 641〜756 f に対し OFF は 1461〜1629 / 868〜1191 f。E は ON0 だけ悪化)。ON は 1 フレームごとの再描画(設計どおり)で CPU を使うため、**競合下での負荷は増える(因果ではなく寄与)**。ただし ON でも 7.9 秒級にはならなかった。
4. D と F の `incidents` に出る 41 秒の項目は、OFF フェーズ(待機描画を意図して止めた区間)を描画停止と誤って数えた**プローブ旧版の分類の誤り**。以降の版では OFF フェーズに重なる描画の空白は対象外にした。E・G・H の 0.41〜0.47 秒の項目は実際の rAF 遅延(Worker・タイマーは生存)。

## 3. soak への組み込み(原因を Codex 環境で確定するため)
`tests/battle/fiona_idle_v3.py` の 320 秒 soak は、停止が起きたとき次を自動で出力・証跡(`FIONA_EVIDENCE`)に保存する。
- 停止ごとの時刻・長さ・止まった層(W/T/R/D)と判定文、ホスト(nproc、loadavg の前後)、longtask 最大値。
- 独立時計(Worker・タイマー・rAF の空白だけを記録)は `FIONA_STALL_CLOCKS=0` で切れる。

## 4. 解析器 P2(限定修正)
- 描画の空白(**停止**)と、アニメ時計が状態を飛び越す(**状態スキップ**)を別の事象にした。
- 旧ルールは、ブランク開始の前後 0.1〜0.36 秒の窓の中にある描画だけを見ていたため、空白が窓全体を呑み込むと「窓内の描画間隔=0」となり、停止を「描画が連続していたのに状態が飛んだ」と誤判定した。新ルールは各スロットを挟む前後の描画の**壁時計での距離**を使う。
- 旧ルールは窓の中の間隔を**アニメ時計**で測っていたため、壁時計は 16ms ごとに描画しているのにアニメ時計だけが飛ぶ本物のスキップを見逃した(新旧の比較テスト S4)。新ルールはこれも検出する。
- 空白がポーズ(dialogueOpen / battlePresentationBusy / actionCinematic / ページ非表示)で全て説明できる場合は `NOT_RUN_PAUSED`(PASS にしない)、説明できない場合は停止として FAIL。閾値は 500ms(従来の 66.7ms 級の揺れは停止にしない)。
- 既存の厳密判定は緩めていない。負例 7/7、窓端切れ、時計リセット判定は従来どおり。

## 5. `ally_motion_p3` の不安定 FAIL(`tools/qa/ally_heal_ready_probe.py`)
mid サンプル(+250ms)で「画像が complete でない」と出た件。アクション呼び出し → `<img src>` 設定 → load → 次の rAF → `decode()` の順序をページ時計で記録した。
- 無負荷: 16 回(PC)+ 12 回(縦)で未準備 0。
- CPU 競合 2 本 + CPU×4: **16 回中 4 回が未準備**(Lou heal 3/8、Fiona heal 1/8)。`heal_pc_load.json` に生ログ。
- 原因: `fiona_skill_charge.png` / `lou_support_charge.png` / `lou_support_heal.png` は単発の静止画で、`BattleMotion` の多コマ先読み対象ではないため、**そのセッションでの初回使用時にフェッチ・デコードされる**。`src` 設定から load までは無負荷で 26〜70ms、負荷下で 57〜285ms。テストは「アクション開始 +250ms の一点」で見るため、Lou heal(`src` 設定がアクション開始 +141〜168ms)は残り約 100ms で間に合わず FAIL する。load 後の `decode()` は 0.2〜78ms で、描画開始(次の rAF)は load の直後に起きる。順序は `src` → フェッチ → load → decode → 次の rAF で、逆転や欠落は見つかっていない。
- 判定: **描画の不具合ではなく、単発画像の初回読み込み遅延(テストの固定時刻サンプルとの競合)**。製品側の改善余地はあるが(戦闘開始時に単発ポーズ画像を先読みする)、これは製品コード変更で未承認。テスト側は、固定 250ms 点を「準備完了を待つ」に変えると検出力が落ちるので、**アサーションもタイムアウトも変更していない**。

## 6. 未確認・限界
- Codex 環境では測定していない。7.9 秒の因果は未確定のまま。
- Android 実機、他ブラウザは未測定。
- 提案(いずれも未実装・要承認): (a) 救出戦(`body.soloRescue`)ではフィオナ待機を対象外にする(見えない描画を止めるだけ)、(b) 単発ポーズ画像の戦闘開始時の先読み、(c) 描画頻度の上限(例 30fps)は見た目の仕様に関わるため作者判断。

## 再現コマンド
```
MODE=on  SECONDS=320 STRESS=0 OUT=a.json python3 -I tools/qa/fiona_v3_stall_probe.py
MODE=alt PHASE_S=40 CYCLES=2 STRESS=4 OUT=e.json python3 -I tools/qa/fiona_v3_stall_probe.py
TRIALS=8 VP=pc STRESS=2 THROTTLE=4 OUT=heal.json python3 -I tools/qa/ally_heal_ready_probe.py
```

## 7. 回帰結果(テスト対象のコード SHA `09bca93c6e0bd108716055c8d00b0c3484ae07fe`、当環境、直列実行)
このコミットより後の変更は本ファイルと証跡ファイルのみ(docs だけ。`git diff 09bca93 HEAD --stat` で確認できる)。既存 QA 原本(旧 `docs/battle/qa/fiona-v3-load/` など)は変更していない。

| 項目 | 結果 |
|---|---|
| `fiona_v3_trace_qa.py`(純 Python。S1〜S5 新旧比較、P1〜P5 ポーズ所有、ATTR 判定、既存の時計リセット・窓端) | 36 ok / FAILS [] |
| `fiona_idle_v3.py`(短縮、通常戦 fixture = `attackGob2` + 可視性) | 44 ok / FAILS [] |
| `fiona_idle_v3.py` + `FIONA_LOOP_SECONDS=320`(`soak_320s_evidence_code-09bca93.json`) | 48 ok / FAILS []、18369 描画、clock_resets 0、最大描画間隔 83.3ms、停止(>500ms)0、72 blink 中 69 完全 |
| `fiona_idle_v3_strict.py`(実系) | 45 ok / FAILS [] |
| `fiona_idle_v3_strict.py`(負例) | 7/7 検出 / FAILS [] |
| `arena_motion_test.py` | 44 ok / FAILS 0 |
| `battle_idle6.py` | 26 ok(2 回とも) |
| `ally_motion_p3.py` | 67 ok(3 回とも)。ただし負荷下では 16 回中 4 回の未準備を `ally_heal_ready_probe.py` で再現できており、**3 回 PASS は「不安定さが解消した」証拠ではない**(第 5 節) |

注: 同 soak の独立時計の記録に、T と R で各 1 回の 200ms 超の空白がある(Worker は無し)。描画ログには 500ms 超の空白も 83.3ms 超の間隔もなく、`traceStop()` の大きな戻り値を受け取るための終了時の評価と重なるため、観測窓内の停止ではないと判断した(個別ログで再確認していない)。
`strict` 負例ログの `BrokenPipeError` は、テストが文脈を閉じたときに静的サーバ(`http.server`)が出す既知の接続中断で、判定とは無関係。
