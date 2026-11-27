const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync('js/runtime-environment.js','utf8');
const cases=[
 ['https://celticmusic-nagoya.github.io/the-windbound-oath/',false],
 ['https://celticmusic-nagoya.github.io/the-windbound-oath/index.html?dev=1&motiontest=1&title=0&legacyVillage=1&height25d=1',false],
 ['https://celticmusic-nagoya.github.io/the-windbound-oath/dev-fresh-20261108.html',false],
 ['https://raw.githack.com/celticmusic-nagoya/the-windbound-oath/main/index.html',true],
 ['https://raw.githack.com/celticmusic-nagoya/the-windbound-oath/fix/example/index.html',true],
 ['https://raw.githack.com/another/the-windbound-oath/main/index.html',false],
 ['https://raw.githack.com/celticmusic-nagoya/the-windbound-oath-other/main/index.html',false],
 ['https://raw.githack.com.example.org/celticmusic-nagoya/the-windbound-oath/main/index.html',false],
 ['http://raw.githack.com/celticmusic-nagoya/the-windbound-oath/main/index.html',false],
 ['http://127.0.0.1:8765/index.html?title=0',true],
 ['http://localhost:8080/index.html',true],
 ['https://example.org/index.html?dev=1',false],
 ['file:///tmp/index.html',false]
];
for(const [url,expected] of cases){
 const window={location:new URL(url)};
 let cls;
 const document={documentElement:{classList:{toggle:(name,value)=>{assert.equal(name,'windbound-dev');cls=value;}}}};
 vm.runInNewContext(source,{window,document});
 assert.equal(window.WINDBOUND_DEV,expected,url);
 assert.equal(cls,expected,url);
 assert.equal(Object.getOwnPropertyDescriptor(window,'WINDBOUND_DEV').writable,false);
}
for(const path of ['index.html','dev-fresh-20261108.html']){
 const html=fs.readFileSync(path,'utf8');
 assert(html.indexOf('js/runtime-environment.js')<html.indexOf('js/field/field-movement.js'));
 assert(html.includes('html:not(.windbound-dev) .dev-only-command{display:none!important}'));
 assert(html.includes('if(window.WINDBOUND_DEV){\n// Reconcile DEV buttons'));
 assert(html.includes('if(!window.WINDBOUND_DEV)return false;\n devResetScreens();'));
 for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)){if(match[1].trim())new vm.Script(match[1]);}
}
for(const path of ['js/prologue-dev.js','js/dev/motion-test.js','js/title-screen.js','js/field/rilde-village.js','js/field/moss-forest-runtime.js'])new vm.Script(fs.readFileSync(path,'utf8'));
const buttons=[{disabled:false},{disabled:false}];
const context={window:{WINDBOUND_DEV:false},document:{body:{classList:{toggle:(name,val)=>assert.equal(val,false)}},querySelectorAll:()=>buttons},devJump:()=>true};
vm.runInNewContext(fs.readFileSync('js/prologue-dev.js','utf8'),context);
assert.equal(context.devJump(),false);assert(buttons.every(x=>x.disabled));
vm.runInNewContext(fs.readFileSync('js/dev/motion-test.js','utf8'),{window:{WINDBOUND_DEV:false}});
console.log('Public/DEV channel, early UI gate, disabled commands, syntax and local QA PASS ('+cases.length+' origins)');
