/* Shops (pure data). stock: item id -> price (G). Items may be consumables ('potion'), or equipment ids (js/data/equipment-data.js).
 * openFrom: first storyStage at which the shop sells. 15 = free roam after the prologue. Before that the shopkeeper only chats,
 * so nothing here can change the prologue / Raider balance. stock[].minStage: extra gate per item (default = openFrom).
 * stock[] gates (all optional, all must hold): minStage, flag:'talkFlag', quest:{id,state}. shop.region is informational.
 * Equipment may be bought once per piece (owned = bag + worn). Prices are a first proposal - tune freely. */
window.ShopData = Object.freeze({
  shops: Object.freeze({
    rilde_general: {name: 'リルド村の道具屋', openFrom: 15, stock: [
      {id: 'potion', price: 20}, {id: 'ether', price: 45},
      {id: 'leather_cap', price: 60}, {id: 'cloth_tunic', price: 50}, {id: 'bronze_ring', price: 90}, {id: 'leather_armor', price: 220}
    ]},
    // 砦の補給係: 実用品。村の道具屋より武器が一段上。
    dunvall_arms: {name: 'ドゥンヴァル砦の補給所', region: 'fort', openFrom: 15, stock: [
      {id: 'potion', price: 20}, {id: 'leather_cap', price: 60}, {id: 'leather_armor', price: 220}, {id: 'iron_sword', price: 380}
    ]},
    // 王都の雑貨商: 回復品（状態異常回復は戦闘側の対応後に追加予定）
    royal_general: {name: '王都の雑貨店', region: 'capital', openFrom: 15, stock: [
      {id: 'potion', price: 22}, {id: 'ether', price: 48}, {id: 'cloth_tunic', price: 55}, {id: 'bronze_ring', price: 95}
    ]},
    // 王都の武具店: 王都限定装備。steel_sword は「商業区の納品依頼」を達成した人にだけ並ぶ（stock[].quest）。
    royal_arms: {name: '王都の武具店', region: 'capital', openFrom: 15, stock: [
      {id: 'iron_sword', price: 400}, {id: 'knight_helm', price: 480}, {id: 'chain_mail', price: 650}, {id: 'silver_ring', price: 500},
      {id: 'steel_sword', price: 900, quest: {id: 'q_capital_delivery', state: 'reported'}}
    ]}
  })
});
