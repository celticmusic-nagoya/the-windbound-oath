/** V06 candidate-only rock LOD selector. Source V05 receipt d4dfac77854d85f796aec1db9ee5861e2efa6e3e.
 * V04 placement QA 92ec34742f6885366f3b6e7e6b61383dc74c1fd0; A3 staging receipt f51f4a25925ba279fa44fa6053fa75f9f813d8bf.
 * D0 source receipt verified; exact LOD GLBs absent. D1-D4 actual scene HOLD; G1 BLOCKED, G2/G3/G4 NOT_RUN.
 * Sampled errors are NOT certified Hausdorff bounds. Pixel targets, margin, near floors and hysteresis are provisional screening choices, not adopted tolerances.
 * No geometry edits, no runtime hookup, no occlusion/culling or collision changes. Caller must validate common node IDs, transforms, union bounds, load readiness and PBR before enabling. Default off; keep LOD0 on missing/invalid inputs. Never hide a rock solely on this selector.
 * Self-test: node --input-type=module -e "import('./tools/map_blueprint/shared_materials_v01/rock_lod_v06.mjs').then(m=>console.log(m.runSelfTest()))"
 * Test executed in JS isolate: {"assertions":410,"sweepSwitches":4,"originOnlyCameraDiagnostic":{"counts":[12,0,0],"behind":0},"status":"SELF_TEST_PASS_NOT_RUNTIME"}
 */
