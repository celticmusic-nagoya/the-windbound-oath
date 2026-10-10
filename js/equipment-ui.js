/* EquipmentUI: the EQUIP tab of the system menu (renderSystemTab('equip') -> EquipmentUI.render(bodyEl)).
 * Left/top: character picker; four slots; pick a slot -> bag pieces for that slot with a before->after stat preview
 * (green = up, red = down); "外す" for the current piece. Plain <button>s: Tab/Enter/Space work, and ArrowUp/Down/Left/Right move focus
 * (pad d-pad mapped to arrow keys works the same). Layout is flex-wrap/grid so it reads on a phone.
 * Logic lives in EquipmentManager / Inventory - this file only draws and calls equip()/unequip(). */
(function () {
  'use strict';
  let who = null, slot = 'weapon', msg = '';
  const E = window.EquipmentData, LABEL = {maxHp: 'HP', maxMp: 'MP', atk: 'ATK', def: 'DEF', mag: 'MAG', spd: 'SPD', cri: 'CRI'};
  const esc = t => String(t).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
  const members = () => Object.entries(PartyManager.members).filter(([, m]) => m.joined).map(([id]) => id);
  const modText = m => Object.entries(m || {}).map(([k, v]) => LABEL[k] + (v > 0 ? '+' : '') + v).join(' ') || '補正なし';
  function render(body) {
    const ids = members(); if (!ids.length) { body.innerHTML = '<p><small>仲間がいません。</small></p>'; return; }
    if (!ids.includes(who)) who = ids[0];
    const worn = EquipmentManager.get(who), st = charStats(who);
    const bag = Inventory.list('equip').filter(i => i.slot === slot);
    const cur = worn[slot] || null;
    const stat = Object.keys(LABEL).map(k => `<span>${LABEL[k]} <b data-stat="${k}">${st[k]}${k === 'cri' ? '%' : ''}</b></span>`).join('');
    let h = `<h3>EQUIPMENT</h3><div class="eqPick" role="tablist">${ids.map(id => `<button type="button" data-eq-char="${id}" class="${id === who ? 'active' : ''}">${esc(CHARACTER_DB[id].name)}</button>`).join('')}</div>
      <div class="stats eqStats">${stat}</div><div class="eqSlots">${E.slots.map(s => {
        const it = worn[s] ? EquipmentManager.def(worn[s]) : null;
        return `<button type="button" data-eq-slot="${s}" class="eqSlot ${s === slot ? 'active' : ''}"><small>${E.slotNames[s]}</small><b>${it ? esc(it.name) : '— なし —'}</b>${it ? `<small>${modText(it.mods)}</small>` : ''}</button>`;
      }).join('')}</div>
      <h3>${E.slotNames[slot]}の候補</h3><div class="eqList">`;
    if (cur) h += `<div class="eqRow"><div><b>${esc(EquipmentManager.def(cur).name)}</b>（装備中）<br><small>${esc(EquipmentManager.def(cur).desc)}</small></div><div class="eqDiff">${diff(EquipmentManager.delta(who, null, slot))}</div><button type="button" data-eq-off="${slot}">外す</button></div>`;
    const ok = bag.filter(i => !EquipmentManager.canEquip(who, i.id, slot));
    h += ok.map(i => `<div class="eqRow"><div><b>${esc(i.name)}</b> ×${i.count}<br><small>${esc(i.desc)}</small><br><small>${modText(i.mods)}</small></div><div class="eqDiff">${diff(EquipmentManager.delta(who, i.id, slot))}</div><button type="button" data-eq-on="${i.id}">装備</button></div>`).join('');
    if (!cur && !ok.length) h += '<p><small>装備できるものを持っていない。</small></p>';
    const other = bag.length - ok.length; if (other) h += `<p><small>${other}個は${esc(CHARACTER_DB[who].name)}には装備できない。</small></p>`;
    h += `</div><p class="eqMsg" role="status" aria-live="polite"><small>${esc(msg)}</small></p>`;
    body.innerHTML = h; msg = '';
    body.querySelectorAll('[data-eq-char]').forEach(b => b.onclick = () => { who = b.dataset.eqChar; render(body); focus(body, `[data-eq-char="${who}"]`); });
    body.querySelectorAll('[data-eq-slot]').forEach(b => b.onclick = () => { slot = b.dataset.eqSlot; render(body); focus(body, `[data-eq-slot="${slot}"]`); });
    body.querySelectorAll('[data-eq-on]').forEach(b => b.onclick = () => { const r = EquipmentManager.equip(who, b.dataset.eqOn, slot); msg = r.ok ? EquipmentManager.def(b.dataset.eqOn).name + 'を装備した。' : '装備できない（' + r.reason + '）。'; render(body); focus(body, `[data-eq-slot="${slot}"]`); });
    body.querySelectorAll('[data-eq-off]').forEach(b => b.onclick = () => { const r = EquipmentManager.unequip(who, b.dataset.eqOff); msg = r.ok ? EquipmentManager.def(r.prev).name + 'を外した。' : ''; render(body); focus(body, `[data-eq-slot="${slot}"]`); });
    body.onkeydown = e => nav(e, body);
  }
  function diff(d) {
    const parts = Object.entries(d).map(([k, v]) => `<span class="${v > 0 ? 'up' : 'dn'}">${LABEL[k]} ${v > 0 ? '▲+' : '▼'}${v}</span>`);
    return parts.join(' ') || '<small>変化なし</small>';
  }
  const focus = (body, sel) => { const e = body.querySelector(sel); if (e) e.focus(); };
  function nav(e, body) {
    const k = {ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1}[e.key]; if (!k) return;
    const all = [...body.querySelectorAll('button:not([disabled])')], i = all.indexOf(document.activeElement); if (i < 0) return;
    e.preventDefault(); all[(i + k + all.length) % all.length].focus();
  }
  window.EquipmentUI = Object.freeze({render});
})();
