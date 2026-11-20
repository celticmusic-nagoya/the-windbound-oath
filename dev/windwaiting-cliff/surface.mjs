import * as T from 'three';

// The Blender originals use generated/box-mapped PBR graphs. Rebuild the
// spatial blend here because glTF has no representation for those nodes.
export async function loadMossTextures(base) {
  const loader = new T.TextureLoader();
  const textures = await Promise.all(['basecolor', 'normal', 'orm'].map(async (channel) => {
    const map = await loader.loadAsync(new URL(`textures/moss_tile_${channel}.png`, base).href);
    if (channel === 'basecolor') map.colorSpace = T.SRGBColorSpace;
    map.wrapS = map.wrapT = T.RepeatWrapping;
    return map;
  }));
  return { color: textures[0], normal: textures[1], orm: textures[2] };
}

// Optional, same-origin photo material candidate; no network dependency during normal play.
export async function loadPhotoSurfaces(base) {
  const loader = new T.TextureLoader();
  const result = {};
  for (const asset of ['sparse_grass', 'stony_dirt_path', 'rock_boulder_dry', 'bark_brown_02']) {
    const dir = new URL(asset + '/', base);
    const response = await fetch(new URL('manifest.json', dir));
    if (!response.ok) throw new Error('Photo manifest HTTP ' + response.status);
    const manifest = await response.json();
    for (const role of ['basecolor', 'normal', 'roughness']) {
      const filename = manifest.textures[role].path;
      if (!/^[a-z]+\.(jpg|png)$/.test(filename)) throw new Error('Invalid photo texture path');
      const map = await loader.loadAsync(new URL(filename, dir).href);
      if (role === 'basecolor') map.colorSpace = T.SRGBColorSpace;
      map.wrapS = map.wrapT = T.RepeatWrapping;
      result[asset + (role === 'basecolor' ? '' : '_' + role)] = map;
    }
  }
  return result;
}

