const S=require(require('path').join(__dirname,'../../js/field/forest-scatter.js'));const fs=require('fs');
const m=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));process.stdout.write(JSON.stringify(S.generate(m).map(e=>({a:e.asset,x:e.x,y:e.y,r:e.render}))));
