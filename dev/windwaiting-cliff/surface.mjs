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
  for (const asset of ['sparse_grass', 'stony_dirt_path']) {
    const map = await loader.loadAsync(new URL(asset + '/basecolor.jpg', base).href);
    map.colorSpace = T.SRGBColorSpace;
    map.wrapS = map.wrapT = T.RepeatWrapping;
    result[asset] = map;
  }
  return result;
}

export function adaptSurfaces(root, renderer, moss = null, photo = null) {
  const terrain = new Set();
  const bark = new Set();
  const rock = new Set();
  root.traverse((mesh) => {
    if (!mesh.isMesh || !mesh.material) return;
    const name = mesh.material.name;
    if (/Slate and weathered limestone|Windward olive turf/.test(name)) terrain.add(mesh.material);
    if (name === 'M_eco_bark') bark.add(mesh.material);
    if (moss && /Damp lower bedrock|Wet boulders and talus|Moss over loose/.test(name)) rock.add(mesh.material);
  });
  const stone = [...terrain].find((material) => material.map)?.map;
  if (stone) stone.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  for (const material of terrain) {
    material.map = null;
    material.vertexColors = false;
    material.color.setRGB(1, 1, 1);
    material.onBeforeCompile = (shader) => {
      shader.uniforms.coastStone = { value: stone };
      if (photo) {
        shader.uniforms.photoGrass = { value: photo.sparse_grass };
        shader.uniforms.photoDirt = { value: photo.stony_dirt_path };
      }
      shader.vertexShader = 'varying vec3 coastPoint;\n' + shader.vertexShader.replace(
        '#include <begin_vertex>', '#include <begin_vertex>\n coastPoint = (modelMatrix * vec4(position, 1.0)).xyz;',
      );
      if (moss) bindMossUniforms(shader, moss);
      shader.fragmentShader = `
        varying vec3 coastPoint;
        uniform sampler2D coastStone;
        ${photo ? 'uniform sampler2D photoGrass, photoDirt;' : ''}
        ${moss ? mossGLSL : ""}
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
          vec3 dirtPhoto = texture2D(photoDirt, coastPoint.xz * .75).rgb;
          grass = mix(dirtPhoto, grassPhoto, smoothstep(.22,.68,pattern));
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
    };
    material.customProgramCacheKey = () => (moss ? 'cliff-coastal-surface-eco-v2' : 'cliff-coastal-surface-v1') + (photo ? '-photo' : '');
  }
  for (const material of rock) bindRockMoss(material, moss);
  for (const material of bark) {
    material.color = new T.Color(0x5c432b);
    material.vertexColors = false;
  }
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

function bindRockMoss(material, moss) {
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
  };
  material.customProgramCacheKey = () => 'cliff-rock-moss-v2';
}
