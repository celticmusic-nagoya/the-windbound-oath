"use strict";
const canvas=document.getElementById("canvas"),ctx=canvas.getContext("2d");
const controls=["opacity","scale","offsetX","offsetY"];
const images={render:null,reference:null},points=[];
function number(id){return Number(document.getElementById(id).value)}
function draw(){
 ctx.clearRect(0,0,384,1024);
 if(images.render)ctx.drawImage(images.render,0,0,384,1024);
 if(images.reference){
  ctx.save();ctx.globalAlpha=number("opacity")/100;
  const k=number("scale")/100,w=384*k,h=1024*k;
  ctx.drawImage(images.reference,(384-w)/2+number("offsetX"),(1024-h)/2+number("offsetY"),w,h);ctx.restore();
 }
 ctx.fillStyle="#fa3";for(const p of points){ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fill()}
 document.getElementById("output").textContent=JSON.stringify({referenceTransform:{scale:number("scale")/100,opacity:number("opacity")/100,offsetX:number("offsetX"),offsetY:number("offsetY")},points},null,2);
}
for(const id of ["render","reference"]){
 document.getElementById(id).addEventListener("change",e=>{
  const file=e.target.files?.[0];if(!file)return;
  const url=URL.createObjectURL(file),img=new Image();
  img.onload=()=>{images[id]=img;URL.revokeObjectURL(url);draw()};
  img.onerror=()=>URL.revokeObjectURL(url);img.src=url;
 });
}
for(const id of controls)document.getElementById(id).addEventListener("input",draw);
canvas.addEventListener("pointerdown",e=>{
 const rect=canvas.getBoundingClientRect();
 points.push({x:Math.round((e.clientX-rect.left)*384/rect.width),y:Math.round((e.clientY-rect.top)*1024/rect.height)});
 draw();
});
document.getElementById("reset").addEventListener("click",()=>{
 for(const [id,val] of Object.entries({opacity:45,scale:100,offsetX:0,offsetY:0}))document.getElementById(id).value=val;
 points.length=0;draw();
});
document.getElementById("export").addEventListener("click",()=>{
 const payload=document.getElementById("output").textContent;
 const url=URL.createObjectURL(new Blob([payload],{type:"application/json"}));
 const a=document.createElement("a");a.href=url;a.download="morwen_landmarks_local.json";a.click();URL.revokeObjectURL(url);
});
draw();
