/* HEADGEAR-LAYER-02: isolated DOM renderer. Never used by production game. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root) root.FieldHeadgearRenderer = api;
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  const directions = Object.freeze(['down','left','right','up']);
  function plan(base, layers, direction) {
    if (!directions.includes(direction)) throw new TypeError('invalid direction');
    if (!base || !base[direction] || typeof base[direction] !== 'string') throw new TypeError('missing base');
    if (!Array.isArray(layers)) throw new TypeError('invalid layers');
    const sorted=[...layers].sort((a,b)=>['upper','middle','lower'].indexOf(a.slot)-['upper','middle','lower'].indexOf(b.slot));
    const slots=new Set();
    for(const layer of sorted){
      if(!['upper','middle','lower'].includes(layer.slot) || slots.has(layer.slot) ||
         !layer.directions || typeof layer.directions[direction]!=='string')throw new TypeError('invalid layer');
      slots.add(layer.slot);
    }
    return Object.freeze([{slot:'base',src:base[direction]},...sorted.map(l=>({slot:l.slot,src:l.directions[direction]}))]);
  }
  function render(documentRef, container, framePlan, imageSize) {
    if (!documentRef || !container || !Array.isArray(framePlan) || !framePlan.length ||
        !Number.isInteger(imageSize.width) || !Number.isInteger(imageSize.height) ||
        imageSize.width<1 || imageSize.height<1) throw new TypeError('invalid render arguments');
    const fragment=documentRef.createDocumentFragment();
    const wrapper=documentRef.createElement('div');
    wrapper.className='headgear-sprite';
    wrapper.style.width=imageSize.width+'px';
    wrapper.style.height=imageSize.height+'px';
    for(const item of framePlan){
      const img=documentRef.createElement('img');
      img.className='headgear-sprite__layer';
      img.dataset.slot=item.slot;
      img.src=item.src;
      img.alt='';
      img.draggable=false;
      wrapper.appendChild(img);
    }
    fragment.appendChild(wrapper);
    container.replaceChildren(fragment);
    return wrapper; // Apply motion transform ONLY to this shared parent.
  }
  return Object.freeze({plan,render});
});
