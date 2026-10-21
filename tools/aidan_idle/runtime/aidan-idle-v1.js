/* Aidan idle v1 -- WebGL2 runtime player (candidate; NOT wired into the game).
 * One official MASTER still + eye-blink overlays, warped by a smooth periodic displacement field (mirror of tools/aidan_idle/idle_motion.py: Idle.field).
 * Nothing is repainted: the MASTER's pixels are only moved.  Loop = 8 s exactly periodic.
 *   const p = await AidanIdleV1.create(canvas, {base:'.../idle_v1/'});  p.start();  p.drawAt(t, eyeState)  (deterministic, for QA)
 */
(function (root) {
  'use strict';
  const TAU = Math.PI * 2;
  const VS = `#version 300 es
  in vec2 p; out vec2 vP; uniform vec4 uRect; // uRect: master-px rect (x0,y0,x1,y1) mapped to the whole canvas
  void main(){ vec2 uv=p*.5+.5; vP=vec2(mix(uRect.x,uRect.z,uv.x), mix(uRect.w,uRect.y,uv.y)); gl_Position=vec4(p,0,1); }`;
  const FS = `#version 300 es
  precision highp float;
  in vec2 vP; out vec4 o;
  uniform sampler2D uM, uWa, uWb, uWc; uniform vec2 uSize; uniform float uU, uBr, uRise, uC, uS, uHs, uBg; uniform vec3 uBgc;
  float ss(float a,float b,float x){float t=clamp((x-a)/(b-a),0.,1.);return t*t*(3.-2.*t);}
  const float TAU=6.283185307179586;
  void main(){
    vec2 q=vP; vec2 st=q/uSize;
    vec3 wa=texture(uWa,st).rgb, wb=texture(uWb,st).rgb, wc=texture(uWc,st).rgb;
    float wTor=wa.r, wHead=wa.g, wHair=wa.b, wG=wb.r, wCL=wb.g, wCR=wb.b, wFL=wc.r, wFR=wc.g, wSk=wc.b;
    float u=uU, X=q.x, Y=q.y; float dx=0., dy=0.;
    dy+=wTor*uRise + wHead*(-1.8*uBr); dx+=wTor*((X-800.)*0.0016*uBr);
    float gx=(X-800.)*uC-(Y-560.)*uS+800.-X, gy=(X-800.)*uS+(Y-560.)*uC+560.-Y;
    dx+=wG*gx; dy+=wG*(gy+uRise*0.8);
    float hh=clamp((230.-Y)/180.,0.,1.);
    dx+=wHair*(1.+1.4*hh)*2.1*uHs;
    dy+=wHair*(0.5+hh)*(-0.9)*(0.5-0.5*cos(TAU*(2.*u-0.22)));
    float dc=clamp(length(q-vec2(830.,400.))/900.,0.,1.);
    { float a=6.2, lag=0.34; float wave=sin(TAU*(2.*u-lag*dc-0.12))+0.35*sin(TAU*(u-0.5*lag*dc));
      dy+=wCL*(a*(0.35+dc))*wave*0.8; dx+=wCL*(a*0.55*dc)*sin(TAU*(2.*u-lag*dc-0.30)); }
    { float a=5.3, lag=0.30; float wave=sin(TAU*(2.*u-lag*dc-0.12))+0.35*sin(TAU*(u-0.5*lag*dc));
      dy+=wCR*(a*(0.35+dc))*wave*0.8; dx+=wCR*(a*0.55*dc)*sin(TAU*(2.*u-lag*dc-0.30)); }
    float df=clamp(length(q-vec2(760.,760.))/900.,0.,1.);
    { float a=4.4, lag=0.42; float wave=sin(TAU*(2.*u-lag*df-0.20));
      dy+=wFL*(a*(0.3+df))*wave*0.8; dx+=wFL*(a*0.5*df)*sin(TAU*(2.*u-lag*df-0.45)); }
    { float a=3.4, lag=0.40; float wave=sin(TAU*(2.*u-lag*df-0.20));
      dy+=wFR*(a*(0.3+df))*wave*0.8; dx+=wFR*(a*0.5*df)*sin(TAU*(2.*u-lag*df-0.45)); }
    dy+=wSk*sin(TAU*(2.*u-0.30));
    vec2 src=(q-vec2(dx,dy))/uSize;
    vec4 c=texture(uM,src);   // premultiplied
    if(src.x<0.||src.y<0.||src.x>1.||src.y>1.) c=vec4(0.);
    o = uBg>0.5 ? vec4(c.rgb+uBgc*(1.-c.a),1.) : c;
  }`;

  function sh(gl, type, src) { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
  async function img(url, pm) { const r = await fetch(url); if (!r.ok) throw new Error(url + ' ' + r.status); return createImageBitmap(await r.blob(), { premultiplyAlpha: pm ? 'premultiply' : 'none', colorSpaceConversion: 'none' }); }

  async function create(canvas, opt) {
    opt = opt || {}; const base = opt.base;
    const meta = await (await fetch(base + 'idle_v1.json')).json(); const [W, H] = meta.size;
    const gl = canvas.getContext('webgl2', { premultipliedAlpha: true, alpha: true, antialias: false, preserveDrawingBuffer: !!opt.preserve });
    if (!gl) throw new Error('webgl2 unavailable');
    const prog = gl.createProgram(); gl.attachShader(prog, sh(gl, gl.VERTEX_SHADER, VS)); gl.attachShader(prog, sh(gl, gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    gl.useProgram(prog);
    const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, 'p'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const U = n => gl.getUniformLocation(prog, n);
    // textures
    const tex = (src, mips, premult) => {
      const t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, !!premult); gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, src);
      if (mips) { gl.generateMipmap(gl.TEXTURE_2D); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR); } else gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    };
    const [master, wa, wb, wc] = await Promise.all([img(base + meta.master, true), ...meta.weights.map(w => img(base + w))]);
    const ov = {}; await Promise.all(['L', 'R'].flatMap(e => [1, 2, 3, 4].map(async s => { ov[e + s] = await img(`${base}eyes/overlay_${e}_s${s}.png`); })));
    // eye states: 0 = MASTER;  s = MASTER with the overlay RGB placed where the overlay is opaque (source-atop keeps the MASTER's alpha)
    const comp = document.createElement('canvas'); comp.width = W; comp.height = H; const cx = comp.getContext('2d', { colorSpace: 'srgb' });
    const states = [tex(master, true, true)];
    for (let s = 1; s <= 4; s++) {
      cx.globalCompositeOperation = 'copy'; cx.drawImage(master, 0, 0); cx.globalCompositeOperation = 'source-atop';
      for (const e of ['L', 'R']) cx.drawImage(ov[e + s], meta.eyeBoxes[e][0], meta.eyeBoxes[e][1]);
      states.push(tex(comp, true, true));
    }
    const wt = [tex(wa, false, false), tex(wb, false, false), tex(wc, false, false)];
    gl.uniform1i(U('uM'), 0); gl.uniform1i(U('uWa'), 1); gl.uniform1i(U('uWb'), 2); gl.uniform1i(U('uWc'), 3);
    for (let i = 0; i < 3; i++) { gl.activeTexture(gl.TEXTURE1 + i); gl.bindTexture(gl.TEXTURE_2D, wt[i]); }
    gl.uniform2f(U('uSize'), W, H);
    const P = meta.loopSeconds, uni = { u: U('uU'), br: U('uBr'), rise: U('uRise'), c: U('uC'), s: U('uS'), hs: U('uHs'), rect: U('uRect'), bg: U('uBg'), bgc: U('uBgc') };
    const BS = meta.blink.seq; const BT = BS.reduce((a, b) => a + b[1], 0);
    const blinkState = (ms) => { if (ms < 0 || ms >= BT) return 0; for (const [s, d] of BS) { if (ms < d) return s; ms -= d; } return 0; };
    let rect = [0, 0, W, H], reduced = false;
    const api = {
      meta, gl, width: W, height: H,
      /** which master-px rectangle fills the canvas (default: the whole master) */
      setRect(x0, y0, x1, y1) { rect = [x0, y0, x1, y1]; },
      /** draw the pose at time t (s, any value) with eye state 0..4;  opaque background colour optional (QA) */
      drawAt(t, eye, bg) {
        const u = ((t % P) + P) % P / P, br = 0.5 - 0.5 * Math.cos(TAU * 2 * u), th = (0.20 * Math.sin(TAU * (2 * u - 0.07)) - 0.08 * br) * Math.PI / 180;
        const hs = Math.sin(TAU * (2 * u - 0.16)) + 0.28 * Math.sin(TAU * (3 * u - 0.30));
        gl.viewport(0, 0, canvas.width, canvas.height); gl.useProgram(prog);
        gl.uniform1f(uni.u, u); gl.uniform1f(uni.br, br); gl.uniform1f(uni.rise, -3 * br); gl.uniform1f(uni.c, Math.cos(th)); gl.uniform1f(uni.s, Math.sin(th)); gl.uniform1f(uni.hs, hs);
        gl.uniform4f(uni.rect, rect[0], rect[1], rect[2], rect[3]); gl.uniform1f(uni.bg, bg ? 1 : 0); if (bg) gl.uniform3f(uni.bgc, bg[0] / 255, bg[1] / 255, bg[2] / 255);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, states[eye | 0]);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
      },
      blinkState,
      /** free-running player (rAF).  Blink gaps 3-6 s from a render-only RNG; never two in a row. */
      start(o) {
        o = o || {}; const rnd = o.rng || Math.random; let t0 = null, next = 1.5 + rnd() * 1.5, bs = -1e9; reduced = !!o.reducedMotion;
        const mq = root.matchMedia && root.matchMedia('(prefers-reduced-motion: reduce)'); if (mq && mq.matches) reduced = true;
        const loop = (now) => {
          api._raf = requestAnimationFrame(loop); if (t0 === null) t0 = now; const t = (now - t0) / 1000;
          if (reduced) { api.drawAt(0, 0); return; }
          if (t >= next) { bs = next; next = t + BT / 1000 + (meta.blink.minGap + rnd() * (meta.blink.maxGap - meta.blink.minGap)) / 1000; }
          api.drawAt(t, blinkState((t - bs) * 1000));
        };
        api._raf = requestAnimationFrame(loop);
      },
      stop() { cancelAnimationFrame(api._raf); },
    };
    return api;
  }
  root.AidanIdleV1 = { create, TAU };
})(window);
