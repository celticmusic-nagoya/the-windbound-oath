# M6 クエスト連動会話・NPC配置構造

## 1. クエスト（`js/quest.js` / `js/field/quest-data.js`）
- 状態：`未受注(unaccepted)` → `進行中(active)` → `達成(complete)` → `報告済み(reported)`。
  保存するのは `active` / `reported` だけ。**`complete` は `active` かつ達成条件が成立したときに自動で導出**されるので、所持品やフラグとずれない。
- 定義：`quest-data.js` の `{name, complete:<条件>, reward:{item|gold:n}, objective:{active,complete}}`。条件は会話と同じ語彙（`item` `flag` `treasure` `talked` `quest` `all/any/not`）。
- 操作：会話の効果 `quest:{id,action:'accept'|'report'}`。`report` は達成条件が成立していれば（未受注でも）完了し、報酬を付与して「…を手に入れた。」ページを出す。
- 表示：システムメニュー `QUEST` タブ（進行中 / 達成（未報告）/ 報告済み＋目的）。
- セーブ：ルートの `quests:{id:state}`。無いセーブ・不正な値は未受注として読み込む。

## 2. 会話データ
- 基本表：`js/field/talk-data.js`（既存の台詞）。クエスト/大事なもの連動：`js/field/talk-data-quests.js`。**同じNPCの表は entry id で統合**されるので、ファイルを分けて足せる。
- 条件で使える状態：`{quest:{id,state}}`、`{item:'id',min:n}`、`{flag:'名前'}`、`{talked:'entryId'}`、`{treasure:'箱id'}`、`{sealOpen:true}`、`{stage:[a,b]}`。
- 効果：`quest` / `set` / `give`。選択肢の各項目にも書ける。
- 優先度の目安：報告(60) > 進行中(50) > 受注の打診(45) > 事後の一言(30) > 既存の通常/封印後の台詞(10/20)。

### 仮（DRAFT）シナリオ
`talk-data-quests.js` と `quest-data.js` の中身は**仕組みの検証用の仮シナリオ**。差し替え・削除は自由（`talk-data-quests.js` を外せば会話は元に戻る）。
- エマ「エマの護符」：通常の台詞を一度聞くと打診（探してみるよ／今は難しい）。護符（`tr_a2_overlook` の宝箱）を持って話しかけると報告→報酬 魔力の雫×1。護符は取り上げない。先に護符を持っていれば、その場で完了。
- 長老：古びたルーン片（`tr_a3_shrine`）を持つと「見せる／見せない」。見せるとフラグ `elder_saw_shard`、以後の一言が変わる。
- 注意：エマは現状DEVレビュー経由でのみ話せる（長老は長老の家で通常プレイでも話せる）。

## 3. NPCレジストリ（`js/field/lind-npc-registry.js`）
NPCの配置・会話id・歩行ルーチン・登場条件・歩行コマの枠を**1か所**に集約（以前は `lind-npcs.js` / `lind-village-life.js` / `lind-emma.js` に分散）。
| 項目 | 内容 |
|---|---|
| `x, footY, height` | 初期位置（足元）と描画の高さ |
| `talk` | FieldTalk のID。台詞が無い間は `null`（elder_man / farmer_female） |
| `routine` | 歩行ルーチン `{kind,speed,offsets,rests}` / `motion`: `play`（子ども）`fishing`（釣り人） |
| `appears` | 登場条件（会話と同じ条件。`null`＝常に）。村の一覧を作る時点で評価 |
| `walk` | `{frames:N}` 導入済み / `{frames:null}` 納品待ち / `{legacy:'..'}` 旧1枚 |

新NPCの追加は「レジストリに1行＋会話の表」だけ。`lind-emma.js` は廃止（エマもレジストリ）。
**歩行コマが納品されたら**：`install_walk_frames.py --write-bounds` で導入 → レジストリの `walk.frames` を枚数に更新。`tests/field/npc_registry.test.js` が、PNG・bounds・`walk.frames` の食い違い（更新漏れ）を検出する。
納品待ち（7体）：young_man / young_woman / elder_man / elder_woman / merchant / innkeeper / caretaker。農夫・エマの追加コマは、同じ手順で上書き導入（農夫は新コマを入れると旧1枚より優先）。

## テスト
`tests/moss/m6_quest.py`（状態遷移・選択・報酬・セーブ・長老のルーン片）、`tests/field/npc_registry.test.js`（配置の整合・歩行コマ枠）、既存の `m4_npc.py` / `walk_intake.py` / `m6_devui.py`。
