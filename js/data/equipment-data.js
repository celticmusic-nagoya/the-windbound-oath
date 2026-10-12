/* Equipment master (pure data). Kept apart from ItemData (consumables / key items): equipment has slot, stat mods and
 * a battle-motion variant, and its owned-count lives in Inventory's 'gear' bag; WHO wears it lives in EquipmentManager.
 * item slot: weapon | head | body | accessory  (the wearer has TWO accessory sockets: accessory1 / accessory2)
 * locked: true = cannot be unequipped or replaced (誓いの剣: Aidan's weapon is fixed after the contract; upgrades are done at a smith with special materials)
 * mods: additive stat bonuses on top of level stats - any of maxHp maxMp atk def mag spd cri
 * motionVariant (weapons): key into img/battle/motion-manifest.json ('aidan:<variant>'); unknown/undelivered -> base motion / still
 * equipBy: character ids allowed to wear it (omit = anyone)
 * 父の剣 has no stat bonus; existing Raider / boss balance is protected. 木剣 is NPC-only.
 * Father sword uses the delivered base Aidan motion (no weapon variant). */
window.EquipmentData = Object.freeze({
  slots: Object.freeze(['weapon', 'head', 'body', 'accessory1', 'accessory2']),
  slotNames: Object.freeze({weapon: '武器', head: '頭', body: '胴', accessory1: '装飾品①', accessory2: '装飾品②'}),
  items: Object.freeze({
    wooden_sword: {name: '木剣', slot: 'weapon', mods: {}, motionVariant: 'wooden', equipBy: [], desc: '稽古用の木剣。軽くて、手に馴染む。（能力補正なし）'},
    father_sword: {name: '父の剣', slot: 'weapon', mods: {}, equipBy: ['aidan'], desc: '騎士団長の父から譲られた剣。（能力補正なし・名称とIDは提案）'},
    oath_sword:   {name: '誓いの剣', slot: 'weapon', mods: {}, locked: true, equipBy: ['aidan'], desc: '風の誓いに応えて目覚めた剣。外すことも替えることもできない。鍛冶屋で特殊素材を使えば鍛え直せる(強化は今後実装)。'},
    iron_sword:   {name: '鉄の剣', slot: 'weapon', mods: {atk: 5}, motionVariant: 'iron', equipBy: ['liam'], desc: '村の鍛冶場で打たれた、飾り気のない鉄の剣。'},
    leather_cap:  {name: '革の帽子', slot: 'head', mods: {def: 1}, desc: 'なめした革を縫い合わせた、丈夫な帽子。'},
    cloth_tunic:  {name: '布のチュニック', slot: 'body', mods: {def: 1}, desc: '村の織り手が仕立てた、動きやすい布の上着。'},
    leather_armor:{name: '革の鎧', slot: 'body', mods: {def: 3}, desc: '胸と肩を硬い革で補強した軽鎧。旅の剣士の定番。'},
    bronze_ring:  {name: '銅の指輪', slot: 'accessory', mods: {maxHp: 5}, desc: '素朴な銅の指輪。身につけると少し体が軽い。'},
    // 王都限定（royal_arms）
    knight_helm:  {name: '騎士の兜', slot: 'head', mods: {def: 2}, desc: '王都の騎士団が使う鉄兜。重いが、頭をしっかり守ってくれる。'},
    chain_mail:   {name: '鎖帷子', slot: 'body', mods: {def: 5}, desc: '細かな鉄の輪を編み上げた鎧。王都の職人の仕事だ。'},
    silver_ring:  {name: '銀の指輪', slot: 'accessory', mods: {maxHp: 12}, desc: '澄んだ光を返す銀の指輪。身につけると力が湧いてくる。'},
    steel_sword:  {name: '鋼の剣', slot: 'weapon', mods: {atk: 9}, motionVariant: 'steel', equipBy: ['liam'], desc: '王都の鍛冶師が鍛えた鋼の剣。刃筋がまっすぐに通っている。'},
    emma_charm:   {name: 'エマの護符', slot: 'accessory', mods: {def: 2, maxHp: 8}, desc: 'エマが祈りを込めて編んだ護符。身につけると不思議と落ち着く。'}
  })
});
