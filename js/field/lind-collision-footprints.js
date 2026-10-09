/* Ground footprints relative to normalized visible content, NOT PNG canvas.
 * Body/foundation and individual front props are solid; central steps/open porch
 * retain a narrow approach lane. Lanes never subtract from collision shapes.
 * depth is the facade's ground line, not the furthest flower/fence in the PNG.
 * Approaches are DEV geometry only, never an interior/event trigger. */
(function () {
  'use strict';
  const profiles={
    lind_elder_house:{door:[.43,.90],lane:[.35,.83,.15,.17],depth:.83,parts:[
      ['wall',.16,.59,.74,.24],['left-fence',.02,.69,.17,.15],
      ['left-foundation',.16,.79,.19,.10],['right-foundation',.50,.79,.34,.065],
      ['left-bed',.15,.81,.18,.10],['right-fence',.85,.70,.12,.14],['right-bed',.59,.82,.27,.07],
      ['front-fence',.50,.85,.14,.13],['front-barrel',.66,.83,.075,.12],
      ['front-pot',.605,.90,.06,.08],['front-crates',.745,.81,.10,.125]]},
    lind_inn:{door:[.605,.925],lane:[.535,.85,.135,.15],depth:.85,parts:[
      ['wall',.15,.57,.73,.28],['awning-base',.04,.76,.30,.15],
      ['left-foundation',.15,.81,.385,.085],['right-foundation',.67,.81,.21,.085],
      ['left-planters',.13,.87,.26,.08],['front-planter',.36,.86,.08,.11],
      ['door-left-planter',.445,.87,.09,.115],['door-right-barrel',.67,.86,.10,.115],
      ['right-cart',.83,.76,.14,.18],['cart-wheel',.83,.85,.135,.105]]},
    lind_aidan_house:{door:[.62,.915],lane:[.55,.84,.14,.16],depth:.84,parts:[
      ['wall',.14,.61,.70,.23],['left-fence',.02,.67,.14,.20],
      ['left-foundation',.14,.80,.40,.10],['right-foundation',.69,.80,.15,.085],
      ['left-bed',.15,.84,.28,.09],['front-barrel',.435,.855,.105,.115],
      ['right-barrels',.83,.78,.14,.13],['right-bed',.78,.88,.10,.05],['front-pot',.745,.83,.09,.085]]},
    lind_item_shop:{door:[.59,.91],lane:[.54,.84,.105,.16],depth:.84,parts:[
      ['wall',.13,.59,.70,.25],['left-fence',.03,.73,.18,.18],
      ['left-foundation',.13,.79,.395,.105],['right-foundation',.645,.79,.185,.10],
      ['front-barrel-left',.21,.84,.14,.125],['front-barrel-right',.39,.83,.15,.137],
      ['front-display',.645,.795,.125,.115],['front-crates',.77,.84,.12,.087],
      ['display-post',.88,.78,.045,.10],['side-barrel',.86,.71,.10,.19],
      ['right-bed',.72,.91,.16,.037]]},
    lind_house_01:{door:[.635,.93],lane:[.55,.86,.17,.14],depth:.86,parts:[
      ['wall',.12,.61,.75,.25],['left-fence',.02,.68,.12,.19],
      ['left-foundation',.12,.80,.42,.095],['right-foundation',.72,.80,.15,.075],
      ['left-bed',.12,.85,.33,.08],['front-fence',.30,.865,.155,.12],
      ['front-barrel',.455,.845,.085,.125],['right-fence',.87,.71,.10,.16],
      ['right-bed',.76,.85,.19,.07],['front-right-fence',.76,.83,.11,.125]]},
    lind_house_02:{door:[.705,.93],lane:[.645,.86,.135,.14],depth:.86,parts:[
      ['wall',.16,.59,.69,.27],['left-fence',.02,.70,.16,.20],
      ['left-foundation',.16,.80,.48,.10],['right-foundation',.78,.80,.07,.06],
      ['left-bed',.12,.85,.34,.10],['front-fence',.26,.82,.20,.145],
      ['front-barrel',.475,.845,.105,.12],['door-left-planter',.575,.83,.07,.08],
      ['right-fence',.85,.71,.13,.19],['right-bed',.78,.86,.11,.06],['door-right-barrel',.795,.805,.085,.09]]},
    lind_house_03:{door:[.645,.93],lane:[.575,.85,.145,.15],depth:.85,parts:[
      ['wall',.13,.61,.70,.24],['left-fence',.02,.71,.14,.19],
      ['left-foundation',.13,.80,.44,.09],['right-foundation',.72,.80,.11,.07],
      ['left-bed',.12,.84,.36,.11],['front-fence',.20,.83,.25,.13],
      ['front-barrel',.445,.84,.125,.128],['right-fence',.82,.70,.14,.20],
      ['right-bed',.73,.87,.13,.06],['door-right-barrel',.73,.795,.09,.10],['front-right-post',.80,.84,.06,.10]]},
    lind_house_04:{door:[.655,.93],lane:[.585,.85,.145,.15],depth:.85,parts:[
      ['wall',.15,.59,.70,.26],['left-fence',.02,.70,.17,.19],
      ['left-foundation',.15,.80,.42,.11],['right-foundation',.73,.80,.12,.08],
      ['left-bed',.13,.85,.31,.09],['front-fence',.20,.86,.24,.10],
      ['front-barrel',.435,.855,.135,.13],['right-fence',.85,.70,.12,.18],['right-bed',.73,.85,.17,.07]]},
    lind_barn:{door:[.47,.965],lane:[.395,.86,.145,.14],depth:.86,parts:[
      ['wall',.16,.55,.72,.31],['left-cart',.03,.66,.21,.22],
      ['left-foundation',.16,.80,.225,.125],['right-foundation',.54,.80,.34,.10],
      ['cart-shafts',.19,.83,.12,.13],['left-stores',.10,.84,.28,.10],
      ['right-stores',.78,.75,.19,.14],['front-stores',.58,.83,.31,.10],
      ['front-barrel',.55,.83,.09,.145],['front-hay',.645,.865,.13,.095],['right-hay',.75,.84,.12,.10]]},
    lind_storage:{door:[.43,1.04],lane:[.36,.945,.15,.155],depth:.89,access:'closed-storage',parts:[
      ['wall',.15,.51,.70,.35],['left-crates',.07,.74,.19,.18],
      ['front-crate',.095,.82,.13,.14],['loose-wood',.265,.855,.08,.09],
      ['right-barrel',.84,.66,.14,.25],['front-logs',.23,.84,.50,.08],['log-base',.355,.80,.43,.105]]},
    lind_cowshed:{door:[.62,1.02],lane:[.535,.90,.185,.20],depth:.79,access:'pen-front',parts:[
      ['shed',.13,.55,.74,.24],['left-fence',.03,.72,.13,.19],
      ['front-left-fence',.18,.77,.33,.16],['front-post',.445,.825,.07,.14],
      ['front-gate',.57,.755,.15,.125],['right-fence',.84,.65,.12,.21]]},
    lind_pigsty:{door:[.69,1.065],lane:[.59,.965,.19,.135],depth:.79,access:'pen-front',parts:[
      ['shed',.13,.55,.73,.24],['left-fence',.03,.72,.14,.19],
      ['front-left-fence',.21,.77,.37,.18],['front-post',.55,.80,.09,.15],
      ['front-gate',.755,.75,.10,.15],['right-fence',.83,.65,.13,.23]]},
    lind_chicken_coop:{door:[.625,.92],lane:[.51,.78,.225,.22],depth:.78,access:'open-gate',parts:[
      ['coop',.21,.50,.60,.28],['left-fence',.05,.71,.14,.22],
      ['left-front-fence',.18,.825,.33,.135],['open-gate-leaf',.735,.805,.085,.14],['right-fence',.80,.70,.13,.23]]},
    train_shed:{door:[.60,.91],lane:[.45,.70,.31,.30],depth:.70,access:'open-porch',parts:[
      ['back-wall',.14,.55,.74,.15],['left-wall',.105,.67,.17,.13],
      ['left-back-post',.065,.705,.095,.14],['front-column',.30,.79,.095,.205],
      ['right-back-post',.90,.62,.055,.195],['right-front-post',.845,.69,.075,.165],
      ['left-platform-edge',.28,.805,.155,.11],['right-platform-edge',.76,.73,.15,.13]]}
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
      role:building ? (/wall|foundation|column|shed|coop/.test(part)?'building':'front-prop') : undefined,
      x:x*object.width,y:y*object.height,width:width*object.width,height:height*object.height}));
    object.collision=null;delete object.collisions;
    if(building?.door)object.doorApproach={x:object.x+building.door[0]*object.width,
      y:object.y+building.door[1]*object.height};
    if(building?.lane){const [x,y,width,height]=building.lane;
      // Debug/QA metadata only: this lane never overrides a solid collision.
      object.doorApproachLane={id:object.id+':door-approach',x:object.x+x*object.width,
        y:object.y+y*object.height,width:width*object.width,height:height*object.height};}
    if(building?.depth!==undefined)object.depthY=object.y+building.depth*object.height;
    if(building)object.approachAccess=building.access||'door';
  }
})();