export function adaptSurfaces(root, renderer, moss = null, photo = null) {
  const terrain = new Set();
  const bark = new Set();
  const rock = new Set();
  const road = new Set();
  const roadMeshes = [];
  root.traverse((mesh) => {
    if (!mesh.isMesh || !mesh.material) return;
    const name = mesh.material.name;
    if (/Slate and weathered limestone|Windward olive turf/.test(name)) terrain.add(mesh.material);
    if (photo && name === 'Weathered ochre footpath') { road.add(mesh.material); roadMeshes.push(mesh); }
    if (name === 'M_eco_bark') bark.add(mesh.material);
    if (moss && /Damp lower bedrock|Wet boulders and talus|Moss over loose/.test(name)) rock.add(mesh.material);
  });
  // Measure the existing route cross-section in world space, without changing collision geometry.
  const routeA = new T.Vector2(8, -17.25), routeB = new T.Vector2(-5.2, -2.8);
  const axis = routeB.clone().sub(routeA).normalize();
  const lateral = new T.Vector2(-axis.y, axis.x);
  let lo = Infinity, hi = -Infinity;
  root.updateMatrixWorld(true);
  for (const mesh of roadMeshes) {
    const p = mesh.geometry.attributes.position;
    const v = new T.Vector3();
    for (let i = 0; i < p.count; i++) {
      v.fromBufferAttribute(p,i).applyMatrix4(mesh.matrixWorld);
      const d = new T.Vector2(v.x,v.z).sub(routeA).dot(lateral);
      lo = Math.min(lo,d); hi = Math.max(hi,d);
    }
  }
  const routeWidth = roadMeshes.length ? new T.Vector2(lo,hi) : new T.Vector2(0,0);
  const shoulderGLSL = `
    uniform vec2 routeWidth;
    float routeShoulder(vec2 p) {
      vec2 a=vec2(8.,-17.25), b=vec2(-5.2,-2.8);
      vec2 axis=normalize(b-a);
      float along=dot(p-a,axis);
      float side=dot(p-a,vec2(-axis.y,axis.x));
      float edge=min(side-routeWidth.x,routeWidth.y-side);
      float endMask=smoothstep(-.45,.2,along)*(1.-smoothstep(length(b-a)-.2,length(b-a)+.45,along));
      float irregular=.10*sin(p.x*8.3+p.y*4.7)+.06*sin(p.y*19.);
      return smoothstep(-.45,.15,edge+irregular)*endMask;
    }
  `;
  const stone = photo?.rock_boulder_dry ?? [...terrain].find((material) => material.map)?.map;
  if (stone) stone.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  for (const material of terrain) {
    material.map = null;
    material.vertexColors = false;
    material.color.setRGB(1, 1, 1);
    material.onBeforeCompile = (shader) => {
      shader.uniforms.coastStone = { value: stone };
      if (photo) {
        shader.uniforms.routeWidth = { value: routeWidth };
        shader.uniforms.photoGrass = { value: photo.sparse_grass };
        shader.uniforms.photoDirt = { value: photo.stony_dirt_path };
        shader.uniforms.photoNormal = { value: photo.sparse_grass_normal };
        shader.uniforms.photoRough = { value: photo.sparse_grass_roughness };
      }
      shader.vertexShader = 'varying vec3 coastPoint;\n' + shader.vertexShader.replace(
        '#include <begin_vertex>', '#include <begin_vertex>\n coastPoint = (modelMatrix * vec4(position, 1.0)).xyz;',
      );
      if (moss) bindMossUniforms(shader, moss);
      shader.fragmentShader = `
        varying vec3 coastPoint;
        uniform sampler2D coastStone;
        ${photo ? 'uniform sampler2D photoGrass, photoDirt, photoNormal, photoRough;' : ''}
        ${moss ? mossGLSL : ""}
        ${photo && roadMeshes.length ? shoulderGLSL : ''}
        float grainHash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
        float grain(vec2 p) {
          vec2 i = floor(p), f = fract(p);
          f = f*f*(3.0-2.0*f);
          return mix(mix(grainHash(i), grainHash(i+vec2(1.,0.)), f.x),
                     mix(grainHash(i+vec2(0.,1.)), grainHash(i+1.), f.x), f.y);
        }
        vec3 coastRock(vec3 direction) {
          vec3 weights = pow(abs(direction), vec3(5.0));
          weights /= max(dot(weights, vec3(1.0)), 0.001);
          vec3 textureColor = texture2D(coastStone, coastPoint.zy * .22).rgb * weights.x +
                              texture2D(coastStone, coastPoint.xz * .22).rgb * weights.y +
                              texture2D(coastStone, coastPoint.xy * .22).rgb * weights.z;
          return textureColor * vec3(.66, .74, .84);
        }
      ` + shader.fragmentShader.replace('#include <map_fragment>', `
        vec3 surfaceNormal = normalize(cross(dFdx(coastPoint), dFdy(coastPoint)));
        float fineGrain = grain(coastPoint.xz * 14.);
        float pattern = grain(coastPoint.xz * .83) * .64 + fineGrain * .36;
        vec3 grass = mix(vec3(.058,.092,.020), vec3(.25,.28,.055), pattern);
        ${photo ? `
          vec3 grassPhoto = texture2D(photoGrass, coastPoint.xz * .75).rgb;
          // Broad, irregular meadow patches retain photographic microdetail.
          float meadowPatch = grain(coastPoint.xz * .18 + vec2(7.1,2.8));
          float meadowEdge = grain(coastPoint.xz * .52);
          float meadowMix = smoothstep(.25,.78,meadowPatch*.78+meadowEdge*.22);
          grass = mix(vec3(.037,.102,.031), vec3(.21,.30,.085), meadowMix);
          grass *= .84 + pattern*.32;
          vec3 dirtPhoto = texture2D(photoDirt, coastPoint.xz * .75).rgb;
          // Preserve art-directed green chroma; borrow photographic luminance/detail.
          float grassLight = dot(grassPhoto, vec3(.2126,.7152,.0722));
          float exposed = smoothstep(.76,.93,pattern) * .12;
          grass *= clamp(.83 + grassLight * .95, .85, 1.22);
          grass = mix(grass, dirtPhoto * vec3(.65,.78,.55), exposed);
          ${roadMeshes.length ? 'grass = mix(grass, dirtPhoto * vec3(1.05,1.02,.90), routeShoulder(coastPoint.xz)*.75);' : ''}
        ` : ''}
        float cover = smoothstep(.55,.86,surfaceNormal.y + (pattern-.5)*.20) *
                      smoothstep(3.3,5.0,coastPoint.y);
        ${moss ? `
          grass = mix(grass, vec3(.25,.27,.085), smoothstep(.60,.94,fineGrain) * .32);
          float mossMask = 0.0;
          vec2 mossUV = coastPoint.xz * 2.0;
          vec3 stoneColor = grass;
          if (cover < .999) {
            stoneColor = coastRock(surfaceNormal);
            mossMask = ecoMossMask(coastPoint, surfaceNormal.y) * (1.0 - cover);
            if (mossMask > .01) stoneColor = mix(stoneColor, texture2D(ecoMossColor, mossUV).rgb, mossMask);
          }
        ` : 'vec3 stoneColor = coastRock(surfaceNormal);'}
        diffuseColor.rgb *= mix(stoneColor, grass, cover);
      `);
      if (moss) addMossResponse(shader, 'mix(1.0, .94 + pattern * .10, cover)');
      if (photo) {
        addPhotoResponse(shader, 'coastPoint', 'cover', 'photoNormal', 'photoRough');
        addRockPhotoResponse(shader, photo, 'coastPoint', 'surfaceNormal', moss ? '(1.0-cover)*(1.0-mossMask)' : '1.0-cover');
      }
    };
    material.customProgramCacheKey = () => (moss ? 'cliff-coastal-surface-eco-v2' : 'cliff-coastal-surface-v1') + (photo ? '-photo-shoulder-rock-v12' : '');
  }
  for (const material of road) {
    material.onBeforeCompile = (shader) => {
      shader.uniforms.routeWidth = { value: routeWidth };
      shader.uniforms.roadPhoto = { value: photo.stony_dirt_path };
      shader.uniforms.roadNormal = { value: photo.stony_dirt_path_normal };
      shader.uniforms.roadRough = { value: photo.stony_dirt_path_roughness };
      shader.vertexShader = 'varying vec3 roadPoint;\n' + shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\n roadPoint = (modelMatrix * vec4(position,1.0)).xyz;');
      shader.fragmentShader = shoulderGLSL + 'varying vec3 roadPoint; uniform sampler2D roadPhoto, roadNormal, roadRough;\n' + shader.fragmentShader.replace('#include <map_fragment>', '#include <map_fragment>\n float edgeCoverage = routeShoulder(roadPoint.xz);\n if (edgeCoverage < fract(52.9829189 * fract(dot(gl_FragCoord.xy,vec2(.06711056,.00583715))))) discard;\n diffuseColor.rgb = mix(diffuseColor.rgb, texture2D(roadPhoto,roadPoint.xz*.75).rgb * vec3(1.18,1.12,.98), .85);');
      addPhotoResponse(shader, 'roadPoint', '1.0', 'roadNormal', 'roadRough');
    };
    material.customProgramCacheKey = () => 'cliff-photo-road-v3';
  }
  for (const material of rock) bindRockMoss(material, moss, photo);
  for (const material of bark) {
    material.color = new T.Color(photo ? 0xffffff : 0x5c432b);
    if (photo) { material.map = photo.bark_brown_02; material.normalMap = photo.bark_brown_02_normal; material.roughnessMap = photo.bark_brown_02_roughness; material.roughness = 1; material.needsUpdate = true; }
    material.vertexColors = false;
  }
}

