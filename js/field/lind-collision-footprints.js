/* Audited ground footprints, relative to normalized visible content, NOT PNG canvas.
 * Roofs/canopies are depth art. Walls, side fences and attached ground props are solid.
 * A door approach denotes outside walkable space, not a new interior/event trigger. */
(function () {
  'use strict';
  const profiles={
    lind_elder_house:{door:[.43,.95],parts:[
      ['wall',.16,.59,.74,.24],['left-fence',.02,.69,.17,.15],
      ['left-bed',.15,.81,.18,.10],['right-fence',.85,.70,.12,.14],['right-bed',.59,.82,.27,.07]]},
    lind_inn:{door:[.58,.96],parts:[
      ['wall',.15,.57,.73,.28],['awning-base',.04,.76,.30,.15],
      ['left-planters',.13,.87,.26,.08],['right-cart',.83,.76,.14,.18]]},
    lind_aidan_house:{door:[.60,.96],parts:[
      ['wall',.14,.61,.70,.23],['left-fence',.02,.67,.14,.20],
      ['left-bed',.15,.84,.30,.09],['right-barrels',.83,.78,.14,.13],['right-bed',.78,.88,.10,.05]]},
    lind_item_shop:{door:[.63,.97],parts:[
      ['wall',.13,.59,.70,.25],['left-barrels',.03,.73,.18,.18],
      ['front-barrels',.16,.85,.32,.11],['right-crates',.73,.83,.22,.09],['side-barrel',.89,.71,.09,.17]]},
    lind_house_01:{door:[.61,.96],parts:[
      ['wall',.12,.61,.75,.25],['left-fence',.02,.68,.12,.19],
      ['left-bed',.12,.85,.33,.08],['right-fence',.87,.71,.10,.16],['right-bed',.76,.85,.19,.07]]},
    lind_house_02:{door:[.62,.96],parts:[
      ['wall',.16,.59,.69,.27],['left-fence',.02,.70,.16,.20],
      ['left-bed',.12,.85,.34,.10],['right-fence',.85,.71,.13,.19],['right-bed',.77,.86,.12,.06]]},
    lind_house_03:{door:[.61,.96],parts:[
      ['wall',.13,.61,.70,.24],['left-fence',.02,.71,.14,.19],
      ['left-bed',.12,.84,.36,.11],['right-fence',.82,.70,.14,.20],['right-bed',.73,.87,.13,.06]]},
    lind_house_04:{door:[.60,.96],parts:[
      ['wall',.15,.59,.70,.26],['left-fence',.02,.70,.17,.19],
      ['left-bed',.13,.85,.34,.09],['right-fence',.85,.70,.12,.18],['right-bed',.73,.85,.17,.07]]},
    lind_barn:{door:[.47,.97],parts:[
      ['wall',.16,.55,.72,.31],['left-cart',.03,.66,.21,.22],
      ['left-stores',.10,.84,.28,.10],['right-stores',.78,.75,.19,.14],['front-stores',.58,.83,.31,.10]]},
    lind_storage:{door:[.40,1.02],parts:[
      ['wall',.15,.51,.70,.35],['left-crates',.07,.74,.19,.18],
      ['right-barrel',.84,.66,.14,.25],['front-logs',.23,.84,.50,.08]]},
    lind_cowshed:{parts:[['shed',.13,.55,.74,.24],['left-fence',.03,.72,.13,.19],
      ['front-fence',.17,.82,.54,.11],['right-fence',.84,.65,.12,.21]]},
    lind_pigsty:{parts:[['shed',.13,.55,.73,.24],['left-fence',.03,.72,.14,.19],
      ['front-fence',.16,.82,.55,.11],['right-fence',.83,.65,.13,.23]]},
    lind_chicken_coop:{parts:[['coop',.21,.50,.60,.28],['left-fence',.05,.71,.14,.22],
      ['left-front-fence',.18,.85,.33,.10],['right-fence',.80,.70,.13,.23]]}
  };
  const props={
    lind_haystack:[['hay-base',.14,.62,.68,.31]],
    lind_hay_bale:[['hay-base',.10,.58,.80,.36]],
    lind_cart:[['cart-body',.08,.30,.60,.44],['shafts',.50,.64,.21,.16],['shaft-ends',.72,.82,.20,.12]],
    lind_farm_tools:[['rack',.10,.72,.65,.20],['bucket',.72,.77,.20,.18]],
    lind_bush:[['bush-base',.10,.62,.80,.30]],
    lind_rock_small:[['rock-base',.12,.58,.76,.32]],
    lind_rock_large:[['rock-base',.10,.58,.80,.34]],
    lind_stump:[['stump-base',.14,.65,.72,.28]],
    lind_crate:[['front-base',.08,.56,.72,.30],['right-base',.72,.48,.20,.28]],
    lind_barrel:[['barrel-base',.10,.68,.80,.28]],
    lind_feed_sack:[['sack-base',.14,.68,.72,.29]],
    lind_water_bucket:[['left-base',.08,.53,.27,.40],['middle-base',.35,.45,.32,.36],['right-base',.67,.35,.28,.36]],
    lind_laundry:[['left-post',.02,.85,.12,.13],['right-post',.86,.63,.10,.13]],
    lind_fish_basket:[['basket-base',.10,.71,.76,.25]],
    train_shed:[['shed',.13,.55,.75,.30],['left-post',.09,.80,.11,.13],['floor-front',.20,.83,.65,.08]],
    train_weapon_rack:[['rack-base',.10,.72,.78,.20],['right-support',.88,.60,.10,.22]],
    train_target:[['stand',.08,.78,.74,.17]],
    train_dummy:[['stand',.21,.84,.59,.13]],
    train_post:[['post-base',.19,.84,.55,.12]],
    train_flag_green:[['pole-base',.12,.86,.13,.12]]
  };
  for(const object of window.LindFieldAssets.objects) {
    const building=profiles[object.id],parts=building?.parts || props[object.boundsId||object.id];
    if(!parts)continue;
    object.collisionCategory=building?'building':'prop';
    object.collisionShapes=parts.map(([part,x,y,width,height])=>({type:'rect',part,
      x:x*object.width,y:y*object.height,width:width*object.width,height:height*object.height}));
    object.collision=null;delete object.collisions;
    if(building?.door)object.doorApproach={x:object.x+building.door[0]*object.width,
      y:object.y+building.door[1]*object.height};
  }
})();
