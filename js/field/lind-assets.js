/* Standalone field production assets. Coordinates below are DEV review positions,
 * not story/save coordinates; final map integration is STEP 12. */
(function () {
  'use strict';
  const base = 'img/field/lind/';
  window.LindFieldAssets = {
    terrain: {
      grass: base + 'terrain/lind_grass.png',
      dirt: base + 'terrain/lind_dirt.png',
      stone: base + 'terrain/lind_stone.png',
      edge: base + 'terrain/lind_grass_dirt_edge.png',
      water: base + 'terrain/lind_water.png',
      riverbank: base + 'terrain/lind_riverbank.png'
    },
    objects: [
      {id:'cliff', label:'崖', path:base+'terrain/lind_cliff.png', x:150, y:50,
        width:180, height:150, collision:[20,80,140,50]}
    ]
  };
})();