// World X/-Z tangent convention: the horizontal photo UV uses X/Z,
// so the OpenGL green channel follows increasing world Z.
function addPhotoResponse(shader, point, mask, normalMap, roughMap) {
  shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>', `
    #include <roughnessmap_fragment>
    roughnessFactor = mix(roughnessFactor, texture2D(${roughMap}, ${point}.xz*.75).r, ${mask}*.65);
  `).replace('#include <normal_fragment_maps>', `
    #include <normal_fragment_maps>
    vec3 photoN = texture2D(${normalMap}, ${point}.xz*.75).rgb*2.0-1.0;
    vec3 photoX = mat3(viewMatrix)*vec3(1.,0.,0.);
    vec3 photoZ = mat3(viewMatrix)*vec3(0.,0.,1.);
    vec3 photoSlope = photoX*photoN.x + photoZ*photoN.y;
    photoSlope -= normal*dot(photoSlope,normal);
    normal = normalize(normal + photoSlope * ${mask} * .35);
  `);
}

const mossGLSL = `
  uniform sampler2D ecoMossColor, ecoMossNormal, ecoMossORM;
  float ecoMossMask(vec3 point, float faceUp) {
    float mossPatch = sin(point.x * 3.7 + sin(point.z * 2.4)) * sin(point.z * 2.8);
    float recess = smoothstep(-.45, .64, mossPatch);
    return smoothstep(.55, .8, faceUp) * (.15 + .60 * recess);
  }
`;

function bindMossUniforms(shader, moss) {
  Object.assign(shader.uniforms, {
    ecoMossColor: { value: moss.color },
    ecoMossNormal: { value: moss.normal },
    ecoMossORM: { value: moss.orm },
  });
}

function addMossResponse(shader, terrainRoughness = '1.0') {
  shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>', `
    #include <roughnessmap_fragment>
    roughnessFactor *= ${terrainRoughness};
    if (mossMask > .01) roughnessFactor = mix(roughnessFactor, texture2D(ecoMossORM, mossUV).g, mossMask);
  `).replace('#include <normal_fragment_maps>', `
    #include <normal_fragment_maps>
    if (mossMask > .01) {
      vec2 mossRelief = texture2D(ecoMossNormal, mossUV).rg * 2.0 - 1.0;
      vec3 mossSlope = mat3(viewMatrix) * vec3(mossRelief.x, 0.0, mossRelief.y);
      normal = normalize(normal + mossSlope * mossMask * .22);
    }
  `);
}

function bindRockMoss(material, moss, photo) {
  if (material.name.includes('Moss over loose')) material.color.setRGB(.16, .145, .125);
  material.onBeforeCompile = (shader) => {
    bindMossUniforms(shader, moss);
    shader.vertexShader = 'varying vec3 rockPoint;\n' + shader.vertexShader.replace(
      '#include <begin_vertex>', `#include <begin_vertex>
        vec4 rockLocal = vec4(position, 1.0);
        #ifdef USE_INSTANCING
          rockLocal = instanceMatrix * rockLocal;
        #endif
        rockPoint = (modelMatrix * rockLocal).xyz;`,
    );
    shader.fragmentShader = 'varying vec3 rockPoint;\n' + mossGLSL + shader.fragmentShader.replace(
      '#include <map_fragment>', `
        #include <map_fragment>
        vec3 rockNormal = normalize(cross(dFdx(rockPoint), dFdy(rockPoint)));
        float mossMask = ecoMossMask(rockPoint, rockNormal.y);
        vec2 mossUV = rockPoint.xz * 2.0;
        if (mossMask > .01) diffuseColor.rgb = mix(diffuseColor.rgb, texture2D(ecoMossColor, mossUV).rgb, mossMask);
      `,
    );
    addMossResponse(shader);
    if (photo) addRockPhotoResponse(shader, photo, 'rockPoint', 'rockNormal', '1.0-mossMask');
  };
  material.customProgramCacheKey = () => photo ? 'cliff-rock-moss-photo-v12' : 'cliff-rock-moss-v2';
}

const rockPhotoGLSL = `
uniform sampler2D rockPhotoNormal, rockPhotoRough;
vec3 rockWeights(vec3 n) {
  vec3 w = pow(abs(n), vec3(5.0));
  return w / max(dot(w, vec3(1.0)), .001);
}
float rockRoughAt(vec3 p, vec3 n) {
  vec3 w = rockWeights(n);
  return dot(w, vec3(texture2D(rockPhotoRough,p.zy*.22).r,
    texture2D(rockPhotoRough,p.xz*.22).r, texture2D(rockPhotoRough,p.xy*.22).r));
}
vec3 rockSlopeAt(vec3 p, vec3 n) {
  vec3 w = rockWeights(n);
  vec2 x = texture2D(rockPhotoNormal,p.zy*.22).rg*2.-1.;
  vec2 y = texture2D(rockPhotoNormal,p.xz*.22).rg*2.-1.;
  vec2 z = texture2D(rockPhotoNormal,p.xy*.22).rg*2.-1.;
  return mat3(viewMatrix)*(w.x*vec3(0.,x.y,x.x)+w.y*vec3(y.x,0.,y.y)+w.z*vec3(z.x,z.y,0.));
}
`;
function addRockPhotoResponse(shader, photo, point, direction, mask) {
  shader.uniforms.rockPhotoNormal = { value: photo.rock_boulder_dry_normal };
  shader.uniforms.rockPhotoRough = { value: photo.rock_boulder_dry_roughness };
  shader.fragmentShader = rockPhotoGLSL + shader.fragmentShader;
  shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>', `
    #include <roughnessmap_fragment>
    roughnessFactor = mix(roughnessFactor, rockRoughAt(${point}, ${direction}), (${mask})*.65);
  `).replace('#include <normal_fragment_maps>', `
    #include <normal_fragment_maps>
    vec3 rockPhotoSlope = rockSlopeAt(${point}, ${direction});
    rockPhotoSlope -= normal*dot(rockPhotoSlope,normal);
    normal = normalize(normal + rockPhotoSlope*(${mask})*.35);
  `);
}
