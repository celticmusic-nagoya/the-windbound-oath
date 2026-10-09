/* DEV art review only: authored terrain, never collision/navigation data.
 * Macro routes retain the existing village axes and bridge approaches.
 * Narrow doorstep trails and farm wear are cosmetic, not new walkable lanes. */
(function () {
  'use strict';
  window.LindTerrainLayout = Object.freeze({
    width:2200, height:1550,
    routes:[
      {id:'village-west-east',points:[[80,610],[600,610],[1000,610],[1435,605]],width:100,seed:11},
      {id:'village-north-south',points:[[730,100],[730,520],[730,970],[730,1350]],width:100,seed:23},
      {id:'bridge-east',points:[[1630,595],[1777,595],[1777,770]],width:60,seed:37},
      {id:'farm-work',points:[[900,1070],[1130,1070],[1400,1070]],width:30,seed:43},
      {id:'orchard-work',points:[[730,1250],[900,1250],[900,1355]],width:28,seed:59}
    ],
    plaza:{id:'wind-stone-plaza',x:745,y:580,width:350,height:300,seed:71},
    trails:[
      {id:'lind_item_shop',points:[[321,704],[525,710],[730,710]],width:28,seed:83},
      {id:'lind_house_02',points:[[640,1220],[730,1220]],width:25,seed:97},
      {id:'lind_aidan_house',points:[[1280,490],[1280,610]],width:28,seed:101},
      {id:'lind_inn',points:[[908,420],[865,470]],width:30,seed:113},
      {id:'lind_elder_house',points:[[490,410],[650,410],[700,430]],width:24,seed:127}
    ],
    // A few work-worn patches, not a world-wide random decoration scatter.
    patches:[
      {x:890,y:1245,width:52,height:35,seed:131},
      {x:1335,y:1070,width:64,height:34,seed:149},
      {x:1690,y:595,width:60,height:50,seed:157}
    ]
  });
})();
