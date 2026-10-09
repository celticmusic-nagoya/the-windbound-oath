/* Reusable DEV overlay: adapters provide world geometry; no map or battle logic here. */
(function () {
  'use strict';
  const ns='http://www.w3.org/2000/svg';let serial=0;
  function node(type,attributes,parent) {
    const element=document.createElementNS(ns,type);
    for(const [key,value] of Object.entries(attributes))element.setAttribute(key,value);
    if(parent)parent.append(element);return element;
  }
  function rect(shape,parent,category=shape.category) {
    return node('rect',{x:shape.x,y:shape.y,width:shape.width,height:shape.height,
      'data-collision-category':category,'data-collision-role':shape.role||'',
      'data-collision-id':shape.id||'',class:'field-collision-shape'},parent);
  }
  function create({world,overlayParent=world,controls,getGeometry,getPlayer}) {
    if(!window.WINDBOUND_DEV)return null;
    let active=false,enabled=false,frame=null,renders=0,svg=null,foot=null,anchor=null,dynamic=[];
    const button=document.createElement('button');button.type='button';button.className='field-collision-toggle';
    button.title='足元:紫 / 建物本体:橙 / 正面小物:黄 / 玄関通路:緑破線 / 水:青';
    (controls.querySelector('.lind-camera-row')||controls).append(button);
    function paintButton(){button.textContent='COLLISION '+(enabled?'ON':'OFF');button.setAttribute('aria-pressed',String(enabled));}
    function stop(){cancelAnimationFrame(frame);frame=null;if(svg)svg.setAttribute('hidden','');}
    function build(geometry) {
      if(svg)svg.remove();dynamic=[];
      svg=node('svg',{class:'field-collision-debug',width:geometry.bounds.width,height:geometry.bounds.height,
        viewBox:`0 0 ${geometry.bounds.width} ${geometry.bounds.height}`,'aria-hidden':'true'},overlayParent);
      const water=geometry.water;
      if(water){const maskId='field-collision-water-'+(++serial),mask=node('mask',{id:maskId,maskUnits:'userSpaceOnUse',
        x:0,y:0,width:geometry.bounds.width,height:geometry.bounds.height},node('defs',{},svg));
        node('rect',{...water.rect,fill:'white'},mask);
        for(const crossing of water.crossings){if(crossing.polygon)node('polygon',{points:crossing.polygon.map(p=>p.join(',')).join(' '),fill:'black'},mask);
          else node('rect',{x:crossing.x,y:crossing.y,width:crossing.width,height:crossing.height,fill:'black'},mask);}
        const area=rect(water.rect,svg,'water');area.setAttribute('mask','url(#'+maskId+')');
      }
      for(const shape of geometry.staticShapes)rect(shape,svg);
      for(const lane of geometry.approachLanes||[])rect(lane,svg,'door-approach');
      for(const shape of geometry.dynamicShapes)dynamic.push(rect(shape,svg,'actor'));
      rect({x:0,y:0,...geometry.bounds},svg,'boundary');
      foot=rect({x:0,y:0,width:FieldCollision.footprint.width,height:FieldCollision.footprint.height},svg,'player');
      anchor=node('circle',{r:2,'data-collision-category':'player',class:'field-collision-anchor'},svg);
    }
    function tick() {
      if(!active||!enabled)return;
      const geometry=getGeometry(),player=getPlayer(),f=FieldCollision.footprint;
      foot.setAttribute('x',player.x+f.x);foot.setAttribute('y',player.y+f.y);
      anchor.setAttribute('cx',player.x+f.anchorX);anchor.setAttribute('cy',player.y+f.anchorY);
      geometry.dynamicShapes.forEach((shape,i)=>{const el=dynamic[i];if(el){el.setAttribute('x',shape.x);el.setAttribute('y',shape.y);}});
      renders++;frame=requestAnimationFrame(tick);
    }
    function setEnabled(value) {
      enabled=active&&Boolean(value);stop();paintButton();
      if(enabled){build(getGeometry());svg.removeAttribute('hidden');tick();}return enabled;
    }
    button.onclick=event=>{setEnabled(!enabled);if(event.detail)button.blur();};paintButton();
    return Object.freeze({setEnabled,setActive(value){active=Boolean(value);if(!active)setEnabled(false);},
      get status(){return {active,enabled,renders,scheduled:frame!==null,overlays:svg?1:0};}});
  }
  window.FieldCollisionDebug=Object.freeze({create});
})();
