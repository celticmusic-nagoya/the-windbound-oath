/* STEP 8: DEV-only landmark actor. No quest, story or save mutation.
 * All image states share the normal canvas transform and physical foot collider.
 * Particles are decoration; their animations never drive state/interaction logic. */
(function () {
  'use strict';
  if (!window.WINDBOUND_DEV || !window.LindFieldAssets) return;
  const base='img/field/lind/landmarks/';
  const paths=Object.freeze({NORMAL:base+'lind_wind_stone.png',
    GLOW:base+'lind_wind_stone_glow.png',OFF:base+'lind_wind_stone_off.png'});
  const b=window.LindFieldContentBounds.lind_wind_stone;
  const scale=95/b[4];
  const object={id:'lind_wind_stone',label:'風の石',actor:'windStone',
    path:paths.NORMAL,x:695,y:490,width:95,height:b[5]*scale,motion:'static',
    collision:[14,100,70,23],
    draw:{x:695-b[2]*scale,y:490-b[3]*scale,width:b[0]*scale,height:b[1]*scale}};
  window.LindFieldAssets.objects.push(object);
  let requested='NORMAL',state='NORMAL',select=null,root=null,notice=null,lastInteraction=null;
  const images={};
  function paint() {
    state=window.LindFieldEnvironment.wind ? requested : 'OFF';
    if(root)root.dataset.state=state;
    Object.entries(images).forEach(([key,image])=>{image.hidden=key!==state;});
    if(select)select.value=state;
  }
  function setState(value) {
    if(!Object.hasOwn(paths,value))return false;
    if(value!=='OFF')requested=value;
    window.LindFieldEnvironment.setWind(value!=='OFF');
    paint();return true;
  }
  function near() {return Math.hypot(px+17-object.x-object.width/2,
    py+42-object.y-object.height)<=105;}
  function interact() {
    if(!window.LindFieldReview?.active)return false;
    notice.hidden=false;
    if(!near()){notice.textContent='風の石へ近づいてください。';return false;}
    target=null;
    lastInteraction={id:object.id,type:'wind_stone',state,reviewOnly:true};
    notice.textContent=state==='OFF' ? 'DEV · 風の石だ。今は光も風の気配もない。' :
      'DEV · 風の石だ。淡い風の気配を感じる。';
    window.dispatchEvent(new CustomEvent('lind-field-interaction',{detail:{...lastInteraction}}));
    return true;
  }
  function mount(parent,controls) {
    root=document.createElement('div');root.className='lind-wind-stone';
    root.dataset.assetId=object.id;
    Object.assign(root.style,{left:object.draw.x+'px',top:object.draw.y+'px',
      width:object.draw.width+'px',height:object.draw.height+'px',
      zIndex:String(Math.round(object.y+object.height))});
    Object.entries(paths).forEach(([key,path])=>{
      const image=document.createElement('img');image.src=path;image.alt='風の石 · '+key;
      image.dataset.stoneState=key;images[key]=image;root.append(image);
    });
    // Three lightweight decorative leaves; external effects have no collision.
    for(let i=0;i<3;i++){
      const leaf=document.createElement('i');leaf.className='lind-stone-leaf';
      leaf.setAttribute('aria-hidden','true');leaf.style.setProperty('--leaf',i);
      root.append(leaf);
    }
    parent.append(root);
    const hit=document.createElement('button');hit.type='button';
    hit.className='lind-stone-interaction';hit.dataset.interactionId=object.id;
    hit.setAttribute('aria-label','風の石を調べる');
    Object.assign(hit.style,{left:object.x-4+'px',top:object.y+45+'px',
      width:object.width+8+'px',height:object.height-35+'px',
      zIndex:String(Math.round(object.y+object.height+1))});
    hit.addEventListener('pointerdown',e=>e.stopPropagation());
    hit.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();interact();});
    parent.append(hit);
    const row=document.createElement('label');row.className='lind-stone-controls';
    row.append(document.createTextNode('風の石 · DEV状態 '));
    select=document.createElement('select');select.id='lindWindStoneState';
    select.setAttribute('aria-label','風の石の状態');
    for(const value of Object.keys(paths)){
      const option=document.createElement('option');option.value=value;option.textContent=value;
      select.append(option);
    }
    select.onchange=()=>setState(select.value);row.append(select);controls.append(row);
    notice=document.createElement('div');notice.id='lindStoneNotice';notice.hidden=true;
    notice.setAttribute('role','status');controls.append(notice);paint();
  }
  function clear() {lastInteraction=null;if(notice)notice.hidden=true;}
  window.addEventListener('lind-wind-change',paint);
  window.LindFieldWindStone=Object.freeze({object,paths,mount,setState,interact,clear,
    nearby:()=>near()&&interact(),get state(){return state;},get lastInteraction(){return lastInteraction;}});
})();
