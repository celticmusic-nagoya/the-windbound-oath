import * as T from 'three';

// The Blender originals use generated/box-mapped PBR graphs. Rebuild the
// spatial blend here because glTF has no representation for those nodes.
export function adaptSurfaces(root, renderer) {
  const terrain = new Set();
  const bark = new Set();
  root.traverse((mesh) => {
    if (!mesh.isMesh || !mesh.material) return;
    const name = mesh.material.name;
    if (/Slate and weathered limestone|Windward olive turf/.test(name)) terrain.add(mesh.material);
    if (name === 'M_eco_bark') bark.add(mesh.material);
  });
  const stone = [...terrain].find((material) => material.map)?.map;
  if (stone) stone.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  for (const material of terrain) {
    material.map = null;
    material.vertexColors = false;
    material.color.setRGB(1, 1, 1);
    material.onBeforeCompile = (shader) => {
      shader.uniforms.coastStone = { value: stone };
      shader.vertexShader = 'varying vec3 coastPoint;\n' + shader.vertexShader.replace(
        '#include <begin_vertex>', '#include <begin_vertex>\n coastPoint = (modelMatrix * vec4(position, 1.0)).xyz;',
      );
      shader.fragmentShader = `
        varying vec3 coastPoint;
        uniform sampler2D coastStone;
        float grainHash(vec2 p) { return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453); }
        float grain(vec2 p) {
          vec2 i = floor(p), f = fract(p);
          f = f*f*(3.0-2.0*f);
          return mix(mix(grainHash(i), grainHash(i+vec2(1.,0.)), f.x),
                     mix(grainHash(i+vec2(0.,1.)), grainHash(i+1.), f.x), f.y);
        }
      ` + shader.fragmentShader.replace('#include <map_fragment>', `
        vec3 surfaceNormal = normalize(cross(dFdx(coastPoint), dFdy(coastPoint)));
        vec3 weights = pow(abs(surfaceNormal), vec3(5.0));
        weights /= max(dot(weights, vec3(1.0)), 0.001);
        vec3 stoneColor = texture2D(coastStone, coastPoint.zy * .22).rgb * weights.x +
                          texture2D(coastStone, coastPoint.xz * .22).rgb * weights.y +
                          texture2D(coastStone, coastPoint.xy * .22).rgb * weights.z;
        stoneColor *= vec3(.66, .74, .84);
        float pattern = grain(coastPoint.xz * .83) * .64 + grain(coastPoint.xz * 14.) * .36;
        vec3 grass = mix(vec3(.058,.092,.020), vec3(.25,.28,.055), pattern);
        float cover = smoothstep(.55,.86,surfaceNormal.y + (pattern-.5)*.20) *
                      smoothstep(3.3,5.0,coastPoint.y);
        diffuseColor.rgb *= mix(stoneColor, grass, cover);
      `);
    };
    material.customProgramCacheKey = () => 'cliff-coastal-surface-v1';
  }
  for (const material of bark) {
    material.color = new T.Color(0x5c432b);
    material.vertexColors = false;
  }
}
