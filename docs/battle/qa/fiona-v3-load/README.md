# Fiona idle v3 - 描画負荷の調査 (Codex FIV3-RQ-02)

調査のみ。ゲームのコードは変更していない。測定ツールは `tools/qa/fiona_v3_load_probe.py`、実測の要約JSONは同じフォルダ。

## 方法
同一ページ・同一画面で、フィオナの待機描画を **ON/OFF 交互**（ON0→OFF0→ON1→OFF1）に切り替え、フィオナの状態機械とは独立に次を同じ時間軸で記録した。
- `requestAnimationFrame` の間隔、50ms `setTimeout` の遅れ、非buffered の longtask（開始前を含めない）
- `drawImage`（幅900px以上）1回ごとの所要時間
- `RUNTIME=main` は、js/assets.js・js/battle-idle-motion.js・フィオナ旧6コマだけを `origin/main`(900e5387) から配信（Codex の方法と同じ）。`THROTTLE=6` は CDP で CPU を6倍遅くする。
- 条件: レイダー戦、1280x720、headless Chromium（ソフトウェア描画、2 CPU）。

## 結果（要約）
| 条件 | フィオナ待機の描画回数 / 平均コスト | rAF間隔 最大 (ON区間) | 参考: OFF区間の最大 | 長タスク最大 |
|---|---|---|---|---|
| head・通常 60s×2周 | 約3200回/60s・0.10 ms（最大6.6 ms） | 250 ms / 83 ms | 367 ms / 67 ms | 63 ms |
| main相当・通常 60s×2周 | 240回/60s・0.02 ms | 117 ms / 100 ms | 84 ms / 67 ms | 0 |
| head・CPU×6 30s×2周 | 約1300回/30s・0.5 ms（最大28 ms） | 133 ms / 117 ms | 83 ms / 133 ms | 95 ms |
| main相当・CPU×6 30s×2周 | 115回/30s・0.1〜0.2 ms | 183 ms / 150 ms | 150 ms / 134 ms | 70 ms |

## 判断
1. **5秒級の停止（Codex: 最大 rAF 5466 ms / longtask 4853 ms）は再現しなかった。** 合計で 4分(通常) + 2分(CPU×6) 測り、最大でも 0.37 秒。
2. **OFF（フィオナ待機を停止）の区間でも、同程度の揺れが出る。** 通常条件では最初の ON0/OFF0 に揺れが集中し（ウォームアップ/ホスト由来と見られる）、OFF0 の最大 367 ms は ON0 の 250 ms より大きい。ただし CPU×6 では ON 区間の方がやや悪い傾向がある（100ms超の rAF 間隔: ON 計7回 / OFF 計2回、p99 83 ms 対 50〜67 ms）。いずれも最大 0.13〜0.37 秒で、5秒級には届かない。
3. **v3 の描画は main相当より回数が多い（約13倍）。** 旧待機は絵が変わる時だけ描くが、v3 は呼吸変形のため毎フレーム描く（設計どおり）。1回あたり平均 0.1 ms（CPU×6 で 0.5 ms）で、60fps の1フレーム 16.7 ms に対し 1〜3%。CPU×6 の測定では main相当の方が間隔の乱れが大きかったが、実行順（head→main）の影響を除けていないので優劣は主張しない。
4. **Aidan の ±45ms (battle_idle6)** は当環境の head で 2/2 PASS（Codex 環境の head では 2/2 FAIL）。環境差か、そこに依存する別要因かは、当環境では確定できない。
5. **確認できた無駄な描画が1つある。** 救出戦（`attackGob1`、`body.soloRescue`）では `css/prologue-combat.css:7` がフィオナの親要素を `visibility:hidden` にするが、`BattleIdleMotion.eligible()` はそれを見ないので、見えないフィオナを描き続ける。ただし停止が観測されたレイダー戦の因果ではない。
6. **結論: 因果は未確定。** 「v3 の描画が共有イベントループを止める」ことを示す証拠は得られず、「環境だけ」とも断定しない。

## 製品コードを変更しなかった理由と、提案（要承認）
- Codex の指示（主因が判明するまで Aidan の hold 値・±45ms を変えない／単純な eligible 変更で再開不能にしない）に従い、製品の速度・閾値・描画は変更していない。
- 提案A（低リスク）: `eligible()` に「通常戦で `body.soloRescue` のときフィオナは対象外」を追加（論理上の出場状態に基づく。canvas自身やimgの可視状態は使わない）。無駄な描画の停止のみで、見た目は変わらない。実装には製品コード変更の承認が必要。
- 提案B: Codex 環境で `tools/qa/fiona_v3_load_probe.py` を同条件で実行（`RUNTIME=head` / `main`、`THROTTLE` を変えて）し、停止が出る区間の ON/OFF の差と main-thread のコールスタック(CDP)を取得する。因果が決まるまでは A を含め製品を触らない選択もある。

## 再現コマンド
```
PHASE_S=60 CYCLES=2 RUNTIME=head  OUT=head.json python3 -I tools/qa/fiona_v3_load_probe.py
PHASE_S=60 CYCLES=2 RUNTIME=main  OUT=main.json python3 -I tools/qa/fiona_v3_load_probe.py   # main = MAIN_REF(既定 origin/main)
THROTTLE=6 PHASE_S=30 CYCLES=2 RUNTIME=head OUT=thr6.json python3 -I tools/qa/fiona_v3_load_probe.py
```
