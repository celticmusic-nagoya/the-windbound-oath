# 装備システム

- データ: `js/data/equipment-data.js`（`EquipmentData`: slots weapon/head/body/accessory、items に name/slot/mods/motionVariant/equipBy）。消費アイテム・大事なもの（`ItemData`）とは別ファイル。
- 所持: `Inventory` が `gear` として保持（`count(id)`＝バッグ内のみ、`list('equip')`）。装備するとバッグ→スロットへ1個移動、外す／入れ替えで戻る。
- 管理: `js/equipment.js` `EquipmentManager`: `equip(char,id[,slot])` `unequip(char,slot)` `get` `bonus` `apply(char,baseStats)` `serialize/load/reset`、イベント `equipment-change`。
- 最終ステータス: `charStats()` が `EquipmentManager.apply` を通す（基本＋レベル成長＋装備加算）。**提案: 初期装備は能力補正なしの父の剣**で、従来のバランスは変わらない。
- 武器の `motionVariant` → `BattleMotion.setVariant(char, variant)` 自動切替（`aidan:wooden` など。コマ未納品なら基本モーション／静止画へフォールバック）。
- セーブ: 既存 v30 に任意項目 `equipment:{v:1,state:{aidan:{weapon:'father_sword'}}}` と `inventory.gear` を追加（IDのみ。数値は保存しない）。旧セーブは装備なしで読める。不正ID・スロット不一致・装備不可キャラは読込時に破棄。
- テスト: `python3 tests/system/equipment_test.py`

## UI・入手（装備UI編）
- UI: システムメニューの **EQUIP タブ**（`js/equipment-ui.js` / `css/equipment.css`）。キャラ選択→4スロット→候補（前後比較 ▲緑/▼赤）→装備/外す。矢印キー・Tab・Enter、390px幅で崩れない。
- 入手: 起動時に父の剣を自動装備（補正なし）。訓練開始では配布しない／エマのクエスト報告で `emma_charm`／崖の石積みの宝箱 `tr_c1_cairn` に `iron_sword`（`ItemData.treasureStage` により stage 15 まで開かない）。
- テスト: `tests/system/equipment_ui_flow_test.py`

提案の旧セーブ移行: エイダン装備の wooden_sword とバッグ内の木剣を father_sword へ置換。空装備・他武器・進行・セーブv30は維持。バッグ合算99超過はロードを中止し元データを保持。採用前に移行方針をレビューする。

## 2026-10-13 仕様変更(剣の固定・装備箇所・解放)
- 装備箇所: `weapon / head / body / accessory1 / accessory2`(旧セーブの `accessory` は `accessory1` に移行)。アクセサリは空いている方に入り、スロット指定で入れ替え可能。
- 武器: 契約後のエイダンは `oath_sword`(誓いの剣, `locked:true`)に固定。外す・替える操作は `reason:'locked'` で拒否。鉄の剣/鋼の剣は `equipBy:['liam']` のみ。強化(鍛冶屋+特殊素材)は未実装で、今回の補正は0。
- 物語連動: `EquipmentManager.setStoryWeapon(char,id)`(バッグを介さずに武器を設定)。祭壇27ページ目(契約)で `oath_sword`。ロード/DEVジャンプ時は `syncStoryEquipment()` がステージから決定(stage<=12: 父の剣、>=13: 誓いの剣)。
- 解放: `EquipmentManager.isUnlocked()/unlock()`(セーブは装備ペイロードの `unlocked:true`)。砦の支給(革の帽子・革の鎧・銅の指輪)で `grantStarterGear()`。stage15以上のセーブ読込でも1回だけ支給。解放前は EQUIP タブを非表示。
- テスト: `tests/system/equipment_test.py` `equipment_ui_flow_test.py` `tests/moss/m18_moss_scenario.py` `m20_sword_equipment.py`
