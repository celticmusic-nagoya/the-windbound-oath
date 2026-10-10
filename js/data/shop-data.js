/* Shops (pure data). stock: item id -> price (G). Items may be consumables ('potion'), or equipment ids (js/data/equipment-data.js).
 * openFrom: first storyStage at which the shop sells. 15 = free roam after the prologue. Before that the shopkeeper only chats,
 * so nothing here can change the prologue / Raider balance. stock[].minStage: extra gate per item (default = openFrom).
 * Equipment may be bought once per piece (owned = bag + worn). Prices are a first proposal - tune freely. */
window.ShopData = Object.freeze({
  shops: Object.freeze({
    rilde_general: {name: 'リルド村の道具屋', openFrom: 15, stock: [
      {id: 'potion', price: 20}, {id: 'ether', price: 45},
      {id: 'leather_cap', price: 60}, {id: 'cloth_tunic', price: 50}, {id: 'bronze_ring', price: 90}, {id: 'leather_armor', price: 220}
    ]}
  })
});
