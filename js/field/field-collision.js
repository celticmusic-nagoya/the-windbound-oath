/* Map-independent feet collision. Static shapes are compiled once, not per movement sample. */
(function () {
  'use strict';
  const footprint=Object.freeze({x:6,y:32,width:22,height:10,anchorX:17,anchorY:42});
  function overlaps(shape,x,y) {
    return x+footprint.x+footprint.width>shape.x && x+footprint.x<shape.x+shape.width &&
      y+footprint.y+footprint.height>shape.y && y+footprint.y<shape.y+shape.height;
  }
  function compile(objects) {
    const shapes=[];
    for(const object of objects) {
      const category=object.collisionCategory || (object.path?.includes('/buildings/') ? 'building' : 'prop');
      const parts=object.collisionShapes || (object.collisions || (object.collision?[object.collision]:[]))
        .map((c,i)=>({type:'rect',x:c[0],y:c[1],width:c[2],height:c[3],part:String(i)}));
      for(const part of parts) {
        if(part.type!=='rect')throw new Error('Unsupported field collision shape: '+part.type);
        if(![part.x,part.y,part.width,part.height].every(Number.isFinite)||part.width<=0||part.height<=0)
          throw new Error('Invalid field collision rectangle: '+object.id);
        shapes.push(Object.freeze({...part,id:object.id+':'+(part.part||shapes.length),objectId:object.id,
          label:object.label,category,x:object.x+part.x,y:object.y+part.y}));
      }
    }
    Object.freeze(shapes);
    return Object.freeze({shapes,blocked(x,y){for(const shape of shapes)if(overlaps(shape,x,y))return true;return false;}});
  }
  window.FieldCollision=Object.freeze({footprint,overlaps,compile});
})();
