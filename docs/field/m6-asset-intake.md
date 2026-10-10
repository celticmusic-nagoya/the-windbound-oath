# M6 アセット受け入れ手順（村人歩行フレーム / モスの森本番アセット）

コードを触らずに「PNGを置く → 登録 → チェッカー → 目視」で差し替えられる構成にしてある。
（ドライランで検証済み：`tests/lind/walk_intake.py`, `tests/moss/m6_asset_swap.py`。どちらも終了時に仮素材と登録を元に戻す）

共通ルール：**1コマ＝1枚の透過RGBA PNG**。アニメ用に1枚へ詰めたスプライトシートは使わない。

---
## A. 村人の歩行フレーム（残り7体 / 農夫・エマの追加コマ）

### 現状（`python3 tools/lind/check_walk_frames.py`）
| NPC | 歩行コマ | 状態 |
|---|---|---|
| boy / girl / farmer_female | 4 | 導入済み |
| emma | 3 | 導入済み（追加コマ歓迎、最大6） |
| farmer_male | 旧1枚（`farmer_male_walk.png`） | 新コマを入れると旧1枚より優先される |
| young_man / young_woman / elder_man / elder_woman / merchant / innkeeper / caretaker | なし | **待機中（7体）** |
| fisherman | 専用方式（釣り） | 対象外 |

### 受け入れスロット（仕様）
- 配置先：`img/field/lind/npc/villagers/<id>_walk_01.png … _06.png`（emma は `img/field/lind/npc/emma/`）。
- **枚数は2〜6、欠番なし、歩行サイクル順**（01→02→…→最後→01 とループ）。
- **キャンバスは `<id>_idle.png` と同寸**。足元の基準線（最下端の不透明ピクセル）が idle と大きくずれると跳ねて見えるため、チェッカーが弾く。
- 描画サイズは idle の可視範囲から決まる（歩行コマで体が伸縮しない）。
- 速度：歩き4コマ/秒、走り6コマ/秒（`lind-npcs.js` の `WALK_FPS`/`RUN_FPS`）。歩いている間だけ時計が進む。
- 歩行ルーチンを持たないNPCは、コマを入れても今は動かない（動かすのは別途ルーチン追加）。

### 手順
1. 納品PNGを任意のフォルダに `<id>_walk_NN.png` の名前で置く。
2. 検証のみ：`python3 tools/lind/install_walk_frames.py <dir> --dry-run`
3. 導入：`python3 tools/lind/install_walk_frames.py <dir> --write-bounds`
   （PNGをidleキャンバスへ揃えて配置し、`js/field/lind-content-bounds.js` に `<id>_walk_NN` を登録。再導入時は古い高番号コマを自動削除）
4. 確認：`python3 tools/lind/check_walk_frames.py`（bounds と PNG の不一致・欠番・サイズ違いを検出）
5. 目視：DEVレビューで該当NPCの歩行を確認。順番が気になる場合は番号を入れ替えて再導入。

`exec-*.png` 形式（前回納品）は従来の `tools/lind/prepare_walk_frames.py` + `walk_frames_manifest.json` のまま使える。

---
## B. モスの森 本番アセット（`docs/field/moss-forest-asset-requests.md`）

### 仕組み
`img/field/moss/manifest.json` の規則は**上から順に最初に一致したもの**が勝つ。本番素材の規則を、仮素材（`"standin": true`）や `"file": null` の**前**に書く。

| セクション | 対象 | 例 |
|---|---|---|
| `node` | マップの props / 個別描画のscatter（木・岩・低木・anc_* ・prop_* ・fx_*） | `{"match":"^tree_ancient","file":"real/tree_ancient_01.png","w":260,"h":380}` |
| `layer` | 地面に焼き込まれる細かい植物（草・花・苔） | `{"match":"^veg_moss_patch","file":"real/moss_patch.png","w":96,"h":60}` |
| `ground` | 地面タイル（正方形・継ぎ目なし） | `"grass":"real/ground_grass.png"` |
| `entity` | 宝箱・異形・封印・ルー・フィオナ | 下記 |

`w`,`h` はワールドpx（画像の見かけの大きさ。足元中央が基準）。

`entity` のキー（未登録＝色つき仮ブロックのまま）：
`chest_closed` / `chest_open` / `symbol` / `seal`（清浄）/ `seal_corrupted`（穢れ）/ `lou` / `fiona`
例：`"entity": {"chest_closed": {"file":"real/chest_closed.png","w":64,"h":52}}`
（エイダンは別系統：`AidanFieldAssets`。ルーは手のひらサイズなので `w,h` は小さく。）

### 手順
1. PNG（透過RGBA）を `img/field/moss/real/` へ置く。
2. `manifest.json` に規則を追加（上記の順序ルール）。
3. `python3 tools/moss/check_assets.py --table`
   - ERROR：ファイル欠落 / RGBAでない / w,h 無し / 正規表現エラー / entityキー不正 → 修正必須。
   - warn `SHADOWED`：その規則は前の規則に負けて効かない → 位置を上へ。
   - 末尾の `real= standin= placeholder=` で、本番化率（node/layer別）を確認できる。
4. 目視：`?dev` の森ジャンプ（A1/A2/A3）で表示確認。戻したいときは規則を消すだけで仮素材に戻る。

### 影響範囲（確認済み）
- コード変更なしで差し替わる（`m6_asset_swap.py`：本番規則あり→実素材、削除→仮素材、コンソールエラー0）。
- `file: null` の規則（`tree_log/ancient/dead`）は「画像なし＝色ブロック」を意味する。本番素材はその**前**に置く。
- 画像が読み込めない場合はその規則だけ無効化され、色ブロックにフォールバック（クラッシュしない）。
- 追加素材は当たり判定を変えない（当たりはマップデータ側）。見た目サイズ `w,h` を変えても衝突は変わらない。

### 未確定（要判断）
- A3の古木・遺構（anc_*）は足元基準で置かれる。大きい画像は後ろの物を隠すので、`h` の上限目安を決めたい。
