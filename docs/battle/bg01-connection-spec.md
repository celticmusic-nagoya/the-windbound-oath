# BG-01 戦闘背景 接続仕様（Codex向け・2026-10-14）

戦闘UI再構築時に、BG-01の描画責務を壊さず移すための契約です。背景処理は戦闘ロジックから独立しています。

## 1. 構成
| 項目 | 内容 |
|---|---|
| 描画DOM | `<div id="battleBg" aria-hidden="true">`。`#attackBattle > .v2BattleStage` の**最初の子**（index.html）。 |
| 切替属性 | `#attackBattle[data-bg="BG-01"]`。属性がある時だけ `#battleBg` を表示。 |
| CSS | `css/style.css` 末尾の3ルール（`#battleBg` / `#attackBattle[data-bg] #battleBg` / `body.normalBattleMode #attackBattle[data-bg]>.v2BattleStage{background:none!important}`）。 |
| JS | `js/battle-background.js` → `window.BattleBackground`（`BG`登録表 / `forEnemy(id)` / `apply(key)` / `applyForEnemy(id)` / `clear()`）。 |
| 画像 | `img/battle/backgrounds/bg_BG-01_main.png`（1536×1024、無加工）。原本 `docs/art/delivered/bg01_20261014/bg_BG-01_main_original.png`。 |
| 前景 | `bg_BG-01_fore.png` は未制作。登録表の `fore:null` が予約枠。前景は仮生成しない。 |

## 2. 適用関数と呼び出しタイミング
- 呼び出し元は `startAttackBattle(id,hp)` の1箇所（`#attackBattle` を `display:block` にした直後、`BattleActorState.begin('normal')` の前）：`window.BattleBackground?.applyForEnemy(id)`。
- 戦闘ごとに必ず再適用されるため、前回のBG-01が次戦に残らない（BG対象外の敵では属性が外れる）。
- ボス戦（`startRaiderBattle`）は呼ばない。`#raiderBattle` は別DOMで対象外。
- 読み込み失敗時：`Image.onerror` で `data-bg` を外し、従来のステージグラデーションへ戻る（戦闘は継続）。

## 3. 拡縮・切り抜き・描画順
- `#battleBg`：`position:absolute; inset:0 -4% -14% -4%; background: center/cover no-repeat; background-position: 50% 0%`（登録表の `pos`）。
- 戦場より下へ14%・左右へ4%はみ出させ、ステージの `overflow:hidden` で切る。縦横比は維持（cover）。引き伸ばしなし。
- 目的：キャラ足元（PC 1280×720 で y≈648）が画像下部の岩・花の帯ではなく土の道に載るようにする。キャラの座標・倍率は一切変更していない。
- 表示範囲の実測：PC=ほぼ全幅、横844×390=左右が少し切れる、縦390×844=中央約35%。
- 描画順：`#battleBg` は z-index 0 でユニット（z20〜26）・HUD・COMMANDより下。`pointer-events:none`。ステージの `:after` 地平線（z1）は背景の上に残る。

## 4. 敵ID→背景ID
`js/battle-background.js` の `RULES`：`/^(attackGob|northGob)/ → 'BG-01'`。他の敵（mossSlime/forestBat/leafyBoar/fieldGob/forestGob 等）は未割当で従来表示。地域判定ロジックはない。背景追加は `BG` に登録し `RULES` に1行足すだけ。

## 5. 共通戦場コンテナへ移行する際の注意
1. `#battleBg` は**戦場領域の先頭の子**に置くこと（UI全体の背景にしない）。新コンテナでも `overflow:hidden` と positioned な祖先が必要。
2. `index.html` に同じ `id="battleField"` が2つある（旧line112の旧DOMと `.v2BattleStage#battleField`）。`getElementById('battleField')` は旧要素を返す。背景関連は `#attackBattle>.v2BattleStage` で参照する（テストもそうしている）。
3. ステージ背景のグラデーションは `body.normalBattleMode #attackBattle>.v2BattleStage{...!important}` 等の積み重ね。`data-bg` 時に `background:none!important` で打ち消している。UI再構築でこの積み重ねを整理する際は、BG有り＝グラデーション無し／BG無し＝従来グラデーション、の2状態を維持すること。
4. 属性名 `data-bg` の置き場所は `#attackBattle`。コンテナを統一するなら `apply()` の `root()` / `layer()` の2つのセレクタだけ更新すればよい。
5. ボス戦へ背景を広げる場合は、RULESに敵IDを足し、`startRaiderBattle` から `applyForEnemy` を呼ぶ＋ `#raiderBattle .rbField` 側に同等のレイヤーが必要（今回は対象外）。
6. 足元位置が変わる場合（座標・倍率・戦場の縦横比）は `pos` と `inset` のはみ出し量を再調整。PC/横/縦の3サイズで足元が土の道に載ることを確認する。
7. 回帰テスト：`tests/battle/bg01_background.py`（割り当て・レイヤー位置・非適用・読み込み失敗フォールバック・ボス非適用を3サイズで検証）。

## 6. 既知の未解決（本件の対象外）
- COMMAND展開時、横・縦画面で味方の足元が操作パネルに隠れる（既存UI）。
- X2：DEVセーブ復元の3失敗（仕様判断待ち）。
