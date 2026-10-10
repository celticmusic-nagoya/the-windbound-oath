/* Shop: buying (logic) + a small modal (UI). Data: js/data/shop-data.js. Gold lives in the legacy global `gold`.
 * Shop.open(shopId) is triggered from a talk choice effect {shop:'rilde_general'} (see js/field/field-talk.js).
 * buy() -> {ok, reason?, item?}  reasons: closed | unknown | owned | gold | max */
(function () {
  'use strict';
  const D = window.ShopData, def = id => (window.EquipmentData.items[id] || window.ItemData.items[id]);
  const stage = () => (typeof storyStage === 'number' ? storyStage : 0);
  const shop = id => D.shops[id] || null;
  const isOpen = id => { const s = shop(id); return Boolean(s) && stage() >= s.openFrom; };
  function stock(id) {
    const s = shop(id); if (!s || !isOpen(id)) return [];
    const gate = e => stage() >= (e.minStage ?? s.openFrom) && (!e.flag || Boolean(window.FieldTalk && FieldTalk.flag(e.flag))) && (!e.quest || (window.Quest && Quest.state(e.quest.id) === e.quest.state));
    return s.stock.filter(e => def(e.id) && gate(e)).map(e => ({...e, ...def(e.id), id: e.id, price: e.price, equip: Boolean(window.EquipmentData.items[e.id])}));
  }
  function buy(shopId, itemId) {
    const e = stock(shopId).find(x => x.id === itemId);
    if (!shop(shopId)) return {ok: false, reason: 'unknown'};
    if (!isOpen(shopId) || !e) return {ok: false, reason: 'closed'};
    if (e.equip && EquipmentManager.owned(itemId) >= 1) return {ok: false, reason: 'owned'};
    if (!e.equip && Inventory.count(itemId) >= 99) return {ok: false, reason: 'max'};
    if (gold < e.price) return {ok: false, reason: 'gold'};
    gold -= e.price; Inventory.add(itemId, 1);
    return {ok: true, item: itemId, price: e.price};
  }
  const REASON = {owned: 'すでに持っている。', gold: 'お金が足りない。', max: 'これ以上は持てない。', closed: '今は売っていない。'};
  const esc = t => String(t).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  const MODS = {maxHp: 'HP', maxMp: 'MP', atk: 'ATK', def: 'DEF', mag: 'MAG', spd: 'SPD', cri: 'CRI'};
  let msg = '';
  function ui(id) {
    let m = document.getElementById('shopModal');
    if (!m) { m = document.createElement('div'); m.id = 'shopModal'; m.setAttribute('role', 'dialog'); m.setAttribute('aria-modal', 'true'); document.body.append(m); }
    const s = shop(id), list = stock(id);
    m.innerHTML = `<div class="shopPanel"><div class="shopHead"><h3>${esc(s.name)}</h3><span class="shopGold">所持金 <b data-shop-gold>${gold}</b> G</span><button type="button" data-shop-close>閉じる</button></div>
      <div class="shopList">${list.map(e => {
        const owned = e.equip && EquipmentManager.owned(e.id) >= 1, can = !owned && gold >= e.price;
        const mods = e.equip ? Object.entries(e.mods || {}).map(([k, v]) => MODS[k] + (v > 0 ? '+' : '') + v).join(' ') || '補正なし' : '';
        return `<div class="shopRow"><div><b>${esc(e.name)}</b>${e.equip ? ' <small>(' + esc(window.EquipmentData.slotNames[e.slot]) + ')</small>' : ' <small>所持 ' + Inventory.count(e.id) + '</small>'}<br><small>${esc(e.desc)}</small>${mods ? '<br><small>' + mods + '</small>' : ''}</div><div class="shopPrice">${e.price} G</div><button type="button" data-shop-buy="${e.id}" ${can ? '' : 'disabled'}>${owned ? '購入済み' : '買う'}</button></div>`;
      }).join('')}</div><p class="shopMsg" role="status" aria-live="polite"><small>${esc(msg)}</small></p></div>`;
    msg = ''; m.style.display = 'block';
    m.querySelector('[data-shop-close]').onclick = close;
    m.querySelectorAll('[data-shop-buy]').forEach(b => b.onclick = () => { const r = buy(id, b.dataset.shopBuy); msg = r.ok ? def(r.item).name + 'を買った。' : REASON[r.reason] || ''; ui(id); const n = m.querySelector('[data-shop-buy]:not([disabled])') || m.querySelector('[data-shop-close]'); n.focus(); });
    m.onkeydown = e => {
      if (e.key === 'Escape') { close(); return; }
      const k = {ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1}[e.key]; if (!k) return;
      const all = [...m.querySelectorAll('button:not([disabled])')], i = all.indexOf(document.activeElement); if (i < 0) return;
      e.preventDefault(); all[(i + k + all.length) % all.length].focus();
    };
    (m.querySelector('[data-shop-buy]:not([disabled])') || m.querySelector('[data-shop-close]')).focus();
  }
  function close() { const m = document.getElementById('shopModal'); if (m) m.style.display = 'none'; window.dispatchEvent(new CustomEvent('shop-close')); }
  function open(id) { if (!isOpen(id)) return false; ui(id); return true; }
  window.Shop = Object.freeze({open, close, buy, stock, isOpen});
})();
