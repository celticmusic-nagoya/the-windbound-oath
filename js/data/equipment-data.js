/* Equipment master (pure data). Kept apart from ItemData (consumables / key items): equipment has slot, stat mods and
 * a battle-motion variant, and its owned-count lives in Inventory's 'gear' bag; WHO wears it lives in EquipmentManager.
 * slot: weapon | head | body | accessory
 * mods: additive stat bonuses on top of level stats - any of maxHp maxMp atk def mag spd cri
 * motionVariant (weapons): key into img/battle/motion-manifest.json ('aidan:<variant>'); unknown/undelivered -> base motion / still
 * equipBy: character ids allowed to wear it (omit = anyone)
 * 木剣 has no stat bonus on purpose: the training sword is auto-equipped, and Raider / boss balance is protected.
 * Starting equipment is EMPTY on purpose: nothing here changes existing battle balance until the player (or a story event) equips it. */
window.EquipmentData = Object.freeze({
  slots: Object.freeze(['weapon', 'head', 'body', 'accessory']),
  slotNames: Object.freeze({weapon: '武器', head: '頭', body: '胴', accessory: '装飾品'}),
  items: Object.freeze({
    wooden_sword: {name: '木剣', slot: 'weapon', mods: {}, motionVariant: 'wooden', equipBy: ['aidan'], desc: '稽古用の木剣。軽くて、手に馴染む。（能力補正なし）'},
    iron_sword:   {name: '鉄の剣', slot: 'weapon', mods: {atk: 5}, motionVariant: 'iron', equipBy: ['aidan', 'liam'], desc: '村の鍛冶場で打たれた、飾り気のない鉄の剣。'},
    leather_cap:  {name: '革の帽子', slot: 'head', mods: {def: 1}, desc: 'なめした革を縫い合わせた、丈夫な帽子。'},
    cloth_tunic:  {name: '布のチュニック', slot: 'body', mods: {def: 1}, desc: '村の織り手が仕立てた、動きやすい布の上着。'},
    leather_armor:{name: '革の鎧', slot: 'body', mods: {def: 3}, desc: '胸と肩を硬い革で補強した軽鎧。旅の剣士の定番。'},
    bronze_ring:  {name: '銅の指輪', slot: 'accessory', mods: {maxHp: 5}, desc: '素朴な銅の指輪。身につけると少し体が軽い。'},
    // 王都限定（royal_arms）
    knight_helm:  {name: '騎士の兜', slot: 'head', mods: {def: 2}, desc: '王都の騎士団が使う鉄兜。重いが、頭をしっかり守ってくれる。'},
    chain_mail:   {name: '鎖帷子', slot: 'body', mods: {def: 5}, desc: '細かな鉄の輪を編み上げた鎧。王都の職人の仕事だ。'},
    silver_ring:  {name: '銀の指輪', slot: 'accessory', mods: {maxHp: 12}, desc: '澄んだ光を返す銀の指輪。身につけると力が湧いてくる。'},
    steel_sword:  {name: '鋼の剣', slot: 'weapon', mods: {atk: 9}, motionVariant: 'steel', equipBy: ['aidan', 'liam'], desc: '王都の鍛冶師が鍛えた鋼の剣。刃筋がまっすぐに通っている。'},
    emma_charm:   {name: 'エマの護符', slot: 'accessory', mods: {def: 2, maxHp: 8}, desc: 'エマが祈りを込めて編んだ護符。身につけると不思議と落ち着く。'}
  })
});
