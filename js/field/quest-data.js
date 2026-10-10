/* Quest definitions (M6). 仮(DRAFT): the first quest is a placeholder scenario for the new quest/talk plumbing;
 * replace or delete freely (talk lines live in js/field/talk-data-quests.js).
 * quest: {name, complete: <TalkConditions condition>, reward: {item|gold: n}, objective: {active, complete}}
 * States: unaccepted -> active -> complete (derived from `complete`) -> reported. */
window.QuestData = Object.freeze({
  quests: Object.freeze({
    q_emma_charm: {
      name: 'エマの護符',
      complete: {item: 'charm_windward'},
      reward: {ether: 1, emma_charm: 1},
      objective: {active: '森の道で、エマの落とした護符を探す', complete: 'エマに護符を見せに行く'}
    },
    // 老人(男) ・ 農作業の女性 のクエスト。台詞は js/field/talk-data-quests.js
    q_oldman_rune: {
      name: '古びたルーンの記憶',
      complete: {item: 'rune_shard_old'},
      reward: {ether: 1},
      objective: {active: '森で古いルーンの欠片を見つけ、老人に見せる', complete: '老人にルーン片を見せに行く'}
    },
    q_farmer_herb: {
      name: '収穫をはばむ影',
      complete: {item: 'herb_moss', min: 3},
      reward: {potion: 2, gold: 30},
      objective: {active: '薬草を3つ集めて、農作業の女性に届ける', complete: '農作業の女性に薬草を届ける'}
    },
    // 王都（仮シナリオ）
    q_capital_comb: {
      name: '王都の失くし物',
      complete: {item: 'silver_comb'},
      reward: {gold: 80, ether: 1},
      objective: {active: '住宅街の老婦人の銀の櫛を、城前広場で探す', complete: '老婦人に銀の櫛を届ける'}
    },
    q_capital_delivery: {
      name: '商業区の納品依頼',
      complete: {item: 'potion', min: 3},
      reward: {gold: 90, ether: 1},
      objective: {active: 'きずぐすりを3つ、商業区の依頼掲示板へ納める', complete: '依頼掲示板できずぐすりを納品する'}
    }
  })
});
