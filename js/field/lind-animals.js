/* Independent field livestock actors. Staged in DEV review until STEP 12.
 * Image state and slow pen movement are unrelated to BattleActorState. */
(function () {
  'use strict';
  const definitions = [
    {id:'cow', label:'牛', width:56, displayScale:1.30, speed:5, rest:6, pen:{x:960,y:987,width:128,height:67}},
    {id:'pig', label:'豚', width:43, speed:7, rest:4, pen:{x:1120,y:985,width:128,height:67}},
    {id:'chicken', label:'鶏', width:24, speed:9, rest:3, pen:{x:1280,y:1000,width:120,height:52}}
  ];
  class FieldAnimal {
    constructor(definition, parent) {
      Object.assign(this, definition);
      if(this.displayScale) {
        const b=window.LindFieldContentBounds[this.id+'_idle'];
        const baseHeight=this.width*b[5]/b[4];
        this.groundAnchor=definition.pen.y+baseHeight;
        const growX=this.width*(this.displayScale-1)/2;
        const maxHeight=Math.max(...['idle','walk'].map(state=>{
          const frame=window.LindFieldContentBounds[this.id+'_'+state];
          return this.width*this.displayScale*frame[5]/frame[4];
        }));
        this.width*=this.displayScale;
        this.pen={...this.pen,x:this.pen.x-growX,width:this.pen.width+growX*2,
          y:this.groundAnchor-maxHeight,height:this.pen.y+this.pen.height-(this.groundAnchor-maxHeight)};
      }
      this.paths = Object.fromEntries(['idle','walk'].map(state => [state,
        'img/field/lind/animals/'+this.id+'_'+state+'.png']));
      this.x = this.pen.x; this.y = this.pen.y;
      this.state = 'IDLE'; this.elapsed = 0; this.direction = 1;
      this.element = document.createElement('div');
      this.element.className = 'lind-animal'; this.element.dataset.animal = this.id;
      this.frames = Object.fromEntries(['idle','walk'].map(state => {
        const image = document.createElement('img'); image.alt = this.label;
        image.src = this.paths[state]; this.element.append(image);
        return [state,image];
      }));
      parent.append(this.element);
      this.render();
    }
    update(seconds) {
      this.elapsed += seconds;
      if (this.state === 'IDLE') {
        if (this.elapsed >= this.rest) { this.state = 'WALK'; this.elapsed = 0; }
      } else {
        this.x += this.direction*this.speed*seconds;
        const end = this.pen.x+this.pen.width-this.width;
        if (this.x >= end || this.x <= this.pen.x) {
          this.x = Math.max(this.pen.x, Math.min(end, this.x));
          this.direction *= -1; this.state = 'IDLE'; this.elapsed = 0;
        }
      }
      this.render();
    }
    render() {
      const frame = this.state === 'WALK' && Math.floor(this.elapsed*4)%2 ? 'walk' : 'idle';
      const b = window.LindFieldContentBounds[this.id+'_'+frame];
      if (!b) return;
      const scale = this.width/b[4];
      this.height = b[5]*scale;
      if(this.groundAnchor!==undefined)this.y=this.groundAnchor-this.height;
      Object.assign(this.element.style, {left:this.x+'px',top:this.y+'px',width:this.width+'px',
        height:this.height+'px',zIndex:String(Math.round(this.y+this.height))});
      Object.entries(this.frames).forEach(([state,image]) => { image.hidden = state !== frame; });
      Object.assign(this.frames[frame].style, {left:-b[2]*scale+'px',top:-b[3]*scale+'px',
        width:b[0]*scale+'px',height:b[1]*scale+'px'});
      this.element.style.transform = this.direction > 0 ? 'scaleX(-1)' : 'scaleX(1)';
      this.element.dataset.state = this.state;
    }
    get foot() { return {x:this.x+this.width*.2,y:this.y+this.height*.72,
      width:this.width*.6,height:this.height*.22}; }
  }
  let actors = [], active = false, frame = null, previous = null;
  function mount(parent) {
    actors = definitions.map(definition => new FieldAnimal(definition, parent));
  }
  function start() {
    if (active) return;
    active = true; previous = null;
    const tick = now => {
      if (!active) return;
      if (previous !== null) actors.forEach(actor => actor.update(Math.min((now-previous)/1000,.1)));
      previous = now; frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
  }
  function stop() { active = false; previous = null; cancelAnimationFrame(frame); }
  function blocked(x, y) {
    return active && actors.some(actor => {
      const c = actor.foot;
      return x+28>c.x && x+6<c.x+c.width && y+42>c.y && y+32<c.y+c.height;
    });
  }
  window.LindFieldAnimals = Object.freeze({mount,start,stop,blocked,
    get actors(){return actors;}, get active(){return active;}});
})();
