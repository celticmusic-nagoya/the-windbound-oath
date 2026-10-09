/* DEV-stage geography: eastern river, central crossing, SE fishing deck.
 * Stand areas reserve space for later fisherman/player integration, not NPCs. */
(function () {
  'use strict';
  const water=Object.freeze({x:1450,y:0,width:180,height:1550});
  // Preserve the approved bank safety margin: existing x+30 / x<1630 checks
  // equal feet overlap with 2px west and 6px east beyond the visible water.
  const collisionEnvelope=Object.freeze({...water,x:water.x-2,width:water.width+8});
  const crossings = [
    // Finite deck strip, excluding transparent canvas and outer rail/supports.
    // Four extra pixels below the old strip remain over the visible bridge.
    {id:'bridge',x:1425,y:580,width:240,height:30},
    {id:'fishing_deck',polygon:[[1432,1345],[1583,1360],[1576,1393],[1411,1376]]}
  ];
  const standingAreas = [
    {id:'fisherman_future',x:1430,y:1325},
    {id:'player',x:1475,y:1337}
  ];
  function inside(point, polygon) {
    let result = false;
    for (let i=0,j=polygon.length-1;i<polygon.length;j=i++) {
      const a=polygon[i],b=polygon[j];
      if ((a[1]>point[1]) !== (b[1]>point[1]) &&
        point[0] < (b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]) result=!result;
    }
    return result;
  }
  function blocked(x, y) {
    const inRiver = FieldCollision.overlaps(collisionEnvelope,x,y);
    if (!inRiver) return false;
    const f=FieldCollision.footprint;
    const foot = {x:x+f.x,y:y+f.y,width:f.width,height:f.height};
    return !crossings.some(c => c.polygon ?
      [[foot.x,foot.y],[foot.x+foot.width,foot.y],[foot.x,foot.y+foot.height],
        [foot.x+foot.width,foot.y+foot.height]].every(p=>inside(p,c.polygon)) :
      foot.x>=c.x && foot.x+foot.width<=c.x+c.width && foot.y>=c.y && foot.y+foot.height<=c.y+c.height);
  }
  window.LindFieldRiver = Object.freeze({blocked,crossings,standingAreas,water,collisionEnvelope});
})();
