# Codex 指示 BB〜FF (2026-10-13 午後) — X/Y/Z 納品確認後の追加分
基準: 最新main(7abb9f3以降)。standing-orders に従う。ゲームのランタイムコード(js/)・採用素材は変更しない。tests/tools/docs のみ。
先に `work/codex-tz`(X/Y/Z納品)はClaudeが統合する。AA(高さ仕様draft)は進行中のものを続行。以下はAAの後に順に。

## BB: エイダン新歩行素材の受入検品(自動テスト化)
本日、剣付きエイダンの歩行素材が入れ替わった(main 93b6193 / 373cd44。`img/field/characters/aidan/` 24枚、`js/field/aidan-field-assets.js`)。
- `tests/moss/m28_aidan_walk_assets.py` を新規: (1)マニフェスト24枚=実ファイル、孤立PNGなし (2)全フレームで足元アンカー行が一致(足元y±1px) (3)体高が方向間で±4%以内(待機と歩行) (4)キャンバス端での切れなし(bbox が端に触れない) (5)左右歩行4コマ・前後6コマ、待機4方向 (6)実ゲーム(index.html, devJump('forest'))で各方向へ移動中、表示中フレーム名が方向と一致(上=walk_up、下=walk_down…) — 手順は Claude の確認スクリプト /tmp 相当を参考に、`MossForest.goFeet` と `.forest-aidan:not([hidden])` を使う。
- 既知の見た目問題(検品で「警告」として記録、失敗にはしない): 前後歩行(walk_down/up)は正面・背面でなく斜め(3/4)向きの絵。待機(正面)との向きの差を数値(顔/体の向きは難しいので、バウンディングボックス幅の比較などで可)で警告化できれば提案。
- 成果: テスト、`docs/qa/aidan-walk-acceptance-20261013.md`。

## CC: リーフィーボア新素材の検品と KO 終端の確認
main 7abb9f3 で差し替え済み(戦闘 `img/battle/enemies/leafy_boar/`、フィールド `img/field/monsters/leafy_boar/`、ko 6コマ、`img/battle/motion-manifest.json`)。
- `tests/moss/m29_leafy_boar_assets.py`: ファイル数/寸法(戦闘480x400・フィールド240x160)/足元行(戦闘390・フィールド154)/中心x/KO 6コマ全再生。
- KO最終コマは「薄く消えかけた絵」。実戦闘で KO 後にその絵が画面に残り続けるか、敵が消えるタイミングとの前後関係を観測して報告(js変更は不可。残る場合は提案のみ)。
- フィールド姿勢の対応(歩き=1-4、警戒=5、溜め=6-7、突進=8-10、息切れ=11)が field-monsters.js の art.poses と整合しているか、突進中に正しいコマが出るか(m15d を参考)。

## DD: 風の舞を「非ナイーブ方針」で再評価(数値は決めない)
Tの固定方針(攻撃のみ)では風の舞は不利だった。回復・TPスキル・風斬りなど現実的な行動を含む複数の方針(攻撃優先/回復優先/風の舞優先/混合)で、通常戦闘とレイダー戦の勝率・被ダメ・ターン数を比較。魔弾MP回復 +0/+3/+4、風の舞 回避+10/+15/+20pt、MP 8/10/12 の格子を表にする。`tools/sim/` と `docs/handoff/wind-dance-policy-sim.md`。最終数値の推奨はせず、差の大きさと傾向だけ。js/変更不可。

## EE: レイダー戦の回避の自動テスト + 高さデータの不正値検査
(1) `tests/moss/m30_raider_dodge.py`: レイダー戦(`heroRaider`)で風の舞を使い、レイダーの通常攻撃/叩きつけ(smash)の各対象で回避が発動した/しない両方の経路を、乱数を固定して確認。回避時に `evade` ポーズ(aidan_evade/fiona_evade)が出ること。`PrologueCombat.dodged`・`BattleStatus.dodges` を参照。
(2) Rの未解決: spawn.level の検証。`tools/moss/validate_height_schema.py`(新規)で、height 付きJSON(`data/maps/*.json`、`data/height-specs/*.json`)の level 値の範囲・型・存在しない level への参照・spawn が到達不能な level にいないか を検査。旧セーブ(map/x/yのみ)が高さ有効後にどの level へ解釈されるか曖昧になる座標の一覧も `docs/qa/old-save-level-ambiguity.md` に。

## FF: 全回帰の再実行(最新main)
V/O の runner で最新mainを全実行し、`docs/qa/full-regression-<date>.md` に。BB/CC/EE の新規テストも含める。新規失敗があれば原因の切り分けまで。

## 報告
各項目完了ごとに `codex-status.md` を更新して通常push。利用制限で止まったら wip コミット。
