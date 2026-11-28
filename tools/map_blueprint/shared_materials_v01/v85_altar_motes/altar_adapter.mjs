// Candidate adapter: Three-compatible mesh/material interface, not a game event hook.
// Caller supplies loaded VFX-only root; never pass base altar root.
export function bindAltarLayers(root, {floating=null, particles=[]}={}) {
  if(!root || typeof root.traverse!=='function') throw new TypeError('VFX root required');
  const ids=['01_stele','02_posts','03_floor'];
  const nodes=new Map(), originals=new Map(), copies=new Map();
  root.traverse(o=>{if(!o.isMesh)return;const id=ids.find(i=>o.name===`V82_FX_${i}`);if(!id||nodes.has(id))throw Error('unexpected or duplicate VFX mesh');nodes.set(id,o);});
  if(nodes.size!==3)throw Error('all three VFX layers required');
  for(const [id,o] of nodes){const m=o.material;if(!m||Array.isArray(m)||typeof m.clone!=='function'||!m.emissive||!Number.isFinite(m.emissiveIntensity))throw Error(`invalid material ${id}`);}
  if(!Array.isArray(particles)||particles.length>24||new Set(particles).size!==particles.length)throw Error('particle pool exceeds budget or repeats');
  for(const o of [floating,...particles].filter(Boolean))if(!o.position||typeof o.position.set!=='function'||!o.material||!Number.isFinite(o.material.opacity)||typeof o.material.clone!=='function')throw Error('invalid optional effect object');
  const extra=[floating,...particles].filter(Boolean);if(new Set([...nodes.values(),...extra]).size!==nodes.size+extra.length)throw Error('effect object reused');
  let disposed=false;
  try{
    for(const o of [...nodes.values(),...extra]){originals.set(o,o.material);const m=o.material.clone();if(m===o.material)throw Error('material not cloned');copies.set(o,m);o.material=m;}
  }catch(e){for(const [o,m] of copies){o.material=originals.get(o);m.dispose?.();}throw e;}
  const anchor={x:93.94316101074219,y:28.604717254638672,z:93.07432556152344}; // GLB floor accessor midpoint; root-local, NOT canonical world placement
  const baseFloating=floating?{x:floating.position.x,y:floating.position.y,z:floating.position.z}:null;
  function off(){root.visible=false;for(const o of nodes.values()){o.visible=false;o.material.emissiveIntensity=0;}for(const o of extra){o.visible=false;o.material.opacity=0;}}
  function apply(frame){if(disposed)throw Error('disposed');const byId=new Map(frame.layers.map(v=>[v.id,v]));if(byId.size!==3||ids.some(i=>!byId.has(i))||frame.layers.length!==3)throw Error('invalid frame layers');
    for(const v of byId.values())if(!Number.isFinite(v.emission)||v.emission<0||v.emission>1||typeof v.visible!=='boolean')throw Error('invalid intensity');
    if(!frame.floating||!Number.isFinite(frame.floating.y)||!Number.isFinite(frame.floating.opacity)||frame.floating.opacity<0||frame.floating.opacity>1||!Array.isArray(frame.particles)||frame.particles.length>24)throw Error('invalid optional frame');
    const activeParticles=new Map();for(const v of frame.particles){if(!Number.isInteger(v.id)||v.id<0||v.id>=particles.length||activeParticles.has(v.id)||![v.x,v.y,v.z,v.opacity].every(Number.isFinite)||v.opacity<0||v.opacity>1)throw Error('invalid particle');activeParticles.set(v.id,v);}
    let visible=false;for(const [id,o] of nodes){const v=byId.get(id);o.visible=v.visible&&v.emission>0;o.material.emissiveIntensity=o.visible?originals.get(o).emissiveIntensity*v.emission:0;visible||=o.visible;}
    if(floating){const v=frame.floating;floating.visible=!!v.visible&&v.opacity>0;floating.material.opacity=floating.visible?v.opacity:0;floating.position.set(baseFloating.x,baseFloating.y+v.y,baseFloating.z);}
    particles.forEach((o,i)=>{const v=activeParticles.get(i);o.visible=!!v&&v.opacity>0;o.material.opacity=o.visible?v.opacity:0;if(v)o.position.set(anchor.x+v.x,anchor.y+v.y,anchor.z+v.z);});
    root.visible=visible; // optional effects must be parented under the same scene transform, caller owns visibility
  }
  off();return Object.freeze({apply,reset(){if(!disposed)off();},dispose(){if(disposed)return;off();for(const [o,m] of copies){o.material=originals.get(o);m.dispose?.();}disposed=true;},anchor:Object.freeze(anchor)});
}
