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
    layer:walkable ? 'groundDecoration' : 'structure', motion:walkable ? 'wind' : 'static',
    collision:walkable ? null : [Math.round(width*.2),Math.round(height*.65),Math.round(width*.6),Math.round(height*.23)]});
  const prop = (id, label, folder, x, y, width, height, motion = 'static', solid = true) => ({id,label,
    path:base+folder+'/'+id+'.png',x,y,width,height,motion,
    layer:solid ? 'structure' : 'groundDecoration',
    collision:solid ? [Math.round(width*.15),Math.round(height*.76),Math.round(width*.7),Math.round(height*.2)] : null});
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
      farm('lind_farm_tools', '農具', 1360, 1320, 70, 90),
      prop('lind_tree_01', '村の木', 'nature', 50, 180, 130, 160, 'wind'),
      prop('lind_bush', '低木', 'nature', 470, 510, 55, 42, 'wind'),
      prop('lind_flower_patch', '白・黄・紫の花', 'nature', 525, 540, 42, 28, 'wind', false),
      prop('lind_grass_tuft', '草・クローバー', 'nature', 840, 740, 36, 28, 'wind', false),
      prop('lind_rock_small', '小石', 'nature', 820, 930, 25, 18),
      prop('lind_rock_large', '大きな石', 'nature', 80, 680, 60, 46),
      prop('lind_stump', '切り株', 'nature', 870, 1110, 36, 30),
      prop('lind_fence', '牛の牧区・柵', 'props', 950, 1025, 150, 30),
      {...prop('lind_fence', '豚の牧区・柵', 'props', 1110, 1025, 150, 30),id:'pig_fence',boundsId:'lind_fence'},
      {...prop('lind_fence', '鶏の牧区・柵', 'props', 1270, 1025, 140, 30),id:'chicken_fence',boundsId:'lind_fence'},
      prop('lind_crate', '木箱', 'props', 1250, 825, 36, 36),
      prop('lind_barrel', '樽', 'props', 1320, 810, 30, 42),
      prop('lind_feed_sack', '飼料', 'props', 905, 965, 30, 38),
      prop('lind_water_bucket', '水桶', 'props', 1055, 965, 38, 24),
      prop('lind_laundry', '洗濯物', 'props', 470, 1230, 115, 95, 'wind'),
      prop('lind_sign', '葉の看板', 'props', 540, 440, 30, 45, 'wind')
    ]
  };
  // Normalize transparent export margins in the renderer, without changing PNGs.
  // Coordinates/width describe visible content; source dimensions preserve aspect.
  window.LindFieldAssets.objects.forEach(obj => {
    const b = window.LindFieldContentBounds?.[obj.boundsId || (obj.id === 'cliff' ? 'lind_cliff' : obj.id)];
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
    if (obj.id === 'lind_tree_01') {
      obj.collision = [Math.round(obj.width*.4),Math.round(obj.height*.84),
        Math.round(obj.width*.22),Math.round(obj.height*.15)];
    }
    if (obj.id === 'lind_laundry') {
      obj.collision = null;
      obj.collisions = [.05,.88].map(x => [Math.round(obj.width*x),
        Math.round(obj.height*.85),Math.round(obj.width*.08),Math.round(obj.height*.13)]);
    }
    if (obj.id === 'lind_fence' || obj.boundsId === 'lind_fence') {
      // Follow the reference's angled fence feet, rather than blocking its sky.
      obj.collision = null;
      obj.collisions = Array.from({length:6}, (_, i) => [Math.floor(obj.width*i/6),
        Math.round(obj.height*(.85-.3*i/5)),Math.ceil(obj.width/6),Math.round(obj.height*.15)]);
    }
  });
})();
