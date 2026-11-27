// Prototype is a loaded mesh from the separate V85 GLB, not part of altar base.
// Keep all new objects invisible before attachment. bindAltarLayers must run before
// adding them to the rune root, which accepts exactly the three rune meshes.
import {bindAltarLayers} from './altar_adapter.mjs';
export function createMotePool(root, prototype, {count=24, coreScale=2.5}={}) {
  if (!root || typeof root.add!=='function' || typeof root.remove!=='function') throw TypeError('root');
  if (!prototype?.isMesh || typeof prototype.clone!=='function' || !prototype.material?.transparent) throw TypeError('transparent mesh prototype');
  if (!Number.isInteger(count)||count<0||count>24||!Number.isFinite(coreScale)||coreScale<=0||coreScale>4) throw RangeError('budget');
  const make=(name)=>{const o=prototype.clone(false);o.name=name;o.visible=false;return o};
  const floating=make('V85_floating_core');floating.scale.multiplyScalar(coreScale);
  const particles=Array.from({length:count},(_,i)=>make(`V85_mote_${i}`));
  const all=[floating,...particles];
  // Anchor is measured floor center of the actual V82 GLB, in root-local glTF coordinates.
  floating.position.set(93.94316101074219,28.604717254638672+.12,93.07432556152344);
  const binding=bindAltarLayers(root,{floating,particles});
  try {for(const o of all){o.material.transparent=true;o.material.depthWrite=false;root.add(o)}}
  catch(e){for(const o of all)root.remove(o);binding.dispose();throw e;}
  let disposed=false;
  return Object.freeze({apply(frame){if(disposed)throw Error('disposed');binding.apply(frame)},reset(){if(!disposed)binding.reset()},dispose(){if(disposed)return;binding.dispose();for(const o of all)root.remove(o);disposed=true},particleCount:count});
}
