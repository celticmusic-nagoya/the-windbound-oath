# Fiona idle v3 FIX3 独立QA FAIL — 98 秒停止の読み取り専用分析

STATUS: **ANALYSIS ONLY — 製品コード変更なし。FIX4 は未着手。**
- Codex 判定: **FAIL / main 統合非推奨**。対象固定 SHA `24f958e526d06c7e3341b3627775abe764fe17e2`(FIX2 `64a8dac7…` の FAIL と原本も維持)。
- 証跡原本: 非公開 `the-windbound-oath-handoff`、ブランチ `handoff/fiona-idle-v3-fix3-qa-codex-20261022`、コミット `8c9ba9de9b93b900e537ef689fdb0e4d0e6eb314`。`MANIFEST.sha256` 51 件を Claude 側で照合し全件一致(不一致 0)。
- 後続 HEAD `e5a95ac9…` に Codex 判定は無い。FAIL を後続 HEAD に流用しない。FAIL を CONDITIONAL/PASS に読み替えない。閾値は緩和しない。
- 区分: [Codex実測] = 上記証跡の値、[Claude算出] = その証跡から Claude が再集計した値、[UNKNOWN]。原因はいずれも**断定しない**。

## 1. 98 秒停止の時系列(soak-2、[Claude算出])
- 要求 320 s の観測に対し wall 478 s、描画 1049(soak-1 は 7983)、STALL 21 件(合計約 357 s=wall の約 75%)。
- 停止は後半に集中し大型化: 3.9 s(84 s)→ 15.2 s(150 s)→ 70.7 s(176 s)→ 47.9 s → 36.8 s → **98.4 s(page-time 350.7 s)** → 40.5 s。
- 98.4 s の区間: 描画ログ D・主スレッド timer T・rAF R の被覆はほぼ 100%、Worker W の被覆 97.1%(単独最長 hole 6044 ms、71 個の hole に分散)。重なる longtask 最大 68043 ms。W が 98 秒連続停止した記録ではない。
- 同区間の製品 host_window は 1 sample のみ=**UNKNOWN**。前後で拾い直すと 243.8 s 幅の bracket(throttle +154.6 s、steal +113221 tick)で、98 秒内の増分には縮められない。

## 2. 計測の信頼性([Claude算出])
| 観点 | soak-1 | soak-2 |
|---|---|---|
| 外部 Python host sampler の標本数/観測 | 743 / 322 s | **156 / 477 s** |
| sampler 間隔 2 s 超の欠損(合計) | 4 回 / 9.0 s | **10 回 / 403.9 s** |
| 最大 sampler 起床遅れ | ≈ 数 s | 159.2 s |
| ≥3 s の STALL のうち外部 sampler 欠損と重なる割合 | 一部 | **全件(≥3 s の 13/13)** |
| cgroup throttle 期間率(cgroup 全体の counter) | 4.8% | **43.5%**(throttled 280 s) |
| /proc/stat steal 比(VM 全体) | 約 34% | **約 78%** |
| iowait 増分 | 17 tick | 0 tick |
| cgroup mem_oom / mem_high イベント | 0 / 0 | 0 / 0(swap は UNKNOWN) |
| PSI | 欠損(UNKNOWN) | 欠損(UNKNOWN) |
- 要点: soak-2 の大型停止では、**ブラウザ外の別プロセス(Python sampler)も同じ区間で止まっている**。ブラウザ内の W/T/R/D と外部 sampler の共通遅延であり、製品の描画ロジック単独では説明しにくい。ただし「環境が原因」とも断定しない(§4)。
- 逆に計測由来の可能性: sampler は 800 超のプロセスを走査し 1 回 320〜657 ms(Codex 実測 HOST_SAMPLER_OVERHEAD)。soak 中の ON/OFF 対照は**未実施**。sampler 自身の CPU 負荷が競合を悪化させた可能性は排除できない。
- 外部 observe.py の 1 Hz 監視でも、欠損(3 s 超の間隔)が arena 10 回(最大 16.1 s)、soak-2 56 回(最大 23.3 s)、それ以前の short/strict/ally 系はほぼ 0。**QA 実行の終盤ほど環境が悪化**している([Claude算出]、原因は UNKNOWN)。

