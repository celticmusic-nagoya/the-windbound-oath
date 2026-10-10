# M6 ④ FieldTalk の動的会話分岐

**実装済み**（`work/moss-forest-m6-inventory-talk`）。
- 条件評価：`js/field/talk-conditions.js`（純関数。`flag/stage/sealOpen/treasure/item/talked/quest` と `all/any/not`。未知キーは偽）。テスト：`tests/field/talk_conditions.test.js`。
- 台詞データ：`js/field/talk-data.js`（従来の村人・長老・エマの台詞を移植。旧 `lind-dialogue.js` / `forest-warnings.js` は廃止）。
- 表示：話者名プレート（`.talkName`）＋台詞。`話者「…」　話者2「…」` の文字列は話者ごとにページ分割。タップ/Enter/Spaceで進行。
- 選択肢：`choice.options[{label,reply,set,give}]`。ボタン（44px以上）または数字キー1〜9。選択中は本文タップで進まない。
- 効果：`set`（会話フラグ。セーブ対象）、`give`（`Inventory.grant`。入手を専用ページで表示）。
- セーブ：`version:30` の `talk:{seen,cycle,flags}`。未知のエントリIDや不正値は読み込み時に捨てる。
- クエスト連携は `FieldTalk.setQuestProvider(fn)` と `field-talk` / `field-talk-end` イベント（クエスト本体は未実装）。
- テスト：`tests/moss/m6_talk.py`（プレート・ページ・選択肢・条件・once・効果・セーブ往復）。以下は設計時の記述。

## 現状
- `FieldTalk.talk(id,{source})` が唯一の入口。提供元（`LindDialogue`, `ForestWarnings`）が `register(ids, lineFn)` で行を返す。
- 分岐は封印の開閉だけ（`PrologueProgress.count()>=3 || storyStage>=13`）。各提供元がバラバラに判定している。
- 順繰り表示用の状態（`used`）はメモリのみ。セーブされない。

## 提案
### 1. 会話をデータ化 `data/talk/<area>.json`
```json
{ "npc":"elder",
  "entries":[
    { "id":"elder_after_seal", "priority":30, "when":{"all":[{"flag":"moss_a3_seal_open"}]},
      "lines":["長老「…」"], "mode":"cycle" },
    { "id":"elder_intro", "priority":10, "when":{"all":[]},
      "lines":["…","…"], "mode":"cycle", "once":false } ] }
```
- 選択規則：`when` を満たす entries のうち **priority 最大**。同点は定義順。
- `mode`: `cycle`（順繰り）/ `once`（一度きり、以降は次点へ）/ `random`。
- 条件の語彙（小さく固定）：`flag`（真偽フラグ）、`stage`（`storyStage` 範囲）、`sealOpen`、`treasureOpened:<id>`、`hasItem:<id>`（M6③）、`talked:<entryId>`、`quest:<id>:<state>`。`all/any/not` で結合。
- 効果（任意）：`set`（フラグ）、`give`（アイテム）、`quest`（開始/進行）、`toast`。1回だけ実行。

### 2. 提供元の統一
- `FieldTalk.loadTable(json)` が NPC ごとに自動で `register`。`LindDialogue` / `ForestWarnings` の表は同じ JSON へ移し、関数提供元は特殊処理用（エマ等）として残せる。
- 入口は今のまま：部屋UI・村UI・DEVレビューが `FieldTalk.talk(id,{source})`。新しい入口（歩いて近づき決定キー、タップ）も同じ関数へ。
- 話者の距離/向き判定、会話中の移動ロック、`field-talk` イベント（ログ・クエスト進行の購読用）は共通化済みイベントに乗せる。

### 3. セーブ
- `talk:{seen:[entryId…], cycle:{npc:index}}` を `PrologueProgress` v2 とは別のルートキーで保存（v29→30 と同時、無ければ空）。
- 保存対象は「一度きり会話の消化」と順繰りの位置のみ。読み込み時に未知の entryId は捨てる（データ更新に強くする）。

### 4. 村イベント/クエスト連携
- クエストは `quest:<id>:<state>` を条件に使うだけ（FieldTalk はクエストの実体を持たない）。
- `field-talk` イベント → クエスト側が購読して状態を進める。会話から直接ストーリー進行を呼ばない（M4 の `onEvent` 方式に揃える）。

### 5. テスト計画
- 条件の単体テスト（node）：優先度、once、cycle、any/all/not。
- E2E：封印前/後でエマ・長老の行が切り替わる（既存 `m4_npc.py` を data 経由で再実行）、セーブ→ロードで once が復活しない、未知 id を含むセーブが壊れない。

## 要判断
1. 条件に使うフラグの正式名一覧（クエスト設計と合わせたい）。
2. 会話ウィンドウの見た目（話者名・選択肢・立ち絵）をどこまで入れるか。現状は `say(text)` の1行表示。
3. 選択肢（はい/いいえ）を `lines` の拡張として入れるか、別イベントにするか。

## 実装順（承認後）
1. 条件評価器 + テーブル読み込み（既存の台詞を移植、挙動不変）→ 2. セーブ → 3. 新入口（近接+決定）→ 4. 効果（set/give/quest）→ 5. クエスト連携。
