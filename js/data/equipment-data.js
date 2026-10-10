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
    emma_charm:   {name: 'エマの護符', slot: 'accessory', mods: {def: 2, maxHp: 8}, desc: 'エマが祈りを込めて編んだ護符。身につけると不思議と落ち着く。'}
  })
});
