# Fiona idle v3 FIX3 - Codex 32 STALL の解析と周辺検証

対象: Codex 独立再QA(`64a8dac75295139835bafaa53a68d29ffd0e36ec`)の証跡。非公開 handoff リポジトリ commit `2927344804c770457cccdd33289314e770b7e4d0`、`reports/FIONA-IDLE-V3/FIX2-CODEX-QA-20261022/`(原本はここ。本ディレクトリへコピーしない。以下は Claude の**解析結果**であり、Codex の判定・原本は変更していない)。
受領時に `TRANSFER_MANIFEST.sha256`(61件)と `original/MANIFEST.sha256`(58件)をすべて `sha256sum -c` で照合し、全件一致。

## 1. 32件のSTALL(`codex_stalls/classification_table.txt`、`stall_classification.csv`)
解析器: `tools/qa/fiona_v3_stall_classify.py`(page-time + `holes.to` で epoch へ。W/T/R の空白を区間との和集合で被覆率にした)。
| 観測 | 結果 | 区分 |
|---|---|---|
| rAF の空白が停止区間の 80% 以上 | **32/32** | 証拠あり。製品描画ログ(D)だけが止まった例は 0 件。描画は rAF の中で走るので、D の停止は rAF 供給の停止と同じ事象 |
| メインタイマーの空白が 70% 以上 | 26/32 | 証拠あり |
| Worker の空白(>200ms のものだけ記録) | 区間の 0%: 5件、50%未満: 9件、50%以上: 18件。最大 95%(8.7 秒の1件) | 証拠あり。Worker も「平常に動いていた」のではなく、断続的・大幅に遅れていた件が多い。ただし 5 件は Worker 無傷でメイン側のみ |
| 単一の長タスクが区間の 90% 以上を占める | 5件(8.7秒の 8735ms を含む。1233ms/983ms/792ms/809ms) | 証拠あり(soak-1 は証跡の long task 一覧が 200 件で打ち切られ、7 件は判定不能 `B?`) |
| 長タスクなしで T と R が長く止まった | 14件+不明7件(例: 4266ms の 1 件は最大 long task 1446ms) | 証拠あり。「JS が数秒走った」型ではなく、イベントループがそもそも回されなかった型 |
| pause / visibility イベント | 0(`events=[]`、`paused_ms=0`) | 証拠あり。非表示・dialogue 等による停止ではない |
| 負荷 | Codex 環境: 描画 8559/6615 回(私の無負荷実測 18369 回)、100ms 超の間隔 317/382 回(私は 1 回)、long task 200+/450 件(私は 0)、loadavg 約 3〜5、cgroup `cpu.max`=4 CPU 相当・`os.cpu_count`=5 | 証拠あり。環境全体が強く飽和していた |

## 2. 原因の候補
**証拠で支持されるもの**
- 共通の遅延: レンダラのメイン/rAF/Worker と、外部の Python 監視(8.7 秒の区間で 7054ms 遅れ)がほぼ同時に遅れている。4 つの時計が同時に遅れるのは、特定の製品コードよりプロセスまたは環境全体への CPU 供給の乱れと整合する。
- 同じ環境での別テストでも同種の症状: `arena_motion_test` は製品と無関係な `page.goto(..., load)` が 30 秒でタイムアウト。`battle_idle6` は rAF で測るフレーム時間が 40〜80ms ずれて FAIL。どちらも rAF/イベントループの遅延に敏感。
**推測段階(この証跡だけでは確定できない)**
- cgroup の CPU クォータによる throttle、VM の steal、I/O またはメモリ圧迫(ページフォールト)、GC、画像 decode。Codex の観測ハーネスは `/proc/pressure/cpu` が無くホスト側サンプルを失っており、throttle・PSI・コンテキストスイッチ・`performance.memory` はいずれも未記録。
- フィオナ待機の寄与: Codex の soak は 2 回とも待機 ON のみで、OFF 対照が無い。私の ON/OFF 比較(`docs/battle/qa/fiona-v3-stall/`)では、競合下で ON は OFF よりフレームが少ない(CPU を余計に使う)が、最大の停止は 0.57 秒止まりで 8.7 秒は再現しなかった。ON は飽和下での遅れやすさに寄与し得るが、8.7 秒という大きさの原因とは言えない。
**否定されたもの(この証跡の範囲で)**: ページ非表示/pause、clock reset(0)、状態 skip(0)、描画器だけが止まる型(0 件)。
**ホスト原因とは断定しない**。製品側の要因(ON の毎フレーム再描画が飽和時の余裕を削る等)も除外できない。

