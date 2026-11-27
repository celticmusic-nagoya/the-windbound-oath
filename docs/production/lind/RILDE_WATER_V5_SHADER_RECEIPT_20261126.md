# Rilde river water V5 — isolated shader execution receipt
Status: candidate, not adopted, not game runtime. Source V4 GLB 3ab3cda5d7756829449bd9eb73a429eb4cf5993ea34b90cea204d7541a36af96; no GLB modification. Same approved CG and CC0 gravel provenance as V4. GLSL ES 300 fragment candidate expected SHA256 eb7b66fa4c3cfe2e034a706410bee0d8c1afc5413d9390ef25aa2a3e62a56f6a.
Actual local EGL GLES 3.2 Mesa 25.0.7-2 llvmpipe compile/link/draw/readback, 960x584 VTK actual geometry opaque color, depth-tested water mask, reflected camera color. This is a software OpenGL ES execution, not WebGL or Android. Time 0 and 1.25s, outside water unchanged exactly on all 8 frames.
| view | mode | visible pixels | animated pixels (any RGB >2) | outside changed |
|---|---:|---:|---:|---:|
| grazing | 0 |146632|108762|0|
| grazing | 1 |146632|99424|0|
| shallow | 0 |461619|151154|0|
| shallow | 1 |461619|156527|0|
Inputs: uScene/uReflection RGB8 sRGB-encoded, same dimensions, nearest. uSurface RGBA32F nearest, local X,Y, approximate depth BU, depth-tested mask 0/1. uNormal periodic RGB8 linear repeat, two scroll phases. uEye local Z-up, uWaterZ actual plane (-2.35 BU), uPixel inverse viewport, uTime seconds, uQuality 0 constant sky proxy /1 planar reflection input. Output RGB sRGB-encoded, alpha 1; no blending into scene. Outside mask copied. Refraction rejects samples outside visible water. Fullscreen triangle, no arbitrary external imagery. Actual camera reflection pass is offline; engine must create matching render targets and correctly handle color space, depth, occluders and transparent ordering before use. Float buffer and full-screen copy costs unmeasured, no claim mobile budget. Need capability gate and V4 static alpha fallback. G2 HOLD: straight bare banks, flat/noisy bed and artificial caustics; real environment render, movement and Android G4 NOT_RUN. Actual output JPEG and tests delivered in chat, local only. No formal placement or adoption.