export const POLICY = Object.freeze({
  "sampledPlacedError": [
    0,
    0.03053214051102557,
    0.04448614167377407
  ],
  "sampleMargin": 1.5,
  "maxPx": [
    0,
    1,
    0.75
  ],
  "minDepth": [
    0,
    12,
    30
  ],
  "enterFraction": 0.8
});
export function chooseRockLod({previous=0,depth,radialRatio,viewportHeight,verticalFovDeg,ready=[true,false,false],studyEnabled=false,hero=false,nearClip=0.1,policy: p=POLICY}={}) {
  // depth = minimum positive camera-space depth over the union of all three LOD bounds.
  // radialRatio = upper bound of hypot(x,y)/z over those bounds; no centre-distance substitute.
  if(!studyEnabled||hero||!Number.isInteger(previous)||previous<0||previous>2||
    ![depth,radialRatio,viewportHeight,verticalFovDeg,nearClip].every(Number.isFinite)||
    depth<=0||radialRatio<0||viewportHeight<=0||verticalFovDeg<=0||verticalFovDeg>=180||nearClip<=0) return {level:0,reason:"protected_or_unknown",estimatedPx:0};
  const focal=viewportHeight/(2*Math.tan(verticalFovDeg*Math.PI/360));
  for(let level=2;level>=1;level--){
    if(ready[level]!==true)continue;
    const error=p.sampledPlacedError[level]*p.sampleMargin;
    const entering=level>previous, limit=p.maxPx[level]*(entering?p.enterFraction:1);
    const minDepth=p.minDepth[level]/(entering?p.enterFraction:1);
    if(depth-error<=nearClip||depth<minDepth)continue;
    const px=focal*error*Math.hypot(1,radialRatio)/(depth-error);
    if(px<=limit)return {level,reason:"sampled_projection_study",estimatedPx:px};
  }
  return {level:0,reason:"detail_required",estimatedPx:0};
}
function selfTest(placements,camera) {
  const base={studyEnabled:true,ready:[true,true,true],viewportHeight:1080,verticalFovDeg:60,radialRatio:0.2,depth:200};
  let tests=0;const assert=(ok,msg)=>{if(!ok)throw Error(msg);tests++};
  assert(chooseRockLod(base).level===2,"far");
  assert(chooseRockLod({...base,depth:8}).level===0,"near");
  assert(chooseRockLod({...base,studyEnabled:false}).level===0,"default off");
  assert(chooseRockLod({...base,hero:true}).level===0,"hero");
  assert(chooseRockLod({...base,ready:[true,true,false]}).level===1,"missing LOD2");
  assert(chooseRockLod({...base,ready:[true,false,false]}).level===0,"missing assets");
  for(const bad of [undefined,NaN,Infinity,-1,0])assert(chooseRockLod({...base,depth:bad}).level===0,"invalid depth");
  assert(chooseRockLod({...base,verticalFovDeg:0}).level===0,"invalid FOV");
  assert(chooseRockLod({...base,radialRatio:10}).level<2,"off-axis");
  assert(chooseRockLod({...base,viewportHeight:2160,depth:100}).level<chooseRockLod({...base,depth:100}).level,"resolution");
  let previous=0,last=0,switches=0;const levels=new Set();
  for(const depth of [...Array.from({length:201},(_,i)=>5+i),...Array.from({length:201},(_,i)=>205-i)]){
    const x=chooseRockLod({...base,depth,previous}); if(x.level!==last)switches++;
    if(x.level>0)assert(x.estimatedPx<=POLICY.maxPx[x.level],"selected threshold");
    levels.add(x.level);previous=last=x.level;
  }
  assert(switches===4&&levels.size===3,"monotone sweep");
  // Locate a hysteresis band and alternate tiny depth changes while retaining state.
  const band=Array.from({length:4000},(_,i)=>10+i*.05).find(depth=>chooseRockLod({...base,depth,previous:1}).level===1&&chooseRockLod({...base,depth,previous:0}).level===0);
  assert(Number.isFinite(band),"hysteresis band");previous=0;
  for(let i=0;i<80;i++){previous=chooseRockLod({...base,depth:band+(i%2?.001:-.001),previous}).level;assert(previous===0,"boundary jitter")}
  // Actual registered camera and placements, origin-only diagnostic; bounds, occlusion and pixel QA NOT_RUN.
  const diff=(a,b)=>a.map((x,i)=>x-b[i]),dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
  const forward=diff(camera.aim,camera.eye),norm=Math.hypot(...forward),f=forward.map(x=>x/norm);
  const counts=[0,0,0];let behind=0;
  for(const p of placements){const d=diff(p.translation,camera.eye),z=dot(d,f);if(z<=0)behind++;
    const rho=z>0?Math.sqrt(Math.max(0,dot(d,d)-z*z))/z:NaN;
    const x=chooseRockLod({...base,depth:z,radialRatio:rho});counts[x.level]++;
  }
  assert(counts.reduce((a,b)=>a+b,0)===12,"12 actual placement records");
  return {assertions:tests,sweepSwitches:switches,originOnlyCameraDiagnostic:{counts,behind},status:"SELF_TEST_PASS_NOT_RUNTIME"};
}
const placements=[{"id":"MOSS_ROCK_01","translation":[1.077969373258611,35.88730437599307,13.062847261482432]},{"id":"MOSS_ROCK_02","translation":[6.595233786197355,35.12132262806929,17.36444324445165]},{"id":"MOSS_ROCK_03","translation":[4.734111303960049,34.469384527775325,31.129622419060922]},{"id":"MOSS_ROCK_04","translation":[17.629762612074956,33.46714135873825,25.967635210390085]},{"id":"MOSS_ROCK_05","translation":[23.1470270250137,32.58262424332951,30.269231193359303]},{"id":"MOSS_ROCK_06","translation":[28.664291437952443,31.591119048888306,34.57082717632852]},{"id":"MOSS_ROCK_07","translation":[34.181555850891186,30.76542015485944,38.87242315929768]},{"id":"MOSS_ROCK_08","translation":[39.698820263830044,29.988317399835356,43.17401914226696]},{"id":"MOSS_ROCK_09","translation":[45.21608467676879,29.158085855617813,47.47561512523612]},{"id":"MOSS_ROCK_10","translation":[54.42254253729561,28.237500694168975,47.045419512385365]},{"id":"MOSS_ROCK_11","translation":[58.095210226441395,28.018903434797945,53.712911293265336]},{"id":"MOSS_ROCK_12","translation":[61.76787791558468,27.790748562783698,60.38040307414349]}];
const camera={"eye":[65.46629967221475,31.04145469656912,80.21376582250929],"aim":[66.4214969613846,28.73543522763558,73.4754018231929]};
export function runSelfTest(){return selfTest(placements,camera);}
