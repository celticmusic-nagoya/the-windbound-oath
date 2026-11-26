#version 300 es
precision highp float;
uniform sampler2D uScene, uReflection, uNormal, uSurface;
uniform vec3 uEye;
uniform float uWaterZ;
uniform vec2 uPixel;
uniform float uTime;
uniform int uQuality;
in vec2 vUV;
out vec4 frag;
vec3 linearize(vec3 c){return mix(c/12.92,pow((c+0.055)/1.055,vec3(2.4)),step(vec3(.04045),c));}
vec3 encode(vec3 c){c=clamp(c,0.,1.);return mix(12.92*c,1.055*pow(c,vec3(1./2.4))-.055,step(vec3(.0031308),c));}
void main(){
 vec3 original=texture(uScene,vUV).rgb;
 vec4 surf=texture(uSurface,vUV);
 if(surf.a<.5){frag=vec4(original,1.);return;}
 vec2 p=surf.xy;
 vec2 a=texture(uNormal,p*.44+vec2(.017,.062)*uTime).xy*2.-1.;
 vec2 b=texture(uNormal,p*.97+vec2(-.021,.093)*uTime).xy*2.-1.;
 vec2 slope=a*.72+b*.28;
 vec3 N=normalize(vec3(slope,1.));
 vec3 V=normalize(uEye-vec3(p,uWaterZ));
 float F=.0204+.9796*pow(1.-clamp(dot(N,V),0.,1.),5.);
 vec2 offset=slope*vec2(9.,7.)*uPixel;
 vec2 refr=clamp(vUV+offset,uPixel,1.-uPixel);
 if(texture(uSurface,refr).a<.5)refr=vUV;
 vec3 T=exp(-surf.z/max(.38,V.z)*vec3(.85,.36,.43));
 vec3 bed=linearize(texture(uScene,refr).rgb)*T+vec3(.027,.105,.077)*(1.-T);
 float c1=sin(p.x*8.7+p.y*3.1+uTime*1.3+4.*slope.x);
 float c2=sin(p.y*9.6-p.x*2.7+uTime*1.7+4.*slope.y);
 float caustic=pow(1.-abs(c1*c2),8.)*.065*exp(-surf.z*3.8)*smoothstep(0.,.08,surf.z);
 bed+=caustic*vec3(.82,1.,.84);
 vec3 reflectCol=vec3(.22,.34,.46);
 if(uQuality==1)reflectCol=linearize(texture(uReflection,clamp(vUV+offset*1.35,uPixel,1.-uPixel)).rgb);
 vec3 H=normalize(normalize(vec3(.35,-.45,.82))+V);
 float highlight=.19*pow(max(dot(N,H),0.),100.);
 frag=vec4(encode(mix(bed,reflectCol,F)+highlight),1.);
}
