# M6 ③ 宝箱報酬と所持品（特別アイテム）設計案

実装はしない。承認後に別ブランチで実装する前提の設計。

## 現状（M5.5）
- 所持品は `battleItems = {potion, ether}` と `gold` のみ（`index.html`）。セーブはルート直下に `battleItems` `gold`。
- 宝箱の開封済みは `PrologueProgress` v2 の `moss.opened[]`。報酬は `MossForestStory` の `TREASURE` 表（potion/ether/gold）。
- 特別アイテム（風よけの護符 / 古びたルーン片）は M4 の文言のみで、データ実体なし。M5.5 では ether/potion に置換済み。

## 提案
### 1. アイテムマスタ `data/items.json`
```json
{ "potion":{"name":"きずぐすり","kind":"consumable","stack":99,"battle":true},
  "ether": {"name":"魔力の雫","kind":"consumable","stack":99,"battle":true},
  "charm_windward":{"name":"風よけの護符","kind":"key","stack":1,"desc":"…"},
  "rune_shard_old":{"name":"古びたルーン片","kind":"key","stack":1,"desc":"…"} }
```
- `kind`: `consumable`（戦闘/メニューで使用）/ `key`（大事なもの：使用・売却・消費不可）/ 将来 `equip`。
- 既存の `battleItems` は**消費アイテムの数量表のまま維持**（戦闘コードを触らない）。

### 2. 所持データ `Inventory`（新モジュール `js/inventory.js`）
- `Inventory.add(id,n)` / `has(id)` / `count(id)` / `list(kind)` / `serialize()` / `load(obj)`。
- 消費アイテムは `battleItems` を内部で読み書き（二重管理しない）。`key` は `keyItems:{id:count}`。
- 宝箱の報酬表を `{potion:2}` 形式から `Inventory.grant(rewards)` に統一。トーストも `data/items.json` の名称から生成。

### 3. セーブ
- ルートに `inventory:{key:{charm_windward:1}}` を追加。`version` は 29→30。**v29 は読み込み可**（`inventory` 無しなら空）。
- 既存セーブの救済（冪等・再付与なし）：`moss.opened` に `tr_a2_overlook` / `tr_a3_shrine` があり `inventory.key` に無ければ、ロード時に一度だけ付与。→ 「箱は開けたのに護符が無い」を防ぐ。
- 開封済みフラグと所持が同じセーブにあるので、M5.5 と同じ整合（二重付与なし）を保てる。

### 4. UI
- システムメニューに「大事なもの」タブ（名称・説明・個数）。消費アイテムは既存の戦闘/メニュー表示のまま。
- 入手時：トースト＋（初回のみ）短い獲得演出は後回し。

### 5. 宝箱テーブルの扱い
- `TREASURE` を `data/treasure.json`（id → rewards）へ外出し。マップJSONの `treasurePoints[].id` と対応。
- どの箱に特別アイテムを入れるかは物語側で決める（下記）。

## 要判断（ユーザーに確認したい）
1. 護符・ルーン片に**効果**を持たせるか（例：護符＝森の穢れ耐性、ルーン片＝A3の石碑イベントの鍵）。無効果の収集品でよいか。
2. 護符・ルーン片を置く箱（現状：護符＝`tr_a2_overlook`、ルーン片＝`tr_a3_shrine` を維持する想定）。
3. 既存セーブ救済（上記3）を入れるか。M5.5以降に開けた箱は ether/potion を受け取っており、護符を追加付与してよいか。
4. 「大事なもの」の上限や並び順、捨てる/使うの可否。

## 実装順（承認後）
1. `data/items.json` + `Inventory`（battleItems連携）→ 2. セーブ v30 + 救済 → 3. 宝箱テーブル外出し → 4. 大事なものタブ → 5. テスト（開封→入手→セーブ→ロード→再開封で増えない／v29読込／救済の冪等）。
