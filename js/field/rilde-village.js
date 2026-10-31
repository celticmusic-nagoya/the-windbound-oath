/* RildeVillage: the Rilde Village maps (data/maps/rilde_*, built by tools/moss/build_rilde_village.py) wired into the story.
 *  - state():    'peace' before the attack, 'ruin' after it (storyStage >= 5, or the flag rilde_ruined). resolve('rilde_village') picks the matching map file,
 *                so doors / exits / save-less story code never care which variant is live. Interiors exist for the peaceful village only (the ruin has no entrances).
 *  - entering:   startOpening() (new game: Aidan wakes in his house) · enter(spawn) (from the cliff trail / the fort road) · afterPrologue() (stage 15: free roam from the fort)
 *  - the story:  stages 0-3 (opening, Fiona, training dummy, the walk to the cliff) run HERE, on top of the existing global helpers (say, setObj, startTraining ...).
 *                Stages 5-8 (the attack itself) are still the scripted legacy scenes; their consequence (the burnt village) is this module's 'ruin' state.
 *  - switch:     ?legacyVillage=1 in the URL keeps the old DOM village as the host (enabled() === false) - nothing else changes.
 * Pure data + hooks: holds no state of its own besides an optional forced state for DEV / tests. Never saved. */
(function () {
  'use strict';
  const q = (() => { try { return new URLSearchParams(location.search); } catch (e) { return new URLSearchParams(); } })();
  const LEGACY = q.get('legacyVillage') === '1';
  let forced = null;
  const stage = () => (typeof storyStage === 'number' ? storyStage : 0);
  const enabled = () => !LEGACY && Boolean(window.MossForestStory && window.MossForest);
  const attacked = () => stage() >= 5 || Boolean(window.FieldTalk && FieldTalk.flag('rilde_ruined'));
  const state = () => forced || (attacked() ? 'ruin' : 'peace');
  const resolve = id => (id === 'rilde_village' ? 'rilde_village_01_' + state() : id);
  const isVillage = m => Boolean(m && /^rilde_village_01_/.test(m.id));
  const isRilde = m => Boolean(m && m.story && m.story.rilde);
  const $id = id => document.getElementById(id);
  const click = el => { if (el && typeof el.onclick === 'function') { el.onclick(); return true; } return false; };
  const legacyNpc = n => document.querySelector('.npc[data-npc="' + n + '"]');
  const toast = t => { if (window.MossForest && MossForest.toast) MossForest.toast(t); };
  function fionaSpot(map) {
    const z = (map.eventZones || []).find(e => e.id === 'ev_fiona_wait'); const s = z && z.shape;
    return s ? {x: s.cx, y: s.cy + 22} : null;
  }
  // ---- map events (interact zones with hook:'rilde_*') ----
  function hook(z, map) {
    const h = z.hook || '';
    switch (true) {
      case h === 'rilde_fiona': {
        click($id('fiona'));                                     // stage 0 -> 1: "遅いよ、エイダン" + objective + 同行
        if (stage() >= 1) { MossForest.setFlag('rilde_fiona_waiting', false); const a = MossForest.actor('fiona'); if (a) a.release(); }
        return true;
      }
      case h === 'rilde_dummy': {
        if (stage() !== 1) { say(stage() === 0 ? '先にフィオナと話そう。' : '使い込まれた訓練用の木人だ。'); return true; }
        startTraining();                                         // opens the existing training battle overlay; stage 2 -> 3 when it ends
        TrainingCheckpoint.watchField();                       // cancelled with the training session on load/reset
        return true;
      }
      case h === 'rilde_drawer': {
        if (!flags.drawer) { flags.drawer = true; say('タンスを調べた。きずぐすりを1個見つけた！'); } else say('衣類がきれいに畳まれている。');
        return true;
      }
      case h === 'rilde_pot': {
        if (!flags.pot) { flags.pot = true; say('壺の中を調べた。3Gを見つけた！'); } else say('壺の中は空だ。');
        return true;
      }
      case h.startsWith('rilde_text:'): return click($id(h.slice(11)));
      case h === 'rilde_balloon_tree': return click($id('balloonTree'));
      case h === 'rilde_kid': return click(legacyNpc('kid'));
      case h === 'rilde_catowner': return click(legacyNpc('catowner'));
      case h === 'rilde_cat': return click(legacyNpc('cat'));
      case h === 'rilde_sign_east': { if (!FieldTalk.talk('rr_sign_east', {source: 'forest'})) say('木の標識：『← リルド村　／　ドゥンヴァル砦 →』'); return true; }
      case h === 'rilde_wind_stone': {
        say(state() === 'ruin' ? '風の石は沈黙している。あの夜から、村に風が戻らない。' : 'エイダン「風の石だ。村の人たちは、風の見張りって呼んでる。」', state() === 'ruin' ? null : {char:'aidan',face:'normal',side:'left'});
        return true;
      }
    }
    return false;
  }
  // ---- map entry (story hook onEnter) ----
  function onEnter(map) {
    if (!isRilde(map)) return;
    if (window.MossForestStory) MossForestStory.syncFlags();
    if (isVillage(map) && stage() === 0 && state() === 'peace') {   // Fiona waits at the training ground until Aidan talks to her
      const sp = fionaSpot(map), a = MossForest.actor('fiona');
      if (sp && a) a.set(sp.x, sp.y);
    }
  }
  const fionaVisible = map => !(map && map.story && map.story.interior);
  // ---- scene routing ----
  function show() { closeDialogue(); forestActive = true; const s = $id('forestScene'); if (s) s.style.display = 'block'; const ins = $id('inside'); if (ins) ins.style.display = 'none'; }
  function enter(spawn, opt = {}) { show(); return MossForestStory.enterMap(opt.map || 'rilde_village', spawn); }
  async function startOpening(token) {
    if(token===undefined)return LoadCoordinator.boot(t=>startOpening(t));
    LoadCoordinator.assertCurrent(token);
    PrologueProgress.resetLegacyEvents();
    storyStage = 0; currentObjective = '家を出て、訓練場のフィオナに会いに行こう'; renderJournal();
    show();
    const pending=MossForestStory.enterMap('rilde_in_aidan','from_bed',{loadToken:token}),request=MossForest.enterCount;
    await pending;LoadCoordinator.assertCurrent(token);
    if(request!==MossForest.enterCount)return;
    popObjective();
    const revision=LoadCoordinator.dialogueRevision;
    // Optional narration never owns readiness or overwrites newer dialogue, even if that dialogue has already closed.
    setTimeout(()=>{
      if(!LoadCoordinator.current(token)||request!==MossForest.enterCount||revision!==LoadCoordinator.dialogueRevision)return;
      if(stage()===0&&MossForest.mapId==='rilde_in_aidan'&&MossForest.active&&!MossForest.entering&&!window.FieldTalk?.active&&!document.body.classList.contains('dialogueOpen'))say('朝の風が窓を揺らしている。今日はフィオナと訓練する約束だった。');
    },350);
  }
  function afterPrologue() {   // stage 15: free roam. The party stands in the fort's keep; the village (now ruined) and the road are open.
    storyStage = 15; const pe = $id('prologueEnd'); if (pe) pe.style.display = 'none';
    return enterWorldMap('fort', 'from_keep');
  }
  const peacefulTrip = () => stage() >= 1 && stage() <= 3 && !attacked();
  // exits that carry story rules (hooks.onVillageExit): returns true when handled
  function exit(t) {
    const id = (t && t.id) || '';
    if (id === 'tr_v_to_cliff') {
      if (stage() < 3) toast('この先は風見の断崖へ続いている。今は訓練場へ向かおう。');
      else if (stage() === 3 || stage() >= 15) { enterCliffFromVillage(); }
      else toast('村へ戻ろう。何かがおかしい。');
      return true;
    }
    if (id === 'tr_v_to_fort') {
      if (stage() < 15) FieldTalk.talk('rr_road_early', {source: 'forest'});
      else if (!FieldTalk.flag('road_dunvall_open')) FieldTalk.talk('rr_road_ask', {source: 'forest'});
      else MossForestStory.enterMap('fort', 'from_road');
      return true;
    }
    if (!enabled()) return false;
    // 陽だまりの道(A1) <-> village north road (F-E2). Peaceful side trip only: open from stage 1 (= after Fiona joined: #fiona click, stage 0 -> 1) through stage 3.
    // Stage 4-14 (cliff sunset / attack / prologue forest) and 15+ (post-prologue; not decided yet) stay closed. The attack's fall goes to A2 (not built here).
    if (id === 'tr_v_to_moss') {
      if (peacefulTrip()) MossForestStory.enterMap(MossForestStory.MAP_IDS.a1, 'from_lind');
      else toast(stage() === 0 ? 'まずは訓練場のフィオナに会いに行こう。' : '今は、北の道へ向かう時ではない。');
      return true;
    }
    if (id === 'tr_to_lind') {
      if (peacefulTrip()) enter('from_moss_forest');
      else toast('崖の上へ戻る道は、もうない。先へ進むしかなさそうだ。');
      return true;
    }
    if (id === 'tr_c1_to_lind') {   // 風見の断崖 -> village south trail
      if (stage() === 3 || stage() >= 15) enter('from_cliff'); else toast('今は、村へ戻る時ではない。');
      return true;
    }
    if (id === 'tr_f1_to_village') { enter('from_fort'); return true; }
    return false;
  }
  function enterCliffFromVillage() {
    MossForestStory.enterCliff().then(() => { if (stage() === 3) setObj('崖の上のビューポイントへ向かおう'); }).catch(()=>{});
  }
  // 長老が街道を示したら(road_dunvall_open)、目的も次へ進める
  window.addEventListener('field-talk-end', e => {
    const d = e.detail || {};
    if (d.entry === 'rr_elder_road' && typeof setObj === 'function') { setObj('東の街道から、ドゥンヴァル砦へ向かおう'); if (typeof popObjective === 'function') popObjective(); if (typeof renderJournal === 'function') renderJournal(); }
  });
  window.RildeVillage = Object.freeze({enabled, state, resolve, hook, onEnter, fionaVisible, enter, startOpening, afterPrologue, exit, isRilde, isVillage,
    force(s) { forced = s === 'peace' || s === 'ruin' ? s : null; return state(); }, get legacy() { return LEGACY; }});
})();
