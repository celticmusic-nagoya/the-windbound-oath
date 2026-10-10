/* Quest definitions (M6). 仮(DRAFT): the first quest is a placeholder scenario for the new quest/talk plumbing;
 * replace or delete freely (talk lines live in js/field/talk-data-quests.js).
 * quest: {name, complete: <TalkConditions condition>, reward: {item|gold: n}, objective: {active, complete}}
 * States: unaccepted -> active -> complete (derived from `complete`) -> reported. */
window.QuestData = Object.freeze({
  quests: Object.freeze({
    q_emma_charm: {
      name: 'エマの護符',
      complete: {item: 'charm_windward'},
      reward: {ether: 1},
      objective: {active: '森の道で、エマの落とした護符を探す', complete: 'エマに護符を見せに行く'}
    }
  })
});
