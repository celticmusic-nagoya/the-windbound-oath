// Canonical paths are relative to index.html, including GitHub Pages subpaths.
window.BATTLE_ASSET_PATHS = Object.freeze({
  aidan: 'img/battle/characters/aidan/',
  fiona: 'img/battle/characters/fiona/',
  lou: 'img/battle/characters/lou/',
  goblin: 'img/battle/enemies/goblin/',
  tainted_goblin: 'img/battle/enemies/tainted_goblin/',
  goblin_raider: 'img/battle/enemies/goblin_raider/'
});

// Only filenames verified in the repository. This registry does not add actions.
const battleAssetFiles = {
  aidan: {
    idle: 'aidan_battle_idle.png', entry: 'aidan_battle_entry.png',
    attack: 'aidan_attack.png', skill: 'aidan_skill.png', wind: 'aidan_skill_wind_slash.png',
    charge: 'aidan_skill_charge.png', awaken: 'aidan_oath_awaken.png',
    evade: 'aidan_evade.png', guard: 'aidan_guard.png',
    damage: 'aidan_damage.png', low_hp: 'aidan_low_hp.png',
    item: 'aidan_item.png', ko: 'aidan_ko.png', victory: 'aidan_victory.png'
  },
  fiona: {
    idle: 'fiona_battle_idle.png', entry: 'fiona_battle_entry.png',
    attack: 'fiona_attack.png', skill: 'fiona_skill_windbloom.png',
    charge: 'fiona_skill_charge.png', heal: 'fiona_skill_heal.png',
    prayer: 'fiona_skill_wind_prayer.png', awaken: 'fiona_oath_awaken.png',
    evade: 'fiona_evade.png', guard: 'fiona_guard.png',
    damage: 'fiona_damage.png', low_hp: 'fiona_low_hp.png',
    item: 'fiona_item.png', ko: 'fiona_ko.png', victory: 'fiona_victory.png'
  },
  lou: {
    idle: 'lou_battle_idle.png', entry: 'lou_battle_entry.png',
    support: 'lou_support.png', charge: 'lou_support_charge.png',
    rune: 'lou_skill_rune.png', heal: 'lou_support_heal.png', blessing: 'lou_support_blessing.png',
    evade: 'lou_evade.png', damage: 'lou_damage.png',
    low_hp: 'lou_low_hp.png', ko: 'lou_ko.png', victory: 'lou_victory.png'
  },
  goblin: {
    idle: 'goblin_battle_idle.png', attack: 'goblin_attack.png',
    call: 'goblin_call.png', damage: 'goblin_damage.png', ko: 'goblin_ko.png'
  },
  tainted_goblin: {
    idle: 'goblin_battle_idle.png', attack: 'goblin_attack.png',
    damage: 'goblin_damage.png', corruption: 'goblin_corruption_burst.png',
    ko: 'goblin_ko.png'
  },
  goblin_raider: {
    idle: 'goblin_raider_battle_idle.png', attack: 'goblin_attack.png',
    call: 'goblin_raider_call.png', enrage: 'goblin_raider_enrage.png',
    ko: 'goblin_raider_ko.png'
  }
};
window.BATTLE_ASSETS = Object.freeze(Object.fromEntries(
  Object.entries(battleAssetFiles).map(([actor, states]) => [actor,
    Object.freeze(Object.fromEntries(Object.entries(states).map(([state, file]) =>
      [state, BATTLE_ASSET_PATHS[actor] + file])))
  ])
));

// Keep the existing cinematic API; these aliases only choose artwork.
window.WINDBOUND_APPROVED_ASSETS = Object.freeze({
  goblin: BATTLE_ASSETS.goblin.idle,
  taintedGoblin: BATTLE_ASSETS.tainted_goblin.idle,
  raider: BATTLE_ASSETS.goblin_raider.idle,
  lou: BATTLE_ASSETS.lou.idle
});
window.V053 = Object.freeze({
  tainted: Object.freeze({
    ...BATTLE_ASSETS.tainted_goblin,
    corrupted_attack: BATTLE_ASSETS.tainted_goblin.attack,
    summon: BATTLE_ASSETS.tainted_goblin.corruption
  }),
  raider: Object.freeze({
    ...BATTLE_ASSETS.goblin_raider,
    horn: BATTLE_ASSETS.goblin_raider.call,
    summon: BATTLE_ASSETS.goblin_raider.call,
    // No dedicated smash or damage pose exists. Never use KO as damage.
    smash: BATTLE_ASSETS.goblin_raider.attack,
    damage: BATTLE_ASSETS.goblin_raider.idle
  })
});

// Presentation art is deliberately separate from battlefield state images.
window.BATTLE_CUTINS = Object.freeze({
 skill: BATTLE_ASSET_PATHS.aidan + 'aidan_skill_cutin.png',
 wind: BATTLE_ASSET_PATHS.aidan + 'aidan_wind_slash_cutin.png',
 windbloom: BATTLE_ASSET_PATHS.fiona + 'fiona_skill_windbloom_cutin.png',
 prayer: BATTLE_ASSET_PATHS.fiona + 'fiona_skill_wind_prayer_cutin.png',
 blessing: BATTLE_ASSET_PATHS.lou + 'lou_skill_cutin.png'
});

// Aidan idle prototype: audited source pixels and boot anchors; PNGs remain untouched.
window.BATTLE_IDLE_ASSETS = Object.freeze({aidan: Object.freeze({
  type:'breathe', width:1536, height:1024, anchor:Object.freeze([888.5,1014]),
  frames:Object.freeze([
    Object.freeze({path:BATTLE_ASSET_PATHS.aidan+'idle/aidan_idle_00.png',anchor:Object.freeze([889.75,1014])}),
    Object.freeze({path:BATTLE_ASSET_PATHS.aidan+'idle/aidan_idle_01.png',anchor:Object.freeze([891.5,1015])}),
    Object.freeze({path:BATTLE_ASSET_PATHS.aidan+'idle/aidan_idle_02.png',anchor:Object.freeze([893.5,1015])}),
    Object.freeze({path:BATTLE_ASSET_PATHS.aidan+'idle/aidan_idle_03.png',anchor:Object.freeze([891.75,1011])})
  ])
})});
