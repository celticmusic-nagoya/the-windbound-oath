# Aidan / Fiona / Lou 戦闘モーション — 素材仕様と納品・実装状況

> 訂正（2026-10-19）: 以前の版は「全て未納品」と記載していたが誤り。2026-10-16 納品ZIP（10枚）等により、下表「納品済み」の行は実装済み（Phase 3）。
> 未納品のまま「実装完了」とは判定しない。多コマ素材が無い状態は静止画フォールバック（`js/assets.js` BATTLE_ASSETS）。

## 状態一覧（Phase 3 時点）
| actor | state | 状態 | 備考 |
|---|---|---|---|
| aidan | attack / skill / draw | 多コマ実装済み（既存） | |
| aidan | damage / low_hp / ko | 多コマ実装済み（Phase 3） | 10/17 改訂版 `*_new` を採用。10/16 の hplow・ko は置換済み |
| fiona | ready | 多コマ実装済み（既存） | |
| fiona | attack / damage / heal / ko | 多コマ実装済み（Phase 3） | 10/16 納品 |
| fiona | winddance | 多コマ実装済み（Phase 3） | 10/17 改訂版。5コマ目の渦は不変。習得ゲート不変 |
| lou | damage / blessing(=lou_magic) | 多コマ実装済み（Phase 3） | 10/16 納品 |
| lou | ko | 多コマ実装済み（Lou-KO フェーズ） | `lou_new_ko`（10/16納品・採用）。ルーはHPを持たず本編ではKOしない。「気絶」は別状態（仕様案: docs/battle/faint-state-proposal.md） |
| fiona | skill(windbloom) / guard / evade / prayer / item / victory / awaken | 静止画のみ・未納品 | 下記P1〜P3 |
| lou | charge→heal / rune / evade / victory / low_hp | 静止画のみ・未納品 | 下記P1〜P3 |

実装は manifest 追記のみで足りる（Phase 3 で battle-actor-state に low_hp 一回再生・winddance・モーション長の確保を追加済み）（`img/battle/motion-manifest.json` に `<actor>.<state>` を足し、連番PNGを置く。コード変更不要）。

## 共通仕様（既存 Aidan 納品物と同じ方式）
- 連番PNG `<actor>_<state>_NN.png`（NN=01〜）、RGBA・背景完全透過（アルファ1〜8のもやを入れない）、1アクション内で同一キャンバスサイズ、足元アンカー固定（既存 idle のキャンバス/アンカーと揃える）。
- 既存待機キャンバス: Fiona idle 1034×678（アンカー約561.7,671）、Fiona ready 946×644、Lou idle 442×724（アンカー約221,420）、参考 Aidan attack 1312×1199。**行動用は待機と同じ足元基準で、武器・エフェクトの振り幅分だけ広いキャンバスで可。コマ間でキャンバスは不変。**
- 各コマの表示時間 ms と、攻撃の当たりコマ（hitFrame）を指定。最終コマは idle へ戻る前提（hold=last）。
- 正式採用済みデザイン（衣装・配色・武器・杖）を変更しない。Fiona の風の舞（5コマ目の渦）と習得ゲートは対象外・不変。

## Fiona（現在静止画: `fiona_*.png`）
| 優先 | state | 内容 | コマ数案 | hitFrame |
|---|---|---|---|---|
| P1 | attack | 通常攻撃（杖/弓など現行静止画の動作） | 6 | 4 |
| P1 | charge→heal | 回復の溜め→発動（2段、現行は charge 260ms→heal 500ms） | 溜め3＋発動4 | — |
| P1 | skill (windbloom) | 風の花（スキル） | 7 | 4 |
| P2 | damage | 被弾 | 3〜4 | — |
| P2 | guard | 防御（保持ポーズ＋開始） | 3 | — |
| P2 | evade | 回避 | 4 | — |
| P3 | prayer (wind prayer) | 風の祈り | 6〜7 | — |
| P3 | item | アイテム使用 | 4 | — |
| P3 | ko / victory / awaken / low_hp | 倒れ／勝利／誓い覚醒／瀕死ループ | 各4〜6 | — |

## Lou（現在静止画: `lou_*.png`）
| 優先 | state | 内容 | コマ数案 |
|---|---|---|---|
| P1 | charge→heal | 妖精の癒し（現行 charge 140ms→heal 660ms） | 溜め2＋発動5 |
| P1 | blessing | 風の加護（現行 1000ms） | 6〜7 |
| P2 | rune | ルーン（スキル/祝福の cut-in 系統は別素材として既存） | 6 |
| P2 | damage / evade | 被弾／回避 | 3〜4 |
| P3 | support | （現行ゲームでは未使用の状態） | — |
| P3 | ko / victory / low_hp | 倒れ／勝利／瀕死 | 各4〜6 |

## 納品後の実装手順（コード変更なし）
1. 連番PNGを `img/battle/characters/<actor>/motion/` に置く。
2. `tools/battle/install_motion_frames.py` で manifest を生成（`--ms`, `--hit`）。
3. `tests/battle/ally_motion_p3.py` を拡張（コマ順・hitFrame・idle復帰）して実ブラウザで検証。

## 検証状況の管理（Phase 3）
- Phase 3 追加: `tests/battle/ally_motion_p3_frames.py`（登録122コマの存在、各モーションの6コマ再生→idle復帰、low_hp一回再生保持、KO停止、PC/縦/横）。
- 実ブラウザ67項目 PASS（待機ループ・行動後idle復帰・被弾/ガード/勝利の状態遷移・風の舞ゲート残存）— **ただし全アニメーションコマの表示確認は未実施（画像読込・状態遷移の確認まで）**。
- Android実機: **UNVERIFIED**。Codex独立QA: **未実施**。
