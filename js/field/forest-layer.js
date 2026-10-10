/* Chunk-composited decoration layer. Ground terrain + decorative scatter (render:'layer') are baked
 * into one <canvas> per chunk instead of one DOM node per item. Only chunks near the viewport exist.
 * Placeholder drawing until real assets exist (ASSET GENERATION REQUIRED): dot/blade/petal shapes. */
(function () {
  'use strict';
  const COLOR=[[/^veg_grass/,'#4f8a3a',3],[/^veg_flower_yellow/,'#f2d34a',3],[/^veg_flower_white/,'#f4f1e6',3],[/^veg_flower_blue/,'#6aa6e8',3],
    [/^veg_fern/,'#2f6e3a',6],[/^veg_reeds/,'#8a9a4a',5],[/^veg_mush/,'#c9a27a',3],[/^gnd_leaflitter/,'#a8732f',4]];
  function style(asset){for(const [re,c,r] of COLOR)if(re.test(asset))return {c,r};return {c:'#6b8f4a',r:3};}
  function create(options) {
    const chunk=options.chunk||512,margin=options.margin??1,map=options.map,parent=options.parent;
    const buckets=new Map(),live=new Map();let lastKey='',built=0;
    const key=(i,j)=>i+','+j;
    for(const e of options.items){const k=key(Math.floor(e.x/chunk),Math.floor(e.y/chunk));let l=buckets.get(k);if(!l)buckets.set(k,l=[]);l.push(e);}
    function ground(ctx,ox,oy){
      const t=map.terrain,G=options.ground;ctx.fillStyle=t.baseColor||'#5d9a45';ctx.fillRect(0,0,chunk+1,chunk+1);
      ctx.save();ctx.translate(-ox,-oy);
      if(G&&G.grass){   // textured ground, world-aligned so chunks tile seamlessly; darkened toward the map's mood colour
        const pat=ctx.createPattern(G.grass,'repeat');pat.setTransform(new DOMMatrix().scale(G.tile/G.grass.width));
        ctx.fillStyle=pat;ctx.fillRect(ox,oy,chunk+1,chunk+1);
        ctx.globalCompositeOperation='multiply';ctx.fillStyle=t.baseColor||'#5d9a45';ctx.globalAlpha=.7;ctx.fillRect(ox,oy,chunk+1,chunk+1);
        ctx.globalAlpha=1;ctx.globalCompositeOperation='source-over';}
      for(const p of t.patches||[]){ctx.beginPath();p.polygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();
        ctx.fillStyle=p.tint||'#fff';ctx.globalAlpha=.35;ctx.fill();ctx.globalAlpha=1;}
      for(const w of t.waters||[]){ctx.fillStyle=ctx.strokeStyle='#5b9fd6';ctx.lineCap=ctx.lineJoin='round';
        if(w.points){ctx.lineWidth=w.width||60;ctx.beginPath();w.points.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.stroke();}
        else if(w.polygon&&w.kind!=='fall'){ctx.beginPath();w.polygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.fill();
          if(w.core){ctx.fillStyle='#2f6f9f';ctx.beginPath();w.core.polygon.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.closePath();ctx.fill();}}}
      for(const c of t.cliffs||[])for(const r of c.segments||[]){
        ctx.fillStyle=c.type==='face_visible'?'#5b4a3c':'#6f6a55';ctx.fillRect(r[0],r[1],r[2],r[3]);
        ctx.fillStyle=c.type==='face_visible'?'#8a7660':'#8e8a6c';ctx.fillRect(r[0],r[1],r[2],c.type==='face_visible'?18:10);}
      for(const w of t.waters||[])if(w.kind==='fall'){ctx.fillStyle='#cfe9f5';ctx.globalAlpha=.8;const q=w.polygon;ctx.fillRect(q[0][0],q[0][1],q[1][0]-q[0][0],q[2][1]-q[0][1]);ctx.globalAlpha=1;}
      const dirt=G&&G.dirt?(()=>{const d=ctx.createPattern(G.dirt,'repeat');d.setTransform(new DOMMatrix().scale(G.tile/G.dirt.width));return d;})():null;
      ctx.lineCap=ctx.lineJoin='round';
      const stroke=p=>{ctx.beginPath();p.points.forEach((q,i)=>i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]));ctx.stroke();};
      if(dirt){ctx.strokeStyle='#4b3a22';ctx.globalAlpha=.45;for(const p of t.paths||[]){ctx.lineWidth=p.width+10;stroke(p);}ctx.globalAlpha=1;}   // halos first so crossings stay clean
      for(const p of t.paths||[]){ctx.strokeStyle=dirt||'#b08a5a';ctx.lineWidth=p.width;stroke(p);}
      ctx.restore();
    }
    function build(i,j){
      const canvas=document.createElement('canvas');canvas.width=canvas.height=chunk+1;   // +1px overlap hides subpixel seamscanvas.className='forest-chunk';
      Object.assign(canvas.style,{position:'absolute',left:i*chunk+'px',top:j*chunk+'px',width:chunk+1+'px',height:chunk+1+'px',pointerEvents:'none',zIndex:'0'});
      const ctx=canvas.getContext('2d'),ox=i*chunk,oy=j*chunk;ground(ctx,ox,oy);
      // Items overhang chunk borders by a few px: draw neighbours' items too (cheap, small radius).
      for(let a=i-1;a<=i+1;a++)for(let b=j-1;b<=j+1;b++)for(const e of buckets.get(key(a,b))||[]){
        const sp=options.sprite&&options.sprite(e.asset);
        if(sp){ctx.drawImage(sp.im,e.x-ox-sp.w/2,e.y-oy-sp.h,sp.w,sp.h);continue;}
        const s=style(e.asset);ctx.fillStyle=s.c;ctx.beginPath();ctx.ellipse(e.x-ox,e.y-oy,s.r,s.r*.7,0,0,6.2832);ctx.fill();}
      built++;return canvas;
    }
    function update(view){
      const i0=Math.max(0,Math.floor(view.x/chunk)-margin),i1=Math.floor((view.x+view.width)/chunk)+margin;
      const j0=Math.max(0,Math.floor(view.y/chunk)-margin),j1=Math.floor((view.y+view.height)/chunk)+margin;
      const k=i0+':'+i1+':'+j0+':'+j1;if(k===lastKey)return;lastKey=k;
      const wanted=new Set();
      for(let i=i0;i<=i1;i++)for(let j=j0;j<=j1;j++){
        if(i*chunk>=map.world.width||j*chunk>=map.world.height)continue;
        const id=key(i,j);wanted.add(id);if(!live.has(id)){const c=build(i,j);parent.appendChild(c);live.set(id,c);}}
      for(const [id,c] of live)if(!wanted.has(id)){c.remove();live.delete(id);}
    }
    function destroy(){for(const c of live.values())c.remove();live.clear();buckets.clear();lastKey='';}
    return Object.freeze({update,destroy,get stats(){return {canvases:live.size,built,items:options.items.length};}});
  }
  window.ForestLayer=Object.freeze({create});
})();
