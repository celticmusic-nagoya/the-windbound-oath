# 風の舞・魔弾MP回復 実装メモ (2026-10-13)

> **【2026-10-27 更新】** 風の舞の数値（回避率+15pt／敵3フェーズ／MP10／重ねがけ不可・再使用で持続更新）はユーザー判断により**暫定採用**であり、最終バランスではない。本文中の「確定」「作者決定」の記述はこの時点の記録。現行仕様: 習得後は通常戦闘・レイダー戦でコマンド表示（`?windDance=off` で無効化）。値は `js/data/support-magic-data.js` で調整する。

## 既存エンジン確認結果
- 「フェーズ」= 敵フェーズ(`enemyRound` 末尾の `BattleStatus.tick`)。バフの `remainingTurns` は **ラウンド開始時のスナップショットに含まれる効果だけ** がtickされるため、プレイヤー行動中に付与した効果は付与ラウンドの敵フェーズでは減らない。→ 付与時 `remainingTurns = フェーズ数-1`(=2) で「発動フェーズ含め3フェーズ」になる。
- 敵攻撃には命中/回避判定が **元々存在しない**(完全決定論)。回避率は基礎0%として `BattleStatus` に `eva_up`(加算pt、上限50%)を追加。`eva_up` が無い限り乱数も消費しない=従来戦闘は完全不変。
- 同種バフは種類キーで上書き(重ねがけは更新)= 推奨仕様と一致。
- プレイヤー攻撃(魔弾含む)には命中判定が無く、対象が生存していれば必ず命中。よって「命中時回復」と「実行時回復」は **対象が倒れている/無効な場合のみ差が出る**(実行時=回復する、命中時=回復しない)。

## 実装 (feat/wind-dance-battle)
- `js/data/support-magic-data.js`: 風の舞 = +0.15 / 3フェーズ / MP10 / 全体 / refresh(作者決定)。`fiona_bolt_mana` = 3(暫定)。
- `js/support-magic.js`: `WindDance.boltMana(timing)`, `mp()`, `effect()`。フラグ: `windDanceCommand`(従来) / `boltMana`=`off|hit|action`(既定off, `?boltMana=hit|action` でテスト)。
- `js/battle-status.js`: `eva_up`, `evasion()`, `dodges()`, 表示「回避↑」。
- `js/prologue-combat.js`: `castWindDance`(通常戦・レイダー戦, 習得+フラグ+MP10必須), `boltMana`(フィオナ通常攻撃のみ), 敵攻撃の回避判定(通常敵・増援・レイダー通常/破砕斬)。
- `index.html`: コマンド有効化(MP不足でdisabled)、ラベル「風の舞 MP10」。
- テスト: `tests/moss/m23_wind_dance_battle.py`(新規), `m21` 更新。

## フラグの状態 / 本番への影響
`windDanceCommand=false`, `boltMana=off` が既定。習得してもコマンドは出ず、回避判定は一切走らない。有効化は作者のバランス確認後。

## 未検証 / 要判断
- レイダー戦での回避は同一コードパスだが自動テストは通常戦のみ(今後追加)。
- 回避時の演出は文言ログ+通常戦のフロート「回避」のみ。専用モーション(evade)は未接続。
- 魔弾MP回復の最終値(量・タイミング)はCodex S のシミュレーション結果待ち。
