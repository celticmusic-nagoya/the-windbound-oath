/* Item master + treasure reward table (M6). Pure data; no behaviour.
 * kind: 'consumable' (battle/menu use; counts live in battleItems), 'key' (大事なもの: no effect, not usable/sellable).
 * 'gold' is a reward currency, not an item. Treasure ids match data/maps/*.json treasurePoints[].id. */
window.ItemData = Object.freeze({
  items: Object.freeze({
    potion:        {name:'きずぐすり', kind:'consumable', desc:'傷口に塗る薬草の軟膏。HPを回復する。'},
    ether:         {name:'魔力の雫',   kind:'consumable', desc:'飲むと魔力が静かに満ちる青い雫。MPを回復する。'},
    charm_windward:{name:'風よけの護符', kind:'key',      desc:'旅人の無事を祈って編まれた、小さな護符。風に揺れると澄んだ音がする。'},
    herb_moss:     {name:'薬草', kind:'key', desc:'森の近くに生える、傷みを和らげる草。畑の土を整えるのにも使われる。'},
    silver_comb:   {name: '銀の櫛', kind: 'key', desc: '細かな花の彫りが入った銀の櫛。誰かの大切な持ち物らしい。'},
    rune_shard_old:{name:'古びたルーン片', kind:'key',    desc:'古いルーンが刻まれた石の欠片。耳を寄せると、かすかに風の音がする。'}
  }),
  // chest id -> minimum storyStage before it can be opened (progression gear; 15 = free roam after the prologue)
  treasureStage: Object.freeze({tr_c1_cairn: 15, tr_a1_wayside_late: 15, tr_a2_ledge_late: 15}),
  // rewards: item id -> count, plus optional gold
  treasure: Object.freeze({
    tr_a1_hollow:{potion:2,herb_moss:1}, tr_a1_stream:{potion:1,herb_moss:1}, tr_a1_meadow:{gold:30}, tr_a1_ford_hidden:{ether:1,gold:20},
    tr_a2_overlook:{ether:1,charm_windward:1}, tr_a2_alcove:{potion:1,gold:20,herb_moss:1}, tr_a2_fern:{potion:1,herb_moss:1}, tr_a2_marker_side:{ether:1,gold:30},
    tr_a3_shrine:{potion:1,ether:1,rune_shard_old:1}, tr_a3_hollowlog:{potion:2}, tr_a3_raider:{ether:1,gold:50}, tr_a3_sentinel:{potion:1,gold:40},
    // 装備箱（stage15まで開かない = プロローグ/Raiderのバランス不変）
    tr_a1_wayside_late:{bronze_ring:1}, tr_a2_ledge_late:{leather_armor:1},
    // ドゥンヴァル砦 / 王都（stage15以降にしか行けない）
    tr_f1_barracks:{potion:2}, tr_f2_tower:{ether:1,gold:60}, tr_f3_armory:{gold:80,cloth_tunic:1}, tr_r1_alley:{gold:50}, tr_r2_garden:{silver_comb:1}, tr_r3_backyard:{potion:1,gold:30},
    // 風見の断崖 (cliff_moher_01_spiral_ascent): herb gathering spots + one chest
    tr_c1_herb_slope_a:{herb_moss:1}, tr_c1_herb_slope_b:{herb_moss:1}, tr_c1_herb_ramp:{herb_moss:1}, tr_c1_herb_lip:{herb_moss:1}, tr_c1_cairn:{potion:1,gold:40,iron_sword:1}
  })
});
