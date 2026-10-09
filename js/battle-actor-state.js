// Artwork only: battle calculations and DOM motion remain in the battle engine.
(() => {
  const states = new Set(['idle', 'attack', 'damage', 'guard', 'low_hp', 'ko', 'victory', 'charge', 'heal', 'blessing', 'call', 'corruption', 'enrage', 'prayer', 'skill', 'wind', 'rune']);
  const temporary = new Set(['attack', 'damage', 'charge', 'heal', 'blessing', 'call', 'corruption', 'enrage', 'prayer', 'skill', 'wind', 'rune']);
  const battles = {
    normal: { actor: 'aidan', image: '#bAidan2 img', health: () => [aahp, 100] },
    raider: { actor: 'aidan', image: '#rbAidan img', health: () => [rbHP, 120] },
    'normal:fiona': { actor: 'fiona', image: '#bFiona2 img', health: () => [normalFHP, 90] },
    'raider:fiona': { actor: 'fiona', image: '#rbFiona img', health: () => [rbFHP, 105] },
    'raider:lou': { actor: 'lou', image: '#rbLou img', health: () => [null, null] },
    // Prepared adapter only; current encounters remain Tainted Goblins.
    'normal:goblin': { actor: 'goblin', image: '#bGob img', health: () => [gghp, null] },
    'normal:tainted_goblin': { actor: 'tainted_goblin', image: '#bGob img', health: () => [gghp, null] },
    'raider:goblin_raider': { actor: 'goblin_raider', image: '#raiderSprite img', health: () => [rbBoss, null] }
  };
  for (const battle of Object.values(battles)) {
    Object.assign(battle, { state: 'idle', sequence: 0, timer: null, guard: false });
  }
  function lookup(context, actor = 'aidan') {
    return battles[actor === 'aidan' ? context : context + ':' + actor];
  }
  function invalidate(battle) {
    clearTimeout(battle.timer);
    battle.timer = null;
    return ++battle.sequence;
  }
  function paint(battle, state) {
    battle.state = state;
    const image = document.querySelector(battle.image);
    const source = BATTLE_ASSETS[battle.actor][state];
    if (image && image.getAttribute('src') !== source) image.src = source;
    window.BattleFacing?.paint(image, battle.actor, state);
    window.BattleIdleMotion?.onState(battle.image, battle.actor, state);
  }
  function resting(battle) {
    const [hp, maxHp] = battle.health();
    if (hp === null) return 'idle'; // Support actors have no invented HP resource.
    return hp <= 0 ? 'ko' : battle.guard ? 'guard' : BATTLE_ASSETS[battle.actor].low_hp && hp <= maxHp * .30 ? 'low_hp' : 'idle';
  }
  function sync(context, actor = 'aidan') {
    const battle = lookup(context, actor);
    if (!battle) return;
    if (battle.health()[0] !== null && battle.health()[0] <= 0 && battle.state !== 'ko') {
      invalidate(battle);
      paint(battle, 'ko');
    } else if (!['ko', 'victory'].includes(battle.state) && !temporary.has(battle.state)) {
      paint(battle, resting(battle));
    }
  }
  function set(actor, state, { battle: context, duration, next, nextDuration } = {}) {
    if (!states.has(state)) return false;
    context ||= document.body.classList.contains('raiderBattleMode') ? 'raider' : 'normal';
    const battle = lookup(context, actor);
    if (!battle || !BATTLE_ASSETS[battle.actor]?.[state]) return false;
    sync(context, actor);
    // KO outranks victory; neither can be replaced by a temporary pose.
    if (battle.state === 'ko' || (battle.state === 'victory' && state !== 'ko')) return false;
    if (state === 'idle' || state === 'low_hp') {
      if (temporary.has(battle.state) || battle.state === 'guard') return false;
      state = resting(battle);
    }
    const sequence = invalidate(battle);
    if (state === 'guard') battle.guard = true;
    paint(battle, state);
    if (duration && temporary.has(state)) {
      battle.timer = setTimeout(() => {
        if (battle.sequence !== sequence) return;
        sync(context, actor);
        if (battle.sequence !== sequence || ['ko', 'victory'].includes(battle.state)) return;
        battle.timer = null;
        if (next) return set(actor, next, { battle: context, duration: nextDuration });
        paint(battle, resting(battle));
      }, duration);
    }
    return true;
  }
  window.BattleActorState = Object.freeze({
    set,
    sync,
    register(context, key, actor, image, health) {
      const id=context+':'+key;
      if(battles[id]) invalidate(battles[id]);
      battles[id]={actor,image,health,state:'idle',sequence:0,timer:null,guard:false};
      paint(battles[id],resting(battles[id]));
    },
    unregister(context,key) { const id=context+':'+key; if(battles[id]){invalidate(battles[id]);delete battles[id];} },
    begin(context, actor = 'aidan') {
      const battle = lookup(context, actor);
      window.BattleIdleMotion?.begin(battle.image);
      invalidate(battle);
      battle.guard = false;
      battle.phase = null;
      paint(battle, resting(battle));
    },
    endGuard(context, actor = 'aidan') {
      lookup(context, actor).guard = false;
      sync(context, actor);
    },
    // Only called after the existing normal-battle recovery has restored HP.
    recover(context, actor = 'aidan') {
      const battle = lookup(context, actor);
      if (battle.state === 'ko' && battle.health()[0] > 0) {
        invalidate(battle);
        paint(battle, resting(battle));
      }
    },
    end(context, actor = 'aidan') { const battle = lookup(context, actor); invalidate(battle); window.BattleIdleMotion?.stop(battle.image); },
    get(context, actor = 'aidan') { return lookup(context, actor)?.state; },
    trackPhase(actor, phase, { battle: context } = {}) {
      const battle = lookup(context, actor);
      if (!battle) return false;
      const previous = battle.phase;
      battle.phase = phase;
      if (previous != null && phase > previous && battle.health()[0] > 0 && BATTLE_ASSETS[actor].enrage) {
        return set(actor, 'enrage', { battle: context, duration: 780 });
      }
      return false;
    },
    action(actor, state, { battle } = {}) {
      if (actor === 'lou' && state === 'heal') {
        return set(actor, 'charge', { battle, duration: 140, next: 'heal', nextDuration: 660 });
      }
      if (actor === 'lou' && state === 'blessing') return set(actor, state, { battle, duration: 1000 });
      if (actor === 'fiona' && state === 'heal') {
        return set(actor, 'charge', { battle, duration: 260, next: 'heal', nextDuration: 500 });
      }
      return set(actor, state, { battle, duration: actor === 'aidan' ? 820 : state === 'attack' ? 680 : 760 });
    }
  });
})();
