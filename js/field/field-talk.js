/* FieldTalk (M5.5 shared trigger -> M6 conditional conversations with speaker plate and choices).
 *   FieldTalk.talk(id,{source})  the single entry for every conversation (room UI, village UI, DEV review event).
 * Conversations come from tables (TalkData / loadTable): the highest-priority entry whose `when` holds is played, using
 * TalkConditions. Function providers (register) remain for special cases. State saved: {seen, cycle, flags}.
 * Display reuses the #msg box: <div.talkName> + <div.talkText> (+ <div.talkChoices>); tap / Enter advances. */
(function () {
  'use strict';
  const providers = new Map(), tables = new Map(), history = [];
  const seen = new Set(), cycle = {}, flags = {};
  let questProvider = id => (window.Quest ? Quest.state(id) : null), session = null;
  const msg = () => document.getElementById('msg');

  // ---------- context for conditions ----------
  const sealOpen = () => (window.PrologueProgress && PrologueProgress.count() >= 3) || (typeof storyStage === 'number' && storyStage >= 13);
  const flagOf = n => Boolean(flags[n]) || Boolean(window.MossForestStory && MossForestStory.flagsNow()[n]);
  const ctx = () => ({
    flag: flagOf,
    stage: () => (typeof storyStage === 'number' ? storyStage : 0),
    sealOpen,
    treasure: id => Boolean(window.MossForest && MossForest.opened.includes(id)) || Boolean(window.Inventory && Inventory.serialize().claimed.includes(id)),
    item: id => (window.Inventory ? Inventory.count(id) : 0),
    talked: id => seen.has(id),
    quest: id => questProvider(id)
  });
  const setQuestProvider = fn => { questProvider = typeof fn === 'function' ? fn : () => null; };

  // ---------- tables ----------
  function loadTable(table) {
    if (!table || typeof table.npc !== 'string' || !Array.isArray(table.entries)) return false;
    for (const e of table.entries) {
      for (const p of TalkConditions.validate(e.when, e.id + '.when')) console.warn('[FieldTalk]', p);
    }
    // Several files may contribute entries for one NPC: merge by entry id (later wins).
    const merged = new Map((tables.get(table.npc) || []).map(e => [e.id, e]));
    for (const e of table.entries) merged.set(e.id, e);
    tables.set(table.npc, [...merged.values()]);
    return true;
  }
  function register(ids, lineFn) { for (const id of [].concat(ids)) providers.set(id, lineFn); }
  const has = id => tables.has(id) || providers.has(id);
  function pick(id) {
    const entries = tables.get(id); if (!entries) return null;
    const c = ctx();
    const ok = entries.filter(e => (e.mode !== 'once' || !seen.has(e.id)) && TalkConditions.test(e.when, c));
    if (!ok.length) return null;
    return ok.reduce((a, b) => ((b.priority || 0) > (a.priority || 0) ? b : a));
  }
  function nextConversation(entry) {
    const n = entry.lines.length; let i;
    if (entry.mode === 'random') i = Math.floor(Math.random() * n);
    else if (entry.mode === 'once') i = 0;
    else { i = (cycle[entry.id] || 0) % n; cycle[entry.id] = i + 1; }
    return entry.lines[i];
  }

  // ---------- pages ----------
  const SPLIT = /　(?=[^\s「」　]{1,10}「)/, SPEAKER = /^([^\s「」　]{1,10})(「[\s\S]*)$/;
  function toPage(p) {
    if (p && typeof p === 'object') return {speaker: p.speaker || '', text: p.text || ''};
    const m = SPEAKER.exec(String(p)); return m ? {speaker: m[1], text: m[2]} : {speaker: '', text: String(p)};
  }
  function pagesOf(conv) {
    const raw = typeof conv === 'string' ? conv.split(SPLIT) : Array.isArray(conv) ? conv : (conv.pages || []);
    return raw.map(toPage);
  }

  // ---------- effects ----------
  function applyEffects(o, pages) {
    if (!o) return;
    if (o.set) for (const [k, v] of Object.entries(o.set)) if (/^[a-z0-9_]{1,40}$/i.test(k)) flags[k] = Boolean(v);
    if (o.quest && window.Quest) {
      const q = o.quest;
      if (q.action === 'accept') Quest.accept(q.id);
      else if (q.action === 'report') {
        const got = Quest.report(q.id);
        if (got && got.length && pages) pages.push({speaker: '', text: Inventory.describe(got) + ' を手に入れた。'});
      }
    }
    if (o.give && window.Inventory) {
      const got = Inventory.grant(o.give);
      if (got.length && pages) pages.push({speaker: '', text: Inventory.describe(got) + ' を手に入れた。'});
    }
  }

  // ---------- presentation in #msg ----------
  function render(page, choices) {
    const box = msg(); if (!box) return;
    box.textContent = '';
    if (page.speaker) { const n = document.createElement('div'); n.className = 'talkName'; n.textContent = page.speaker; box.append(n); }
    const t = document.createElement('div'); t.className = 'talkText'; t.textContent = page.text; box.append(t);
    if (choices) {
      const w = document.createElement('div'); w.className = 'talkChoices'; w.setAttribute('role', 'group');
      choices.forEach((o, i) => {
        const b = document.createElement('button'); b.type = 'button'; b.textContent = o.label; b.dataset.choice = i;
        b.addEventListener('click', e => { e.stopPropagation(); choose(i); });
        w.append(b);
      });
      box.append(w);
    }
    box.style.display = 'block'; document.body.classList.add('dialogueOpen');
  }
  const live = () => session && msg() && msg().style.display !== 'none' && msg().querySelector('.talkText');
  function show() {
    const s = session, last = s.i >= s.pages.length - 1;
    render(s.pages[s.i], last && s.choice ? s.choice.options : null);
  }
  function finish() {
    const s = session; session = null; if (!s) return;
    if (typeof closeDialogue === 'function') closeDialogue();
    window.dispatchEvent(new CustomEvent('field-talk-end', {detail: {id: s.id, entry: s.entryId}}));
  }
  function advance() {
    const s = session; if (!s) return;
    if (s.i < s.pages.length - 1) { s.i++; show(); return; }
    if (s.choice) return;   // waiting for a choice
    finish();
  }
  function choose(i) {
    const s = session; if (!s || !s.choice) return;
    const o = s.choice.options[i]; if (!o) return;
    s.choice = null;
    const reply = o.reply ? pagesOf(o.reply) : [];
    applyEffects(o, reply);
    if (!reply.length) { finish(); return; }
    s.pages = reply; s.i = 0; show();
  }
  function run(id, entry, conv) {
    const pages = pagesOf(conv); if (!pages.length) return false;
    const choice = conv.choice && Array.isArray(conv.choice.options) && conv.choice.options.length ? conv.choice : null;
    applyEffects(conv, pages);
    session = {id, entryId: entry && entry.id, pages, i: 0, choice};
    show(); return true;
  }

  function talk(id, {source = 'ui'} = {}) {
    if (typeof document === 'undefined') return false;
    const entry = pick(id);
    if (entry) {
      const conv = nextConversation(entry);
      if (!run(id, entry, conv)) return false;
      seen.add(entry.id);
    } else if (providers.has(id) && typeof say === 'function') {
      const text = providers.get(id)(id); if (!text) return false; session = null; say(text);
    } else return false;
    history.push({id, source, at: Date.now()}); if (history.length > 20) history.shift();
    window.dispatchEvent(new CustomEvent('field-talk', {detail: {id, source, entry: entry && entry.id}}));
    return true;
  }

  // tap / keys while a conversation is on screen
  function attachTap() {
    const box = msg(); if (!box) return;
    box.addEventListener('click', e => { if (!live() || e.target.closest('.talkChoices')) return; e.stopImmediatePropagation(); advance(); }, true);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attachTap); else attachTap();
  window.addEventListener('keydown', e => {
    if (!live()) return;
    const n = session.choice ? session.choice.options.length : 0;
    if (n && /^[1-9]$/.test(e.key) && +e.key <= n) { e.preventDefault(); e.stopImmediatePropagation(); choose(+e.key - 1); return; }
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'z') { e.preventDefault(); e.stopImmediatePropagation(); if (!n) advance(); }
  }, true);
  window.addEventListener('lind-field-interaction', e => { const d = e.detail; if (d && d.id) talk(d.id, {source: 'review'}); });

  // ---------- save ----------
  function entryIds() { return new Set([...tables.values()].flat().map(e => e.id)); }
  function serialize() { return {seen: [...seen], cycle: {...cycle}, flags: {...flags}}; }
  function load(data) {
    seen.clear(); for (const k of Object.keys(cycle)) delete cycle[k]; for (const k of Object.keys(flags)) delete flags[k];
    session = null;
    if (!data || typeof data !== 'object') return;
    const known = entryIds();
    for (const id of Array.isArray(data.seen) ? data.seen.slice(0, 1000) : []) if (typeof id === 'string' && known.has(id)) seen.add(id);
    for (const [k, v] of Object.entries(data.cycle || {})) if (known.has(k) && Number.isInteger(v) && v >= 0 && v < 100000) cycle[k] = v;
    for (const [k, v] of Object.entries(data.flags || {})) if (/^[a-z0-9_]{1,40}$/i.test(k)) flags[k] = Boolean(v);
  }
  const setFlag = (k, v = true) => { if (/^[a-z0-9_]{1,40}$/i.test(k)) flags[k] = Boolean(v); };

  for (const src of [window.TalkData, window.TalkDataQuests]) if (src) for (const t of src.tables) loadTable(t);
  window.FieldTalk = Object.freeze({flag: flagOf, seenEntry: id => seen.has(id), register, loadTable, has, talk, pick, setFlag, setQuestProvider, serialize, load,
    get active() { return Boolean(live()); }, get history() { return history.slice(); }});
})();
