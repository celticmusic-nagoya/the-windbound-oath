/* Destination navigation uses the caller's live collision predicate. No map IDs,
 * bridge coordinates, saved state or actor logic belong to this module. */
(function () {
  'use strict';
  const defaults=Object.freeze({width:2160,height:1500,maxNodes:12000,grid:16});
  let bounds={width:defaults.width,height:defaults.height},maxNodes=defaults.maxNodes,baseGrid=defaults.grid;
  let current=null,path=[],index=0,blockedFrames=0,replans=0,steps=0,actorWaitFrames=0;
  let statistics={plans:0,expanded:0,milliseconds:0,outcome:'idle'};
  function clear(){current=null;path=[];index=0;blockedFrames=0;replans=0;steps=0;actorWaitFrames=0;}
  function segment(a,b,blocked) {
    const distance=Math.hypot(b.x-a.x,b.y-a.y),n=Math.max(1,Math.ceil(distance/2));
    for(let i=1;i<=n;i++)if(blocked(a.x+(b.x-a.x)*i/n,a.y+(b.y-a.y)*i/n))return false;
    return true;
  }
  function plan(start,goal,blocked,grid=baseGrid) {
    const began=performance.now();statistics.plans++;
    if(segment(start,goal,blocked)){statistics.expanded=0;statistics.milliseconds=performance.now()-began;return [goal];}
    const columns=Math.floor(bounds.width/grid)+1,rows=Math.floor(bounds.height/grid)+1;
    const cache=new Map(),nodes=new Map(),heap=[];
    const point=id=>({x:id%columns*grid,y:Math.floor(id/columns)*grid});
    const valid=id=>{if(!cache.has(id)){const p=point(id);cache.set(id,!blocked(p.x,p.y));}return cache.get(id);};
    function push(n){heap.push(n);let i=heap.length-1;while(i){const p=(i-1)>>1;if(heap[p].f<=n.f)break;heap[i]=heap[p];i=p;}heap[i]=n;}
    function pop(){const first=heap[0],last=heap.pop();if(heap.length){let i=0;while(i*2+1<heap.length){let c=i*2+1;if(c+1<heap.length&&heap[c+1].f<heap[c].f)c++;if(heap[c].f>=last.f)break;heap[i]=heap[c];i=c;}heap[i]=last;}return first;}
    const heuristic=p=>Math.hypot(p.x-goal.x,p.y-goal.y);
    const sx=Math.round(start.x/grid),sy=Math.round(start.y/grid);
    // Connect the exact actor position to nearby grid vertices without snapping.
    for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
      const x=sx+dx,y=sy+dy;if(x<0||x>=columns||y<0||y>=rows)continue;
      const id=y*columns+x,p=point(id);if(!valid(id)||!segment(start,p,blocked))continue;
      const g=Math.hypot(p.x-start.x,p.y-start.y),node={id,g,f:g+heuristic(p),parent:null};nodes.set(id,node);push(node);
    }
    let found=null,expanded=0;
    while(heap.length&&expanded<maxNodes) {
      const n=pop();if(nodes.get(n.id)!==n||n.closed)continue;n.closed=true;expanded++;
      const p=point(n.id),cx=n.id%columns,cy=Math.floor(n.id/columns);
      if(heuristic(p)<=grid*2&&segment(p,goal,blocked)){found=n;break;}
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++){
        if(!dx&&!dy)continue;const x=cx+dx,y=cy+dy;if(x<0||x>=columns||y<0||y>=rows)continue;
        const id=y*columns+x,other=nodes.get(id);if(other?.closed||!valid(id))continue;
        const q=point(id),g=n.g+Math.hypot(dx,dy)*grid;if(other&&other.g<=g)continue;
        if(!segment(p,q,blocked))continue;
        const next={id,g,f:g+heuristic(q),parent:n};nodes.set(id,next);push(next);
      }
    }
    statistics.expanded=expanded;statistics.milliseconds=performance.now()-began;
    // Most routes need only the coarser grid. Retry narrow passages at 8px
    // instead of paying that cost for every long-distance destination.
    if(!found)return grid>8?plan(start,goal,blocked,Math.max(8,grid/2)):null;
    const result=[goal];for(let n=found;n;n=n.parent)result.unshift(point(n.id));
    // Remove redundant vertices only when the swept foot collider permits it.
    const smooth=[];let from=start;
    for(let i=0;i<result.length;){let j=i;while(j+1<result.length&&segment(from,result[j+1],blocked))j++;
      smooth.push(result[j]);from=result[j];i=j+1;}
    return smooth;
  }
  function destination(x,y,blocked) {
    clear();
    const staticBlocked=blocked.staticBlocked||blocked;
    const p={x:Math.max(0,Math.min(bounds.width,x)),y:Math.max(0,Math.min(bounds.height,y))};
    if(!Number.isFinite(p.x)||!Number.isFinite(p.y)||staticBlocked(p.x,p.y)){statistics.outcome='blocked-destination';return null;}
    statistics.outcome='moving';return p;
  }
  function follow(x,y,target,blocked) {
    if(!target){clear();return {x,y,target:null};}
    // Optional Lind review policy: route around locked world geometry, then
    // respect live actors during the movement sweep. Other callers are unchanged.
    const staticBlocked=blocked.staticBlocked||blocked,dynamicBlocked=blocked.dynamicBlocked;
    // Detours keep 2px clearance from live actors, avoiding a corner waypoint
    // that grazes their feet. This does not inflate locked static geometry.
    const detourBlocked=(qx,qy)=>staticBlocked(qx,qy)||dynamicBlocked(qx-2,qy-2)||
      dynamicBlocked(qx+2,qy-2)||dynamicBlocked(qx-2,qy+2)||dynamicBlocked(qx+2,qy+2);
    const waitForActor=()=>{
      actorWaitFrames++;statistics.outcome='waiting-actor';
      // Reuse the existing bounded planner for an actor that remains ahead.
      // Failed live detours never invalidate the statically reachable destination.
      if(actorWaitFrames%120===30&&!dynamicBlocked(x,y)&&!dynamicBlocked(target.x,target.y)){
        const detour=plan({x,y},target,detourBlocked);
        if(detour){path=detour;index=0;actorWaitFrames=0;statistics.outcome='detouring-actor';}
      }
      return {x,y,target};
    };
    const finish=(outcome,unreachable=false)=>{clear();statistics.outcome=outcome;return {x,y,target:null,unreachable};};
    if(Math.hypot(target.x-x,target.y-y)<=FieldMovement.settings.arrivalRadius)return finish('arrived');
    if(staticBlocked(x,y)||staticBlocked(target.x,target.y))return finish('blocked',true);
    if(target!==current){
      clear();current=target;
      const occupied=dynamicBlocked?.(x,y)||dynamicBlocked?.(target.x,target.y);
      path=occupied?null:plan({x,y},target,blocked);
      if(!path)path=plan({x,y},target,staticBlocked);
      if(!path)return finish('no-route',true);
    }
    // A moving animal can overlap the stationary player's feet. Do not push the
    // player or abandon their destination; resume on the existing RAF when clear.
    if(dynamicBlocked?.(x,y))return waitForActor();
    while(index<path.length-1&&Math.hypot(path[index].x-x,path[index].y-y)<=1)index++;
    const next=path[index],distance=Math.hypot(next.x-x,next.y-y);
    const frameScale=FieldMovement.frameScale||1,v=Math.min(distance,FieldMovement.settings.pointerStep*frameScale);
    const dx=distance?(next.x-x)/distance*v:0,dy=distance?(next.y-y)/distance*v:0;
    const fromX=x,fromY=y,moved=FieldMovement.advance(x,y,dx,dy,blocked,{assist:false,bounds});
    const progress=Math.hypot(moved.x-x,moved.y-y);x=moved.x;y=moved.y;
    // Preserve existing axis sliding around corners before deciding to wait.
    if(progress<.1&&dynamicBlocked?.(x+dx,y+dy))return waitForActor();
    actorWaitFrames=0;statistics.outcome='moving';
    steps+=frameScale;if(steps>3600){x=fromX;y=fromY;return finish('timeout',true);}
    blockedFrames=progress<.1?blockedFrames+frameScale:0;
    if(blockedFrames>=12) {
      if(replans>=3)return finish('blocked',true);
      replans++;blockedFrames=0;path=plan({x,y},target,staticBlocked);index=0;
      if(!path)return finish('no-route',true);
    }
    if(Math.hypot(target.x-x,target.y-y)<=FieldMovement.settings.arrivalRadius)return finish('arrived');
    return {x,y,target};
  }
  // Per-map configuration. configure() with no argument restores the Lind defaults.
  // Large maps raise the grid (coarser A*) and maxNodes; pointer-follow movement is
  // bounded by the same width/height through FieldNavigation.bounds.
  function configure(options={}) {
    bounds={width:options.width??defaults.width,height:options.height??defaults.height};
    maxNodes=options.maxNodes??defaults.maxNodes;baseGrid=options.grid??defaults.grid;clear();
  }
  window.FieldNavigation=Object.freeze({destination,follow,cancel:clear,configure,
    get bounds(){return {...bounds};},
    get status(){return {...statistics,blockedFrames,actorWaitFrames,replans,waypoints:path.length,active:Boolean(current)};}});
})();
