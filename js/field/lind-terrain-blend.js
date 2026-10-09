/* Static cosmetic terrain for the DEV village review. Existing PNG textures;
 * one transparent canvas, no frame loop, input, collision or save mutations. */
(function () {
  'use strict';
  if (!window.WINDBOUND_DEV || !window.LindTerrainLayout) return;
  const layout=LindTerrainLayout;
  let canvas,assets,model,promise,painted=false,redraws=0;
  const connected=[],shortTrails=[];
  function hash(n) { const v=Math.sin(n*127.1+311.7)*43758.5453;return v-Math.floor(v); }
  function wave(distance,seed) {
    return Math.sin(distance/23+seed)*3.3+Math.sin(distance/9.7+seed*.37)*1.4;
  }
  function samples(points) {
    const result=[];let distance=0;
    for(let i=1;i<points.length;i++) {
      const a=points[i-1],b=points[i],length=Math.hypot(b[0]-a[0],b[1]-a[1]);
      const count=Math.max(1,Math.ceil(length/8));
      for(let n=0;n<count;n++)result.push({x:a[0]+(b[0]-a[0])*n/count,
        y:a[1]+(b[1]-a[1])*n/count,d:distance+length*n/count});
      distance+=length;
    }
    const end=points.at(-1);result.push({x:end[0],y:end[1],d:distance});
    result.forEach((p,i)=>{const a=result[Math.max(0,i-1)],b=result[Math.min(result.length-1,i+1)],
      length=Math.hypot(b.x-a.x,b.y-a.y)||1;p.nx=-(b.y-a.y)/length;p.ny=(b.x-a.x)/length;});
    return result;
  }
  function smooth(points) {
    const p=new Path2D(),last=points.at(-1),first=points[0];
    p.moveTo((last.x+first.x)/2,(last.y+first.y)/2);
    points.forEach((a,i)=>{const b=points[(i+1)%points.length];p.quadraticCurveTo(a.x,a.y,(a.x+b.x)/2,(a.y+b.y)/2);});
    p.closePath();return p;
  }
  function ribbon(route,extra=0) {
    const left=[],right=[];
    for(const p of route.samples) {
      const amount=Math.min(1,route.width/50),half=route.width/2+extra;
      const a=half+wave(p.d,route.seed)*amount,b=half+wave(p.d,route.seed+17)*amount;
      left.push({x:p.x+p.nx*a,y:p.y+p.ny*a});
      right.push({x:p.x-p.nx*b,y:p.y-p.ny*b});
    }
    return smooth([...left,...right.reverse()]);
  }
  // Rounded outer patches and concave route joins reuse the same texture layers.
  function patch(shape,extra=0) {
    const points=[];
    for(let i=0;i<80;i++) {
      const angle=i*Math.PI/40,c=Math.cos(angle),s=Math.sin(angle),
        irregular=wave(i*7,shape.seed)*.65;
      points.push({x:shape.x+Math.sign(c)*Math.pow(Math.abs(c),.45)*(shape.width/2+extra+irregular),
        y:shape.y+Math.sign(s)*Math.pow(Math.abs(s),.45)*(shape.height/2+extra+irregular)});
    }
    return smooth(points);
  }
  function texture(ctx,image,size) {
    const tile=document.createElement('canvas');tile.width=tile.height=size;
    const c=tile.getContext('2d');c.imageSmoothingEnabled=true;c.imageSmoothingQuality='high';c.drawImage(image,0,0,size,size);
    return ctx.createPattern(tile,'repeat');
  }
  function distanceTo(point,route) {
    let distance=Infinity;
    for(let i=1;i<route.points.length;i++) {
      const a=route.points[i-1],b=route.points[i],dx=b[0]-a[0],dy=b[1]-a[1],
        t=Math.max(0,Math.min(1,((point.x-a[0])*dx+(point.y-a[1])*dy)/(dx*dx+dy*dy)));
      distance=Math.min(distance,Math.hypot(point.x-a[0]-t*dx,point.y-a[1]-t*dy));
    }
    return distance;
  }
  function clearTrail(points) {
    return samples(points).every(p=>!model.blocked(p.x-17,p.y-42)&&!LindFieldRiver.blocked(p.x-17,p.y-42));
  }
  function trails() {
    return layout.trails.map(config=>{
      const object=assets.objects.find(o=>o.id===config.id),door=object?.doorApproach;
      if(!door)return null;
      let points=[[door.x,door.y],...config.points];
      if(clearTrail(points))connected.push(config.id);
      else {
        // Never paint a new apparent route through a locked wall/prop. Retain
        // only the clear doorstep section; navigation is not used or modified.
        points=[[door.x,door.y]];
        for(let y=8;y<=32;y+=8) {
          const candidate=[door.x,door.y+y];
          if(!clearTrail([points.at(-1),candidate]))break;
          points.push(candidate);
        }
        shortTrails.push(config.id);
      }
      return points.length>1?{...config,points}:null;
    }).filter(Boolean);
  }
  function protect(point,radius=0) {
    const bridge=LindFieldRiver.crossings.find(c=>c.id==='bridge');
    if(point.x>bridge.x-30-radius&&point.x<bridge.x+bridge.width+30+radius&&
      point.y>bridge.y-12-radius&&point.y<bridge.y+bridge.height+12+radius)return true;
    return assets.objects.some(o=>o.doorApproachLane&&point.x>o.doorApproachLane.x-radius&&
      point.x<o.doorApproachLane.x+o.doorApproachLane.width+radius&&
      point.y>o.doorApproachLane.y-radius&&point.y<o.doorApproachLane.y+o.doorApproachLane.height+radius);
  }
  function paint(images) {
    const ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;
    const dirt=texture(ctx,images.dirt,128),grass=texture(ctx,images.grass,256),stone=texture(ctx,images.stone,64);
    const routes=[...layout.routes,...trails()].map(r=>({...r,samples:samples(r.points)}));
    const fill=(path,pattern,alpha=1)=>{ctx.globalAlpha=alpha;ctx.fillStyle=pattern;ctx.fill(path);ctx.globalAlpha=1;};
    // All faint skirts first, all solid cores afterward: intersecting roads
    // have no double-opacity seam and preserve readable open centers.
    for(const [extra,alpha]of[[9,.18],[5,.45]]) {
      routes.forEach(r=>fill(ribbon(r,extra),dirt,alpha));
      fill(patch(layout.plaza,extra+16),dirt,alpha);
    }
    routes.forEach(r=>fill(ribbon(r),dirt));
    fill(patch(layout.plaza,14),dirt);fill(patch(layout.plaza,5),stone,.45);fill(patch(layout.plaza),stone);
    layout.patches.forEach(p=>{fill(patch(p,7),dirt,.2);fill(patch(p),dirt,.55);});
    // Small grass incursions occur at edges, not road centers or door/bridge lanes.
    for(const route of routes)for(let i=2;i<route.samples.length-2;i+=5)for(const side of[-1,1]) {
      const p=route.samples[i],seed=route.seed+i*13+side*29,radius=3+hash(seed)*4,
        edge=route.width/2+wave(p.d,route.seed+(side<0?17:0))*.8,
        q={x:p.x+p.nx*side*edge,y:p.y+p.ny*side*edge};
      const plaza=layout.plaza;
      if(protect(q,radius)||routes.some(r=>r!==route&&distanceTo(q,r)<r.width*.52+radius)||
        (Math.abs(q.x-plaza.x)<plaza.width/2+15&&Math.abs(q.y-plaza.y)<plaza.height/2+15))continue;
      const tuft=new Path2D();tuft.ellipse(q.x,q.y,radius,radius*.7,seed,0,Math.PI*2);fill(tuft,grass,.92);
      if(hash(seed+3)>.65) {
        const crumb=new Path2D(),offset=edge+8+hash(seed+5)*3;
        crumb.ellipse(p.x+p.nx*side*offset,p.y+p.ny*side*offset,2+hash(seed+7)*2,2,0,0,Math.PI*2);
        fill(crumb,dirt,.6);
      }
    }
    // Existing west bank stays in place; nibble only its grass-facing seam.
    for(let y=12;y<layout.height;y+=15) {
      const x=1400+wave(y,181),q={x,y};
      if(protect(q,12)||y>1300&&y<1430)continue;
      const edge=new Path2D();edge.ellipse(x,y,7+hash(y)*4,12,0,0,Math.PI*2);fill(edge,grass,.9);
    }
    // Mirror the dry grass/stone portion only, never a static water strip.
    const bank=document.createElement('canvas');bank.width=54;bank.height=128;
    const bc=bank.getContext('2d');bc.imageSmoothingEnabled=false;bc.translate(54,0);bc.scale(-1,1);
    bc.drawImage(images.riverbank,0,0,images.riverbank.width*54/128,images.riverbank.height,0,0,54,128);
    const bankPattern=ctx.createPattern(bank,'repeat');bankPattern.setTransform(new DOMMatrix().translate(1630,0));
    const bankRoute={width:54,seed:191,samples:samples([[1657,0],[1657,1550]])};
    ctx.save();const bankClip=new Path2D();bankClip.rect(1630,0,54,layout.height);
    bankClip.rect(1630,530,54,150);ctx.clip(bankClip,'evenodd');fill(ribbon(bankRoute),bankPattern,.9);ctx.restore();
    for(let y=12;y<layout.height;y+=15) {
      const q={x:1682+wave(y,211),y};if(protect(q,12))continue;
      const edge=new Path2D();edge.ellipse(q.x,q.y,8+hash(y+17)*4,12,0,0,Math.PI*2);fill(edge,grass,.95);
    }
    painted=true;redraws++;canvas.hidden=false;
    canvas.parentElement.querySelectorAll('[data-terrain-rectangle]').forEach(e=>e.hidden=true);
  }
  function ready() {
    if(!canvas)return Promise.reject(new Error('Terrain review not mounted'));
    if(!promise)promise=Promise.all(['grass','dirt','stone','riverbank'].map(name=>new Promise((resolve,reject)=>{
      const image=new Image();image.onload=()=>resolve([name,image]);image.onerror=()=>reject(new Error('Terrain image failed: '+assets.terrain[name]));image.src=assets.terrain[name];
    }))).then(entries=>paint(Object.fromEntries(entries)));
    return promise;
  }
  function mount(parent,source,collisionModel) {
    assets=source;model=collisionModel;
    canvas=document.createElement('canvas');canvas.width=layout.width;canvas.height=layout.height;
    canvas.className='lind-terrain-transition';canvas.hidden=true;canvas.setAttribute('aria-hidden','true');parent.append(canvas);
  }
  window.LindFieldTerrain=Object.freeze({mount,ready,get status(){return {
    ready:painted,redraws,canvases:canvas?1:0,width:layout.width,height:layout.height,
    connectedTrails:[...connected],shortDoorstepTrails:[...shortTrails]};}});
})();