## 3. 解析器・ツールの変更(テスト/診断のみ。製品コードの変更なし)
- P2(`e1000ff`): pause の証拠なしの 500〜600ms の空白を NOT_RUN_PAUSED にしない。所有には実在する pause の被覆が必要で、許容は `min(600, gap/2)`。新規テスト 13 件。
- 本ブランチ: 停止層ラベルから原因断定を除去(`classify_incident` は層名だけ述べ、`cause undetermined`)。`stall_coverage()` を追加し、Codex が指摘した「短い Worker 遅延が全体凍結に見える」合成ケース(8 秒の D/T/R 空白 + 250ms の W 空白)を ATTR8 で固定。
- soak: `tools/qa/host_sampler.py`(0.25 秒周期。cgroup `cpu.stat` の throttle、PSI、steal、chrom* の自発/非自発コンテキストスイッチ、サンプラ自身の起床遅れ。各ソースは欠損可)を追加し、証跡へ保存。各 STALL に被覆率・重なる long task・同時刻のホスト指標を付与。long task は 200 件で切らない。
- 次回 Codex 再QAで原因を切り分ける読み方: 停止区間内で `d_throttled_usec` が増えれば CPU クォータ、`d_psi_cpu_some_us` と `d_steal_ticks` が増えれば競合/VM、`d_invol_ctxt` が大きければ preemption、いずれも動かず `wake_delay` だけ大きければ監視側も止められた(環境全体の停止)。

## 4. Lou heal 画像の先読み A/B(`preload_ab/*.json`、`tools/qa/ally_heal_ready_probe.py` に `PRELOAD=1` を追加。**ゲームは無変更**、ページ内で `Image()+decode()` を戦闘開始後に実行)
| 条件(PC 1280x720、CPU 競合2本+CPU×4) | 先読みなし | 先読みあり |
|---|---|---|
| Lou heal の mid(+250ms)未準備 | 7/8, 7/8, 7/8, 7/8(計 **28/32**) | **0/32** |
| Fiona heal | 0/8, 0/8, 0/8, 2/8(計 2/32) | 0/32 |
| 縦持ち 390x844(同負荷、6 回) | Lou 3/6 | Lou 0/6 |
| 無負荷 | 0/8 | 0/8 |
副作用の測定: 先読みの所要は無負荷 0.25〜0.56 秒、負荷下 0.40〜3.1 秒(4 枚並列の fetch+decode、非同期)。先読み中の long task は最大 189ms(負荷下)、無負荷 57ms。メモリ増は 4 枚分のデコード済み画像。結果は安定して再現した。
**判断**: 先読みは未準備を実測で解消する。ただし製品コードの変更(`BattleMotion` の先読み対象への追加、または戦闘開始時の `Image()`)であり、**対象と根拠をここに示す段階**。実装には作者の承認が必要(未実装)。テストの 250ms サンプル/アサーション/タイムアウトは変更していない。

## 5. 回帰(Claude 環境、`FIX3` ブランチ。結果は下の「検証結果」)

### 検証結果(Claude 環境 2 CPU・直列実行・コード SHA は本ブランチ HEAD のコミットで確認。`regression/summary.txt`。`FAIL=` 列は行頭 `FAIL` の数で、`FAILS []` の 1 行を含む)
| 項目 | 結果 |
|---|---|
| `fiona_v3_trace_qa.py` | 51 ok / FAILS [] |
| `fiona_idle_v3.py`(短縮) | 44 ok / FAILS [] |
| `fiona_idle_v3_strict.py` 実系 / 負例 | 45 ok / FAILS [] ・ 負例 7/7 検出 / FAILS [] |
| 320 秒 soak ×2(`regression/soak*_evidence.json.gz`、host_samples 付き) | 48 ok ×2。描画 18215 / 18351、reset 0、最大描画間隔 233.3 / 66.7 ms、STALL 0、pause 扱い 0。当環境では停止は再現せず(Codex 環境の 1233 / 8700 ms は再現していない) |
| `arena_motion_test.py` | 無負荷 44 ok、CPU 競合2本 44 ok。**Codex の起動 timeout は当環境で再現せず** |
| `ally_motion_p3.py` | 無負荷 67 ok、CPU 競合2本 67 ok(1 回ずつ。不安定さの解消の証拠にしない。先読み無しの probe では競合下で Lou heal が 28/32 未準備) |
| `battle_idle6.py` | 無負荷 26 ok。**CPU 競合2本で 1 FAIL を再現**(raider Aidan の per-frame 時間 ±45ms)。assertion・hold は変更していない |

## 6. 回帰原因の切り分け
- `battle_idle6`: **製品の挙動 × 環境(負荷)× テストの測り方**の組み合わせ。製品の Aidan 待機は `js/battle-motion.js` のフレームごとの連鎖 `setTimeout`(ドリフト補正なし)で進むため、タイマーが遅れるとフレーム時間が実際に伸びる。テストはそれを rAF(16.7ms 刻み)で測り ±45ms で比較する。無負荷では通り、競合で遅れると落ちる。製品の欠陥と断定はしない(フィオナ v3 は時計基準の rAF 描画で影響を受けない)。時計基準にする案は製品変更で、未実施・要承認。テストを緩めない。
- `arena_motion_test` の `goto(load)` 30 秒 timeout: 当環境では再現せず。製品と無関係な最初のページ読み込みでの timeout なので、**環境要因(Codex 環境の飽和)の可能性が高いが未確定**。次回 Codex 再QAのホスト指標で確認する。
- 修正候補と副作用(いずれも未実装): ①先読み(第4節)― 副作用は起動後の一時的な CPU/ネットワーク。②Aidan 待機を時計基準にする ― 見た目の仕様に関わる。③待機描画の頻度上限や救出戦での停止 ― 見た目の仕様・作者判断。ゲーム仕様・難易度・採用素材は変更していない。
