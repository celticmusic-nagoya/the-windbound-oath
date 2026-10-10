# 装備システム

- データ: `js/data/equipment-data.js`（`EquipmentData`: slots weapon/head/body/accessory、items に name/slot/mods/motionVariant/equipBy）。消費アイテム・大事なもの（`ItemData`）とは別ファイル。
- 所持: `Inventory` が `gear` として保持（`count(id)`＝バッグ内のみ、`list('equip')`）。装備するとバッグ→スロットへ1個移動、外す／入れ替えで戻る。
- 管理: `js/equipment.js` `EquipmentManager`: `equip(char,id[,slot])` `unequip(char,slot)` `get` `bonus` `apply(char,baseStats)` `serialize/load/reset`、イベント `equipment-change`。
- 最終ステータス: `charStats()` が `EquipmentManager.apply` を通す（基本＋レベル成長＋装備加算）。**初期装備は空**で、従来のバランスは変わらない。
- 武器の `motionVariant` → `BattleMotion.setVariant(char, variant)` 自動切替（`aidan:wooden` など。コマ未納品なら基本モーション／静止画へフォールバック）。
- セーブ: 既存 v30 に任意項目 `equipment:{v:1,state:{aidan:{weapon:'wooden_sword'}}}` と `inventory.gear` を追加（IDのみ。数値は保存しない）。旧セーブは装備なしで読める。不正ID・スロット不一致・装備不可キャラは読込時に破棄。
- テスト: `python3 tests/system/equipment_test.py`
