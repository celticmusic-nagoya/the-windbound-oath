// Artwork only: battle calculations and DOM motion remain in the battle engine.
(() => {
  const states = new Set(['idle', 'attack', 'damage', 'guard', 'low_hp', 'ko', 'victory']);
  const battles = {
    normal: { image: '#bAidan2 img', health: () => [aahp, 100] },
    raider: { image: '#rbAidan img', health: () => [rbHP, 120] }
  };
  for (const battle of Object.values(battles)) {
    Object.assign(battle, { state: 'idle', sequence: 0, timer: null, guard: false });
  }
  function invalidate(battle) {
    clearTimeout(battle.timer);
    battle.timer = null;
    return ++battle.sequence;
  }
  function paint(battle, state) {
    battle.state = state;
    const image = document.querySelector(battle.image);
    const source = BATTLE_ASSETS.aidan[state];
    if (image && image.getAttribute('src') !== source) image.src = source;
  }
  function resting(battle) {
    const [hp, maxHp] = battle.health();
    return hp <= 0 ? 'ko' : battle.guard ? 'guard' : hp <= maxHp * .30 ? 'low_hp' : 'idle';
  }
  function sync(context) {
    const battle = battles[context];
    if (!battle) return;
    if (battle.health()[0] <= 0 && battle.state !== 'ko') {
      invalidate(battle);
      paint(battle, 'ko');
    } else if (!['ko', 'victory', 'attack', 'damage'].includes(battle.state)) {
      paint(battle, resting(battle));
    }
  }
  function set(actor, state, { battle: context, duration } = {}) {
    if (actor !== 'aidan' || !states.has(state)) return false;
    context ||= document.body.classList.contains('raiderBattleMode') ? 'raider' : 'normal';
    const battle = battles[context];
    if (!battle) return false;
    sync(context);
    // KO outranks victory; neither can be replaced by a temporary pose.
    if (battle.state === 'ko' || (battle.state === 'victory' && state !== 'ko')) return false;
    if (state === 'idle' || state === 'low_hp') {
      if (['attack', 'damage', 'guard'].includes(battle.state)) return false;
      state = resting(battle);
    }
    const sequence = invalidate(battle);
    if (state === 'guard') battle.guard = true;
    paint(battle, state);
    if (duration && ['attack', 'damage'].includes(state)) {
      battle.timer = setTimeout(() => {
        if (battle.sequence !== sequence) return;
        sync(context);
        if (battle.sequence !== sequence || ['ko', 'victory'].includes(battle.state)) return;
        battle.timer = null;
        paint(battle, resting(battle));
      }, duration);
    }
    return true;
  }
  window.BattleActorState = Object.freeze({
    set,
    sync,
    begin(context) {
      const battle = battles[context];
      invalidate(battle);
      battle.guard = false;
      paint(battle, resting(battle));
    },
    endGuard(context) {
      battles[context].guard = false;
      sync(context);
    },
    // Only called after the existing normal-battle recovery has restored HP.
    recover(context) {
      const battle = battles[context];
      if (battle.state === 'ko' && battle.health()[0] > 0) {
        invalidate(battle);
        paint(battle, resting(battle));
      }
    },
    end(context) { invalidate(battles[context]); },
    get(context) { return battles[context]?.state; }
  });
})();
