/* Standalone field production assets. Coordinates below are DEV review positions,
 * not story/save coordinates; final map integration is STEP 12. */
(function () {
  'use strict';
  const base = 'img/field/lind/';
  const building = (id, label, x, y, width, height) => ({id, label,
    path:base+'buildings/'+id+'.png', x, y, width, height,
    collision:[Math.round(width*.18),Math.round(height*.62),Math.round(width*.64),Math.round(height*.27)]});
  const farm = (id, label, x, y, width, height, walkable = false) => ({id, label,
    path:base+'farm/'+id+'.png', x, y, width, height,
    layer:walkable ? 'groundDecoration' : 'structure',
    collision:walkable ? null : [Math.round(width*.2),Math.round(height*.65),Math.round(width*.6),Math.round(height*.23)]});
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
      building('lind_house_04', '村人の家 4', 430, 740, 270, 220),
      building('lind_barn', '納屋', 970, 640, 250, 190),
      building('lind_storage', '倉庫', 1220, 660, 190, 155),
      farm('lind_cowshed', '牛舎', 950, 880, 150, 140),
      farm('lind_pigsty', '豚舎', 1110, 880, 150, 140),
      farm('lind_chicken_coop', '鶏小屋', 1270, 880, 140, 140),
      farm('lind_field_wheat', '小麦畑', 920, 1080, 150, 150, true),
      farm('lind_field_vegetables', '野菜畑', 1110, 1080, 150, 150, true),
      farm('lind_field_flower', '花畑', 1280, 1080, 130, 130, true),
      farm('lind_orchard_apple', 'リンゴ果樹', 930, 1280, 250, 190),
      farm('lind_haystack', '干し草', 1190, 1320, 80, 100),
      farm('lind_hay_bale', '干し草ロール', 1300, 1330, 60, 60),
      farm('lind_cart', '荷車', 1110, 1235, 75, 75),
      farm('lind_farm_tools', '農具', 1360, 1320, 70, 90)
    ]
  };
  // Normalize transparent export margins in the renderer, without changing PNGs.
  // Coordinates/width describe visible content; source dimensions preserve aspect.
  window.LindFieldAssets.objects.forEach(obj => {
    const b = window.LindFieldContentBounds?.[obj.id === 'cliff' ? 'lind_cliff' : obj.id];
    if (!b) return;
    const oldHeight = obj.height;
    const scale = obj.width/b[4];
    obj.height = Math.round(b[5]*scale);
    obj.draw = {x:obj.x-b[2]*scale, y:obj.y-b[3]*scale,
      width:b[0]*scale, height:b[1]*scale};
    if (obj.collision) {
      obj.collision[1] = Math.round(obj.collision[1]*obj.height/oldHeight);
      obj.collision[3] = Math.round(obj.collision[3]*obj.height/oldHeight);
    }
    if (obj.id === 'lind_orchard_apple') {
      obj.collision = null;
      obj.collisions = [.17,.62].map(x => [Math.round(obj.width*x),
        Math.round(obj.height*.74),Math.round(obj.width*.18),Math.round(obj.height*.16)]);
    }
  });
})();
