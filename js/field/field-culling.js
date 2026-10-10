/* Chunked DOM culling for large field maps (Moss Forest). Entries are registered once with
 * a world-space box; only entries whose chunk is within `margin` chunks of the viewport
 * are kept as live DOM nodes. Nodes are created lazily via entry.create() and removed on
 * exit, so the live count stays near maxLiveNodes regardless of world size.
 * Map-independent: knows nothing about Lind, Moss Forest, collision or story. */
(function () {
  'use strict';
  function create(options) {
    const chunk=options.chunk||512,margin=options.margin??1,maxLive=options.maxLiveNodes||600;
    const parent=options.parent,chunks=new Map(),live=new Map();
    let lastKey='',peak=0,overBudget=0;
    const k=(i,j)=>i+','+j;
    function add(entry) {
      // entry: {id,x,y,w,h,create:()=>HTMLElement}
      const i0=Math.floor(entry.x/chunk),i1=Math.floor((entry.x+(entry.w||0))/chunk);
      const j0=Math.floor(entry.y/chunk),j1=Math.floor((entry.y+(entry.h||0))/chunk);
      for(let i=i0;i<=i1;i++)for(let j=j0;j<=j1;j++){const key=k(i,j);let l=chunks.get(key);if(!l){l=[];chunks.set(key,l);}l.push(entry);}
    }
    // view: world-space viewport {x,y,width,height}. Cheap when the visible chunk window is unchanged.
    function update(view) {
      const i0=Math.floor(view.x/chunk)-margin,i1=Math.floor((view.x+view.width)/chunk)+margin;
      const j0=Math.floor(view.y/chunk)-margin,j1=Math.floor((view.y+view.height)/chunk)+margin;
      const key=i0+':'+i1+':'+j0+':'+j1;if(key===lastKey)return false;lastKey=key;
      const wanted=new Map();
      for(let i=i0;i<=i1;i++)for(let j=j0;j<=j1;j++)for(const e of chunks.get(k(i,j))||[])wanted.set(e.id,e);
      for(const [id,node] of live)if(!wanted.has(id)){node.remove();live.delete(id);}
      for(const [id,e] of wanted)if(!live.has(id)){const node=e.create();parent.appendChild(node);live.set(id,node);}
      peak=Math.max(peak,live.size);if(live.size>maxLive)overBudget++;
      return true;
    }
    function clear(){for(const node of live.values())node.remove();live.clear();chunks.clear();lastKey='';}
    return Object.freeze({add,update,clear,
      get stats(){return {live:live.size,peak,overBudget,chunks:chunks.size,maxLive};}});
  }
  window.FieldCulling=Object.freeze({create});
})();
