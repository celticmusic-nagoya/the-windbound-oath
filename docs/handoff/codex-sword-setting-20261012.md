# Codex 引継(第3弾): 剣設定の変更とエイダン素材(2026-10-12)

## 1. 確定した設定変更(ユーザー決定)
1. エイダンのアセットは今後すべて「背中に剣あり」で統一する(再生成素材は後日ユーザーが共有)。
2. **木剣は訓練場の少年剣士が振るだけ**にする。エイダンは騎士団長の父から譲られた剣を最初から持つ設定。
3. モス森の「剣を失う」場面を次の流れに変える: ゴブリンレイダー遭遇で剣が折られる → ルーの支援・フィオナの風の舞で一瞬足止め → 誓いの剣が反応しエイダンが剣と契約 → ボス戦突入。

## 2. 影響箇所(調査済み・未着手)
- 木剣の自動配布/装備: `index.html` 453〜454行(`wooden_sword` を追加・装備)。`js/equipment.js`、`js/data/equipment-data.js`(木剣定義、`motionVariant:'wooden'`)、`docs/system-equipment.md`、`tests/system/equipment_test.py`、`equipment_ui_flow_test.py`。
- 誓いの剣/戦闘: `js/prologue-combat.js`、`js/prologue-dev.js`、`js/field/aidan-field-actor.js`。
- モス森会話: `js/field/talk-data-scenes.js`(現行の「剣を失う」会話)。10ページ構成と会話UIの仕組みは変更しない。複数話者の間は全角スペースで改行(全会話共通ルール)。
- 引き継ぎ文書: `docs/handoff/scenario_handoff_for_chatgpt.md`(新設定を追記)。

## 3. 依頼(推奨の分担。まず調査と差分案まで。mainにはマージしない)
- 依頼G(調査): 上記の影響箇所と、初期装備・戦闘モーション(木剣→剣)・セーブ互換(装備に `wooden_sword` を持つ既存セーブの扱い)への影響を表にする。コード変更なし。
- 依頼H(実装案): 専用ブランチ `work/codex-sword-setting` で、木剣の自動装備を外し初期武器を「父の剣」(仮ID)にする案と、既存セーブの移行案を、差分として提示。テストの期待値更新も含める。
- シナリオ(モス森の場面の台詞・演出・フラグ)は Claude が担当するので触らない。

## 4. 触らないもの
`feat/field-height-prototype` の高さ関連ファイル(`field-height.js` ほか)。採用済みキャラ素材。本編のセーブ形式(変更が必要なら先に相談)。

## 5. アセット側の状況(参考)
- 側面歩行(剣なし・仮)は `feat/aidan-side-walk-v4`(058adf5)。生成指示文: `docs/art/chatgpt_aidan_walk_prompts.md`(a7b4b3b)。
- 再生成の不足18コマ(側面4・前斜め6・後ろ斜め6・待機2)がユーザーから届き次第、Claude が組み込む。
