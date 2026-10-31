/* QA-only: evaluate pure conversation data, normalize presentation-independent behavior and expose explicit portrait metadata. */
const fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const FILES=['talk-data.js','talk-data-quests.js','talk-data-scenes.js','talk-data-capital.js','talk-data-rilde.js','talk-data-attack.js'];
const NAMES={'エイダン':'aidan','フィオナ':'fiona','ルー':'lou','エマ':'emma'};
const SPLIT=/　(?=[^\s「」　]{1,10}「)/,SPEAKER=/^([^\s「」　]{1,10})(「[\s\S]*)$/;
const parse=p=>typeof p==='object'?{speaker:p.speaker||'',text:p.text||''}:((m)=>m?{speaker:m[1],text:m[2]}:{speaker:'',text:String(p)})(SPEAKER.exec(String(p)));
function rawPages(c){return(typeof c==='string'?c.split(SPLIT):Array.isArray(c)?c:c.pages||[])}
function pages(c){const dc=c&&typeof c==='object'&&!Array.isArray(c)?c:null;let char=dc?.char;return rawPages(c).map((p,i)=>{let pg={...parse(p)};if(p&&typeof p==='object')for(const k of ['char','face','side'])if(p[k]!==undefined)pg[k]=p[k];const meta=dc?.portraits?.[i];if(meta)for(const k of ['char','face','side'])if(meta[k]!==undefined)pg[k]=meta[k];if(pg.char!==undefined)char=pg.char;else if(char!==undefined)pg.char=char;if(i===0&&pg.face===undefined&&dc?.face!==undefined&&pg.char!==undefined)pg.face=dc.face;if(pg.side===undefined&&dc?.side!==undefined&&pg.char)pg.side=dc.side;return pg})}
function normalize(c){const o=typeof c==='object'&&!Array.isArray(c)?{...c}:{};for(const k of ['char','face','side','portraits'])delete o[k];o.pages=rawPages(c).map(parse);if(o.choice)o.choice={...o.choice,options:o.choice.options.map(v=>({...v,...(v.reply?{reply:normalize(v.reply)}:{})}))};return o}
function stable(o){return JSON.stringify(o,(_,v)=>v&&typeof v==='object'&&!Array.isArray(v)?Object.fromEntries(Object.entries(v).sort(([a],[b])=>a.localeCompare(b))):v)}
function indexLogic(html){return html
 .replace(/function say\(t, portrait\)/,'function say(t)')
 .replace(/\n if\(portrait&&window\.TalkPortrait\)\{[^\n]+\}\n else window\.TalkPortrait\?\.close\('legacySay'\);/,'')
 .replace(/\n window\.TalkPortrait\?\.close\('legacySay'\);/,'')
 .replace(/say\(('フィオナ「[^'\n]+'),\{[^}\n]+\}\)/g,'say($1)')
 .replace(/\/\/ Presentation-only bridge:[^\n]*\nfunction storyPortraitPage\([\s\S]*?\n}\n/,'')
 .replace(/^const (?:hill|return|fort)PortraitPages=\[[^\n]+\];\n/gm,'')
 .replace(/^const aftermathPortraitPages=[^\n]+;/m,'const aftermathPortraitPages=\"presentation\";')
 .replace(/storyPortraitPage\('[^']+','[^']+',[\w.]+,[\w]+\);/g,'')
 .replace(/window\.TalkPortrait\?\.close\('story:[^']+'\);/g,'')
 .replace(/(<script src=\"[^\"?]+)\?v=[^\"]+/g,'$1');}
function snapshot(read=fs.readFileSync.bind(fs)){const context={window:{}};vm.createContext(context);for(const f of FILES)vm.runInContext(read('js/field/'+f,'utf8'),context);
 const tables=Object.values(context.window).filter(v=>Array.isArray(v?.tables)).flatMap(v=>v.tables),conversations=[];
 function add(c,key,npc){conversations.push({key,npc,pages:pages(c),portraits:c?.portraits||null});c?.choice?.options.forEach((v,i)=>{if(v.reply)add(v.reply,key+'/reply'+i,npc)})}
 for(const t of tables)for(const e of t.entries)e.lines.forEach((c,i)=>add(c,e.id+'/'+i,t.npc));
 const normalized=tables.map(t=>({...t,entries:t.entries.map(e=>({...e,lines:e.lines.map(normalize)}))}));
 const html=read('index.html','utf8'),arrays={},metadata={},cinematic=[];
 for(const n of ['hillLines','returnLines','louIntroLines','altarLines','aftermathLines','fortLines']){const m=html.match(new RegExp('const '+n+'=([\\s\\S]*?\\n\\]);?'));if(!m)throw Error(n);arrays[n]=vm.runInNewContext('('+m[1]+')');const mn=n==='aftermathLines'?'aftermathPortraitPages':n.replace('Lines','PortraitPages');const mm=html.match(new RegExp('const '+mn+'=([^;\\n]+);'));metadata[n]=mm?vm.runInNewContext('('+mm[1]+')'):[];arrays[n].forEach((text,i)=>cinematic.push({key:n,page:i,...parse(text),...(metadata[n][i]||{char:null})}))}
 arrays.escapeLines=[...context.window.TalkDataAttack.escapeLines];metadata.escapeLines=context.window.TalkDataAttack.escapePortraits||[];arrays.escapeLines.forEach((text,i)=>cinematic.push({key:'escapeLines',page:i,...parse(text),...(metadata.escapeLines[i]||{char:null})}));
 const training=[];for(const m of html.matchAll(/say\(('フィオナ「[^'\n]+')(?:,(\{[^\n]+?\}))?\)/g)){const text=vm.runInNewContext(m[1]);training.push({key:'trainingSay',page:training.length,...parse(text),...(m[2]?JSON.parse(m[2]):{char:null})})}
 const village=read('js/field/rilde-village.js','utf8'),forest=read('js/field/moss-forest-story.js','utf8');
 const stone=village.match(/say\(state\(\) === 'ruin' \? ('[^'\n]+') : ('[^'\n]+')/),rune=forest.match(/msg_a3_rune_stone:('[^'\n]+')/);
 const inspectText=[vm.runInNewContext(stone[2]),vm.runInNewContext(stone[1]),vm.runInNewContext(rune[1])];
 const inspection=inspectText.map((text,i)=>({key:'fieldInspection',page:i,...parse(text),...(i===0&&village.includes("state() === 'ruin' ? null : {char:'aidan',face:'normal',side:'left'}")?{char:'aidan',face:'normal',side:'left'}:{char:null})}));
 const behavior={tables:normalized,attackText:context.window.TalkDataAttack.text,attackFlags:context.window.TalkDataAttack.flags,arrays,inspection:inspectText,training:training.map(({speaker,text})=>({speaker,text}))};
 const index_logic_sha256=crypto.createHash('sha256').update(indexLogic(html)).digest('hex');
 return{index_logic_sha256,behavior_sha256:crypto.createHash('sha256').update(stable(behavior)).digest('hex'),behavior,conversations,cinematic,training,inspection,metadata};}
if(require.main===module){const s=snapshot();console.log(JSON.stringify(s))}else module.exports={snapshot,FILES,NAMES,parse,pages,stable,indexLogic};