## 3. arena 30 秒 timeout
- 最初の `Page.goto(...?dev=1)`(load 待ち 30 s)で timeout、assert 0 件。原 timeout は変更していない。
- arena 実行中 load1 は 5.5〜7.1(他テストより高い)、外部 1 Hz 監視に 10 回の欠損。同時間帯に環境全体が遅い状態だった**相関**はあるが、arena 固有の問題か環境かは未切分け。arena では host_sampler は動いていない。
- arena timeout 後に残存した Chromium 等のプロセスが次の soak-2 を圧迫した可能性(procs 数: soak-1 812 → soak-2 833)は**仮説**であり、プロセス一覧の記録が無く UNKNOWN。

## 4. 原因候補と識別テスト(調査計画の一部は §5)
| 候補 | 支持する観測 | 反証・不足 | 識別する追加テスト |
|---|---|---|---|
| H1 VM/ホストの CPU 供給不足(steal・cgroup throttle) | steal 78%、throttle 43.5%、外部 sampler も停止 | PSI 欠損。steal/throttle は VM・cgroup 全体の値で、98 秒区間内に限定できない | ゲーム非起動の最小プローブ(Worker+timer+rAF なし=純 Python tick 刻みのみ)を同条件で走らせ、steal と刻み欠損が一致するか |
| H2 計測器自身の負荷(sampler の /proc 走査) | 走査 0.3〜0.7 s/回、soak 中 ON/OFF 未実施 | sampler も止まっているので「加害者」だけでは説明しにくい | 同一条件で sampler OFF/低頻度(PID 限定・1 Hz)/ON を交互に 3 回ずつ |
| H3 製品(描画・GC・decode) | longtask 68 s が重なる | Worker と外部プロセスも止まる。製品単独なら外部 sampler は止まらないはず | 同環境でゲーム非起動 vs 起動の比較。製品を Idle だけ描画する最小ページとの比較 |
| H4 前テストの残存プロセス(arena timeout 後) | procs 増・終盤悪化 | プロセス一覧の記録なし | 各テスト前後に `ps` 全件を保存し、残存を数える |
| H5 ブラウザプロセスの停止・再起動 | — | 記録なし(PID/starttime 未保存) | PID・starttime・role 単位で記録(§5) |
| H6 ディスク/メモリ | iowait ≈ 0、OOM 0 | Codex 環境の空き容量は未取得(UNKNOWN)、swap UNKNOWN | 各 run 前に `df`・`free`・swap・cgroup memory.events を保存 |

## 5. FIX4 前の調査計画(提案のみ・製品実装なし)
条件を揃えて比較する(各条件 ≥3 回、同一 Codex 環境、連続実行しない=間に環境を休ませ、前後でプロセス一覧と df/free を保存):
1. **ホスト基準**: ゲームも Chromium も起動せず、軽量 Python の 4 Hz tick と /proc/stat(steal)だけを 320 s。
2. **最小ブラウザ**: 空ページ + rAF/timer/Worker のみ(製品なし)。
3. **ゲーム起動(計測器最小)**: 製品 + rAF/timer/Worker のみ、host sampler なし。
4. **ゲーム起動(従来計測)**: 現行の host sampler ON。
5. 上記を **CPU 競合なし/あり**、**空き容量を十分確保した状態**で。
6. sampler の改善案(診断コードのみ): PID/role/starttime 単位、対象をレンダラ主スレッド/ブラウザ数 PID に限定、走査コスト自己記録。
評価: 各条件で最大 gap・STALL 数・sampler 欠損・steal 比を並べ、計測器 ON/OFF で差が出るかを見る。

## 6. FIX4 に進むべきか — 推奨(暫定)
**製品側 FIX4 には進まない。** 現証跡は環境供給不足を示唆するが、環境・計測・製品のいずれも根因と断定できない。まず §5 の対照測定(診断のみ)を行い、ゲーム非起動のホスト基準でも欠損が出るなら環境、出なければ製品/計測の再検討に進む。作者承認なしに製品コードは変更しない。

## 7. 作者承認が必要な操作
Codex への対照測定依頼(Codex 環境での実行)、診断コード(host_sampler の改修)の追加コミット、容量確保のための削除(別紙「容量調査」)、FIX4 への着手。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
