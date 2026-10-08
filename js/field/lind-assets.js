/* Standalone field production assets. Coordinates below are DEV review positions,
 * not story/save coordinates; final map integration is STEP 12. */
(function () {
  'use strict';
  const base = 'img/field/lind/';
  const building = (id, label, x, y, width, height) => ({id, label,
    path:base+'buildings/'+id+'.png', x, y, width, height,
    collision:[Math.round(width*.18),Math.round(height*.62),Math.round(width*.64),Math.round(height*.27)]});
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
        width:180, height:150, collision:[20,80,140,50]},
      building('lind_elder_house', '長老の家', 370, 150, 280, 230),
      building('lind_inn', '宿屋', 720, 110, 310, 270),
      building('lind_aidan_house', 'エイダンの家', 1100, 210, 290, 230),
      building('lind_item_shop', '道具屋', 150, 450, 290, 230),
      building('lind_house_01', '村人の家 1', 140, 810, 270, 220),
      building('lind_house_02', '村人の家 2', 450, 960, 270, 220),
      building('lind_house_03', '村人の家 3', 110, 1140, 270, 220),
      building('lind_house_04', '村人の家 4', 760, 840, 270, 220),
      building('lind_barn', '納屋', 970, 640, 250, 190),
      building('lind_storage', '倉庫', 1220, 660, 190, 155)
    ]
  };
})();
