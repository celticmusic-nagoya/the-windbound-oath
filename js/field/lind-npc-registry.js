/* Single source of truth for Rilde Village field NPCs (M6): placement, conversation id, walking routine,
 * appearance condition and the walk-frame slot. Pure data (browser: window.LindNpcRegistry, node: module.exports).
 *
 *   id / label        actor id (= idle PNG name) and display name
 *   x, footY, height  home position (feet) and drawn height in world px
 *   sprite            'villagers' (img/field/lind/npc/villagers/<id>_idle.png) | 'emma' (img/field/lind/npc/emma/)
 *   talk              FieldTalk id (talk-data tables), or null while the NPC has no lines yet; the DEV review / room UI talk through FieldTalk.talk(talk)
 *   routine           walking routine {kind,speed,offsets,rests} (js/field/lind-village-life.js) or null
 *   motion            null | 'play' (LindChildren plaza chase) | 'fishing' (LindFisherman)
 *   appears           TalkConditions condition (flags/stage/quest...) evaluated when the NPC list is built; null = always
 *   walk              expected walk frames: {frames:N} installed, {frames:null} waiting for delivery, {legacy:'<id>_walk'}
 *                     frames live next to the idle PNG as <id>_walk_01..NN.png (tools/lind/install_walk_frames.py)
 * Order matters (actor update/phase order). Add a new NPC by adding one entry + a talk table; no other file changes. */
(function (root) {
  'use strict';
  const R = (kind, speed, a, b, rests) => ({kind, speed, offsets: [a, b], rests});
  const npcs = [
    {id: 'farmer_male',   label: '農夫',         x: 970,  footY: 1190, height: 46, sprite: 'villagers', talk: 'farmer_male',   routine: R('WORKER', 3, [18, 0], [0, 0], [9, 13]),     motion: null, appears: null, walk: {legacy: 'farmer_male_walk', frames: null}},
    {id: 'farmer_female', label: '農作業の女性', x: 1150, footY: 1200, height: 44, sprite: 'villagers', talk: null, routine: R('WORKER', 2.6, [-12, 4], [0, 0], [12, 17]), motion: null, appears: null, walk: {frames: 4}},
    {id: 'young_man',     label: '青年',         x: 630,  footY: 665,  height: 46, sprite: 'villagers', talk: 'young_man',     routine: R('LOCAL_WALKER', 5, [-18, 8], [0, 0], [7, 11]), motion: null, appears: null, walk: {frames: 6}},
    {id: 'young_woman',   label: '若い女性',     x: 805,  footY: 665,  height: 44, sprite: 'villagers', talk: 'young_woman',   routine: R('LOCAL_WALKER', 4.3, [18, 8], [0, 0], [10, 14]), motion: null, appears: null, walk: {frames: 6}},
    {id: 'elder_man',     label: '老人',         x: 460,  footY: 405,  height: 42, sprite: 'villagers', talk: null,     routine: R('ELDERLY', 1.8, [4, 0], [0, 0], [24, 32]),   motion: null, appears: null, walk: {frames: 6}},
    {id: 'elder_woman',   label: '村の老婆',     x: 790,  footY: 1060, height: 39, sprite: 'villagers', talk: 'elder_woman',   routine: R('ELDERLY', 1.6, [-4, 0], [0, 0], [29, 38]),  motion: null, appears: null, walk: {frames: 6}},
    {id: 'boy',           label: '男の子',       x: 600,  footY: 700,  height: 31, sprite: 'villagers', talk: 'boy',           routine: null, motion: 'play', appears: null, walk: {frames: 4}},
    {id: 'girl',          label: '女の子',       x: 850,  footY: 725,  height: 31, sprite: 'villagers', talk: 'girl',          routine: null, motion: 'play', appears: null, walk: {frames: 4}},
    {id: 'merchant',      label: '道具屋の商人', x: 420,  footY: 690,  height: 45, sprite: 'villagers', talk: 'merchant',      routine: R('SHOP', 2, [5, 0], [0, 0], [18, 27]),        motion: null, appears: null, walk: {frames: null}},
    {id: 'innkeeper',     label: '宿屋の主人',   x: 850,  footY: 420,  height: 45, sprite: 'villagers', talk: 'innkeeper',     routine: R('SHOP', 2, [-5, 0], [0, 0], [23, 31]),       motion: null, appears: null, walk: {frames: 6}},
    {id: 'fisherman',     label: '釣り人',       x: 1447, footY: 1367, height: 46, sprite: 'villagers', talk: 'fisherman',     routine: null, motion: 'fishing', appears: null, walk: {frames: null}},
    {id: 'caretaker',     label: '家畜の世話係', x: 1350, footY: 1170, height: 45, sprite: 'villagers', talk: 'caretaker',     routine: R('WORKER', 3.2, [0, -12], [0, 0], [11, 19]),  motion: null, appears: null, walk: {frames: 6}},
    {id: 'emma',          label: 'エマ',         x: 820,  footY: 780,  height: 38, sprite: 'emma',      talk: 'emma',          routine: R('EMMA', 1.2, [4, -2], [0, 0], [24, 36]),     motion: null, appears: null, walk: {frames: 3}}
  ];
  const dirs = {villagers: 'img/field/lind/npc/villagers/', emma: 'img/field/lind/npc/emma/'};
  const idlePath = n => dirs[n.sprite] + n.id + '_idle.png';
  const walkPath = (n, i) => dirs[n.sprite] + n.id + '_walk_' + String(i).padStart(2, '0') + '.png';
  // definitions for LindFieldNPCs: registry entries whose `appears` holds (cond/ctx optional: no ctx = always)
  function definitions(test, ctx) {
    return npcs.filter(n => !n.appears || !test || test(n.appears, ctx)).map(n => ({...n, path: idlePath(n)}));
  }
  const api = {npcs, dirs, idlePath, walkPath, definitions, get: id => npcs.find(n => n.id === id)};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.LindNpcRegistry = api;
})(typeof window !== 'undefined' ? window : globalThis);
