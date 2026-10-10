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
    const index=buildIndex(shapes);
    return Object.freeze({shapes,blocked(x,y){return index.blocked(x,y);}});
  }
  // Uniform spatial hash over compiled rects. A shape is registered in every cell
  // its rect touches; a query inspects only the cells touched by the foot box.
  // Result is identical to scanning all shapes, so Lind behaviour is unchanged.
  const CELL=128;
  function buildIndex(shapes,getEnabled) {
    const cells=new Map();
    const key=(i,j)=>i+','+j;
    shapes.forEach((shape,n)=>{
      const i0=Math.floor(shape.x/CELL),i1=Math.floor((shape.x+shape.width)/CELL);
      const j0=Math.floor(shape.y/CELL),j1=Math.floor((shape.y+shape.height)/CELL);
      for(let i=i0;i<=i1;i++)for(let j=j0;j<=j1;j++){
        const k=key(i,j);let list=cells.get(k);if(!list){list=[];cells.set(k,list);}list.push(n);
      }
    });
    return {cells,blocked(x,y) {
      const fx=x+footprint.x,fy=y+footprint.y;
      const i0=Math.floor(fx/CELL),i1=Math.floor((fx+footprint.width)/CELL);
      const j0=Math.floor(fy/CELL),j1=Math.floor((fy+footprint.height)/CELL);
      for(let i=i0;i<=i1;i++)for(let j=j0;j<=j1;j++) {
        const list=cells.get(key(i,j));if(!list)continue;
        for(const n of list){const shape=shapes[n];if(overlaps(shape,x,y)&&(!getEnabled||getEnabled(shape)))return true;}
      }
      return false;
    }};
  }
  // Map-data collision (Moss Forest schema v2). Input is world-space blockers whose
  // final shape is always rect(s): {id, shape:'rect',x,y,w,h} or {id, shape:'rects', rects:[[x,y,w,h]...]}.
  // `enabledWhen:{flag,is}` is evaluated live against flags(name), so a story seal can
  // open without recompiling. Ellipses/polygons must be converted to rects by the data
  // tools beforehand; anything else throws, like compile().
  function compileMap(blockers,flags=()=>undefined) {
    const shapes=[];
    for(const b of blockers) {
      const list=b.shape==='rect'?[[b.x,b.y,b.w,b.h]]:b.shape==='rects'?b.rects:null;
      if(!list)throw new Error('Unsupported field collision shape: '+b.shape);
      list.forEach((r,i)=>{
        if(!r.every(Number.isFinite)||r[2]<=0||r[3]<=0)throw new Error('Invalid field collision rectangle: '+b.id);
        // Rects are world-space (feet basis): overlaps() tests them against the 22x10 foot box,
        // i.e. actor top-left = feet - (anchorX, anchorY).
        shapes.push(Object.freeze({type:'rect',x:r[0],y:r[1],width:r[2],height:r[3],id:b.id+':'+i,objectId:b.id,
          category:b.tag||'prop',enabledWhen:b.enabledWhen||null}));
      });
    }
    Object.freeze(shapes);
    const enabled=shape=>!shape.enabledWhen||Boolean(flags(shape.enabledWhen.flag))===Boolean(shape.enabledWhen.is);
    const index=buildIndex(shapes,enabled);
    return Object.freeze({shapes,blocked(x,y){return index.blocked(x,y);}});
  }
  window.FieldCollision=Object.freeze({footprint,overlaps,compile,compileMap});
})();
