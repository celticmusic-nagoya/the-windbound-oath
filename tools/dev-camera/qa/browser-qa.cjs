// Development-only Chromium QA; not an Android device test.
const {chromium}=require('playwright');
const fs=require('node:fs'),http=require('node:http'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),glb=process.env.AIDAN_GLB_PATH;
if(!glb||!fs.existsSync(glb))throw Error('AIDAN_GLB_PATH missing');
const html=fs.readFileSync(path.join(root,'index.html'),'utf8')
 .replaceAll('https://cdn.jsdelivr.net/npm/three@0.170.0/','/node_modules/three/');
const mime={'.js':'text/javascript','.html':'text/html','.glb':'model/gltf-binary'};
const server=http.createServer((req,res)=>{
 let file;
 if(req.url==='/') {res.setHeader('Content-Type','text/html; charset=utf-8');res.end(html);return}
 if(req.url==='/model.glb')file=glb;
 else if(req.url.startsWith('/node_modules/three/'))file=path.join(__dirname,'node_modules/three',req.url.slice('/node_modules/three/'.length));
 else {res.writeHead(404);res.end();return}
 if(!file.startsWith(path.join(__dirname,'node_modules/three'))&&file!==glb){res.writeHead(403);res.end();return}
 res.setHeader('Content-Type',mime[path.extname(file)]||'application/octet-stream');
 fs.createReadStream(file).on('error',()=>{res.destroy()}).pipe(res);
});
(async()=>{
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({headless:true,args:['--use-gl=angle','--use-angle=swiftshader','--enable-webgl']});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:'+server.address().port+'/',{waitUntil:'networkidle'});
  await page.locator('#file').setInputFiles(glb);
  await page.getByRole('status').getByText('読込完了',{exact:false}).waitFor({timeout:90000});
  assert.equal(errors.length,0,errors.join('\n'));
  assert.ok(await page.locator('#layers input[type=checkbox]').count()>=2,'expected grouped visibility controls');
  const canvas=page.locator('canvas');assert.ok(await canvas.isVisible());
  for(const view of ['game','front','back','left','right','top'])await page.locator('[data-view="'+view+'"]').click();
  await page.locator('#fit').click();
  const rect=await canvas.boundingBox();assert.ok(rect&&rect.width>200&&rect.height>200);
  await page.mouse.move(rect.x+rect.width/2,rect.y+rect.height/2);
  await page.mouse.down();await page.mouse.move(rect.x+rect.width/2+70,rect.y+rect.height/2+45,{steps:8});await page.mouse.up();
  await page.locator('#layers input[type=checkbox]').first().uncheck();
  await page.locator('#layers input[type=checkbox]').first().check();
  await page.screenshot({path:process.env.AIDAN_QA_SCREENSHOT||'/tmp/aidan-dev-camera-qa.png',fullPage:true});
  console.log(JSON.stringify({status:'PASS',viewports:'390x844',presets:6,groupCount:await page.locator('#layers input[type=checkbox]').count(),pageErrors:errors.length}));
 }finally{await browser.close();server.close()}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
